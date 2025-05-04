import pandas as pd
import os
import sys
import json
from datetime import datetime

# Add project root to path to allow imports from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def load_movies_data():
    """Load the movies dataset with embeddings"""
    try:
        movies_df = pd.read_csv(config.MOVIES_CSV_PATH)
        # Convert string representation of embeddings to list
        movies_df['overview_embedding'] = movies_df['overview_embedding'].apply(
            lambda x: json.loads(x) if isinstance(x, str) else x
        )
        return movies_df
    except Exception as e:
        print(f"Error loading movies data: {e}")
        return pd.DataFrame()


def load_emoji_data():
    """Load the emoji dataset"""
    try:
        emoji_df = pd.read_csv(config.EMOJI_CSV_PATH)
        return emoji_df
    except Exception as e:
        print(f"Error loading emoji data: {e}")
        return pd.DataFrame()


def parse_genres(genre_string):
    """Parse the pipe-separated genre string into a list"""
    if pd.isna(genre_string) or not genre_string:
        return []
    return genre_string.split('|')


def extract_genres_from_dataframe():
    """Extract all unique genres from the movies dataframe"""
    movies_df = load_movies_data()
    all_genres = []
    
    for genre_str in movies_df['genres'].dropna():
        genres = parse_genres(genre_str)
        all_genres.extend(genres)
    
    return sorted(list(set(all_genres)))


def create_directory_if_not_exists(directory_path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def get_timestamp():
    """Get current timestamp string for filenames"""
    return datetime.now().strftime(config.LOG_TIMESTAMP_FORMAT)