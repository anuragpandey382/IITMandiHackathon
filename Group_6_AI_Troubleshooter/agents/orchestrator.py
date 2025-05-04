"""
Main orchestrator that coordinates all agents in the RAG system.
"""
import os
from typing import Dict, List, Any, Optional
import json

from agents.base_agent import BaseAgent
from agents.image_analysis_agent import ImageAnalysisAgent
from agents.retrieval_agent import RetrievalAgent
from agents.evaluation_agent import EvaluationAgent
from agents.web_search_agent import WebSearchAgent
from agents.generation_agent import GenerationAgent
from agents.models import Document, QueryResult, ReferenceLink, RelevantDocument

class Orchestrator(BaseAgent):
    """
    Main orchestrator that coordinates all agents in the RAG system.
    
    This class is responsible for coordinating the workflow between all specialized agents
    to process a user query and generate a response using appropriate retrieval strategies.
    """
    
    def __init__(self, faiss_index_path: str, model: str = "gpt-4o-mini", 
                lower_threshold: float = 0.3, upper_threshold: float = 0.7):
        """
        Initialize the orchestrator with all required agents.
        
        Args:
            faiss_index_path (str): Path to the FAISS index
            model (str): LLM model to use
            lower_threshold (float): Lower threshold for document relevance
            upper_threshold (float): Upper threshold for document relevance
        """
        super().__init__("Orchestrator")
        
        self.log("Initializing RAG system components")
        
        # Initialize all agents
        self.image_agent = ImageAnalysisAgent()
        self.retrieval_agent = RetrievalAgent(faiss_index_path, model=model)
        self.evaluation_agent = EvaluationAgent(model=model, 
                                               lower_threshold=lower_threshold, 
                                               upper_threshold=upper_threshold)
        self.web_search_agent = WebSearchAgent(model=model)
        self.generation_agent = GenerationAgent(model=model)
    
    def process_image(self, query: str, image_bytes: bytes) -> str:
        """
        Process an image using the image analysis agent.
        
        Args:
            query (str): Query about the image
            image_bytes (bytes): Raw image bytes
            
        Returns:
            str: Analysis of the image
        """
        self.log("Processing image")
        return self.image_agent.run(query, image_bytes)
    
    def run(self, query: str, image_bytes: Optional[bytes] = None,conversation_history: Optional[List[Dict[str, Any]]] = None) -> QueryResult:
        """
        Process a query and generate a response using the RAG system.
        
        Args:
            query (str): User query
            image_bytes (Optional[bytes]): Optional image data
            
        Returns:
            QueryResult: Final result containing response and references
        """
        self.log(f"Processing query: {query}")
        # Process image if provided
        if image_bytes:
            self.log("Image detected, processing image")
            query = self.process_image(query, image_bytes)
            self.log(f"Image analysis complete, new query: {query[:100]}...")
        
        # Step 1: Determine if retrieval is necessary and retrieve documents
        retrieval_performed, documents = self.retrieval_agent.run(query)
        
        # If retrieval wasn't necessary, generate a response directly
        if not retrieval_performed:
            self.log("Retrieval not necessary, generating direct response")
            generation_result = self.generation_agent.run(query,conversation_history ,"none")
            
            return QueryResult(
                final_response=generation_result["response"],
                reference_links=generation_result["sources"],
                relevant_docs=[]
            )
        
        # Step 2: Evaluate document relevance
        eval_result = self.evaluation_agent.run(query, documents)
        strategy = eval_result["retrieval_strategy"]
        relevance_scores = eval_result["relevance_scores"]
        
        # Step 3: Process according to determined strategy
        web_result = None
        if strategy in ["web_only", "hybrid"]:
            self.log(f"Strategy {strategy} requires web search")
            web_result = self.web_search_agent.run(query)
        
        # Step 4: Generate response based on strategy
        scores = [score.score for score in relevance_scores]
        
        generation_result = self.generation_agent.run(
            query=query,
            strategy=strategy,
            documents=documents if strategy in ["kb_only", "hybrid"] else None,
            scores=scores if strategy in ["kb_only", "hybrid"] else None,
            web_result=web_result if strategy in ["web_only", "hybrid"] else None,
            conversation_history=conversation_history
        )
        
        # Step 5: Prepare final result
        final_response = generation_result["response"]
        reference_links = generation_result["sources"]
        
        # Add relevant documents to the result
        relevant_docs = []
        for i, (doc, score) in enumerate(zip(documents, scores)):
            if score >= self.evaluation_agent.lower_threshold:
                relevant_docs.append(RelevantDocument(
                    content_preview=doc.preview(),
                    score=score,
                    url=doc.metadata.get('url', 'No URL available')
                ))
        
        # Sort relevant docs by score in descending order
        relevant_docs = sorted(relevant_docs, key=lambda x: x.score, reverse=True)
        
        self.log("Query processing complete")
        return QueryResult(
            final_response=final_response,
            reference_links=reference_links,
            relevant_docs=relevant_docs
        )