import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain.prompts import PromptTemplate
from langchain.prompts import ChatPromptTemplate
from langchain.load import dumps, loads
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")

embedder = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    model_kwargs={"device": "cpu"}
)

# llm =  HuggingFaceEndpoint(
#     repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1", 
#     temperature=0.7,
#     max_length=200)
genai.configure(api_key=api_key)
llm = genai.GenerativeModel("gemini-2.0-flash")
chat = llm.start_chat()


# RAG-Fusion: Related
template = """
You are a helpful assistant that generates multiple search queries based on a single input query.

Input Query:
{question}

Instructions:
- Generate 4 relevant and diverse search queries.
- Output only the queries as a JSON array of strings.
- Do not include any explanation or extra text.

Example Output:
[
  "how to fix memory error in MATLAB",
  "MATLAB memory allocation issues",
  "optimize MATLAB code for large data",
  "MATLAB crashing due to memory limit"
]
"""
prompt_rag_fusion = ChatPromptTemplate.from_template(template)

def generate_search_queries(query: str):
    try:
        formatted_messages = prompt_rag_fusion.format_messages(question=query)
        prompt_str = "\n\n".join([msg.content for msg in formatted_messages])
        response = llm.generate_content(prompt_str)
        text = response.text.strip()
        # Extract JSON block inside code block
        json_match = re.search(r"```json\s*(\[.*?\])\s*```", text, re.DOTALL)
        if json_match:
            json_block = json_match.group(1)
            queries = json.loads(json_block)
            if not isinstance(queries, list) or len(queries) != 4:
                raise ValueError(f"Expected 4 queries, got {len(queries)}")
            return queries
        raise ValueError("Could not extract valid JSON block from response.")
    except Exception as e:
        return f"❌ Error: {str(e)}"
    

# RRF Function
def reciprocal_rank_fusion(results: list[list], k=60):
    fused_scores = {}
    for docs in results:
        for rank, doc in enumerate(docs):
            doc_str = dumps(doc)
            fused_scores[doc_str] = fused_scores.get(doc_str, 0) + 1 / (rank + k)
    reranked_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    return [loads(doc) for doc, _ in reranked_results]  # return docs only



prompt_template = ChatPromptTemplate.from_messages([
    ("system", 
     "You are an expert assistant helping engineers troubleshoot and optimize MATLAB systems.\n\n"
     "**Instructions:**\n"
     "- Use only the given context to answer the question.\n"
     "- Do not make up information or rely on prior knowledge.\n"
    #  "- If the context is insufficient, respond strictly with: \"I don't know\".\n"
     "- Be concise, clear, and technical in your answer.\n\n"
     "**Response Guideline:**\n"
     "Structure the answer clearly with relevant technical headings (e.g., \"Issue\", \"Root Cause\", \"Fix\", \"Notes\") only if appropriate. Use your judgment to decide which headings best organize the answer."
    ),
    ("user", 
     "Context:\n{context}\n\n"
     "Question:\n{question}\n\n"
     "Answer:"
    )
])

def AnswerRagAgent(query: str, vectorstore_name: str, k: int = 6):
    try:
        # index_path = f"/home/piyush/DCIM/code/projects/DL/DLHackathon/backend/{vectorstore_name}"
        # # index_path = vectorstore_name
        # vectorstore = FAISS.load_local(index_path, embedder, allow_dangerous_deserialization=True)
        # docs = vectorstore.similarity_search(query, k=k)
        # print(f"🔍 Found {len(docs)} relevant documents.")
        # for i, doc in enumerate(docs):
        #     print(f"\nDocument {i + 1}:")
        #     print(f"Content: {doc.page_content}")
        #     print(f"Metadata: {doc.metadata}\n")
        # context = "\n\n".join([doc.page_content for doc in docs])
        # prompt = prompt_template.format(context=context, question=query)
        # response = llm.invoke(prompt)
        # formatted_messages = prompt_template.format_messages(context=context, question=query)
        # prompt_str = "\n\n".join([f"{msg.content}" for msg in formatted_messages])
        # response = llm.generate_content(prompt_str)
        # llm_response = response.text.strip().lower()
        # # return response.strip()
        # return llm_response

        generated_queries = generate_search_queries(query)
        print(f"🔎 Generated Queries: {generated_queries}")

        index_path = f"/home/piyush/DCIM/code/projects/DL/DLHackathon/backend/{vectorstore_name}"
        vectorstore = FAISS.load_local(index_path, embedder, allow_dangerous_deserialization=True)

        all_results = []
        for q in generated_queries:
            docs = vectorstore.similarity_search(q, k=k)
            all_results.append(docs)
        print(f"📚 Retrieved document sets for {len(generated_queries)} queries.")

        final_docs = reciprocal_rank_fusion(all_results, k=60)
        print(f"✅ Final RRF documents: {len(final_docs)}")

        context = "\n\n".join([doc.page_content for doc in final_docs])
        links = [doc.metadata.get("source", "No link available") for doc in final_docs]  # Extract links from metadata
        formatted_messages = prompt_template.format_messages(context=context, question=query)
        prompt_str = "\n\n".join([f"{msg.content}" for msg in formatted_messages])
        # response = llm.generate_content(prompt_str)
        response = chat.send_message(prompt_str)

        # return response.text.strip()
        return {
            "answer": response.text.strip(),
            "contributing_links": links
        }

    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    # query = "How do I fix segmentation faults in MATLAB?"
    # query = "How to resolve MATLAB system error?"
    # query = "Where is the Real-Time tab?"
    # query = "How to resolve MATLAB segmentation fault?"
    # query = "when Simulink models cause seg faults?"
    query = "What is ldd:FATAL: Could not load library xyz.so? How do I fix it?"
    vectorstore_name = "faiss_vector_store"
    answer = AnswerRagAgent(query, vectorstore_name)
    print("🤖", answer)
