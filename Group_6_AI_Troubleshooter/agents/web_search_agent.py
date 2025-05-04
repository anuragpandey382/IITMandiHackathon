"""
Web Search Agent for retrieving information from the web.
"""
import json
from typing import List, Tuple
from langchain_community.tools import DuckDuckGoSearchResults
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from agents.base_agent import BaseAgent
from agents.models import ReferenceLink, WebSearchResult

class QueryRewriterInput(BaseModel):
    """Input model for query rewriting"""
    query: str = Field(..., 
                      description="The query rewritten for better web search results.")

class KnowledgeRefinementInput(BaseModel):
    """Input model for knowledge refinement"""
    key_points: str = Field(..., 
                           description="Key information extracted from the document in bullet-point form.")

class WebSearchAgent(BaseAgent):
    """Agent for searching the web for information"""
    
    def __init__(self, model="gpt-4o-mini"):
        """
        Initialize the web search agent.
        
        Args:
            model (str): LLM model to use for query rewriting and knowledge refinement
        """
        super().__init__("WebSearchAgent")
        self.llm = ChatOpenAI(model=model, temperature=0)
        self.search_tool = DuckDuckGoSearchResults()
        
        # Create query rewriting chain
        self.query_rewrite_prompt = PromptTemplate(
            input_variables=["query"],
            template="Rewrite the following query to make it more suitable for a web search:\n{query}\nRewritten query:"
        )
        self.query_rewrite_chain = self.query_rewrite_prompt | self.llm.with_structured_output(QueryRewriterInput)
        
        # Create knowledge refinement chain
        self.knowledge_refinement_prompt = PromptTemplate(
            input_variables=["document"],
            template="Extract the key information from the following document in bullet points:"
                     "\n{document}\nKey points:"
        )
        self.knowledge_refinement_chain = self.knowledge_refinement_prompt | self.llm.with_structured_output(KnowledgeRefinementInput)
    
    def rewrite_query(self, query: str) -> str:
        """
        Rewrite a query to make it more suitable for web search.
        
        Args:
            query (str): Original query
            
        Returns:
            str: Rewritten query
        """
        self.log(f"Rewriting query: {query}")
        input_data = {"query": query}
        rewritten_query = self.query_rewrite_chain.invoke(input_data).query.strip()
        self.log(f"Rewritten query: {rewritten_query}")
        return rewritten_query
    
    def extract_knowledge(self, document: str) -> List[str]:
        """
        Extract key knowledge points from a document.
        
        Args:
            document (str): Document text
            
        Returns:
            List[str]: Key points extracted from the document
        """
        self.log("Extracting key points from document")
        input_data = {"document": document}
        result = self.knowledge_refinement_chain.invoke(input_data).key_points
        key_points = [point.strip() for point in result.split('\n') if point.strip()]
        self.log(f"Extracted {len(key_points)} key points")
        return key_points
    
    def extract_sources(self, web_results: str) -> List[ReferenceLink]:
        """
        Extract sources from web search results.
        
        Args:
            web_results (str): Raw web search results
            
        Returns:
            List[ReferenceLink]: List of reference links
        """
        try:
            results = json.loads(web_results)
            sources = []
            for result in results:
                title = result.get('title', 'Untitled')
                link = result.get('link', '')
                if link:
                    sources.append(ReferenceLink(title=title, url=link))
                    
            return sources
        except json.JSONDecodeError:
            self.log("Error parsing search results")
            return []
    
    def run(self, query: str) -> WebSearchResult:
        """
        Run web search for a query.
        
        Args:
            query (str): The user's query
            
        Returns:
            WebSearchResult: Web search result containing knowledge and sources
        """
        rewritten_query = self.rewrite_query(query)
        self.log(f"Performing web search with query: {rewritten_query}")
        
        # Perform web search
        web_results = self.search_tool.run(rewritten_query)
        self.log("Web search complete")
        
        # Extract knowledge
        key_points = self.extract_knowledge(web_results)
        web_knowledge = "\n".join(key_points)
        
        # Extract sources
        sources = self.extract_sources(web_results)
        self.log(f"Found {len(sources)} sources")
        
        return WebSearchResult(knowledge=web_knowledge, sources=sources)