from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END, add_messages
from langgraph.checkpoint.memory import MemorySaver
import pandas as pd
import os
import json
import ast
import pickle
import torch
from dotenv import load_dotenv
from pydantic import BaseModel as PydanticBaseModel, Field
from typing import List, Optional, Dict, Any, TypedDict, Annotated
import re

from langchain_community.vectorstores import FAISS
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from fastapi import FastAPI 

load_dotenv()

class MovieRecommendation(PydanticBaseModel):
    title: str = Field(description="The title of the movie")
    imdb_rating: Optional[float] = Field(description="IMDb rating of the movie (0-10)", default=None)
    description: Optional[str] = Field(description="Brief description of the movie", default=None)
    year: Optional[int] = Field(description="Year the movie was released", default=None)
    runtime: Optional[int] = Field(description="Runtime in minutes", default=None)

class MovieRecommendations(PydanticBaseModel):
    movies: List[MovieRecommendation] = Field(description="List of recommended movies")
    response_text: str = Field(description="The original LLM response text")

class MovieRecState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    context: Optional[List[Document]]
    query: Optional[str]
    response: Optional[str]
    retrieval_type: str 
    web_results: Optional[List[Dict[str, Any]]]
    collected_mood: Optional[str]
    collected_genre: Optional[str]
    collected_subgenre: Optional[str]
    collected_length: Optional[str]
    collected_similar_movies: Optional[str]  # Changed from directors to similar movies
    collected_actors: Optional[str]     
    structured_movies: Optional[Dict[str, Any]]  # New field for structured movie data

class ChatRequest(PydanticBaseModel):
    query: str
    thread_id: str 

class MovieData(PydanticBaseModel):
    title: str
    imdb_rating: Optional[float] = None
    year: Optional[int] = None
    description: Optional[str] = None
    runtime: Optional[int] = None

class ChatResponse(PydanticBaseModel):
    response: str
    movies: List[MovieData] = []
    next_question: Optional[str] = None  # Added field for the next question
    retrieved_documents: Optional[List[Dict[str, Any]]] = []  # Add this field for document metadata

device = "cuda" if torch.cuda.is_available() else "cpu"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": device},
    encode_kwargs={"normalize_embeddings": True},
)

def create_vector_db(csv_path, faiss_index_path, pickle_path):
    if os.path.exists(faiss_index_path) and os.path.exists(pickle_path):
        try:
            with open(pickle_path, "rb") as f:
                stored_docs = pickle.load(f)
            vectordb = FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)
            return vectordb
        except Exception as e:
            print(f"Error loading existing vector DB: {e}")

    df = pd.read_csv(csv_path)
    documents = []
    for idx, row in df.iterrows():
        try:
            # --- Robust Genre Parsing --- 
            genres_raw = row.get('genres') # Use .get() for safety
            genres_list = []
            if pd.isna(genres_raw):
                genres = "N/A"
            elif isinstance(genres_raw, str):
                try:
                    # Attempt safe evaluation first
                    evaluated = ast.literal_eval(genres_raw)
                    if isinstance(evaluated, list):
                        genres_list = [str(g).strip() for g in evaluated] # Ensure items are strings
                    elif isinstance(evaluated, str): # Handle case like '"Action"'
                         genres_list = [evaluated.strip()]
                    else:
                         genres_list = [str(evaluated).strip()] # Handle other literals
                except (ValueError, SyntaxError):
                    # Fallback: Treat as comma-separated string
                    genres_list = [g.strip() for g in genres_raw.split(',') if g.strip()]
                genres = ", ".join(genres_list) if genres_list else "N/A"
            elif isinstance(genres_raw, list): # Handle if it's already a list somehow
                 genres_list = [str(g).strip() for g in genres_raw]
                 genres = ", ".join(genres_list) if genres_list else "N/A"
            else:
                # Handle other unexpected types
                genres = "N/A"
            # --- End Robust Genre Parsing ---
            
            # --- Safely Access Row Data ---
            movie_id = row.get('id', f'MISSING_ID_{idx}') # Use index as fallback ID
            title = row.get('title', 'Unknown Title')
            year = row.get('year', 'Unknown Year')
            rating = row.get('rating', 'N/A')
            plot_summary = row.get('plot_summary', 'No summary available.')
            # --- End Safe Access ---
            
            metadata = {
                "source": f"{movie_id}-{title}",
                "title": title,
                "year": year,
                "genres": genres, # Already handled above
                "rating": rating
            }
            page_content = f"Title: {title}\nYear: {year}\nGenres: {genres}\nRating: {rating}\nPlot Summary: {plot_summary}"
            documents.append(Document(page_content=page_content, metadata=metadata))
        except Exception as e:
            print(f"Error processing row {idx}: {e}")
    
    if not documents:
        print("No documents were created from the CSV.")
        return None

    vectordb = FAISS.from_documents(documents, embeddings)
    vectordb.save_local(faiss_index_path)
    with open(pickle_path, "wb") as f:
        pickle.dump(documents, f)
    return vectordb

