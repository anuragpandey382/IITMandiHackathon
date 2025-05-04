import http.client
import json


def get_prime_link(show_id="tt0374887"):
    conn = http.client.HTTPSConnection("streaming-availability.p.rapidapi.com")

    headers = {
        'x-rapidapi-key': "51f3af8964mshc9c390103e97486p1cc214jsnf4d2e48e6b14",
        'x-rapidapi-host': "streaming-availability.p.rapidapi.com"
    }

    if show_id:
        conn.request("GET", f"/shows/{show_id}?country=us", headers=headers)
        res = conn.getresponse()
        streaming_data = res.read().decode("utf-8")

        data = json.loads(streaming_data)
        streaming_options = data.get("streamingOptions", {}).get("us", [])

        for option in streaming_options:
            service = option["service"]["name"].lower()
            link = option["link"]
            if "prime" in service or "amazon" in service:
                return link  # ✅ Return the Amazon Prime link immediately

        return None  # No Amazon Prime link found
    else:
        return None  # Invalid show_id
