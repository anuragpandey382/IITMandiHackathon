"""
Retrieval Agent for retrieving relevant documents.
"""
from typing import List, Tuple
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from agents.base_agent import BaseAgent
from agents.models import Document

class RetrievalResponse(BaseModel):
    """Response model for retrieval decision"""
    response: str = Field(..., 
                          title="Determines if retrieval is necessary",
                          description="Output only 'Yes' or 'No'.")

class RetrievalAgent(BaseAgent):
    """Agent for retrieving relevant documents"""
    
    def __init__(self, faiss_index_path, model="gpt-4o-mini"):
        """
        Initialize the retrieval agent.
        
        Args:
            faiss_index_path (str): Path to the FAISS index
            model (str): LLM model to use for decisions
        """
        super().__init__("RetrievalAgent")
        self.llm = ChatOpenAI(model=model, temperature=0)
        self.faiss_index_path = faiss_index_path
        self.top_k = 3
        
        # Initialize vector store
        try:
            self.log(f"Loading FAISS index from {faiss_index_path}")
            from langchain_huggingface import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(model_name="all-mpnet-base-v2")
            self.vectorstore = FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)
            self.log("Successfully loaded FAISS index")
        except Exception as e:
            self.log(f"Failed to load FAISS index: {str(e)}")
            raise ValueError(f"Failed to load FAISS index: {str(e)}")
        
        # Create retrieval decision chain
        self.retrieval_prompt = PromptTemplate(
            input_variables=["query"],
            template="Given the query '{query}', determine if retrieval is necessary. Output only 'Yes' or 'No'."
        )
        self.retrieval_chain = self.retrieval_prompt | self.llm.with_structured_output(RetrievalResponse)
    
    def should_retrieve(self, query: str) -> bool:
        """
        Determine if retrieval is necessary for this query.
        
        Args:
            query (str): The user's query
            
        Returns:
            bool: True if retrieval is necessary, False otherwise
        """
        self.log(f"Determining if retrieval is necessary for query: {query}")
        input_data = {"query": query}
        retrieval_decision = self.retrieval_chain.invoke(input_data).response.strip().lower()
        self.log(f"Retrieval decision: {retrieval_decision}")
        return retrieval_decision == 'yes'
    
    def retrieve_documents(self, query: str) -> List[Document]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query (str): The user's query
            
        Returns:
            List[Document]: Retrieved documents
        """
        self.log(f"Retrieving documents for query: {query}")
        raw_docs = self.vectorstore.similarity_search(query, k=self.top_k)
        
        # Convert to our Document model
        docs = []
        for doc in raw_docs:
            docs.append(Document(
                content=doc.page_content,
                metadata=doc.metadata
            ))
            
        self.log(f"Retrieved {len(docs)} documents")
        return docs
    
    def run(self, query: str) -> Tuple[bool, List[Document]]:
        """
        Run retrieval process for a query.
        
        Args:
            query (str): The user's query
            
        Returns:
            Tuple[bool, List[Document]]: A tuple containing:
                - Boolean indicating if retrieval was performed
                - List of retrieved documents (empty if retrieval wasn't performed)
        """
        should_retrieve = self.should_retrieve(query)
        
        if not should_retrieve:
            self.log("Retrieval deemed unnecessary")
            return False, []
            
        documents = self.retrieve_documents(query)
        return True, documents