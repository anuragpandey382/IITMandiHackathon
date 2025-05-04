from flask import Flask, render_template, request
import requests
import os
from dotenv import load_dotenv

app = Flask(__name__)

# URLs and API setup
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
MOOD_API_URL = "http://172.18.40.123:5001/get-movies"

load_dotenv()
TMDB_BEARER_TOKEN = os.getenv("TMDB_BEARER_TOKEN")

headers = {
    "accept": "application/json",
    "Authorization": TMDB_BEARER_TOKEN
}

def get_genres():
    url = f"{TMDB_BASE_URL}/genre/movie/list"
    params = {"language": "en-US"}
    response = requests.get(url, headers=headers, params=params)
    genres = {}
    if response.ok:
        data = response.json()
        for genre in data.get("genres", []):
            genres[genre["id"]] = genre["name"]
    return genres

def get_top_movies():
    movies = []
    url = f"{TMDB_BASE_URL}/trending/all/day"
    params = {"language": "en-US", "page": 1}
    response = requests.get(url, headers=headers, params=params)
    if response.ok:
        data = response.json()
        genres_lookup = get_genres()
        for movie in data.get("results", [])[:10]:
            title = movie.get("title") or movie.get("name") or "Untitled"
            poster_path = movie.get("poster_path")
            poster_url = TMDB_IMAGE_BASE_URL + poster_path if poster_path else ""
            release_date = movie.get("release_date") or movie.get("first_air_date") or ""
            year = release_date.split("-")[0] if release_date else "N/A"
            movie_genres = [genres_lookup.get(genre_id, "Unknown") for genre_id in movie.get("genre_ids", [])]
            movies.append({
                "title": title,
                "poster": poster_url,
                "genres": ", ".join(movie_genres),
                "year": year
            })
    return movies

@app.route("/", methods=["GET", "POST"])
def index():
    search_query = request.form.get("query", "").strip()
    recommended_movies = []

    if search_query:
        try:
            # Step 1: Fetch JSON response from MOOD_API_URL
            mood_response = requests.post(MOOD_API_URL, json={"prompt": search_query, "channel": 2})
            if mood_response.status_code == 200:
                mood_data = mood_response.json()
                movie_titles = [movie["title"] for movie in mood_data.get("movies", [])]

                # Step 2: Fetch detailed data for each movie title from TMDB API
                for title in movie_titles:
                    tmdb_url = f"{TMDB_BASE_URL}/search/movie"
                    params = {"query": title, "language": "en-US"}
                    tmdb_response = requests.get(tmdb_url, headers=headers, params=params)
                    if tmdb_response.ok:
                        tmdb_data = tmdb_response.json()
                        if tmdb_data.get("results"):
                            movie = tmdb_data["results"][0]  # Take the first result
                            poster_path = movie.get("poster_path")
                            poster_url = TMDB_IMAGE_BASE_URL + poster_path if poster_path else ""
                            release_date = movie.get("release_date", "")
                            year = release_date.split("-")[0] if release_date else "N/A"
                            genres = movie.get("genre_ids", [])
                            genres_lookup = get_genres()
                            movie_genres = [genres_lookup.get(genre_id, "Unknown") for genre_id in genres]
                            recommended_movies.append({
                                "title": movie.get("title"),
                                "poster": poster_url,
                                "genres": ", ".join(movie_genres),
                                "year": year
                            })
        except Exception as e:
            print(f"[ERROR] Failed to fetch data: {e}")

    # Step 3: If no search query or no results, fetch top movies
    if not recommended_movies:
        recommended_movies = get_top_movies()

    return render_template("index.html", movies=recommended_movies)

@app.route("/popular-movies", methods=["GET"])
def popular_movies():
    url = f"{TMDB_BASE_URL}/movie/popular"
    params = {"language": "en-US", "page": 1}
    response = requests.get(url, headers=headers, params=params)
    movies = []
    if response.ok:
        data = response.json()
        genres_lookup = get_genres()
        for movie in data.get("results", [])[:10]:
            title = movie.get("title")
            poster_path = movie.get("poster_path")
            poster_url = TMDB_IMAGE_BASE_URL + poster_path if poster_path else ""
            release_date = movie.get("release_date", "")
            year = release_date.split("-")[0] if release_date else "N/A"
            movie_genres = [genres_lookup.get(genre_id, "Unknown") for genre_id in movie.get("genre_ids", [])]
            movies.append({
                "title": title,
                "poster": poster_url,
                "genres": ", ".join(movie_genres),
                "year": year
            })
    return render_template("index.html", movies=movies)

@app.route("/popular-shows", methods=["GET"])
def popular_shows():
    url = f"{TMDB_BASE_URL}/tv/popular"
    params = {"language": "en-US", "page": 1}
    response = requests.get(url, headers=headers, params=params)
    shows = []
    if response.ok:
        data = response.json()
        genres_lookup = get_genres()
        for show in data.get("results", [])[:10]:
            title = show.get("name")
            poster_path = show.get("poster_path")
            poster_url = TMDB_IMAGE_BASE_URL + poster_path if poster_path else ""
            release_date = show.get("first_air_date", "")
            year = release_date.split("-")[0] if release_date else "N/A"
            show_genres = [genres_lookup.get(genre_id, "Unknown") for genre_id in show.get("genre_ids", [])]
            shows.append({
                "title": title,
                "poster": poster_url,
                "genres": ", ".join(show_genres),
                "year": year
            })
    return render_template("index.html", movies=shows)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        return f"Logged in as {username}"
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        return f"Logged in as {username}"
    return render_template("register.html")

@app.route("/temp", methods=["GET", "POST"])
def temp():
    return render_template("temp.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)