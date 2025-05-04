import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment.")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

def get_matlab_suggestions(query: str) -> str:
    """
    Function to get MATLAB autocomplete suggestions based on a partial query.
    """
    prompt = f"""
    You are a MATLAB expert assistant. A user is trying to troubleshoot issues in MATLAB and has typed a partial query: "{query}". 

    Suggest the top 3 ways to autocomplete their query with accurate and commonly searched MATLAB troubleshooting phrases. 

    Only give suggestions starting with the exact partial query provided by user.

    Focus only on MATLAB related queries such as syntax errors, runtime errors, Simulink issues, or environment configuration problems, etc. Do not include general programming terms. Avoid giving explanations — just return 3 bullet-point suggestions.
    
    Do not include any other text or context. Just return the suggestions in a simple string separated by a $ sign.
    """

    response = model.generate_content(prompt)
    return response.text.strip()

if __name__ == "__main__":
    query = "how to pl"
    print("Query:")
    print(query)
    suggestions = get_matlab_suggestions(query)
    print("MATLAB Suggestions:")
    print(suggestions)
