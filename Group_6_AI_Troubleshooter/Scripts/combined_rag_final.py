import os
import sys
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.tools import DuckDuckGoSearchResults
from langchain.vectorstores import FAISS
import openai
import base64

# Load environment variables from a .env file
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel("gemini-1.5-flash")

def generate_prompt(query,image_bytes):
    """Dynamically generate enhanced prompt for detailed MATLAB error description with relevance check"""
    system_prompt = (
        """
            YOU ARE A MATLAB TROUBLESHOOTING ASSISTANT, HIGHLY EXPERIENCED IN DEBUGGING MATLAB CODE, UNDERSTANDING ERROR MESSAGES, AND INTERPRETING MATLAB OUTPUTS FROM TEXT AND IMAGES. YOUR ROLE IS TO HELP USERS UNDERSTAND MATLAB ERRORS SHOWN IN SCREENSHOTS, IN COMBINATION WITH THEIR WRITTEN QUERIES.

            ###OBJECTIVE###

            YOUR TASK IS TO EXAMINE A SCREENSHOT AND USER QUERY TO DETERMINE WHETHER IT IS RELATED TO MATLAB PROGRAMMING, THEN IF RELEVANT, PROVIDE A CLEAR AND DETAILED DESCRIPTION OF THE ERROR.

            ###WHEN TO ANALYZE VS. WHEN TO REJECT###

            - IF EITHER THE IMAGE OR THE QUERY IS CLEARLY UNRELATED TO MATLAB (e.g., no MATLAB code, no MATLAB error messages, no MATLAB-specific context):
            - RESPOND WITH:  
                `Irrelevant Question: This service is specifically designed to analyze MATLAB code errors. The provided image or query does not appear to be related to MATLAB.`  
            - DO NOT PROCEED WITH ANY ANALYSIS IF THIS APPLIES.

            - IF BOTH THE IMAGE AND THE QUERY ARE RELATED TO MATLAB:
            - CONTINUE WITH THE ERROR DESCRIPTION.

            ###HOW TO ANALYZE A VALID MATLAB ERROR###

            ONCE YOU HAVE DETERMINED THAT THE IMAGE AND QUERY ARE MATLAB-RELATED, FOLLOW THIS TROUBLESHOOTING STRUCTURE:

            ####CHAIN OF THOUGHTS####  
            1. **UNDERSTAND THE USER'S QUERY**: Identify what aspect of the error or code they are trying to understand.  
            2. **REVIEW THE SCREENSHOT**: Extract visible MATLAB-related content such as error messages, code, and variable names.  
            3. **IDENTIFY KEY DETAILS**:
            - Exact MATLAB error message
            - Line number or function/script mentioned
            - Any visible call stack
            - MATLAB error ID (if present)
            - Function or variable names relevant to the error
            4. **CONNECT TO USER'S QUERY**: Use the query to frame or clarify the error in context.  
            5. **COMPOSE A PRECISE, NEUTRAL DESCRIPTION**: Focus only on what the error is and what the screenshot shows. Do **not** offer solutions unless explicitly requested.

            ###RESPONSE FORMAT###

            FORMAT ALL OUTPUTS AS FOLLOWS:

            ## Error Description  
            - Briefly restate what the user seems to be asking  
            - Describe the MATLAB error visible in the screenshot using appropriate terminology  
            - Include specific elements (error text, line numbers, functions, variables, call stack, etc.)  
            - Keep the tone explanatory and neutral — no assumptions, no solutions

            ###WHAT NOT TO DO###

            - DO NOT ANALYZE SCREENSHOTS OR QUERIES THAT ARE NOT MATLAB-RELATED
            - DO NOT GUESS OR SPECULATE ABOUT SOLUTIONS
            - DO NOT PROVIDE DEBUGGING TIPS OR FIXES
            - DO NOT RESPOND WITH GENERIC ANSWERS UNRELATED TO THE ERROR MESSAGE
            - DO NOT SKIP ERROR DETAILS — ALWAYS INCLUDE ERROR TEXT, LINE INFO, AND CONTEXT IF VISIBLE

            ###EXAMPLES###

            ####✅ VALID CASE:  
            - Screenshot shows `Undefined function or variable 'fooVar'.`  
            - Query: *"Why am I getting this error when I run my script?"*  

            **Response:**  
            ## Error Description  
            The user is asking about an undefined variable error in their script.  
            The screenshot displays the MATLAB error message:  
            `Undefined function or variable 'fooVar'.`  
            This error typically occurs when the variable has not been declared before use.  
            It appears at line 12 of the script `myScript.m`, as shown in the call stack.

            ####❌ INVALID CASE:  
            - Screenshot of a Python traceback  
            - Query: *"What does this error mean?"*  

            **Response:**  
            `Irrelevant Question: This service is specifically designed to analyze MATLAB code errors. The provided image or query does not appear to be related to MATLAB.`

"""
    )
    image_bytes = base64.b64encode(image_bytes).decode("utf-8")
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_bytes}"
                    }
                }
            ]
        }
    ]

    # Call GPT-4o
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.2,
        max_tokens=512
    )

    # Extract response text
    return response.choices[0].message.content

