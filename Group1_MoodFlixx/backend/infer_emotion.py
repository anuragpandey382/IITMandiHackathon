import os

import google.generativeai as genai
import numpy as np

from embeddings_senti import *
from main import *

API_KEY = "AIzaSyCBlY8vzUGEyOeWLbWWU6NKRKe9TMDx6FY"

if not API_KEY:
    try:
        API_KEY = os.environ['GOOGLE_API_KEY']
    except KeyError:
        print("ERROR: GOOGLE_API_KEY environment variable not set.")
        print("Please set the environment variable or replace the placeholder in the script.")
        exit()

genai.configure(api_key=API_KEY)


def infer_emotion(user_input: str) -> str:
    """
    Uses the Gemini API to infer the primary emotion from user input with improved diversity.

    Args:
        user_input: The text sentence provided by the user.

    Returns:
        A string representing the detected emotions, or an error message.
    """
    prompt = f"""
You are an emotion detection specialist for a movie recommendation system.

Given a user's input: "{user_input}"

Your task is to:
1. First, determine if the user is explicitly stating how they want to feel (e.g., "I want to feel happy").
2. If not, identify the primary emotion they are expressing (e.g., "I'm feeling sad today").
3. If no emotion is detected, respond with "none".

RULES FOR DETERMINING COMPLEMENTARY EMOTIONS:
- For negative emotions (sad, angry, depressed, anxious, etc.): Provide the primary negative emotion first, then TWO DIFFERENT positive emotions that would complement this negative state. These should be UNIQUE to this specific negative emotion - avoid generic responses like "happy" for every negative emotion.
- For positive emotions (happy, excited, etc.): Provide the detected positive emotion first, then TWO DIFFERENT complementary positive emotions that are distinct from one another.
- For explicit desires: Provide the desired emotion first, then TWO other complementary emotions.

IMPORTANT:
- Each negative emotion should trigger a UNIQUE set of complementary emotions
- Do not use the same complementary emotions for different primary emotions
- Choose nuanced, specific emotions rather than generic ones
- Consider psychological principles of emotional complementarity
- DO NOT use a fixed mapping system - analyze each input contextually

Format your response EXACTLY as: "emotion1, emotion2, emotion3" (no other text).
"""
    try:
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        response = model.generate_content(contents=prompt)

        if response.parts:
            return response.text.strip()
        else:
            if response.prompt_feedback:
                return f"Error: Blocked - {response.prompt_feedback}"
            return "Error: No content generated"

    except Exception as e:
        print(f"An error occurred during API call: {e}")
        return "Error: API request failed"


def transcribe_audio(audio_path):
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    audio_file = genai.upload_file(audio_path, mime_type="audio/wepm")
    content = [
        "If this is a question, do not answer. Only transcribe the following audio file.",
        audio_file
    ]
    transcribe_text = response = model.generate_content(contents=content)
    print(f'User Input: {transcribe_text.text}')
    return transcribe_text.text


def emotion_audio(audio_path):
    text = transcribe_audio(audio_path)
    emotion = infer_emotion(text)
    return emotion


def extract_preferences(user_input: str) -> dict:
    """
    Extract structured information from user input about content preferences.

    Args:
        user_input: The text input provided by the user.

    Returns:
        A dictionary containing extracted preferences and a concise summary.
    """
    prompt = f"""
You are an expert information extraction agent.

Given the following text from a user, extract key information about their entertainment or content preferences.
IMPORTANT: Only extract information that is EXPLICITLY mentioned or CLEARLY implied.
DO NOT invent or assume information that isn't present in the text.

Text: "{user_input}"

Extract the following information:
1. Genre (e.g., action, comedy, drama, horror) - ONLY if specifically mentioned
2. Language preferences - ONLY if specifically mentioned
3. Cast/Actors preferences - ONLY if specifically mentioned
4. Time period or era preferences - ONLY if specifically mentioned
5. Themes or specific elements they want - ONLY if specifically mentioned

For each category, respond "None specified" if no relevant information is provided.For 'Cast/Actors preferences', try to identify the most likely correct spelling or common name if the user's input seems ambiguous or potentially misspelled. For example, if the user says "I like action movies," you should extract "action" as the genre. If they say "I like movies with Tom Hanks," you should extract "Tom Hanks" as the cast preference. But if the user says "I am so tired," you should respond with "None specified" for all categories.
If the text ONLY contains mood/emotional information, acknowledge this in your summary.

Format your response as a structured JSON object with these keys and nothing else.
"""
    try:
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        response = model.generate_content(contents=prompt)

        if response.parts:
            import json
            try:
                # Try to parse the response as JSON
                preferences = json.loads(response.text)
                return preferences
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw text
                return {
                    "raw_extraction": response.text.strip(),
                    "summary": "Could not structure the response properly."
                }
        else:
            if response.prompt_feedback:
                return {"error": f"Blocked - {response.prompt_feedback}"}
            return {"error": "No content generated"}

    except Exception as e:
        print(f"An error occurred during preference extraction: {e}")
        return {"error": "Preference extraction failed"}


