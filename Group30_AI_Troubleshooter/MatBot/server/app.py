import torch
from typing import Dict, List, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig
from langchain_huggingface import HuggingFaceEmbeddings  # Updated import
from langchain_chroma import Chroma  # Updated import
from langchain.schema import Document
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.tools.tavily_search import TavilySearchResults

# -------------------- Load Embeddings + Chroma Vectorstore --------------------
def load_embedding_model(persist_dir="Embed-all-Act/chroma_index"):
    """
    Loads the embedding model and Chroma vectorstore.
    Args:
        persist_dir (str): Directory to persist the Chroma index.
    Returns:
        tuple: Embedding model and Chroma vectorstore instance.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🔄 Loading embedding model on {device}...")

    try:
        embedding_model = HuggingFaceEmbeddings(
            model_name="BAAI/bge-base-en-v1.5",
            model_kwargs={"device": device}
        )

        vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=embedding_model
        )
        return embedding_model, vectorstore
    except Exception as e:
        raise RuntimeError(f"Failed to load embedding model or vectorstore: {e}")

# -------------------- Load Mistral Model --------------------
def load_mistral_model(model_id="mistralai/Mistral-7B-Instruct-v0.2", use_4bit=True):
    """
    Loads the Mistral model for text generation.
    Args:
        model_id (str): Model identifier.
        use_4bit (bool): Whether to use 4-bit quantization.
    Returns:
        pipeline: Text generation pipeline.
    """
    print(f"🔄 Loading {model_id}...")

    try:
        if use_4bit:
            quant_config = BitsAndBytesConfig(
                load_in_4bit=True, 
                bnb_4bit_compute_dtype=torch.float16
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map="auto",
                quantization_config=quant_config,
                torch_dtype=torch.float16
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map="auto",
                torch_dtype=torch.float16
            )

        tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
        tokenizer.pad_token = tokenizer.eos_token

        text_gen = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device_map="auto",
            max_new_tokens=1024,
            do_sample=True,
            temperature=0.3,
            top_k=50,
            top_p=0.95,
            repetition_penalty=1.2,
            pad_token_id=tokenizer.eos_token_id
        )
        return text_gen
    except Exception as e:
        raise RuntimeError(f"Failed to load Mistral model: {e}")

# -------------------- Prompt Formatter --------------------
from typing import Optional

def format_prompt(question: str, context: str, additional_web_context: Optional[str] = None) -> str:
    """
    Creates a well-structured prompt for the Mistral model that will return nicely formatted Markdown.
    
    Args:
        question (str): User's question.
        context (str): Documentation context.
        additional_web_context (Optional[str]): Additional context from web search.
    
    Returns:
        str: Formatted prompt that encourages structured Markdown responses.
    """
    cleaned_context = context.strip()
    
    web_context_section = ""
    if additional_web_context:
        web_context_section = f"""
        ## Additional Information From Web Search:
        
        
        {additional_web_context}
        
        """
    
    return f"""<s>[INST] You are an expert technical assistant specializing in MATLAB, programming, and data analysis. 

            System Instructions:
            1. Answer the user's question based primarily on the provided documentation context.
            2. If the documentation context is insufficient, use any additional web search information provided.
            3. Provide practical, step-by-step solutions.
            4. Include relevant code examples when helpful.
            5. If you're unsure or if information is missing, acknowledge the limitations in your answer.
            6. Format your response in well-structured Markdown to make it easily readable on the web.
            7. Focus on technical accuracy and precision.
            8. While responding write only the MATLAB code in '' code block.
            9. Do not include any other text in the code block.
            10. Ensure good formatting and readability in your response and have good spacing too.
            

            ## Documentation Context:

            code
            {cleaned_context}
            
            {web_context_section}
            ## User Question: 
            {question} [/INST]
        """
        

# -------------------- Query Database --------------------
def query_database(query: str, embedding_model, vectorstore, k: int = 5) -> List[Document]:
    """
    Queries the database for top-k similar documents.
    Args:
        query (str): User query.
        embedding_model: Embedding model instance.
        vectorstore: Chroma vectorstore instance.
        k (int): Number of top results to return.
    Returns:
        List[Document]: Top-k similar documents.
    """
    print("🔎 Embedding user query and searching database...")
    embedded_query = embedding_model.embed_query(query)
    docs = vectorstore.similarity_search_by_vector(embedded_query, k=k)
    print(f"✅ Found {len(docs)} relevant documents")
    return docs

# -------------------- Web Search Function --------------------
def search_web(query: str, tavily_api_key: str) -> Dict[str, str]:
    """
    Performs a web search and Wikipedia search for additional context.
    Args:
        query (str): User query.
        tavily_api_key (str): Tavily API key.
    Returns:
        Dict[str, str]: Combined context from web and Wikipedia.
    """
    if not tavily_api_key:
        print("⚠ No Tavily API key provided, skipping web search")
        return {"context": ""}
        
    print("🌐 Performing web search for additional context...")
    
    # Wikipedia Search
    wiki_context = ""
    try:
        wiki_docs = WikipediaLoader(query=query, load_max_docs=2).load()
        if wiki_docs:
            wiki_context = "\n\n".join([
                f'From Wikipedia ({doc.metadata["source"]}):\n{doc.page_content}'
                for doc in wiki_docs
            ])
    except Exception as e:
        print(f"⚠ Wikipedia search error: {str(e)}")

    # Web Search via Tavily
    web_context = ""
    try:
        tavily_search = TavilySearchResults(max_results=3, tavily_api_key=tavily_api_key)
        web_docs = tavily_search.invoke(query)
        if web_docs:
            web_context = "\n\n".join([
                f'From {doc["url"]}:\n{doc["content"]}'
                for doc in web_docs
            ])
    except Exception as e:
        print(f"⚠ Tavily search error: {str(e)}")

    # Combine contexts
    combined_context = "\n\n".join(filter(None, [wiki_context, web_context]))
    return {"context": combined_context}

# -------------------- Main Function --------------------
def generate_response(user_query: str, embedding_model=None, vectorstore=None, model_pipeline=None, 
                      tavily_api_key: str ="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", use_web_search: bool = False) -> str:
    """
    Generates a response to the user's query.
    Args:
        user_query (str): User's question.
        embedding_model: Preloaded embedding model.
        vectorstore: Preloaded vectorstore.
        model_pipeline: Preloaded model pipeline.
        tavily_api_key (str): Tavily API key.
        use_web_search (bool): Whether to use web search.
    Returns:
        str: Generated response.
    """
    # Load models if not provided
    if embedding_model is None or vectorstore is None:
        embedding_model, vectorstore = load_embedding_model()
    
    if model_pipeline is None:
        model_pipeline = load_mistral_model()

    # Perform similarity search
    top_docs = query_database(user_query, embedding_model, vectorstore, k=5)
    combined_context = "\n".join(doc.page_content for doc in top_docs)
    
    # Perform web search if enabled
    web_context = ""
    if use_web_search:
        web_results = search_web(user_query, tavily_api_key)
        web_context = web_results["context"]
    
    # Create prompt
    prompt = format_prompt(user_query, combined_context, web_context)
    
    # Generate response
    print("🧠 Generating response...")
    result = model_pipeline(prompt)[0]['generated_text']
    used_metadata = [doc.metadata for doc in top_docs]
    
    # Extract assistant's response
    response_start = result.find("[/INST]")
    response = result[response_start + len("[/INST]"):].strip() if response_start != -1 else result

    # Format response to include code blocks
    response = response.replace("", "<pre>").replace("```", "</pre>")
    return response, used_metadata

# -------------------- Command Line Interface --------------------
if _name_ == "_main_":
    tavily_api_key = "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"  # Replace with your API key or use os.getenv()
    use_web = input("🌐 Use web search? (y/n): ").strip().lower().startswith("y")

    # Load models once
    embedding_model, vectorstore = load_embedding_model()
    model_pipeline = load_mistral_model()

    while True:
        user_input = input("\n📝 Your question (or type 'q' to quit): ")
        if user_input.strip().lower() in {"q", "quit", "exit"}:
            print("👋 Exiting. Have a great day!")
            break

        response, used_metadata = generate_response(
            user_query=user_input,
            embedding_model=embedding_model,
            vectorstore=vectorstore,
            model_pipeline=model_pipeline,
            use_web_search=use_web
        )
        print("\n🤖 Response:\n", response)
        
        print("\n📄 Used Metadata:", used_metadata)