# Define response models
class RetrievalResponse(BaseModel):
    response: str = Field(..., title="Determines if the query is related to MATLAB troubleshooting and should be retrieved from a MATLAB knowledge base?", description="Output only 'Yes' or 'No'.")

class RelevanceResponse(BaseModel):
    response: str = Field(..., title="Determines if context is relevant", 
                        description="Output only 'Relevant' or 'Irrelevant'.")

class GenerationResponse(BaseModel):
    response: str = Field(..., title="Generated response", description="The generated response.")

class SupportResponse(BaseModel):
    response: str = Field(..., title="Determines if response is supported",
                        description="Output 'Fully supported', 'Partially supported', or 'No support'.")

class UtilityResponse(BaseModel):
    response: int = Field(..., title="Utility rating", description="Rate the utility of the response from 1 to 5.")

class RetrievalEvaluatorInput(BaseModel):
    relevance_score: float = Field(..., description="Relevance score between 0 and 1, "
                                                   "indicating the document's relevance to the query.")

class QueryRewriterInput(BaseModel):
    query: str = Field(..., description="The query rewritten for better web search results.")

class KnowledgeRefinementInput(BaseModel):
    key_points: str = Field(..., description="Key information extracted from the document in bullet-point form.")

# Define prompt templates
retrieval_prompt = PromptTemplate(
    input_variables=["query"],
    template="Given the query '{query}', determine if retrieval is necessary. Output only 'Yes' or 'No'."
)

relevance_prompt = PromptTemplate(
    input_variables=["query", "context"],
    template="Given the query '{query}' and the context '{context}', determine if the context is relevant. Output only 'Relevant' or 'Irrelevant'."
)

generation_prompt = PromptTemplate(
    input_variables=["query", "context"],
    template="Given the query '{query}' and the context '{context}', generate a response."
)

support_prompt = PromptTemplate(
    input_variables=["response", "context"],
    template="Given the response '{response}' and the context '{context}', determine if the response is supported by the context. Output 'Fully supported', 'Partially supported', or 'No support'."
)

utility_prompt = PromptTemplate(
    input_variables=["query", "response"],
    template="Given the query '{query}' and the response '{response}', rate the utility of the response from 1 to 5."
)

