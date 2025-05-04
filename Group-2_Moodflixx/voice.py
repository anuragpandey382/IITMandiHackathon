from typing import List, Dict, Optional, Union  # add Union to existing import
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from CStrings.iterative import iterative_cstring_gen
from KnowledgeBase.knowledge_base import Get_knowledge_Base_Lang
from langchain.schema import Document
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
import streamlit as st
import sqlite3
import asyncio
import httpx
from datetime import datetime
import os
import webbrowser
from urllib.parse import urlencode
import speech_recognition as sr
# import content

# --------------------
# Configuration
# --------------------

load_dotenv()
vs = Get_knowledge_Base_Lang()  # instantiate vector search (LangChain knowledge base)

# Load secrets - Ensure these are set in Streamlit Cloud or your .streamlit/secrets.toml
GOOGLE_CLIENT_ID = st.secrets.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8502"  # e.g., "http://localhost:8501" for local dev

# Basic check if secrets are loaded
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not REDIRECT_URI:
    st.error("OAuth secrets not found! Please configure GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and REDIRECT_URI in Streamlit secrets.")
    st.stop()

# --- SQLite Database Setup ---
def init_db():
    conn = sqlite3.connect('movie_recommender.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (email TEXT PRIMARY KEY, name TEXT, created_at TIMESTAMP)''')
    
    # Create watch_history table
    c.execute('''CREATE TABLE IF NOT EXISTS watch_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_email TEXT,
                  movie_id TEXT,
                  movie_name TEXT,
                  year INTEGER,
                  genre TEXT,
                  description TEXT,
                  imdb_rating REAL,
                  added_at TIMESTAMP,
                  FOREIGN KEY (user_email) REFERENCES users(email))''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# --- Initialize User-Specific Session State ---
if "user" not in st.session_state:
    st.session_state.user = None
if "token" not in st.session_state:
    st.session_state.token = None
if "watch_history" not in st.session_state:
    st.session_state.watch_history = []
if "seen_movies" not in st.session_state:
    st.session_state.seen_movies = {}
if 'added_movie_ids' not in st.session_state:
    st.session_state.added_movie_ids = set()

# --------------------
# SQLite Helper Functions
# --------------------

def get_user_watch_history(user_email: str) -> List[Dict]:
    """Gets the user's watch history from SQLite."""
    conn = sqlite3.connect('movie_recommender.db')
    c = conn.cursor()
    c.execute('''SELECT movie_id, movie_name, year, genre, description, 
                 imdb_rating 
                 FROM watch_history WHERE user_email = ?''', (user_email,))
    movies = []
    for row in c.fetchall():
        movies.append({
            'id': row[0],
            'movie_name': row[1],
            'year': row[2],
            'genre': row[3],
            'description': row[4],
            'imdbRating': row[5]
        })
    conn.close()
    return movies

def add_movie_to_watch_history(user_email: str, movie: Dict):
    """Adds a movie to the user's watch history in SQLite."""
    conn = sqlite3.connect('movie_recommender.db')
    c = conn.cursor()
    c.execute('''INSERT INTO watch_history 
                 (user_email, movie_id, movie_name, year, genre, description, 
                 imdb_rating, added_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (user_email, movie['id'], movie['movie_name'], movie['year'],
               movie['genre'], movie['description'], movie['imdbRating'], datetime.now()))
    conn.commit()
    conn.close()

def remove_movie_from_watch_history(user_email: str, movie_id: str):
    """Removes a movie from the user's watch history in SQLite."""
    conn = sqlite3.connect('movie_recommender.db')
    c = conn.cursor()
    c.execute('''DELETE FROM watch_history 
                 WHERE user_email = ? AND movie_id = ?''', (user_email, movie_id))
    conn.commit()
    conn.close()

def create_or_get_user(user_email: str, user_name: str):
    """Creates a new user or gets existing user from SQLite."""
    conn = sqlite3.connect('movie_recommender.db')
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO users (email, name, created_at)
                 VALUES (?, ?, ?)''', (user_email, user_name, datetime.now()))
    conn.commit()
    conn.close()

# --------------------
# OAuth Functions
# --------------------

def get_google_auth_url():
    """Generate Google OAuth URL."""
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

async def get_token(code: str) -> Optional[Dict]:
    """Exchange authorization code for access token."""
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error getting token: {e}")
            return None

async def get_user_info(access_token: str) -> Optional[Dict]:
    """Fetches user info from Google using the access token."""
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            user_dict = response.json()
            return {"email": user_dict.get("email"), "name": user_dict.get("name")}
        except Exception as e:
            st.error(f"An error occurred while fetching user info: {e}")
            return None

def handle_login() -> Optional[Dict]:
    """Handles Google OAuth login and user data loading."""
    if st.session_state.user:
        return st.session_state.user

    # Check for authorization code in URL
    query_params = st.experimental_get_query_params()
    if 'code' in query_params:
        code = query_params['code'][0]
        token = asyncio.run(get_token(code))
        if token:
            st.session_state.token = token
            user_info = asyncio.run(get_user_info(token['access_token']))
            if user_info and user_info.get("email"):
                st.session_state.user = user_info
                user_email = user_info["email"]
                user_name = user_info.get("name", "")

                # Create or get user in SQLite
                create_or_get_user(user_email, user_name)

                # Load watch history
                st.session_state.watch_history = get_user_watch_history(user_email)
                st.session_state.seen_movies = {
                    movie['id']: True for movie in st.session_state.watch_history
                }

                st.rerun()
            else:
                st.error("Could not fetch user information or email from Google. Please try again.")
                st.session_state.token = None
                st.session_state.user = None
        else:
            st.error("Failed to get access token. Please try again.")
            st.session_state.token = None
            st.session_state.user = None
    else:
        # Show login button
        if st.button("Continue with Google"):
            auth_url = get_google_auth_url()
            webbrowser.open(auth_url)
            st.info("Please complete the Google login in your browser and return to this page.")

    return st.session_state.user

def handle_logout():
    """Clears session state for logout."""
    if st.sidebar.button("Logout"):
        for key in ["user", "token", "watch_history", "seen_movies", "added_movie_ids"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# --------------------
# Recommendation Logic (Placeholder)
# --------------------
class MovieRecommendation(BaseModel):
    title: str = Field(..., description="Movie title")
    year: Union[str, int]
    genre: str
    director: str
    reason: str = Field(..., description="Why this movie is recommended")

class FinalMovieList(BaseModel):
    recommendations: List[MovieRecommendation]

def build_context_string(movies: List[dict]) -> str:
    """Format candidate movies into a single context string for the LLM."""
    context = ""
    for i, movie in enumerate(movies, 1):
        context += f"""
            Movie {i}:
            Title: {movie.get("Title", "N/A")}
            Year: {movie.get("Year", "N/A")}
            Genre: {movie.get("Genre", "N/A")}
            Director: {movie.get("Director", "N/A")}
            Cast: {movie.get("Cast", "N/A")}
            Metascore: {movie.get("Metascore", "N/A")}
            Description: {movie.get("Full Description", "N/A")}
        """
    return context

prompt_template = PromptTemplate.from_template(
    """
You are a movie assistant. Given the following movie candidates, select the best {k} movie recommendations for the user.

Provide your response in the following JSON format:
```json
{{
  "recommendations": [
    {{
      "title": "...",
      "year": ...,
      "genre": "...",
      "director": "...",
      "reason": "..."
    }}
  ]
}}
Movies:
{context}
"""
)

def get_top_k_movies_llm(combined_movies: List[dict], k: int = 5) -> dict:
    """Use LLM (ChatGroq) to select the top k movie recommendations from candidates."""
    # Build the context string for LLM prompt
    context_str = build_context_string(combined_movies)
    prompt = prompt_template.invoke({"context": context_str, "k": k})
    
    # Call the LLM (ChatGroq model) with the prompt
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
    response = llm.invoke(prompt)
    
    # Parse the LLM's JSON response using the Pydantic model
    try:
        start = response.content.find("{")
        end = response.content.rfind("}") + 1
        json_content = response.content[start:end]
        parsed = FinalMovieList.model_validate_json(json_content)
        return parsed.model_dump()
    except Exception as e:
        # Return error info if parsing fails
        return {"error": str(e), "raw_response": response.content}

def get_recommendations(mood_answers: List[str], user_email: str) -> List[Dict]:
    """Generate movie recommendations based on the user's mood answers."""
    # Map the mood_answers list to a user_data dictionary for prompt generation
    keys = ["mood", "runtime", "age", "genre", "language", "year", "actor"]
    user_data = {keys[i]: mood_answers[i] if i < len(mood_answers) else "" 
                 for i in range(len(keys))}
    
    # 1. Generate characteristic search prompts
    resp = iterative_cstring_gen(user_data, 3, 2)
    
    # 2. Vector similarity search for each prompt
    results = []
    for iterres in resp:
        similar_docs = vs.similarity_search(iterres.prompt, k=1)
        for doc in similar_docs or []:
            md = doc.metadata
            results.append({
                "Title": md.get("original_title", "N/A"),
                "Year": md.get("release_date", "N/A"),
                "Genre": md.get("genres", "N/A"),
                "Director": md.get("director", "N/A"),
                "Cast": md.get("cast", "N/A"),
                "Full Description": doc.page_content,
            })
    if not results:
        return []
    
    # 3. LLM to pick top 5
    top_movies = get_top_k_movies_llm(results, k=5)
    if "error" in top_movies:
        st.error(f"Recommendation generation error: {top_movies['error']}")
        return []
    
    # 4. Extract and annotate with an 'id'
    final_recs = top_movies.get("recommendations", [])
    for idx, rec in enumerate(final_recs):
        # assign a simple unique id (you can customize this)
        rec["id"] = f"rec_{idx}"
    return final_recs


# --------------------
# Streamlit Page Layout
# --------------------

def main():
    st.set_page_config(page_title="Movie Mood Recommender", page_icon="🎥", layout="wide")
    # Apply custom CSS for cinematic theme and improved UI
    st.markdown(
        '''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@600&family=Roboto&display=swap');
            .stApp { background-color: #121212; color: #f0f0f0; }
            html, body { scroll-behavior: smooth; }
            html, body, [data-testid="stAppViewContainer"] { font-family: 'Roboto', sans-serif; }
            h1, h2, h3, h4, h5, h6, .streamlit-expanderHeader { font-family: 'Oswald', sans-serif; }
            [data-testid="stSidebar"] { background-color: #1E1E1E; color: #f0f0f0; }
            [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 { font-family: 'Oswald', sans-serif; color: #fff; }
            .streamlit-expanderHeader { background-color: #333; color: #f0f0f0; }
            .streamlit-expanderContent { background-color: #1f1f1f; color: #f0f0f0; }
            .card { background-color: #262626; padding: 15px; border-radius: 8px; border: 1px solid #444; box-shadow: 0 4px 6px rgba(0,0,0,0.5); margin-bottom: 15px; }
            .card:hover { box-shadow: 0 6px 8px rgba(0,0,0,0.7); }
            .card-title { font-size: 1.1rem; font-weight: bold; margin-bottom: 5px; color: #fff; font-family: 'Oswald', sans-serif; }
            .card-meta { font-size: 0.9rem; color: #ccc; margin-bottom: 5px; }
            .card-description { font-size: 0.9rem; color: #aaa; }
            details summary { cursor: pointer; }
            details summary::-webkit-details-marker { display: none; }
            details summary:after { content: ' ▼'; font-size: 0.8em; color: #ccc; }
            details[open] summary:after { content: ' ▲'; font-size: 0.8em; color: #ccc; }
            [data-testid="stForm"] { background-color: #1f1f1f; padding: 15px; border: 1px solid #444; border-radius: 8px; }
            input[type="text"] { background-color: #333; color: #fff; border: 1px solid #555; }
            input[type="text"]::placeholder { color: #bbb; }
            div.stButton > button { border-radius: 5px; background-color: #444; color: #fff; border: 1px solid #555; padding: 0.4rem 0.8rem; }
            div.stButton > button:hover { background-color: #555; border-color: #666; }
        </style>
        ''',
        unsafe_allow_html=True
    )
    st.title("🎬 Movie Mood Recommender")
    user = handle_login()
    if not user:
        st.warning("Please log in using Google to continue.")
        st.stop()
    st.sidebar.header(f"👋 Welcome, {user.get('name', user.get('email'))}!")
    st.sidebar.write(f"Logged in as: 📧 {user.get('email')}")
    # Option 1: Using link_button (Streamlit 1.12.0+)
    # st.link_button("Home", "MoodHandling/mood_handling_voice.py", icon="🏠")
    # st.markdown("[🏠 Home](./pages/voice.py)")
    handle_logout()

    st.markdown("---")

    # --- Watch History Display Section ---
    with st.expander("🍿 View/Manage Your Watch History"):
        if not st.session_state.watch_history:
            st.info("Your watch history is empty. Add movies from recommendations to build your history.")
        else:
            st.subheader("📽️ Your Watched Movies")
            num_history_cols = 4
            history_cols = st.columns(num_history_cols)
            
            for idx, movie in enumerate(st.session_state.watch_history):
                col_index = idx % num_history_cols
                with history_cols[col_index]:
                    st.markdown(
                    # Display each watched movie in a styled card
                        f"""
                        <div class="card">
                            <p class="card-title">{movie.get('movie_name', 'N/A')} ({movie.get('year', 'N/A')})</p>
                            <p class="card-meta"><strong>Genre:</strong> {movie.get('genre', 'N/A')}</p>
                            <p class="card-meta"><strong>Rating:</strong> {movie.get('imdbRating', 'N/A')} ⭐</p>
                            <details><summary>Description</summary><div class="card-description">{movie.get('description', 'N/A')}</div></details>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button("🗑️ Remove", key=f"remove_{movie['id']}_{idx}"):
                        try:
                            remove_movie_from_watch_history(user['email'], movie['id'])
                            st.session_state.watch_history.pop(idx)
                            if 'seen_movies' in st.session_state:
                                st.session_state.seen_movies.pop(movie['id'], None)
                            st.success(f"Removed '{movie.get('movie_name', 'Movie')}' from history.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to remove movie: {e}")

    st.markdown("---")

    # --- Mood Questionnaire and Recommendations Section ---
    st.subheader("🎭 Get Movie Recommendations Based on Your Mood")
    st.caption("Answer these questions to help us find movies matching your mood.")
    duration = st.sidebar.slider("Recording Duration (seconds)", min_value=5, max_value=60, value=20, step=5)
    
    transcription = ""

    action = st.button("▶️ Start Recording")
    if action:
        r = sr.Recognizer()
        chunks = []
        timer_placeholder = st.empty()
        with sr.Microphone() as mic:
            r.adjust_for_ambient_noise(mic, duration=15)
            for sec in range(duration, 0, -1):
                timer_placeholder.info(f"🔴 Recording... {sec} seconds left")
                chunk = r.record(mic, duration=1)
                chunks.append(chunk)
            timer_placeholder.success("⏹️ Recording complete!")

        # Combine audio chunks
        sample_rate = chunks[0].sample_rate
        sample_width = chunks[0].sample_width
        raw_data = b"".join(chunk.get_raw_data() for chunk in chunks)
        full_audio = sr.AudioData(raw_data, sample_rate, sample_width)

        # Transcribe
        try:
            with st.spinner("📝 Transcribing..."):
                transcription = r.recognize_google(full_audio)
            st.subheader("📝 Transcription")
            st.write(transcription)
        except Exception as e:
            st.error(f"Transcription Error: {e}")
            st.stop()

    submit_button = True
    mood_answers: List[str] = ["" , "" , "" , "" , "" , "" , ""]  # Placeholder for mood answers
    mood_answers[0] = transcription

    if submit_button:
        st.session_state.added_movie_ids = set()

        if not any(mood_answers):
            st.warning("Please answer at least one question to get recommendations.")
        else:

            with st.spinner("Generating recommendations based on your mood..."):
                movies = get_recommendations(mood_answers, user['email'])
            
            st.session_state.recommendations = movies
            st.session_state.show_recommendations = True

    if st.session_state.get('show_recommendations', False):
        movies = st.session_state.recommendations
        st.markdown("---")
        if movies:
            st.subheader("🎯 Here are some movies tailored to your mood:")

            history_ids = {m.get('id') for m in st.session_state.watch_history if m.get('id')}
            unwatched_movies = [m for m in movies if m.get('id') not in history_ids]
            filtered_movies = [m for m in unwatched_movies if m.get('id') not in st.session_state.added_movie_ids]

            if not filtered_movies:
                st.info("No new recommendations match your criteria, or you've already seen/added them all from this batch!")
            else:
                num_rec_cols = 3
                rec_cols = st.columns(num_rec_cols)

                # Initialize selected movies in session state if not exists
                if 'selected_movies' not in st.session_state:
                    st.session_state.selected_movies = set()

                # Track current selections
                current_selections = set()

                for idx, movie in enumerate(filtered_movies):
                    with rec_cols[idx % num_rec_cols]:
                        movie_identifier = movie.get('id')
                        if not movie_identifier:
                            st.warning(f"Recommendation {idx+1} missing 'id'. Skipping.")
                            continue

                        # Styled display for recommended movie title
                        st.markdown(f"<div class='card-title'>{movie.get('title', 'N/A')} ({movie.get('year', 'N/A')})</div>", unsafe_allow_html=True)
                        if movie.get('description'):
                            st.markdown(f"<div class='card-description'><em>{movie['description']}</em></div>", unsafe_allow_html=True)
                        if movie.get('imdbRating'):
                            st.markdown(f"<div class='card-meta'>IMDb Rating: {movie.get('imdbRating')} ⭐ ({movie.get('genre', 'N/A')})</div>", unsafe_allow_html=True)

                        # Initialize checkbox state if not exists
                        checkbox_key = f"add_{movie_identifier}_{idx}"  # Make the key unique
                        if checkbox_key not in st.session_state:
                            st.session_state[checkbox_key] = False

                        # Check if movie is already in watch history
                        is_in_history = any(m['id'] == movie_identifier for m in st.session_state.watch_history)
                        
                        # Create checkbox with improved labels
                        st.checkbox(
                            "✓ In Watch History" if is_in_history else "➕ Add to Watch History",
                            key=checkbox_key,
                            value=st.session_state[checkbox_key]
                        )

                        if st.session_state.get(checkbox_key, False):
                            current_selections.add(movie_identifier)
                        else:
                            current_selections.discard(movie_identifier)

                # Review/Finalize Button
                review_selections = st.button("✅ Add Selected to Watch History")

                if review_selections:
                    added_count = 0
                    failed_movies = []
                    for idx, movie in enumerate(filtered_movies):
                        movie_identifier = movie.get('id')
                        checkbox_key = f"add_{movie_identifier}_{idx}"
                        if st.session_state.get(checkbox_key, False):
                            movie_to_add = {
                                'id': movie_identifier,
                                'movie_name': movie.get('title'),
                                'year': movie.get('year'),
                                'genre': movie.get('genre'),
                                'description': movie.get('description'),
                                'imdbRating': movie.get('imdbRating'),
                            }
                            try:
                                add_movie_to_watch_history(user['email'], movie_to_add)
                                st.session_state.watch_history.append(movie_to_add)
                                if 'seen_movies' in st.session_state:
                                    st.session_state.seen_movies[movie_identifier] = True
                                added_count += 1
                                st.session_state[checkbox_key] = False  # Uncheck after adding
                            except Exception as e:
                                failed_movies.append(movie.get('title', 'Unknown Movie'))
                                st.error(f"Failed to add movie '{movie.get('title')}': {e}")

                    if added_count > 0:
                        st.success(f"✅ Successfully added {added_count} movie(s) to your watch history!")
                        if failed_movies:
                            st.warning(f"⚠️ Failed to add the following movies: {', '.join(failed_movies)}")
                        st.rerun()

        else:
            st.error("Sorry, we couldn't find any recommendations at this time. Please try again later.")

if __name__ == "__main__":
    main()