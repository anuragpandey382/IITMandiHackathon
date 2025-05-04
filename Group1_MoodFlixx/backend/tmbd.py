import logging
import os
from collections import defaultdict, Counter

import requests

from imdb_methods import get_imdb_ids_from_titles

# Configure logging
# Keep logging for warnings/errors from API calls, but remove INFO level logging for process steps
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# Use environment variable for API key, fallback to hardcoded default if not set
# It's highly recommended to set the TMDB_API_KEY environment variable for security.
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "c1d9838cb53ac7338fab312d3fd44590")
if TMDB_API_KEY == "c1d9838cb53ac7338fab312d3fd44590":
    logging.warning(
        "Using hardcoded default TMDB_API_KEY. Consider setting TMDB_API_KEY environment variable for security.")

BASE_URL = "https://api.themoviedb.org/3"

# Minimum number of votes for a movie to be considered for the playlist
MIN_VOTE_COUNT = 100  # You can adjust this threshold

# Number of top weighted characteristics to select from each field (Genre, Actor, Keyword)
TOP_N_CHARACTERISTICS = 3

# Maximum number of unique movies in the final playlist
MAX_PLAYLIST_SIZE = 10


# --- TMDB API Interaction Functions (Remain internal helpers) ---

def _tmdb_request(endpoint, params=None):
    """Internal helper to make a GET request to the TMDB API."""
    if params is None:
        params = {}
    params['api_key'] = TMDB_API_KEY
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"TMDB API request failed for endpoint {endpoint}: {e}")
        return None


def _search_movie(movie_title):
    """Internal helper: Searches for a movie by title and returns the first result's ID and title."""
    endpoint = "/search/movie"
    params = {'query': movie_title}
    data = _tmdb_request(endpoint, params)
    if data and data.get('results'):
        first_result = data['results'][0]
        return first_result.get('id'), first_result.get('title')

    logging.warning(f"Could not find movie on TMDB: '{movie_title}'")
    return None, None


def _get_movie_details(movie_id):
    """Internal helper: Gets movie details by ID."""
    endpoint = f"/movie/{movie_id}"
    return _tmdb_request(endpoint)


def _get_movie_credits(movie_id):
    """Internal helper: Gets movie credits by ID."""
    endpoint = f"/movie/{movie_id}/credits"
    return _tmdb_request(endpoint)


def _get_movie_keywords(movie_id):
    """Internal helper: Gets movie keywords by ID."""
    endpoint = f"/movie/{movie_id}/keywords"
    data = _tmdb_request(endpoint)
    if data and data.get('keywords'):
        return data['keywords']
    return []


def _discover_movies(genre_id=None, actor_id=None, keyword_id=None, language=None):
    """Internal helper: Discovers movies based on criteria, sorted by vote average."""
    endpoint = "/discover/movie"
    params = {
        'sort_by': 'vote_average.desc',
        'vote_count.gte': MIN_VOTE_COUNT,
        'include_adult': False,
        'include_video': False,
        'page': 1  # Explicitly request the first page
    }
    if genre_id:
        params['with_genres'] = genre_id
    if actor_id:
        params['with_people'] = actor_id
    if keyword_id:
        params['with_keywords'] = keyword_id
    if language:
        params['with_original_language'] = language

    data = _tmdb_request(endpoint, params)
    if data and data.get('results'):
        return [movie for movie in data['results'] if
                movie.get('vote_average', 0) > 0 and movie.get('vote_count', 0) >= MIN_VOTE_COUNT]
    return []


# --- Frequency Calculation (Remain internal helpers) ---

def _get_top_weighted(counts_dict, n):
    """Internal helper: Gets the top N items based on their weighted count from a defaultdict."""
    sorted_items = sorted(counts_dict.items(), key=lambda item: item[1], reverse=True)
    return sorted_items[:n]


def _get_most_frequent_language(language_counts_counter):
    """Internal helper: Gets the most frequent language from a Counter dictionary."""
    if language_counts_counter:
        return language_counts_counter.most_common(1)[0][0]
    return None