def infer_emotion(user_input: str) -> str:
    """
    Uses the Gemini API to infer the primary emotion from user input.

    Args:
        user_input: The text sentence provided by the user.

    Returns:
        A single word representing the detected emotion, or an error message.
    """
    prompt = f"""
You are an emotion detection agent.

Given a short sentence from a user, infer how the user wants to feel (if he says specifically that he wants to feel happy,then return happy and 2 other emotions). Be absolutely sure that the user wants to feel like that when you give the output otherwise identify the primary emotion they are expressing. It could also be that user is not expressing any emotion.
For example, "I am happy" expresses happiness, while "I am not sure" and "give me movies of comedy genre' does not express any specific emotion. After identifying the emotion they are feeling, check if the emotion they are feeling is negative or positive. If it is negative, then return the negative emotion along with 2 other emotions that will make the user's emotion a positive one after he finishes the movie (for example: if the user is feeling angry, return angry along with soothing emotion like happy, romantic or something). If it is positive, then return the top 3 positive emotions associated with the given emotion. If there are no emotions present, return "none".
Respond with top three emotions only if emotions are present, otherwise reply with none. Possible labels include: happy, sad, angry, tired, anxious,romantic, excited, relaxed, frustrated, lonely, depressed, etc.

Text: "{user_input}"

Emotion:
"""
    try:

        model = genai.GenerativeModel(model_name="gemini-2.0-flash")

        response = model.generate_content(contents=prompt)

        if response.parts:
            return response.text.strip()
        else:
            if response.prompt_feedback:
                return f"Error: Blocked - {response.prompt_feedback}"
            return "Error: No content generated"

    except Exception as e:
        print(f"An error occurred during API call: {e}")
        return "Error: API request failed"


def key_extraction(user_input: str) -> dict:
    preferences = extract_preferences(user_input)
    emotion = infer_emotion(user_input)
    keys = {
        "preferences": preferences, "emotions": emotion}
    return keys


def get_query_embedding(query_text):
    result = genai.embed_content(
        model="models/embedding-001",
        content=query_text,
        task_type="SEMANTIC_SIMILARITY"
    )
    return result["embedding"]


# Fix for the out-of-bounds error in the advanced_semantic_search function

