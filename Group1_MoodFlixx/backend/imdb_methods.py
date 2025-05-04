from imdb import Cinemagoer


def get_imdb_id_from_title(title, max_results=1):
    """
    Retrieve IMDb ID for a given movie/show title.

    Args:
        title (str): The title of the movie or show
        max_results (int): Maximum number of results to return

    Returns:
        list: A list of dictionaries containing title and imdb_id
    """
    # Create an IMDb instance
    ia = Cinemagoer()

    # Search for the title
    search_results = ia.search_movie(title)

    # Handle case where no results are found
    if not search_results:
        return []

    # Limit the number of results
    search_results = search_results[:max_results]

    # Format the results
    formatted_results = []
    for item in search_results:
        result = {
            'title': item.get('title', 'N/A'),
            'imdb_id': f"tt{item.movieID}"
        }
        formatted_results.append(result)

    return formatted_results


def get_imdb_ids_from_titles(titles, max_results_per_title=1):
    """
    Retrieve IMDb IDs for multiple movie/show titles.

    Args:
        titles (list): List of movie or show titles
        max_results_per_title (int): Maximum number of results to return per title

    Returns:
        str: Space-separated string of IMDb IDs
    """
    all_ids = []

    for title in titles:
        results = get_imdb_id_from_title(title, max_results_per_title)
        if results:
            # Add only the first result's ID for each title
            all_ids.append(results[0]['imdb_id'])

    # Join all IDs with spaces
    return ' '.join(all_ids)

    # Display the results