class CombinedRAG:
    def __init__(self, faiss_index_path, model="gpt-4o-mini", max_tokens=1000, temperature=0, 
                 lower_threshold=0.3, upper_threshold=0.7, top_k=3):
        """
        Initialize the combined RAG system.
        
        Args:
            faiss_index_path (str): Path to the existing FAISS index
            model (str): LLM model to use
            max_tokens (int): Maximum tokens for generation
            temperature (float): Temperature for generation
            lower_threshold (float): Lower threshold for document relevance scores
            upper_threshold (float): Upper threshold for document relevance scores
            top_k (int): Number of documents to retrieve
        """
        print("Loading existing FAISS index...")
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(model_name="all-mpnet-base-v2")
            self.vectorstore = FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)
            print("Successfully loaded existing index")
        except Exception as e:
            print(f"Failed to load existing index: {str(e)}")
            raise ValueError("Failed to load index. Please check the path and try again.")
        
        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold
        self.top_k = top_k
        
        # Initialize language model
        self.llm = ChatOpenAI(model=model, max_tokens=max_tokens, temperature=temperature)
        
        # Initialize search tool for web retrieval
        self.search = DuckDuckGoSearchResults()
        
        # Create chains for self-RAG components
        self.retrieval_chain = retrieval_prompt | self.llm.with_structured_output(RetrievalResponse)
        self.relevance_chain = relevance_prompt | self.llm.with_structured_output(RelevanceResponse)
        self.generation_chain = generation_prompt | self.llm.with_structured_output(GenerationResponse)
        self.support_chain = support_prompt | self.llm.with_structured_output(SupportResponse)
        self.utility_chain = utility_prompt | self.llm.with_structured_output(UtilityResponse)

    def evaluate_document_relevance(self, query, document):
        """Evaluate document relevance with a numerical score (CRAG approach)"""
        prompt = PromptTemplate(
            input_variables=["query", "document"],
            template="On a scale from 0 to 1, how relevant is the following document to the query? "
                     "Query: {query}\nDocument: {document}\nRelevance score:"
        )
        chain = prompt | self.llm.with_structured_output(RetrievalEvaluatorInput)
        input_variables = {"query": query, "document": document}
        result = chain.invoke(input_variables).relevance_score
        return result
    
    def rewrite_query(self, query):
        """Rewrite query for web search (CRAG approach)"""
        prompt = PromptTemplate(
            input_variables=["query"],
            template="Rewrite the following query to make it more suitable for a web search:\n{query}\nRewritten query:"
        )
        chain = prompt | self.llm.with_structured_output(QueryRewriterInput)
        input_variables = {"query": query}
        return chain.invoke(input_variables).query.strip()
    
    def knowledge_refinement(self, document):
        """Extract key points from document (CRAG approach)"""
        prompt = PromptTemplate(
            input_variables=["document"],
            template="Extract the key information from the following document in bullet points:"
                     "\n{document}\nKey points:"
        )
        chain = prompt | self.llm.with_structured_output(KnowledgeRefinementInput)
        input_variables = {"document": document}
        result = chain.invoke(input_variables).key_points
        return [point.strip() for point in result.split('\n') if point.strip()]
    
    def perform_web_search(self, query):
        """Perform web search with a rewritten query (CRAG approach)"""
        rewritten_query = self.rewrite_query(query)
        print(f"Rewritten query for web search: {rewritten_query}")
        web_results = self.search.run(rewritten_query)
        
        # Process and extract knowledge from web results
        web_knowledge = "\n".join(self.knowledge_refinement(web_results))
        
        # Extract sources from web results
        import json
        try:
            results = json.loads(web_results)
            sources = [(result.get('title', 'Untitled'), result.get('link', '')) for result in results]
        except json.JSONDecodeError:
            print("Error parsing search results")
            sources = []
            
        return web_knowledge, sources
    
    def run(self, query):
        """
        Run the combined RAG system on a query.
        
        This combines both Self-RAG's step-by-step evaluation and CRAG's relevance scoring
        and web search capabilities.
        
        Args:
            query (str): The user's query
            
        Returns:
            dict: Dictionary containing final_response, reference_links, and relevant_docs
        """
        print(f"\nProcessing query: {query}")
        result = {
            "final_response": "",
            "reference_links": [],
            "relevant_docs": []
        }

        # Step 1: Determine if retrieval is necessary (Self-RAG)
        print("Step 1: Determining if retrieval is necessary...")
        input_data = {"query": query}
        retrieval_decision = self.retrieval_chain.invoke(input_data).response.strip().lower()
        print(f"Retrieval decision: {retrieval_decision}")

        if retrieval_decision == 'yes':
            # Step 2: Retrieve relevant documents
            print("Step 2: Retrieving relevant documents...")
            docs = self.vectorstore.similarity_search(query, k=self.top_k)
            contexts = [(doc.page_content, doc.metadata) for doc in docs]

            for doc in docs: print(doc.metadata)
            print(f"Retrieved {len(contexts)} documents")

            # Step 3: Evaluate document relevance using CRAG's numerical scoring
            print("Step 3: Evaluating relevance of retrieved documents...")
            relevant_contexts = []
            eval_scores = []
            
            for i, (context, metadata) in enumerate(contexts):
                # Get numerical relevance score (CRAG approach)
                score = self.evaluate_document_relevance(query, context)
                eval_scores.append(score)
                print(f"Document {i + 1} relevance score: {score}")
                
                # Add to relevant docs list if score is decent (above lower threshold)
                if score >= self.lower_threshold:
                    doc_info = {
                        "content_preview": context[:200] + "..." if len(context) > 200 else context,
                        "score": score,
                        "url": metadata.get('parent_url', 'No URL available')
                    }
                    result["relevant_docs"].append(doc_info)
                
                # Also check binary relevance (Self-RAG approach)
                input_data = {"query": query, "context": context}
                relevance = self.relevance_chain.invoke(input_data).response.strip().lower()
                print(f"Document {i + 1} binary relevance: {relevance}")
                
                if relevance == 'relevant':
                    relevant_contexts.append((context, metadata, score))
            
            # CRAG approach: determine action based on max score
            max_score = max(eval_scores) if eval_scores else 0
            
            # If no relevant contexts or max score below lower threshold
            if not relevant_contexts or max_score < self.lower_threshold:
                print("No relevant contexts found or relevance score too low. Performing web search...")
                web_knowledge, web_sources = self.perform_web_search(query)
                
                # Add web sources to reference links
                for title, link in web_sources:
                    if link:  # Only add if link exists
                        result["reference_links"].append({"title": title, "url": link})
                
                # Generate response using web knowledge
                print("Generating response using web knowledge...")
                sources_text = "\n".join([f"{title}: {link}" if link else title for title, link in web_sources])
                input_data = {
                    "query": query, 
                    "context": f"Web search results:\n{web_knowledge}\n\nSources:\n{sources_text}"
                }
                result["final_response"] = self.generation_chain.invoke(input_data).response
                return result
            
            # If max score between thresholds, combine retrieved and web knowledge
            elif self.lower_threshold <= max_score < self.upper_threshold:
                print("Document relevance score in ambiguous range. Combining retrieved and web knowledge...")
                
                # Get best document
                best_context = max(relevant_contexts, key=lambda x: x[2])
                retrieved_knowledge = "\n".join(self.knowledge_refinement(best_context[0]))
                
                # Add best context source to reference links
                doc_url = best_context[1].get('url', 'No URL available')
                if doc_url != 'No URL available':
                    result["reference_links"].append({"title": "Retrieved document", "url": doc_url})
                
                # Get web knowledge
                web_knowledge, web_sources = self.perform_web_search(query)
                
                # Add web sources to reference links
                for title, link in web_sources:
                    if link:  # Only add if link exists
                        result["reference_links"].append({"title": title, "url": link})
                
                # Combine knowledge sources
                combined_context = f"Retrieved knowledge:\n{retrieved_knowledge}\n\nWeb knowledge:\n{web_knowledge}"
                sources_text = f"Retrieved from database: {best_context[1].get('url', 'No URL available')}\n"
                sources_text += "\n".join([f"Web: {title}: {link}" if link else f"Web: {title}" for title, link in web_sources])
                
                # Generate response
                print("Generating response using combined knowledge...")
                input_data = {"query": query, "context": f"{combined_context}\n\nSources:\n{sources_text}"}
                result["final_response"] = self.generation_chain.invoke(input_data).response
                return result
            
            # If score above upper threshold, proceed with Self-RAG process for retrieved docs
            else:
                print("Document relevance score high. Using retrieved documents with Self-RAG process...")
                
                # Step 4-6: Follow Self-RAG approach for response generation
                print("Step 4: Generating responses using relevant contexts...")
                responses = []
                for i, (context, metadata, score) in enumerate(relevant_contexts):
                    print(f"Generating response for context {i + 1}...")
                    input_data = {"query": query, "context": context}
                    response = self.generation_chain.invoke(input_data).response

                    # Step 5: Assess support
                    print(f"Step 5: Assessing support for response {i + 1}...")
                    input_data = {"response": response, "context": context}
                    support = self.support_chain.invoke(input_data).response.strip().lower()
                    print(f"Support assessment: {support}")

                    # Step 6: Evaluate utility
                    print(f"Step 6: Evaluating utility for response {i + 1}...")
                    input_data = {"query": query, "response": response}
                    utility = int(self.utility_chain.invoke(input_data).response)
                    print(f"Utility score: {utility}")

                    responses.append((response, support, utility, metadata))

                # Select the best response based on support and utility
                print("Selecting the best response...")
                best_response = max(responses, key=lambda x: (x[1] == 'fully supported', x[2]))
                print(f"Best response support: {best_response[1]}, utility: {best_response[2]}")
                
                # Add source information
                source_url = best_response[3].get('url', 'No source URL available')
                if source_url != 'No source URL available':
                    result["reference_links"].append({"title": "Primary source", "url": source_url})
                
                result["final_response"] = best_response[0]
                return result
        else:
            # Generate without retrieval
            print("Generating without retrieval...")
            input_data = {"query": query, "context": "No retrieval necessary."}
            result["final_response"] = self.generation_chain.invoke(input_data).response
            return result