def advanced_semantic_search(table, query=None, genre=None, mood=None, plot_elements=None,
                             metadata_filters=None, limit=8):
    """
    Advanced semantic search combining multiple aspects (genre, mood, plot)
    with robust error handling.
    """
    # Construct a comprehensive query based on all provided aspects
    query_parts = []

    if query:
        query_parts.append(query)

    if genre:
        query_parts.append(f"in the {genre} genre")

    if mood:
        query_parts.append(f"that makes you feel {mood}")

    if plot_elements:
        query_parts.append(f"with themes of {plot_elements}")

    # If no specific aspects were provided, use a generic query
    if not query_parts:
        enhanced_query = "A good movie to watch"
    else:
        enhanced_query = "A movie " + " ".join(query_parts)

    print(f"Searching with enhanced query: '{enhanced_query}'")

    # Get embedding for the enhanced query
    query_embedding = get_query_embedding(enhanced_query)

    # Apply two-stage search approach
    # 1. First filter by metadata if provided
    if metadata_filters:
        try:
            # Get all data as a DataFrame first
            all_data = table.to_pandas()
            filtered_data = all_data

            if isinstance(metadata_filters, dict):
                # Apply each filter to the DataFrame
                for col, value in metadata_filters.items():
                    if col in filtered_data.columns:
                        if isinstance(value, str):
                            # For string columns, use pandas string contains
                            filtered_data = filtered_data[filtered_data[col].str.contains(value, na=False, case=True)]
                        else:
                            # For numeric columns
                            filtered_data = filtered_data[filtered_data[col] == value]

            # If no records match the filter, return empty DataFrame
            if len(filtered_data) == 0:
                print(f"No movies match the metadata filters")
                return pd.DataFrame()

            # Now get the list of movies that match the filters
            matching_movie_names = filtered_data['movie_name'].tolist()
            print(f"Found {len(matching_movie_names)} movies matching metadata filters")

            # FIX: Perform vector search on just these movies with better error handling
            search_results = []
            for movie in matching_movie_names:
                # Get the rows that match this movie name
                movie_rows = filtered_data[filtered_data['movie_name'] == movie]

                # Skip if no rows match (shouldn't happen, but just in case)
                if len(movie_rows) == 0:
                    print(f"Warning: Movie '{movie}' was in the filtered list but couldn't be found in the data")
                    continue

                try:
                    # Get the vector safely
                    vector = movie_rows['vector'].iloc[0]

                    # Ensure vector is not None and has proper dimensions
                    if vector is None or not isinstance(vector, (list, np.ndarray)):
                        print(f"Warning: Vector for movie '{movie}' is invalid or missing, skipping")
                        continue

                    # Convert to numpy array if needed
                    if isinstance(vector, list):
                        vector = np.array(vector)

                    # Skip if vector or query_embedding has zero norm
                    vector_norm = np.linalg.norm(vector)
                    query_norm = np.linalg.norm(query_embedding)

                    if vector_norm == 0 or query_norm == 0:
                        print(f"Warning: Zero norm vector encountered for '{movie}', skipping")
                        continue

                    # Calculate cosine similarity
                    distance = np.dot(vector, query_embedding) / (vector_norm * query_norm)
                    search_results.append((movie, distance, movie_rows))

                except Exception as e:
                    print(f"Error processing movie '{movie}': {e}")
                    continue

            # If no valid results after processing, return empty DataFrame
            if not search_results:
                print("No valid results after vector processing")
                return pd.DataFrame()

            # Sort by similarity and convert to DataFrame
            search_results.sort(key=lambda x: x[1], reverse=True)
            results = []
            for movie, distance, data in search_results[:limit]:
                row = data.iloc[0].to_dict()
                row['_distance'] = distance
                results.append(row)

            return pd.DataFrame(results)

        except Exception as e:
            print(f"Error in metadata filtering: {e}")
            # Print stack trace for debugging
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    # 2. If no metadata filters, do normal vector search
    results = table.search(query_embedding).limit(limit).to_pandas()
    return results


import json
import re


