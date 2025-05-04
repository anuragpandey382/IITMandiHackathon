import json

import requests


def get_api_recommendations(payload):
    api_url = "https://9c12-2401-4900-5d24-5c56-8d54-9fdd-f21-cc0d.ngrok-free.app/recommendations"

    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        recommendations = response.json()
        return recommendations.get('recommendations')

    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            try:
                print(f"Response Body: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"Response Body: {e.response.text}")


if __name__ == "__main__":
    payload = {
        "Lord of the Rings": 5,
        "Harry Potter": 4,
        "The Matrix": 5,
        "Inception": 3,
    }
    recommendations = get_api_recommendations(payload)
    print("Recommendations:", recommendations)