CSV_PATH = "data\processed\processed_movies.csv"
FAISS_INDEX_PATH = "faiss_index"
PICKLE_PATH = "documents.pkl"
vector_db = create_vector_db(CSV_PATH, FAISS_INDEX_PATH, PICKLE_PATH)

def get_retriever(k_value=7):
    if vector_db is None:
        raise ValueError("Vector DB is not initialized. Cannot create retriever.")
    return vector_db.as_retriever(search_kwargs={"k": k_value})

groq_api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(temperature=0, groq_api_key=groq_api_key, model_name="llama3-70b-8192")
tavily_tool = TavilySearchResults(max_results=5)

QUERY_ANALYZER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert query analyzer. Your task is to determine the type of retrieval required for a user's movie query."
            "Analyze the user's message and classify it into one of the following categories based ONLY on the user's explicit request:"
            "'semantic' - For queries asking for movies based on plot similarity, themes, mood, or general descriptions (e.g., 'movies like Inception', 'uplifting films')."
            "'keyword' - For queries asking for movies based on specific factual criteria like actors, directors, genres, titles, or years (e.g., 'movies starring Tom Hanks', 'sci-fi movies from the 90s', 'films directed by Nolan')."
            "'none' - For greetings, conversational fillers, or questions not related to movie recommendations (e.g., 'hello', 'how are you?', 'tell me a joke')."
            "Respond ONLY with 'semantic', 'keyword', or 'none'."
        ),
        ("human", "{question}"),
    ]
)

analyzer_chain = QUERY_ANALYZER_PROMPT | llm | StrOutputParser()

def analyze_query(state: MovieRecState) -> Dict:
    if not state["messages"]:
        return {"retrieval_type": "none", "query": None}
    
    last_message = state["messages"][-1]
    if not isinstance(last_message, HumanMessage):
        return {"retrieval_type": "none", "query": None}
        
    user_question = last_message.content
    retrieval_type = analyzer_chain.invoke({"question": user_question})
    return {"retrieval_type": retrieval_type.strip().lower(), "query": user_question}

def adaptive_retrieval(state: MovieRecState) -> Dict:
    query = state.get("query")
    current_retrieval_type = state.get("retrieval_type", "none") 
    retrieved_docs = []

    if query and current_retrieval_type != "none":
        try:
            retriever = get_retriever() 
            retrieved_docs = retriever.invoke(query)
        except Exception as e:
            print(f"Error during FAISS retrieval: {e}")
            
    return {"context": retrieved_docs}

def web_search(state: MovieRecState) -> Dict:
    query = state.get("query")
    web_results = []
    if query:
        try:
            web_results = tavily_tool.invoke({"query": query})
        except Exception as e:
            print(f"Error during Tavily web search: {e}")
    
    return {"web_results": web_results}