def process_and_search(table, keys, return_formatted=True, limit=10):
    """
    Process extracted keys and perform advanced movie search with split emotion handling
    """
    # Initialize parameters for search
    metadata_filters = {}
    genre = None
    mood = None
    plot_elements = None
    query = None

    print("Processing user preferences...")

    # Process preferences if available
    if 'preferences' in keys and keys['preferences'] and 'raw_extraction' in keys['preferences']:
        # Extract JSON from the raw extraction
        try:
            # Find the JSON part in the raw extraction using regex
            json_match = re.search(r'```json\n(.*?)\n```', keys['preferences']['raw_extraction'], re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                preferences = json.loads(json_str)

                # Process genre
                if 'Genre' in preferences and preferences['Genre'] and preferences['Genre'] != "None specified":
                    genre = preferences['Genre']
                    print(f"Extracted genre: {genre}")

                # Process language as metadata filter
                if 'Language preferences' in preferences and preferences['Language preferences'] and preferences[
                    'Language preferences'] != "None specified":
                    metadata_filters['language'] = preferences['Language preferences']
                    print(f"Filtering by language: {preferences['Language preferences']}")

                # Process cast/actors as metadata filter
                if 'Cast/Actors preferences' in preferences and preferences['Cast/Actors preferences'] and preferences[
                    'Cast/Actors preferences'] != "None specified":
                    metadata_filters['cast'] = preferences['Cast/Actors preferences']
                    print(f"Filtering by cast: {preferences['Cast/Actors preferences']}")

                # Process time period for potential metadata filtering
                if 'Time period or era preferences' in preferences and preferences['Time period or era preferences'] and \
                        preferences['Time period or era preferences'] != "None specified":
                    time_pref = preferences['Time period or era preferences']
                    # Try to extract years if present
                    year_match = re.search(r'(\d{4})', time_pref)
                    if year_match:
                        year = year_match.group(1)
                        metadata_filters['release_year'] = year
                        print(f"Filtering by year: {year}")
                    else:
                        # If no specific year, use as plot element
                        if plot_elements:
                            plot_elements += f" and set in {time_pref}"
                        else:
                            plot_elements = f"set in {time_pref}"
                        print(f"Added time period to plot elements: {time_pref}")

                # Process themes/elements as plot elements
                if 'Themes or specific elements they want' in preferences and preferences[
                    'Themes or specific elements they want'] and preferences[
                    'Themes or specific elements they want'] != "None specified":
                    plot_elements = preferences['Themes or specific elements they want']
                    print(f"Added plot elements: {plot_elements}")

        except Exception as e:
            print(f"Error processing preferences JSON: {e}")
    # Process emotions with the split approach
    results = pd.DataFrame()

    if 'emotions' in keys and keys['emotions']:
        try:
            # Split the comma-separated emotions
            emotions = [e.strip() for e in keys['emotions'].split(',')]

            if emotions and len(emotions) > 0:
                # Get the first emotion (primary emotion)
                primary_emotion = emotions[0]

                # Check if primary emotion is negative
                negative_emotions = ['sad', 'angry', 'depressed', 'anxious', 'frustrated',
                                     'lonely', 'tired', 'bored', 'disappointed', 'stressed']

                is_negative = any(neg in primary_emotion.lower() for neg in negative_emotions)

                if is_negative and len(emotions) > 1:
                    # For negative emotions, do two separate searches
                    print(f"Performing split search for negative emotion: {primary_emotion}")

                    # 1. Search with just the primary negative emotion (30% of results)
                    neg_limit = max(int(limit * 0.3), 1)  # At least 1 result
                    print(f"Searching for {neg_limit} movies matching negative emotion: {primary_emotion}")

                    neg_results = advanced_semantic_search(
                        table=table,
                        query=query,
                        genre=genre,
                        mood=primary_emotion,  # Use primary negative emotion
                        plot_elements=plot_elements,
                        metadata_filters=metadata_filters,
                        limit=neg_limit
                    )

                    # 2. Search with complementary positive emotions (70% of results)
                    pos_limit = limit - len(neg_results)
                    complementary = emotions[1:]
                    complementary_mood = ", ".join(complementary)
                    print(f"Searching for {pos_limit} movies matching complementary emotions: {complementary_mood}")

                    pos_results = advanced_semantic_search(
                        table=table,
                        query=query,
                        genre=genre,
                        mood=complementary_mood,  # Use complementary emotions
                        plot_elements=plot_elements,
                        metadata_filters=metadata_filters,
                        limit=pos_limit
                    )

                    # Combine the results
                    results = pd.concat([neg_results, pos_results], ignore_index=True)
                    print(
                        f"Combined {len(neg_results)} negative emotion movies with {len(pos_results)} positive emotion movies")

                else:
                    # For positive emotions or when no complementary emotions available
                    mood = ", ".join(emotions)
                    print(f"Searching with all emotions: {mood}")

                    results = advanced_semantic_search(
                        table=table,
                        query=query,
                        genre=genre,
                        mood=mood,
                        plot_elements=plot_elements,
                        metadata_filters=metadata_filters,
                        limit=limit
                    )

        except Exception as e:
            print(f"Error processing emotions: {e}")

    # If no emotions were processed or there was an error, do a generic search
    if len(results) == 0:
        print("\nPerforming advanced semantic search with extracted parameters...")
        print(f"Genre: {genre or 'Not specified'}")
        print(f"Mood: {mood or 'Not specified'}")
        print(f"Plot elements: {plot_elements or 'Not specified'}")
        print(f"Metadata filters: {metadata_filters or 'None'}")

        results = advanced_semantic_search(
            table=table,
            query=query,
            genre=genre,
            mood=mood,
            plot_elements=plot_elements,
            metadata_filters=metadata_filters,
            limit=limit
        )

    # Format results (existing code)
    if return_formatted:
        formatted_results = {
            "search_parameters": {
                "genre": genre,
                "mood": mood,
                "plot_elements": plot_elements,
                "metadata_filters": metadata_filters
            },
            "results": []
        }

        if len(results) > 0:
            for i, row in results.iterrows():
                # Create a clean movie result object for each movie
                movie_result = {
                    "rank": i + 1,
                    "title": row['movie_name'],
                    "similarity_score": float(row['_distance'])
                }
                if 'movie_id' in row:
                    movie_result["imdb_id"] = row['movie_id']

                # Add all other metadata (except for internal fields)
                for col in row.index:
                    if col not in ['id', 'vector', 'movie_name', '_distance']:
                        # Handle different data types appropriately
                        if isinstance(row[col], (np.float64, np.float32, float)):
                            movie_result[col] = float(row[col])
                        elif isinstance(row[col], (np.int64, np.int32, int)):
                            movie_result[col] = int(row[col])
                        else:
                            movie_result[col] = str(row[col])

                formatted_results["results"].append(movie_result)

        return results, formatted_results
    return results


# Example of using the pipeline integration
# print("\n=== TESTING PIPELINE INTEGRATION ===")

# Example extracted keys from your pipeline
example_keys = {
    'preferences': {
        'raw_extraction': '```json\n{\n  "Genre": "Action",\n  "Language preferences": "Hindi",\n  "Cast/Actors preferences": "Shah Rukh Khan",\n  "Time period or era preferences": "2010s",\n  "Themes or specific elements they want": "Revenge and family"\n}\n```',
        'summary': 'User wants Action movies in Hindi with Shah Rukh Khan, set in the 2010s with themes of revenge and family.'
    },
    'emotions': 'Top three emotions:\n1. Excited\n2. Happy\n3. Thrilled'
}


#### Process the keys and perform search
# results_df, formatted_results = process_and_search(table, keys, limit=10)  

# Display results
# print("\nSearch Results:")
# if len(results_df) > 0:
#     for i, row in results_df.iterrows():
#         metadata_info = ", ".join([f"{col}: {row[col]}" for col in row.index 
#                                   if col not in ['id', 'vector', 'movie_name', '_distance']])
#         print(f"{i+1}. {row['movie_name']} (score: {row['_distance']:.4f})")
#         print(f"   {metadata_info}")
# else:
#     print("No matching movies found")


def get_refined_recommendations(formatted_results, max_recommendations=5):
    # Convert formatted results to JSON string for the prompt
    results_json = json.dumps(formatted_results, indent=2)
    system_prompt = f"""
You are an expert movie recommendation agent. Your task is to analyze search results
and provide the user with {max_recommendations} truly excellent recommendations.

## User's Preferences and Search Results
```json
{results_json}
```

## Your Task
1. Analyze the search results above, which are ranked by semantic similarity
2. Select the {max_recommendations} BEST movies to recommend, considering:
   - Relevance to the user's preferences (genre, mood, plot elements)
   - Movie quality (ratings, if available)
   - Diversity of recommendations (don't recommend too many similar movies)
   - Any specific requirements in the user's preferences

3. Format your response as follows:
   - Start with a brief, conversational introduction addressing the user's preferences
   - List the {max_recommendations} recommended movies with:
     - Title and year (if available)
     - Director (if available)
     - Cast (if available)
     - IMDb ID (if available)
     - A brief 1-2 sentence explanation of WHY you're recommending this specific movie
   - End with a brief conclusion

Keep your response conversational and helpful. Focus on quality explanations rather than generic descriptions.

DO NOT mention the similarity scores or ranking from the search results.
DO NOT make up information that's not in the search results.
DO NOT recommend more than {max_recommendations} movies.
"""
    # Create the prompt for the LLM
    prompt = system_prompt

    # Call the Gemini model
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    response = model.generate_content(prompt)

    return response.text
