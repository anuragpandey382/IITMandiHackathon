# backend/agents/image_to_query_agent.py

import google.generativeai as genai
from PIL import Image
import io

# Initialize Gemini
genai.configure(api_key="YOUR_API_KEY")
llm = genai.GenerativeModel("gemini-2.0-flash")

def generate_query_from_image(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        prompt = "Analyze this image and generate a short, relevant technical search query that captures the key topic or issue."

        response = llm.generate_content([prompt, image])
        return response.text.strip()
    except Exception as e:
        return f"❌ Error: {str(e)}"