def parse_user_preferences(state: MovieRecState) -> Dict:
    """
    Parse user messages to extract and update preferences from any message,
    not just in response to specific questions.
    """
    messages = state['messages']
    
    # Get current state values with defaults
    collected_mood = state.get("collected_mood")
    collected_genre = state.get("collected_genre") 
    collected_subgenre = state.get("collected_subgenre")
    collected_length = state.get("collected_length")
    collected_similar_movies = state.get("collected_similar_movies")
    collected_actors = state.get("collected_actors")
    
    # Only process if we have at least one message with user input
    if not messages or not isinstance(messages[-1], HumanMessage):
        return {}
    
    # Get the latest user message and our previous message if exists
    latest_user_msg = messages[-1].content
    prev_ai_msg = ""
    
    # Find the most recent AI message if it exists
    for msg in reversed(messages[:-1]):
        if isinstance(msg, AIMessage):
            prev_ai_msg = msg.content.lower()
            break
    
    updates = {}
    
    # Enhanced batch preference parser - looks for all preferences at once
    batch_parse_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a preference parser specialized in movie recommendations.
        Analyze the user's message and extract ALL preferences mentioned for watching movies.
        Format your response as a valid JSON object with ONLY these keys: "mood", "genre", "subgenre", "length", "similar_movies", "actors".
        The "similar_movies" field should contain movie titles the user mentions liking or wanting something similar to.
        Use null for any preference not found in the message.
        Example response: {"mood": "relaxing", "genre": "comedy", "subgenre": null, "length": "short", "similar_movies": "The Matrix", "actors": null}
        """),
        ("human", """User message: {user_msg}
        Previous assistant message (if any): {prev_ai_msg}
        
        Extract ALL movie preferences from this message. Return ONLY the JSON object.
        """)
    ])
    
    # If this is the first turn or if the message seems to contain multiple preferences,
    # use the batch parser to try to extract everything at once
    if len(messages) <= 2 or len(latest_user_msg.split()) > 15:
        try:
            # Fix the error by ensuring all variables exist
            batch_parse_chain = batch_parse_prompt | llm | StrOutputParser()
            json_response = batch_parse_chain.invoke({
                "user_msg": latest_user_msg,
                "prev_ai_msg": prev_ai_msg
            })
            
            try:
                parsed_prefs = json.loads(json_response)
                print(f"Batch parsed preferences: {parsed_prefs}")
                
                # Only update preferences that aren't already set
                if not collected_mood and parsed_prefs.get("mood"):
                    updates["collected_mood"] = parsed_prefs["mood"]
                    print(f"Updated mood from batch parser: {parsed_prefs['mood']}")
                
                if not collected_genre and parsed_prefs.get("genre"):
                    updates["collected_genre"] = parsed_prefs["genre"]
                    print(f"Updated genre from batch parser: {parsed_prefs['genre']}")
                    
                if not collected_subgenre and parsed_prefs.get("subgenre"):
                    updates["collected_subgenre"] = parsed_prefs["subgenre"]
                    print(f"Updated subgenre from batch parser: {parsed_prefs['subgenre']}")
                    
                if not collected_length and parsed_prefs.get("length"):
                    updates["collected_length"] = parsed_prefs["length"]
                    print(f"Updated length from batch parser: {parsed_prefs['length']}")
                    
                if not collected_similar_movies and parsed_prefs.get("similar_movies"):
                    updates["collected_similar_movies"] = parsed_prefs["similar_movies"]
                    print(f"Updated similar movies from batch parser: {parsed_prefs['similar_movies']}")
                    
                if not collected_actors and parsed_prefs.get("actors"):
                    updates["collected_actors"] = parsed_prefs["actors"]
                    print(f"Updated actors from batch parser: {parsed_prefs['actors']}")
                
            except json.JSONDecodeError:
                print("Failed to parse JSON response from batch parser")
                
        except Exception as e:
            print(f"Error in batch preference parsing: {e}")
            # Add this fallback for the first turn
            if len(messages) == 1 and "mood" in str(e):
                # On the first turn with empty conversation, the greeting might be too vague
                # We'll skip parsing rather than trying to force it
                print("First turn detected - skipping batch parsing")
            
    # Use the targeted parser as a fallback for specific preference questions
    if not updates:
        parse_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a preference parser. Extract user preferences from their message based on context.
            Respond ONLY with the extracted value or "null" if not found.
            Do not include any explanation or additional text."""),
            ("human", """Previous AI Message: {prev_ai_msg}
            User Message: {user_msg}
            Looking for: {looking_for}
            
            Extract ONLY the user's {looking_for} preference. Respond with just that value or "null".
            """)
        ])
        
        parse_chain = parse_prompt | llm | StrOutputParser()
        
        # Based on current state, determine what to parse
        try:
            # First collect mood if not present
            if not collected_mood:
                if "mood" in prev_ai_msg or len(messages) <= 2:
                    mood = parse_chain.invoke({
                        "prev_ai_msg": prev_ai_msg,
                        "user_msg": latest_user_msg,
                        "looking_for": "mood"
                    }).strip()
                    
                    if mood.lower() != "null":
                        updates["collected_mood"] = mood
                        print(f"Parsed mood: {mood}")
                        
            # Then collect genre if mood is present but genre isn't
            elif not collected_genre:
                if "genre" in prev_ai_msg or len(messages) <= 2:
                    genre = parse_chain.invoke({
                        "prev_ai_msg": prev_ai_msg,
                        "user_msg": latest_user_msg,
                        "looking_for": "genre"
                    }).strip()
                    
                    if genre.lower() != "null":
                        updates["collected_genre"] = genre
                        print(f"Parsed genre: {genre}")
            
            # Then collect subgenre if mood and genre are present but subgenre isn't            
            elif not collected_subgenre:
                if "subgenre" in prev_ai_msg or len(messages) <= 2:
                    subgenre = parse_chain.invoke({
                        "prev_ai_msg": prev_ai_msg,
                        "user_msg": latest_user_msg,
                        "looking_for": "subgenre"
                    }).strip()
                    
                    if subgenre.lower() != "null":
                        updates["collected_subgenre"] = subgenre
                        print(f"Parsed subgenre: {subgenre}")
                        
            # Collect length if mood, genre, and subgenre are present
            elif not collected_length:
                if "length" in prev_ai_msg or len(messages) <= 2:
                    length = parse_chain.invoke({
                        "prev_ai_msg": prev_ai_msg,
                        "user_msg": latest_user_msg,
                        "looking_for": "length"
                    }).strip()
                    
                    if length.lower() != "null":
                        updates["collected_length"] = length
                        print(f"Parsed length: {length}")
            
            # Collect similar movies if previous preferences are present but similar movies aren't
            elif not collected_similar_movies:
                if "similar" in prev_ai_msg or "like" in prev_ai_msg or len(messages) <= 2:
                    similar_movies = parse_chain.invoke({
                        "prev_ai_msg": prev_ai_msg,
                        "user_msg": latest_user_msg,
                        "looking_for": "similar_movies"
                    }).strip()
                    
                    if similar_movies.lower() != "null":
                        updates["collected_similar_movies"] = similar_movies
                        print(f"Parsed similar movies: {similar_movies}")
                        
            # Finally collect actors if all other preferences are present
            elif not collected_actors:
                if "actor" in prev_ai_msg or len(messages) <= 2:
                    actors = parse_chain.invoke({
                        "prev_ai_msg": prev_ai_msg,
                        "user_msg": latest_user_msg,
                        "looking_for": "actors"
                    }).strip()
                    
                    if actors.lower() != "null":
                        updates["collected_actors"] = actors
                        print(f"Parsed actors: {actors}")
        except Exception as e:
            print(f"Error parsing user preferences: {e}")
    
    return updates

