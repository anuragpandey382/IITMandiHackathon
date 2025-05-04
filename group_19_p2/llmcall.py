import requests

# Set your API key here or via environment variable
API_KEY = "AIzaSyBWb5O_8-tYNazvqOAjBWdcqmU--JF-EAg"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

MAX_INPUT_LENGTH = 500  # Example limit, adjust as needed

def generate_summary(data):
    # Extract parameters from the input data
    jaggedness = data.get("Jaggedness", "")
    cracks = data.get("Cracks", "")
    redness = data.get("redness", "")
    segmented_image_path = data.get("segmented_image_path", "")
    white_coating = data.get("white_coating", "")
    papillae_analysis = data.get("papillae_analysis", "")

    if not jaggedness or not cracks or not redness or not segmented_image_path:
        return {"reply": "Missing required parameters."}

    # Check for length limitations
    input_text = f"Jaggedness: {jaggedness}, Cracks: {cracks}, Redness: {redness}, Segmented Image: {segmented_image_path}, White Coating: {white_coating}, Papillae Analysis: {papillae_analysis}"
    if len(input_text) > MAX_INPUT_LENGTH:
        return {"reply": f"Input is too long. Please keep the input under {MAX_INPUT_LENGTH} characters."}

    # Formulate the input message for summarization
    user_message = (
    f"Jaggedness: {jaggedness}, Cracks: {cracks}, Redness: {redness}, "
    f"Segmented Image: {segmented_image_path}, White Coating: {white_coating}, "
    f"Papillae Analysis: {papillae_analysis}. "
    "Provide a direct answer with possible tongue-related diseases and a brief summary in under 100 words. "
    "Do not provide explanations, only the answer and summary."
        )

    # Disclaimer about model usage

    payload = {
        "contents": [{
            "parts": [{"text": user_message}]
        }]
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        return {
            "reply": reply,
        }

    except requests.exceptions.RequestException as e:
        return {"reply": f"API Error: {str(e)}"}
    except KeyError:
        return {"reply": "Error: Unexpected response format."}


