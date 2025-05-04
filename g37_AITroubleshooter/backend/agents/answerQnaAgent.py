import re
from langchain.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEndpoint
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

BACKEND_URL = "http://127.0.0.1:5000/get-answer"
def fetch_answer(object_id):
    try:
        response = requests.get(f"{BACKEND_URL}?objectId={object_id}")
        if response.status_code == 200:
            return response.json().get("answer", "")
        else:
            return ""
    except Exception as e:
        print(f"Error fetching answer for {object_id}: {e}")
        return ""



# llm = HuggingFaceEndpoint(
#     repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
#     temperature=0.3,
#     max_length=512
# )
genai.configure(api_key=api_key)
llm = genai.GenerativeModel("gemini-2.0-flash")
chat = llm.start_chat()


rag_prompt_template = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert assistant helping users troubleshoot and understand MATLAB-related queries.\n\n"
     "**Instructions:**\n"
     "- First, try to use the provided list of related question-answer pairs as much as possible.\n"
     "- If the Q&A pairs don't fully answer the query, you may use your own knowledge to complete the response.\n"
     "- Organize the answer using clear and meaningful sections, depending on the nature of the query. Examples of useful section headings include: 'Summary', 'Cause', 'Resolution', 'Notes', 'Clarification', etc.\n"
     "- Include only the sections relevant to the query. Do not force unnecessary sections.\n"
     "- Ensure clarity, helpfulness, and technical correctness.\n\n"
     "**Response Guideline:**\n"
     "Use your judgment to choose section headings that best organize the answer. You are not restricted to a fixed format."
     "But Try to use headings to organize the answer.\n\n"
    ),
    ("user",
     "User Query: {query}\n\n"
     "Related Question-Answer Pairs:\n{qa_pairs}")
])


def extract_final_answer(llm_response: str) -> str:
    last_a_index = llm_response.rfind("A:")
    if last_a_index != -1:
        return llm_response[last_a_index + 2:].strip()
    return llm_response[last_a_index + 2:].strip()


def AnswerQnaAgent(query: str, related_qa) -> str:
    qa_pairs = []
    contributing_link = []
    for item in related_qa:
        answer = fetch_answer(item["objectId"]) # database backend call
        if answer:
            qa_pairs.append({
                "question": item["question"],
                "answer": answer['answer']
            })
            for i in answer['contributing_links']:
                contributing_link.append(i)
            print("Contributing Links:", answer['contributing_links'])

    formatted_qa = "\n\n".join(
        f"Q: {pair['question']}\nA: {pair['answer']}" for pair in qa_pairs
    )
    # for pair in qa_pairs:
    #     print(f"Q: {pair['question']}\nA: {pair['answer']}")
    
    # prompt = rag_prompt_template.format_messages(query=query, qa_pairs=formatted_qa)
    # response = llm.invoke(prompt).strip()
    formatted_messages = rag_prompt_template.format_messages(query=query,qa_pairs=formatted_qa)
    prompt_str = "\n\n".join([f"{msg.content}" for msg in formatted_messages])
    # response = llm.generate_content(prompt_str)
    response = chat.send_message(prompt_str)
    llm_response = response.text.strip().lower()
    # final_answer = extract_final_answer(response)
    # return llm_response
    return {
        "answer": llm_response,
        "contributing_links": contributing_link
    }




if __name__ == "__main__":

    # query = "How do I fix segmentation faults in MATLAB?"
    # query = "How to resolve MATLAB system error?"
    # query = "Where is the Real-Time tab?"
    # query = "How to resolve MATLAB segmentation fault?"
    query = "when Simulink models cause seg faults?"
    # query = "What is ldd:FATAL: Could not load library xyz.so? How do I fix it?"
    # related_qa = [
    #     {"question": "What causes segmentation faults in MATLAB?", "answer": "Segmentation faults usually occur due to invalid memory access in compiled MEX functions."},
    #     {"question": "How to debug segmentation faults?", "answer": "Use MATLAB's crash dump logs and debug with GDB if MEX is involved."},
    #     {"question": "Can Simulink models cause segmentation faults?", "answer": "Yes, if S-functions have invalid memory access or indexing issues."}
    # ]
    related_qa = [
        {"question": "How to debug segmentation faults?", "objectId": "68163cc7309002da1587611a"},
        {"question": "What causes segmentation faults in MATLAB?", "objectId": "68163cc3309002da15876119"},
        {"question": "Can Simulink models cause segmentation faults?", "objectId": "68163ca8309002da15876118"},
    ]

    answer = AnswerQnaAgent(query, related_qa)
    print("📌 Answer:\n", answer)