def analyze_initial_input(state: MovieRecState) -> Dict:
    """
    Process the initial user input to extract any preferences mentioned upfront.
    This allows the system to skip steps when preferences are already specified.
    """
    if not state["messages"] or not isinstance(state["messages"][-1], HumanMessage):
        return {}
    
    # For the very first message, add special handling
    if len(state["messages"]) == 1:
        # Get the initial message content
        user_msg = state["messages"][0].content.lower()
        
        # Check if the first message clearly indicates a mood
        mood_keywords = {
            "happy": "happy", 
            "sad": "sad", 
            "excited": "excited", 
            "relaxed": "relaxed", 
            "nostalgic": "nostalgic",
            "romantic": "romantic",
            "scared": "scared",
            "thrilled": "thrilled"
        }
        
        # Direct mood statement detection
        for keyword, mood in mood_keywords.items():
            if f"feeling {keyword}" in user_msg or f"i'm {keyword}" in user_msg or f"im {keyword}" in user_msg:
                print(f"Detected direct mood statement: {mood}")
                return {"collected_mood": mood}
    
    # Get preferences from the first user message using the regular parser
    preference_updates = parse_user_preferences(state)
    
    print(f"Initial preference analysis: {preference_updates}")
    
    # Return the detected preferences
    return preference_updates

FIRST_MOOD_QUESTION = "What mood are you in for a movie today?"

RESPONSE_GENERATOR_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a conversational movie recommendation assistant that adapts to the user's preferences.
Your goal is to gather MOOD, GENRE, SUBGENRE, LENGTH, SIMILAR MOVIES, and ACTORS preferences, but you should skip asking for any preferences that are already collected.

