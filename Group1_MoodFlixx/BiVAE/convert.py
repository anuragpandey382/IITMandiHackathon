import pandas as pd
import difflib
from imdb import Cinemagoer  # IMDbPY library

# Load the movies CSV file into a pandas DataFrame
movies_df = pd.read_csv('ml-32m/movies.csv')

#movie_english = pd.read_csv('content/IMDB-Full_Detail_1000.csv')
movies_2 = pd.read_csv('content/combined_movies.csv')


def movie_from_ID(id):
    """
    Convert a movie ID to a movie title.
    """
    global movies_df

    row = movies_df[movies_df['movieId'] == id]
    return row['title'].values[0]

def titles_from_recs(recs):
    """
    Convert a list of movie IDs to their titles.
    """
    global movies_df

    titles = []
    for rec in recs:
        titles.append(movie_from_ID(rec))
    return titles

def get_movie_id_from_title(title):
    """
    Retrieve movie ID for a given title.

    Args:
        title (str): The title of the movie

    Returns:
        int: The movie ID
    """
    global movies_df

    # Get all titles from the DataFrame
    all_titles = movies_df['title'].tolist()

    # Find the closest match to the input title
    closest_matches = difflib.get_close_matches(title, all_titles, n=1, cutoff=0.6)

    if not closest_matches:
        return None

    # Get the row for the closest match
    row = movies_df[movies_df['title'] == closest_matches[0]]

    return int(row['movieId'].values[0])

def watchlist_titles_to_ids(watchlist):
    """
    Convert a watchlist of movie titles to their corresponding IDs.

    Args:
        watchlist (dict): A dictionary of movie titles and their ratings

    Returns:
        dict: A dictionary of movie IDs and their ratings
    """
    global movies_df

    # Create a dictionary to store the movie IDs
    watchlist_ids = {}

    for title in watchlist.keys():
        # Get the movie ID for the title
        movie_id = get_movie_id_from_title(title)
        if movie_id is not None:
            watchlist_ids[movie_id] = watchlist[title]

    return watchlist_ids

def imbd_from_title(title):
    """
    Get the IMDb ID for a given movie title.
    """
    global movies_2

    # Get all titles from movies_2 DataFrame
    all_titles = movies_2['movie_name'].tolist()

    # Find the closest match to the input title
    closest_matches = difflib.get_close_matches(title, all_titles, n=1, cutoff=0.6)

    if not closest_matches:
        return None

    # Get the row for the closest match
    row = movies_2[movies_2['movie_name'] == closest_matches[0]]

    # Return the imdb_id if available
    if not row.empty and 'imdb_id' in row.columns:
        return row['imdb_id'].values[0]
    else:
        return None

def imdb_from_recommendations(recommendations):
    """
    Accepts a list of movie titles (recommendations) and returns a list of IMDb IDs for those titles.
    Drops any titles for which an IMDb ID cannot be found.

    Args:
        recommendations (list of str): List of movie titles.

    Returns:
        list of str: List of IMDb IDs (non-empty).
    """
    imdb_ids = []
    for title in recommendations:
        imdb_id = imbd_from_title(title)
        if imdb_id:
            imdb_ids.append(imdb_id)
    return imdb_ids


if __name__ == "__main__":
    # Example usage
    # movie_id = 1  # Replace with the desired movie ID
    # movie_title = movie_from_ID(movie_id)
    # print(f"Movie ID {movie_id} corresponds to: {movie_title}")

    print(get_movie_id_from_title("The Shawshank Redemption"))