# --- Core Playlist Generation Function ---

def generate_movie_playlist_from_dict(initial_movies_dict):
    """
    Generates a movie playlist of titles based on the characteristics of
    initial movies and their feedback scores, capped at a maximum size
    and sorted by rating.

    Args:
        initial_movies_dict: A dictionary where keys are movie titles (string)
                             and values are feedback scores (numerical).

    Returns:
        A list of strings, where each string is the title of a movie
        in the generated playlist (capped and sorted by rating).
        Returns an empty list if no playlist can be generated or found.
    """
    # Convert dictionary input to the internal list format (title, score)
    # Ensure only valid string keys are processed
    initial_movies_list = [(k, v) for k, v in initial_movies_dict.items() if isinstance(k, str)]
    if not initial_movies_list:
        logging.warning("Input dictionary is empty or contains no string keys. Cannot generate playlist.")
        return []

    weighted_genre_counts = defaultdict(float)
    weighted_actor_counts = defaultdict(float)
    weighted_keyword_counts = defaultdict(float)
    language_counts = Counter()

    # --- Step 1: Process initial movie list to extract characteristics ---
    for movie_title, feedback_score in initial_movies_list:
        try:
            score = float(feedback_score) if feedback_score is not None else 0
        except (ValueError, TypeError):
            logging.warning(
                f"Invalid feedback score type for '{movie_title}': {type(feedback_score)}. Using score 0 for weighting.")
            score = 0

        # Skip movies with a score of 0 as they won't contribute weight
        if score <= 0:
            # logging.info(f"Skipping movie '{movie_title}' due to zero or negative score ({score}).") # Removed for cleaner output
            continue

        movie_id, found_title = _search_movie(movie_title)

        if movie_id is None:
            continue  # Skip if movie not found

        details = _get_movie_details(movie_id)
        credits = _get_movie_credits(movie_id)
        keywords_data = _get_movie_keywords(movie_id)

        if details:
            genres = details.get('genres', [])
            genre_ids = [g['id'] for g in genres]
            language_code = details.get('original_language')

            for genre_id in genre_ids:
                weighted_genre_counts[genre_id] += score

            if language_code:
                language_counts[language_code] += 1

        if credits and credits.get('cast'):
            actors = credits['cast'][:10]
            actor_ids = [a['id'] for a in actors]

            for actor_id in actor_ids:
                weighted_actor_counts[actor_id] += score

        if keywords_data:
            keyword_ids = [k['id'] for k in keywords_data]
            for keyword_id in keyword_ids:
                weighted_keyword_counts[keyword_id] += score

    # --- Step 2: Calculate weighted frequencies and identify top N ---
    top_weighted_genres = _get_top_weighted(weighted_genre_counts, TOP_N_CHARACTERISTICS)
    top_weighted_actors = _get_top_weighted(weighted_actor_counts, TOP_N_CHARACTERISTICS)
    top_weighted_keywords = _get_top_weighted(weighted_keyword_counts, TOP_N_CHARACTERISTICS)
    most_frequent_language = _get_most_frequent_language(language_counts)

    # --- Step 3: Gather all potential playlist candidates ---
    # Store candidates as dictionaries first to keep rating info for sorting
    playlist_candidates = {}

    # Gather candidates based on Top Weighted Genres
    for genre_id, weight in top_weighted_genres:
        if genre_id is None or weight <= 0: continue
        top_movies = _discover_movies(genre_id=genre_id, language=most_frequent_language)
        if top_movies:
            best_movie = top_movies[0]
            if best_movie['id'] not in playlist_candidates:
                playlist_candidates[best_movie['id']] = {
                    'id': best_movie.get('id'),
                    'title': best_movie.get('title'),  # Keep title for the final output
                    'release_date': best_movie.get('release_date'),
                    'vote_average': best_movie.get('vote_average'),  # Keep rating for sorting
                    'vote_count': best_movie.get('vote_count'),
                    'source_characteristic': f'Weighted Genre ID: {genre_id}'
                    # Keep source for potential debugging if needed later
                }

    # Gather candidates based on Top Weighted Actors
    for actor_id, weight in top_weighted_actors:
        if actor_id is None or weight <= 0: continue
        top_movies = _discover_movies(actor_id=actor_id, language=most_frequent_language)
        if top_movies:
            best_movie = top_movies[0]
            if best_movie['id'] not in playlist_candidates:
                playlist_candidates[best_movie['id']] = {
                    'id': best_movie.get('id'),
                    'title': best_movie.get('title'),
                    'release_date': best_movie.get('release_date'),
                    'vote_average': best_movie.get('vote_average'),
                    'vote_count': best_movie.get('vote_count'),
                    'source_characteristic': f'Weighted Actor ID: {actor_id}'
                }

    # Gather candidates based on Top Weighted Keywords
    for keyword_id, weight in top_weighted_keywords:
        if keyword_id is None or weight <= 0: continue
        top_movies = _discover_movies(keyword_id=keyword_id, language=most_frequent_language)
        if top_movies:
            best_movie = top_movies[0]
            if best_movie['id'] not in playlist_candidates:
                playlist_candidates[best_movie['id']] = {
                    'id': best_movie.get('id'),
                    'title': best_movie.get('title'),
                    'release_date': best_movie.get('release_date'),
                    'vote_average': best_movie.get('vote_average'),
                    'vote_count': best_movie.get('vote_count'),
                    'source_characteristic': f'Weighted Keyword ID: {keyword_id}'
                }

    # --- Step 4: Final Playlist Capping and Sorting ---

    final_playlist_candidates_list = list(playlist_candidates.values())

    # Sort the candidates by vote average in descending order
    # Need rating here for sorting, even though it's not in the final output list
    final_playlist_candidates_list.sort(key=lambda x: x.get('vote_average', 0), reverse=True)

    # Take the top MAX_PLAYLIST_SIZE movies (still as dictionaries)
    top_rated_candidates = final_playlist_candidates_list[:MAX_PLAYLIST_SIZE]

    # --- Final Step: Extract only the titles ---
    # Create the final list containing only movie titles
    final_playlist_titles_only = [movie.get('title') for movie in top_rated_candidates if movie.get('title')]

    return get_imdb_ids_from_titles(final_playlist_titles_only)


