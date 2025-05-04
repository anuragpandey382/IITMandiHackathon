#I'm assuming I will get a normalised vector in format --> anger, fear, joy, sadness, surprise, disgust, neutral
from .utils import query_movies_by_emotion , query_movies_ensemble
import pandas as pd

def recommend_top_movies_for_mood(inputstream,mood_vector,semantic_vector=None,tagline_vector=None,num_movies=10):
    """
    Queries movies based on a mood vector and returns the top movies
    sorted by popularity.

    Args:
        mood_vector (list): A normalized vector representing mood
                             in the format [anger, fear, joy, sadness, surprise, disgust, neutral].

    Returns:
        pandas.DataFrame: A DataFrame of top movies sorted by popularity
                          in descending order.
    """
    if inputstream is None:
        return "Error: inputstream is None."
    if inputstream == 1:
        top_movies = query_movies_by_emotion(mood_vector)
        if isinstance(top_movies, pd.DataFrame):
            top_movies_sorted = top_movies.sort_values('popularity', ascending=False)
            return top_movies_sorted[:num_movies]
        else:
            return "Error: query_movies_by_emotion did not return a DataFrame."
    else:
        top_movies = query_movies_ensemble(mood_vector, semantic_vector, tagline_vector)
        if isinstance(top_movies, pd.DataFrame):
            top_movies_sorted = top_movies.sort_values('popularity', ascending=False)
            return top_movies_sorted[:num_movies]
        else:
            return "Error: query_movies_ensemble did not return a DataFrame."