**Dynamic Conversation Flow:**
1. **Analyze State:** Look at what preferences are already collected: `collected_mood`, `collected_genre`, `collected_subgenre`, `collected_length`, `collected_similar_movies`, `collected_actors`.

2. **Determine Next Question:**
    - If `collected_mood` is 'Missing': Ask the standardized mood question.
    - Else if `collected_genre` is 'Missing': Ask the standardized genre question.
    - Else if `collected_subgenre` is 'Missing': Ask the standardized subgenre question.
    - Else if `collected_length` is 'Missing': Ask about length.
    - Else if `collected_similar_movies` is 'Missing': Ask about similar movies.
    - Else if `collected_actors` is 'Missing': Ask about actors.
    - Else: Provide final recommendations based on all collected preferences.

**Guidelines for Each Step:**
- Use the preferences you have to provide 7-10 tailored movie recommendations before asking the next question
- For each movie, include TITLE, IMDb RATING (when available), and a BRIEF (1-2 sentence) justification
- Sort recommendations by IMDb rating when available
- Format recommendations clearly (e.g., using bullet points)
- When multiple preferences are collected at once, acknowledge them and move to the next missing preference

**IMPORTANT: Use these EXACT standardized questions:**
- For mood (if missing): "What mood are you in for a movie today?"
- For genre (if mood collected): "What genre would you like to watch?"
- For subgenre (if genre collected): "Do you have a specific subgenre preference?"
- For length (if subgenre collected): "Do you prefer short, medium, or long movies?"
- For similar movies (if length collected): "Are there any movies you've enjoyed that you'd like to see something similar to?"
- For actors (if similar movies collected): "Are there any specific actors you wish to see in your movie?"

**DO NOT alter these questions or include previously collected preferences in the questions.** 
Always ask the exact standardized questions as specified above.

**Input Context:**
- `messages`: Full conversation history.
- `collected_mood`, `collected_genre`, `collected_subgenre`, `collected_length`, `collected_similar_movies`, `collected_actors`: Preferences gathered so far.
- `{{context}}`: Database results based on latest query/topic.
- `{{web_results}}`: Web results based on latest query/topic.

--- START OF TURN INFO ---
Collected Mood: {collected_mood}
Collected Genre: {collected_genre}
Collected Subgenre: {collected_subgenre}
Collected Length: {collected_length}
Collected Similar Movies: {collected_similar_movies}
Collected Actors: {collected_actors}
Context from internal database (based on latest query/topic):
{{context}}

Web Search Results (based on latest query/topic):
{{web_results}}

output json if your output is intro text + movies , then keep intro text seperate and movies seperate 


