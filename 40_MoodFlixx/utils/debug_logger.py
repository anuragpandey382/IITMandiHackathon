import os
import pandas as pd
import sys

# Add project root to path to allow imports from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.data_processor import create_directory_if_not_exists, get_timestamp


def save_similarity_filtered_data(filtered_df):
    """
    Save similarity filtered dataframe for debugging
    
    Args:
        filtered_df: DataFrame with similarity-filtered movies
    """
    create_directory_if_not_exists(config.SIMILARITY_FILTERED_DIR)
    timestamp = get_timestamp()
    output_file = os.path.join(
        config.SIMILARITY_FILTERED_DIR, 
        f"similarity_filtered_{timestamp}.csv"
    )
    
    # Save only necessary columns
    output_df = filtered_df[['movie_id', 'movie_name', 'year', 'genres', 
                             'overview', 'similarity_score']].copy()
    
    output_df.to_csv(output_file, index=False)
    return output_file


def save_genre_filtered_data(filtered_df):
    """
    Save genre filtered dataframe for debugging
    
    Args:
        filtered_df: DataFrame with genre-filtered movies
    """
    create_directory_if_not_exists(config.GENRE_FILTERED_DIR)
    timestamp = get_timestamp()
    output_file = os.path.join(
        config.GENRE_FILTERED_DIR, 
        f"genre_filtered_{timestamp}.csv"
    )
    
    # Save only necessary columns
    output_df = filtered_df[['movie_id', 'movie_name', 'year', 'genres', 
                             'overview', 'similarity_score', 'genre_match_score', 
                             'final_score']].copy()
    
    output_df.to_csv(output_file, index=False)
    return output_file