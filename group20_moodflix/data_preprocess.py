"""
Data preprocessing script for the IMDB 5000 movie dataset.
This script downloads and cleans the dataset for basic processing.
"""

import os
import pandas as pd
import numpy as np
import requests
import zipfile
import io
from typing import List, Dict, Any, Optional

# Constants
DATASET_URL = "https://www.kaggle.com/datasets/carolzhangdc/imdb-5000-movie-dataset/download"
DATASET_PATH = "data/movie_data"
PROCESSED_DATA_PATH = "data/processed"

def download_dataset(url: str = DATASET_URL, path: str = DATASET_PATH) -> str:
    """
    Download the IMDB 5000 movie dataset from Kaggle.
    Note: This requires Kaggle API credentials to be set up.
    Alternative: Download manually from Kaggle and place in the data directory.
    
    Args:
        url: URL to download the dataset from
        path: Path to save the dataset to
        
    Returns:
        Path to the downloaded dataset
    """
    # Create the directory if it doesn't exist
    os.makedirs(path, exist_ok=True)
    
    # For this example, we'll assume the dataset is downloaded manually
    # as Kaggle requires authentication
    print(f"Please download the IMDB 5000 movie dataset from {url}")
    print(f"and extract it to {os.path.abspath(path)}")
    
    # Check if the dataset exists
    csv_path = os.path.join(path, "movie_metadata.csv")
    if os.path.exists(csv_path):
        print(f"Dataset found at {csv_path}")
        return csv_path
    else:
        print(f"Dataset not found at {csv_path}")
        return None

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the IMDB 5000 movie dataset.
    
    Args:
        df: DataFrame containing the IMDB 5000 movie dataset
        
    Returns:
        Cleaned DataFrame
    """
    # Make a copy to avoid modifying the original
    df_clean = df.copy()
    
    # Drop duplicates
    df_clean = df_clean.drop_duplicates(subset=['movie_title'])
    
    # Clean movie titles (remove trailing spaces and special characters)
    df_clean['movie_title'] = df_clean['movie_title'].str.strip()
    
    # Convert numeric columns to appropriate types
    numeric_cols = ['budget', 'gross', 'imdb_score', 'num_voted_users', 
                   'title_year', 'movie_facebook_likes', 'duration']
    
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # Fill missing values
    df_clean['plot_keywords'] = df_clean['plot_keywords'].fillna('')
    df_clean['movie_imdb_link'] = df_clean['movie_imdb_link'].fillna('')
    df_clean['language'] = df_clean['language'].fillna('Unknown')
    df_clean['country'] = df_clean['country'].fillna('Unknown')
    df_clean['title_year'] = df_clean['title_year'].fillna(0).astype(int)
    df_clean['duration'] = df_clean['duration'].fillna(0).astype(int)
    df_clean['director_name'] = df_clean['director_name'].fillna('Unknown')
    
    # Clean actor names
    actor_cols = ['actor_1_name', 'actor_2_name', 'actor_3_name']
    for col in actor_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna('Unknown')
    
    # Create a combined genres column if it doesn't exist
    if 'genres' in df_clean.columns:
        df_clean['genres'] = df_clean['genres'].fillna('')
    
    # Create a combined plot column
    df_clean['plot_summary'] = df_clean.apply(
        lambda row: f"This {row['genres']} movie is directed by {row['director_name']} "
                   f"and stars {row['actor_1_name']}, {row['actor_2_name']}, and {row['actor_3_name']}. "
                   f"Keywords: {row['plot_keywords']}",
        axis=1
    )
    
    # Filter out movies with missing crucial information
    df_clean = df_clean[df_clean['movie_title'] != '']
    
    return df_clean

def save_processed_data(df: pd.DataFrame, path: str = PROCESSED_DATA_PATH) -> str:
    """
    Save the processed data to disk.
    
    Args:
        df: DataFrame containing the processed data
        path: Path to save the processed data to
        
    Returns:
        Path to the saved processed data
    """
    # Create the directory if it doesn't exist
    os.makedirs(path, exist_ok=True)
    
    # Save the processed data
    processed_path = os.path.join(path, "processed_movies.csv")
    df.to_csv(processed_path, index=False)
    
    return processed_path

def process_movie_data() -> Dict[str, Any]:
    """
    Process the IMDB 5000 movie dataset.
    
    Returns:
        Dictionary containing the processed data
    """
    # Download the dataset
    csv_path = download_dataset()
    
    if not csv_path or not os.path.exists(csv_path):
        return {"error": "Dataset not found. Please download it manually."}
    
    # Load the dataset
    df = pd.read_csv(csv_path)
    
    # Clean the dataset
    df_clean = clean_dataset(df)
    
    # Save the processed data
    processed_path = save_processed_data(df_clean)
    
    return {
        "processed_data_path": processed_path,
        "num_movies": len(df_clean),
        "data": df_clean
    }

if __name__ == "__main__":
    # Process the movie data
    result = process_movie_data()
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Processed {result['num_movies']} movies")
        print(f"Processed data saved to {result['processed_data_path']}")
        
        # Display sample of the processed data
        print("\nSample of processed data:")
        print(result["data"].head(3)[['movie_title', 'director_name', 'genres', 'imdb_score']])