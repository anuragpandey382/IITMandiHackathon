import requests
import json

api_url = "https://9c12-2401-4900-5d24-5c56-8d54-9fdd-f21-cc0d.ngrok-free.app/recommendations"


movie_ratings = {
    "You Are My Sunshine (2015)": 5.0,
    "5 to 7 (2014)": 5.0,
    "Vesna (1947)": 5.0,
    "Afonya (1975)": 5.0,
    "We'll Live Till Monday (1968)": 5.0,
    "The Beginning (1970)": 5.0,
    "Walking the Streets of Moscow (1963)": 5.0,
    "Don't Grieve! (1969)": 5.0,
    "Oblomov (1980)": 5.0,
    "Holiday (2014)": 4.0,
    "Hecate (1982)": 5.0
}
payload = {
    "watchlist": movie_ratings,
    "num_recommendations": 20
}

try:
    response = requests.post(api_url, json=payload)
    response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

    recommendations = response.json()
    print("Recommendations received:")
    # print(json.dumps(recommendations, indent=2))
    print(recommendations.get('recommendations'))

except requests.exceptions.RequestException as e:
    print(f"Error calling API: {e}")
    if hasattr(e, 'response') and e.response is not None:
         print(f"Status Code: {e.response.status_code}")
         try:
             print(f"Response Body: {e.response.json()}")
         except json.JSONDecodeError:
             print(f"Response Body: {e.response.text}")