"""
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

def extract_movie_data(text: str) -> Dict:
    """Extract structured movie data from LLM response text."""
    movies = []
    
    # Pattern matching for movie titles with ratings, years, etc.
    # Look for patterns like "Movie Title (YYYY)" or "Movie Title - X.Y/10"
    title_pattern = r'[•\-\*\d+\.]\s+(?:\*\*)?([^(\n:]+)(?:\*\*)?(?:\s+\((\d{4})\)|\s+-\s+|\s+:)?'
    rating_pattern = r'(?:rating|scored|rated|scores?):?\s*(?:is\s*)?(\d+\.?\d*)\s*(?:\/\s*10)?'
    
    # Find all potential movie mentions
    lines = text.split('\n')
    current_movie = None
    description_text = ""
    
    for line in lines:
        title_match = re.search(title_pattern, line, re.IGNORECASE)
        if title_match:
            # If we already have a movie being processed, add it to our list
            if current_movie:
                current_movie.description = description_text.strip() if description_text.strip() else None
                movies.append(current_movie)
                description_text = ""
            
            # Start a new movie
            title = title_match.group(1).strip()
            year = None
            if title_match.group(2):
                try:
                    year = int(title_match.group(2))
                except ValueError:
                    pass
                    
            # Check for rating in the same line
            rating_match = re.search(rating_pattern, line, re.IGNORECASE)
            imdb_rating = None
            if rating_match:
                try:
                    imdb_rating = float(rating_match.group(1))
                except ValueError:
                    pass
            
            # Create new movie object
            current_movie = MovieRecommendation(
                title=title,
                year=year,
                imdb_rating=imdb_rating,
                description=None,
                runtime=None
            )
            
            # Any text after the title/rating might be part of description
            title_end = title_match.end()
            if title_end < len(line):
                description_text = line[title_end:].strip()
        
        elif current_movie and line.strip() and not line.startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.')):
            # If the line isn't the start of a new movie, it's probably description text
            description_text += " " + line.strip()
            
            # Check for runtime in the line
            runtime_match = re.search(r'(?:runtime|duration|length):?\s*(?:is\s*)?(\d+)\s*(?:min|minutes)', line, re.IGNORECASE)
            if runtime_match:
                try:
                    current_movie.runtime = int(runtime_match.group(1))
                except ValueError:
                    pass
    
    # Don't forget the last movie
    if current_movie:
        current_movie.description = description_text.strip() if description_text.strip() else None
        movies.append(current_movie)
    
    # Return structured data along with original text
    return {
        "movies": movies,
        "response_text": text
    }

def generate_response(state: MovieRecState) -> Dict:
    # Get context and web results, handle None cases
    context_docs = state.get("context", [])
    context_texts = [doc.page_content for doc in context_docs]
    formatted_context = "\n---\n".join(context_texts) if context_texts else "No internal context found."
    
    web_search_results = state.get("web_results", [])
    formatted_web_results = "\n---\n".join([json.dumps(res) for res in web_search_results]) if web_search_results else "No web search results found."

    # Parse user preferences from conversation
    preference_updates = parse_user_preferences(state)

    # Get conversation history and current collected state (including any updates)
    messages = state['messages']
    collected_mood = preference_updates.get("collected_mood", state.get("collected_mood"))
    collected_genre = preference_updates.get("collected_genre", state.get("collected_genre"))
    collected_subgenre = preference_updates.get("collected_subgenre", state.get("collected_subgenre"))
    collected_length = preference_updates.get("collected_length", state.get("collected_length"))
    collected_similar_movies = preference_updates.get("collected_similar_movies", state.get("collected_similar_movies"))
    collected_actors = preference_updates.get("collected_actors", state.get("collected_actors"))

    # Create the chain for generation
    chain = RESPONSE_GENERATOR_PROMPT | llm | StrOutputParser()
    
    response_text = "Sorry, I encountered an error while generating the response."
    
    try:
        # Invoke the chain, passing current state info
        response_text = chain.invoke({
            "context": formatted_context,
            "web_results": formatted_web_results,
            "messages": messages, # Pass the history
            "collected_mood": collected_mood if collected_mood else "Missing",
            "collected_genre": collected_genre if collected_genre else "Missing",
            "collected_subgenre": collected_subgenre if collected_subgenre else "Missing",
            "collected_length": collected_length if collected_length else "Missing",
            "collected_similar_movies": collected_similar_movies if collected_similar_movies else "Missing",
            "collected_actors": collected_actors if collected_actors else "Missing",
        })
        
        # Process the response to extract structured movie data
        structured_movies = extract_movie_data(response_text)
        # print(f"\n📊 Structured movie data extracted: {len(structured_movies['movies'])} movies")
        # for i, movie in enumerate(structured_movies['movies']):
        #     print(f"{i+1}. {movie.title} " + 
        #           f"({movie.year if movie.year else 'Year unknown'}) " + 
        #           f"⭐ {movie.imdb_rating if movie.imdb_rating else 'Rating unknown'}")
            
    except Exception as e:
        print(f"Error during response generation: {e}")
        structured_movies = {"movies": [], "response_text": response_text}
    
    # Return the new AI message, preference updates, and structured movie data
    return {
        "messages": [AIMessage(content=response_text)], 
        "structured_movies": structured_movies,
        **preference_updates
    }

# --- Graph Nodes: Additional Nodes for Guided Start ---

def check_conversation_start(state: MovieRecState) -> Dict[str, str]:
    """Checks if this is the first user message and returns the next step key."""
    # The input to the graph is the user's query, making the history length 1 initially.
    if len(state['messages']) == 1:
        print("-- First turn, asking for mood.")
        return {"next_step": "ask_mood"}
    else:
        print("-- Continuing conversation, analyzing query.")
        return {"next_step": "analyze"}

def ask_mood_question(state: MovieRecState) -> Dict:
    """Returns the hardcoded first question asking for the user's mood."""
    return {"messages": [AIMessage(content=FIRST_MOOD_QUESTION)]}