# Argument parsing functions
def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Combined RAG method")
    parser.add_argument('--index_path', type=str, required=True, 
                        help='Path to existing FAISS index')
    parser.add_argument('--query', type=str, 
                        default="Error: Cannot connect to target 'TargetPC1': Cannot connect to target.",
                        help='Query to be processed')
    parser.add_argument('--model', type=str, default="gpt-4o-mini",
                        help='LLM model to use')
    return parser.parse_args()


# Main entry point
if __name__ == "__main__":
    with open('test.png', 'rb') as f:
      image_bytes = f.read()

    args = parse_args()
    args.query = generate_prompt("Solve this", image_bytes)
    rag = CombinedRAG(
        faiss_index_path=args.index_path,
        model=args.model
    )
    result = rag.run(args.query)
    
    print("\n--- Final Output ---")
    print("\nResponse:")
    print(result["final_response"])
    
    if result["reference_links"]:
        print("\nReference Links:")
        for ref in result["reference_links"]:
            print(f"- {ref['title']}: {ref['url']}")
    else:
        print("\nReference Links: None")
    
    if result["relevant_docs"]:
        print("\nRelevant Documents:")
        for i, doc in enumerate(sorted(result["relevant_docs"], key=lambda x: x["score"], reverse=True)):
            print(f"\n[{i+1}] Score: {doc['score']:.2f}")
            print(f"URL: {doc['url']}")
            print(f"Preview: {doc['content_preview']}")
    else:
        print("\nRelevant Documents: None")
    
    print("\nJSON Output:")
    import json
    print(json.dumps(result, indent=2))