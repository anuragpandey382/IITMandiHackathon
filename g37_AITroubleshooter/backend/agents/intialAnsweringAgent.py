import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment.")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")
chat = model.start_chat()


def InitialAnsweringAgent(query: str) -> str:
    """
    Function to answer initial query that is not related to MATLAB.
    """
    prompt = f"""
    Query : {query}
    Prompt : Be friendly, keep your answer short and simple.
    """

    # response = model.generate_content(prompt)
    response = chat.send_message(prompt)
    return {
        'answer': response.text.strip(),
        'contributing_links': []
    }

if __name__ == "__main__":
    query = "Who is the president of the USA?"
    print("Query:")
    print(query)
    suggestions = InitialAnsweringAgent(query)
    print("Answer:")
    print(suggestions)