# --- Graph Building with Dynamic Preference Handling ---
def build_graph():
    workflow = StateGraph(MovieRecState)
    
    # Add nodes
    workflow.add_node("check_start", check_conversation_start)
    workflow.add_node("ask_mood_initial", ask_mood_question)
    workflow.add_node("analyze_initial_input", analyze_initial_input)  # New node for initial preference detection
    workflow.add_node("analyze_query", analyze_query)
    workflow.add_node("adaptive_retrieval", adaptive_retrieval)
    workflow.add_node("web_search", web_search)
    workflow.add_node("generate_response", generate_response)

    # Set entry point
    workflow.set_entry_point("check_start")

    # Define conditional edges from the start check
    workflow.add_conditional_edges(
        "check_start",
        lambda state: state["next_step"],
        {
            "ask_mood": "analyze_initial_input",  # First check for initial preferences
            "analyze": "analyze_query",
        }
    )
    
    # After analyzing initial input, decide whether to ask for mood or proceed with response
    workflow.add_conditional_edges(
        "analyze_initial_input",
        lambda state: "generate_response" if state.get("collected_mood") else "ask_mood_initial",
        {
            "ask_mood_initial": "ask_mood_initial",
            "generate_response": "adaptive_retrieval",  # Skip mood question if already detected
        }
    )

    # Edge for the hardcoded mood question path
    workflow.add_edge("ask_mood_initial", END)

    # Define edges for the main conversational flow
    workflow.add_edge("analyze_query", "adaptive_retrieval")
    workflow.add_edge("adaptive_retrieval", "web_search")
    workflow.add_edge("web_search", "generate_response")
    workflow.add_edge("generate_response", END)
    
    return workflow

# --- Initialize Graph & Memory ---
workflow = build_graph()

memory = MemorySaver()

if vector_db is None:
    print("CRITICAL ERROR: Vector DB failed to initialize. Exiting.")
    exit() 

# Add debug info about first-turn handling
print("Initializing conversation graph with enhanced first-turn handling")
graph = workflow.compile(checkpointer=memory)

