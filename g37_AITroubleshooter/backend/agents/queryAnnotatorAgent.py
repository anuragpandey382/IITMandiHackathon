from langchain_huggingface import HuggingFaceEndpoint
from langchain.prompts import PromptTemplate
import os

os.environ["HUGGINGFACEHUB_API_TOKEN"] = "your_hf_api_key_here"

llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.1",
    task="text-generation",
    temperature=0.0,
    max_new_tokens=10
)

CLASSES = [
    "Troubleshooting System Configuration",
    "Troubleshooting Model Preparation",
    "Troubleshooting Control and Instrumentation",
    "Troubleshooting Performance Optimization",
    "More Troubleshooting: Simulink Real-Time Support"
]

prompt_template = PromptTemplate.from_template("""
You are an expert MATLAB troubleshooter.

Your task is to read the user's query and decide **which one** of the following 5 troubleshooting categories it belongs to:

1. Troubleshooting System Configuration  
2. Troubleshooting Model Preparation  
3. Troubleshooting Control and Instrumentation  
4. Troubleshooting Performance Optimization  
5. More Troubleshooting: Simulink Real-Time Support

Only return the exact category name from the list. No extra words, no explanation, no punctuation. Just return the label.

User Query:
{query}

Category:
""")

def classify_troubleshooting_category(query: str) -> str:
    prompt = prompt_template.format(query=query)
    response = llm.invoke(prompt)
    return response.strip()

def category_to_faiss_key(category: str) -> str:
    normalized = category.lower().replace(":", "").replace("-", "").replace(" ", "_")
    return f"faiss_{normalized}"

if __name__ == "__main__":
    query = "My model takes too long to run in real-time target machine."
    category = classify_troubleshooting_category(query)
    faiss_key = category_to_faiss_key(category)

    print("Predicted category:", category)
    print("Corresponding FAISS key:", faiss_key)
