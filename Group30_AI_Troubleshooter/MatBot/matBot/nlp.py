import google.generativeai as genai
import os
from dotenv import load_dotenv
from pathlib import Path


env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

GEMAPI = os.getenv("GEMAPI")

class GeminiQueryFormatter:
    def __init__(self, api_key: str = "AIzaSyAaIDq55k6Nm-tv3YuhbYuIpSEX0z6AasU", model_name: str = "models/gemini-1.5-pro"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def format_query(self, query: str) -> str:
        prompt = (
            "Format this user query properly by fixing spelling errors and improving grammar. "
            "And If user query does't being related to the MATLAB programming language"
            "Then return the query and ask query should be related to matlab"
            "Don't explain, just return the cleaned version.\n\n"
            f"Query: {query}"
        )
        response = self.model.generate_content(prompt)
        return response.text.strip()

if __name__ == "__main__":
    formatter = GeminiQueryFormatter(api_key=GEMAPI)
    # user_input = "whaat is th problm in mtalab matrix indexig?"
    user_input= input("Enter:")
    formatted = formatter.format_query(user_input)
    print("[Original Query]:", user_input)
    print("[Formatted Query]:", formatted)
    
    
