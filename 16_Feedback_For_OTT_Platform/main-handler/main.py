from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv
import base64
import cv2
from emotion_module import run_emotion_detection
import threading
import numpy as np
from deepface import DeepFace  # Using DeepFace for emotion detection
from tensorflow.keras.models import load_model

app = Flask(__name__)
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# Load environment variables
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
     url = f"{TMDB_BASE_URL}/trending/all/day"#     params = {"language": "en-US", "page": 1}
     response = requests.get(url, headers=headers, params=params)
     if response.ok:
         data = response.json()
         genres_lookup = get_genres()
         for movie in data.get("results", [])[:10]:
             title = movie.get("title")
             poster_path = movie.get("poster_path")
             poster_url = TMDB_IMAGE_BASE_URL + poster_path if poster_path else ""
             description = movie.get("overview")
             release_date = movie.get("release_date", "")
             year = release_date.split("-")[0] if release_date else "N/A"
             movie_genres = [genres_lookup.get(genre_id, "Unknown") for genre_id in movie.get("genre_ids", [])]
             movies.append({
                 "title": title,
                 "poster": poster_url,
                 "description": description,
                 "genres": ", ".join(movie_genres),
                 "year": year
             })
     return movies

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == 'GET' and request.args.get("mood") == "1":
        print("yes")
        return render_template("index1.html")

    # Default behavior or search
    search_query = request.form.get("query", "")
    recommended_movies = "Yes" #get_top_movies()
    return render_template("index.html", movies=recommended_movies)

@app.route("/mood-based", methods=["GET", "POST"])
def mood_based():
    # You can add logic here for mood-based movie recommendations, if needed
    return render_template("index-2.html")


@app.route('/detect_emotion', methods=['POST'])
def detect_emotion():
    emotion = run_emotion_detection()
    return jsonify({'emotion': emotion})


if __name__ == "__main__":
    app.run(debug=True)