# --- Example Usage (for demonstration) ---
if __name__ == "__main__":
    # Define the input in the requested dictionary format
    initial_movies_input = {
        # "The Shawshank Redemption": 5,
        # "The Dark Knight": 4,
        # "Pulp Fiction": 5,
        # "Fight Club": 4,
        # "Forrest Gump": 5,
        # "Inception": 4,
        # "The Matrix": 5,
        # "Goodfellas": 4,
        # "Interstellar": 5,
        # "Parasite": 5,
        # "Avengers: Endgame": 3,
        # "La La Land": 4,
        # "Spirited Away": 5,
        # "The Godfather": 5,
        # "The Lord of the Rings: The Fellowship of the Ring": 4,
        "Titanic": 1,
        # "Eternal Sunshine of the Spotless Mind": 5,
        # "The Silence of the Lambs": 4,
        # ("Invalid Key Tuple", 5): 4,  # Example of non-string key (will be skipped)
        # "Saving Private Ryan": 4,
        # "The Green Mile": 5,
        "Step Brothers": 2,
        "The Room": 1,
        # "Avatar": 3,
        # "Dune": 4,
        # "The Grand Budapest Hotel": 5,
        # "Mad Max: Fury Road": 4
    }

    print("Generating playlist with dictionary input...")
    # Call the main function with the dictionary input
    generated_playlist_titles = generate_movie_playlist_from_dict(initial_movies_input)

    print("\n" + "=" * 50)
    print("Final Generated Playlist (Returned List of Titles):")
    print("=" * 50)
    if generated_playlist_titles:
        # Print the returned list of titles
        for i, title in enumerate(generated_playlist_titles):
            print(f"{i + 1}. {title}")
    else:
        print("Could not generate a playlist or no movies found matching criteria.")
