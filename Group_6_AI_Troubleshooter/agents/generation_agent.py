"""
Generation Agent for creating responses based on retrieved information.
"""
from typing import List, Dict, Any, Optional
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from agents.base_agent import BaseAgent
from agents.models import Document, WebSearchResult, ReferenceLink

class GenerationResponse(BaseModel):
    """Response model for generated content"""
    response: str = Field(..., 
                         title="Generated response", 
                         description="The generated response.")

class GenerationAgent(BaseAgent):
    """Agent for generating responses based on retrieved information"""
    
    def __init__(self, model="gpt-4o-mini"):
        """
        Initialize the generation agent.
        
        Args:
            model (str): LLM model to use for generating responses
        """
        super().__init__("GenerationAgent")
        self.llm = ChatOpenAI(model=model, max_tokens=1000, temperature=0)
        
        # Create generation chain
        self.generation_prompt = PromptTemplate(
            input_variables=["query", "context"],
            template="Given the query '{query}' and the context '{context}', generate a comprehensive and accurate response."
        )
        self.generation_chain = self.generation_prompt | self.llm.with_structured_output(GenerationResponse)
    
    def _prepare_kb_context(self, query: str, documents: List[Document], scores: List[float]) -> Dict[str, Any]:
        """
        Prepare context from knowledge base documents.
        
        Args:
            query (str): The user's query
            documents (List[Document]): List of retrieved documents
            scores (List[float]): Relevance scores for documents
            
        Returns:
            Dict: Dictionary with context and sources
        """
        # Sort documents by relevance score
        doc_score_pairs = list(zip(documents, scores))
        sorted_pairs = sorted(doc_score_pairs, key=lambda pair: pair[1], reverse=True)
        
        # Extract content from documents
        content_parts = []
        sources = []
        
        for doc, score in sorted_pairs:
            content_parts.append(f"Document (relevance: {score:.2f}):\n{doc.content}")
            
            # Add source if available
            url = doc.metadata.get('source_url', '')
            if url:
                sources.append(ReferenceLink(
                    title=f"Document (score: {score:.2f})",
                    url=url
                ))
        
        context = "\n\n".join(content_parts)
        return {
            "context": context, 
            "sources": sources
        }
    
    def generate_from_kb(self, query: str, documents: List[Document], scores: List[float], conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate response from knowledge base documents.
        
        Args:
            query (str): The user's query
            documents (List[Document]): List of retrieved documents
            scores (List[float]): Relevance scores for documents
            
        Returns:
            Dict: Dictionary with generated response and sources
        """
        self.log("Generating response from knowledge base documents")
        
        # Prepare context from documents
        context_data = self._prepare_kb_context(query, documents, scores)
        
        # Generate response
        input_data = {"query": query, "context": context_data["context"]}
        # Include conversation history if provided
        if conversation_history:
            input_data["history"] = conversation_history
            self.log(f"Conversation history length: {len(conversation_history)}")
        
        response = self.generation_chain.invoke(input_data).response
        
        return {
            "response": response,
            "sources": context_data["sources"]
        }
    
    def generate_from_web(self, query: str, web_result: WebSearchResult,conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate response from web search results.
        
        Args:
            query (str): The user's query
            web_result (WebSearchResult): Web search result
            
        Returns:
            Dict: Dictionary with generated response and sources
        """
        self.log("Generating response from web search results")
        
        # Prepare context
        sources_text = "\n".join([f"{source.title}: {source.url}" for source in web_result.sources])
        context = f"Web search results:\n{web_result.knowledge}\n\nSources:\n{sources_text}"
        
        # Generate response
        input_data = {"query": query, "context": context}
        # Include conversation history if provided
        if conversation_history:
            input_data["history"] = conversation_history
            self.log(f"Conversation history length: {len(conversation_history)}")

        response = self.generation_chain.invoke(input_data).response
        
        return {
            "response": response,
            "sources": web_result.sources
        }
    
    def generate_hybrid(self, query: str, documents: List[Document], scores: List[float], 
                       web_result: WebSearchResult,conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate hybrid response from both knowledge base and web search.
        
        Args:
            query (str): The user's query
            documents (List[Document]): List of retrieved documents
            scores (List[float]): Relevance scores for documents
            web_result (WebSearchResult): Web search result
            
        Returns:
            Dict: Dictionary with generated response and sources
        """
        self.log("Generating hybrid response from KB documents and web search")
        
        # Prepare KB context
        kb_context = self._prepare_kb_context(query, documents, scores)
        
        # Combine contexts
        combined_context = (
            f"Knowledge Base Information:\n{kb_context['context']}\n\n"
            f"Web Search Information:\n{web_result.knowledge}"
        )
        
        # Generate response
        input_data = {"query": query, "context": combined_context}
        # Include conversation history if provided
        if conversation_history:
            input_data["history"] = conversation_history
            self.log(f"Conversation history length: {len(conversation_history)}")

        response = self.generation_chain.invoke(input_data).response
        
        # Combine sources
        sources = kb_context["sources"] + web_result.sources
        
        return {
            "response": response,
            "sources": sources
        }
    
    def generate_without_context(self, query: str,conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate response without any context.
        
        Args:
            query (str): The user's query
            
        Returns:
            Dict: Dictionary with generated response and empty sources
        """
        self.log("Generating response without context")
        
        # Generate response
        input_data = {"query": query, "context": "No specific context available."}
        # Include conversation history if provided
        if conversation_history:
            input_data["history"] = conversation_history
            self.log(f"Conversation history length: {len(conversation_history)}")

        response = self.generation_chain.invoke(input_data).response
        
        return {
            "response": response,
            "sources": []
        }
    
    def run(self, query: str, strategy: str, documents: List[Document] = None, 
           scores: List[float] = None, web_result: WebSearchResult = None,conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Run the generation agent with the specified strategy.
        
        Args:
            query (str): The user's query
            strategy (str): Strategy to use ('kb_only', 'web_only', 'hybrid', or 'none')
            documents (List[Document], optional): Retrieved documents
            scores (List[float], optional): Relevance scores
            web_result (WebSearchResult, optional): Web search result
            
        Returns:
            Dict: Dictionary with generated response and sources
        """
        self.log(f"Generating response using strategy: {strategy}")
        
        if strategy == 'kb_only':
            return self.generate_from_kb(query, documents, scores,conversation_history)
        elif strategy == 'web_only':
            return self.generate_from_web(query, web_result,conversation_history)
        elif strategy == 'hybrid':
            return self.generate_hybrid(query, documents, scores, web_result,conversation_history)
        else:  # 'none'
            return self.generate_without_context(query,conversation_history)