app = FastAPI(
    title="Movie Recommendation Agent API",
    description="API for interacting with a LangGraph-based movie recommendation agent."
)

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    inputs = {"messages": [HumanMessage(content=request.query)]}
    final_response_message = "Sorry, I couldn't generate a response."
    structured_movies = []
    next_question = None  # Initialize the next question field
    retrieved_documents = []  # Initialize retrieved documents list

    try:
        for event in graph.stream(inputs, config=config, stream_mode="values"):
            final_state_event = event

        if final_state_event and 'messages' in final_state_event:
            # Extract document metadata from context if available
            if 'context' in final_state_event and final_state_event['context']:
                for doc in final_state_event['context']:
                    # Extract relevant metadata from each document
                    doc_metadata = {
                        "title": doc.metadata.get("title", "Unknown"),
                        "source": doc.metadata.get("source", "Unknown"),
                        "year": doc.metadata.get("year", None),
                        "genres": doc.metadata.get("genres", "Unknown"),
                        "rating": doc.metadata.get("rating", None),
                        "relevance_score": getattr(doc, "relevance_score", None),
                        # Include a snippet of the content
                        "content_snippet": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    }
                    retrieved_documents.append(doc_metadata)
            
            ai_messages = [msg for msg in final_state_event['messages'] if isinstance(msg, AIMessage)]
            if ai_messages:
                raw_response = ai_messages[-1].content

                # Extract structured movie data if available
                if 'structured_movies' in final_state_event and 'movies' in final_state_event['structured_movies']:
                    movie_dicts = []
                    for movie in final_state_event['structured_movies']['movies']:
                        # Skip entries that are clearly not movies but introductory text
                        if movie.title.lower().startswith(('here are', 'based on', 'considering', 'given your')):
                            continue
                            
                        # Clean the movie title - remove any non-movie text
                        clean_title = movie.title
                        if ':' in clean_title:
                            clean_title = clean_title.split(':')[0].strip()
                        if '-' in clean_title and not clean_title.strip().startswith('-'):
                            clean_title = clean_title.split('-')[0].strip()
                        clean_title = clean_title.split('**')[0] if '**' in clean_title else clean_title
                            
                        # Clean the description to remove any AI questions or prompts
                        clean_description = None
                        movie_year = movie.year  # Default to the extracted year
                                                
                        if movie.description:
                            # Extract year from description if not already set
                            year_match = re.search(r'\((\d{4})\)', movie.description)
                            if not movie_year and year_match:
                                try:
                                    movie_year = int(year_match.group(1))
                                except (ValueError, IndexError):
                                    pass
                            
                            # Split by question mark to remove questions
                            parts = movie.description.split('?')
                            clean_description = parts[0].strip()
                            
                            # Check if there's standard transition text and remove it
                            transition_phrases = [
                                "What genre", "Do you have", "Are there any", 
                                "Do you prefer", "Would you like"
                            ]
                            
                            for phrase in transition_phrases:
                                if phrase in clean_description:
                                    clean_description = clean_description[:clean_description.rfind(phrase)].strip()
                                    
                            # Check for rating pattern in description and extract if available
                            rating_match = re.search(r'Rating:\s*(\d+\.?\d*)', clean_description)
                            clean_imdb_rating = movie.imdb_rating
                            if not clean_imdb_rating and rating_match:
                                try:
                                    clean_imdb_rating = float(rating_match.group(1))
                                except (ValueError, IndexError):
                                    pass
                        
                        # Only add movies with proper titles (not introductory text)
                        if clean_title and not clean_title.isdigit():
                            movie_dicts.append({
                                "title": clean_title,
                                "imdb_rating": clean_imdb_rating,
                                "year": movie_year,
                                "description": clean_description,
                                "runtime": movie.runtime 
                            })
                            
                    structured_movies = movie_dicts

                # Extract the intro text (explanation) and next question separately
                lines = raw_response.split('\n')
                intro_text = []
                extraction_stage = "intro"  # Start by collecting intro text
                
                for line in lines:
                    # If we hit a movie recommendation, we're done with intro
                    if (line.strip().startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.')) or
                        "Rating:" in line or "IMDb" in line or
                        re.search(r'\(\d{4}\)', line) or  # Year pattern (e.g., (2023))
                        re.search(r'[\d\.]+\/10', line)):  # Rating pattern (e.g., 8.5/10)
                        extraction_stage = "movies"
                        continue
                        
                    if extraction_stage == "intro":
                        intro_text.append(line)
                
                # Join the intro lines or use a default message
                if intro_text:
                    final_response_message = '\n'.join(intro_text).strip()
                else:
                    final_response_message = "Here are some movie recommendations based on your preferences."
                
                # Extract the next question from the raw response
                # Look for standardized questions that match our defined patterns
                standard_questions = [
                    "What mood are you in for a movie today?",
                    "What genre would you like to watch?",
                    "Do you have a specific subgenre preference?",
                    "Do you prefer short, medium, or long movies?",
                    "Are there any movies you've enjoyed that you'd like to see something similar to?",
                    "Are there any specific actors you wish to see in your movie?"
                ]
                
                # Check if any standard question appears in the raw response
                for question in standard_questions:
                    if question in raw_response:
                        next_question = question
                        break
                
                # If no standard question found, look for a question mark
                if not next_question:
                    question_matches = re.findall(r'([^.!?]*\?)', raw_response)
                    if question_matches:
                        # Take the last question from the response
                        next_question = question_matches[-1].strip()

    except Exception as e:
        final_response_message = f"An error occurred: {e}"
        print(f"Exception in chat_endpoint: {e}")

    # Create the ChatResponse object with intro text, movies list, and next question
    response_obj = ChatResponse(
        response=final_response_message, 
        movies=structured_movies,
        next_question=next_question,
        retrieved_documents=retrieved_documents  # Include retrieved document metadata
    )
    
    print(f"Response: {response_obj.response}")
    print(f"Movies count: {len(response_obj.movies)}")
    if response_obj.movies:
        for i, movie in enumerate(response_obj.movies[:min(3, len(response_obj.movies))]):
            print(f"  Movie {i+1}: {movie.title} ({movie.year if movie.year else 'Unknown'}) - {movie.imdb_rating}")
    print(f"Documents retrieved: {len(response_obj.retrieved_documents)}")
    print(f"Next question: {response_obj.next_question}")
    
    return response_obj

if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8001)