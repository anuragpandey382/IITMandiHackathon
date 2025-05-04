"""
Evaluation Agent for assessing document relevance, support, and utility.
"""
from typing import Dict, List
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from agents.base_agent import BaseAgent
from agents.models import Document, RelevanceScore

class RelevanceResponse(BaseModel):
    """Response model for relevance evaluation"""
    response: str = Field(..., 
                          title="Determines if context is relevant", 
                          description="Output only 'Relevant' or 'Irrelevant'.")

class RetrievalEvaluatorInput(BaseModel):
    """Input model for numerical relevance scoring"""
    relevance_score: float = Field(..., 
                                  description="Relevance score between 0 and 1, "
                                  "indicating the document's relevance to the query.")

class SupportResponse(BaseModel):
    """Response model for support assessment"""
    response: str = Field(..., 
                          title="Determines if response is supported",
                          description="Output 'Fully supported', 'Partially supported', or 'No support'.")

class UtilityResponse(BaseModel):
    """Response model for utility rating"""
    response: int = Field(..., 
                         title="Utility rating", 
                         description="Rate the utility of the response from 1 to 5.")

class EvaluationAgent(BaseAgent):
    """Agent for evaluating document relevance, support, and utility"""
    
    def __init__(self, model="gpt-4o-mini", lower_threshold=0.3, upper_threshold=0.7):
        """
        Initialize the evaluation agent.
        
        Args:
            model (str): LLM model to use
            lower_threshold (float): Lower threshold for relevance scores
            upper_threshold (float): Upper threshold for relevance scores
        """
        super().__init__("EvaluationAgent")
        self.llm = ChatOpenAI(model=model, temperature=0)
        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold
        
        # Create evaluation chains
        self.relevance_prompt = PromptTemplate(
            input_variables=["query", "context"],
            template="Given the query '{query}' and the context '{context}', determine if the context is relevant. Output only 'Relevant' or 'Irrelevant'."
        )
        self.relevance_chain = self.relevance_prompt | self.llm.with_structured_output(RelevanceResponse)
        
        self.numerical_relevance_prompt = PromptTemplate(
            input_variables=["query", "document"],
            template="On a scale from 0 to 1, how relevant is the following document to the query? "
                     "Query: {query}\nDocument: {document}\nRelevance score:"
        )
        self.numerical_relevance_chain = self.numerical_relevance_prompt | self.llm.with_structured_output(RetrievalEvaluatorInput)
        
        self.support_prompt = PromptTemplate(
            input_variables=["response", "context"],
            template="Given the response '{response}' and the context '{context}', determine if the response is supported by the context. Output 'Fully supported', 'Partially supported', or 'No support'."
        )
        self.support_chain = self.support_prompt | self.llm.with_structured_output(SupportResponse)
        
        self.utility_prompt = PromptTemplate(
            input_variables=["query", "response"],
            template="Given the query '{query}' and the response '{response}', rate the utility of the response from 1 to 5."
        )
        self.utility_chain = self.utility_prompt | self.llm.with_structured_output(UtilityResponse)
    
    def evaluate_relevance(self, query: str, documents: List[Document]) -> List[RelevanceScore]:
        """
        Evaluate the relevance of documents to a query.
        
        Args:
            query (str): The user's query
            documents (List[Document]): List of documents to evaluate
            
        Returns:
            List[RelevanceScore]: Relevance scores for each document
        """
        self.log(f"Evaluating relevance of {len(documents)} documents")
        results = []
        
        for i, doc in enumerate(documents):
            self.log(f"Evaluating document {i+1}/{len(documents)}")
            
            # Get binary relevance
            input_data = {"query": query, "context": doc.content}
            binary_relevance = self.relevance_chain.invoke(input_data).response.strip().lower()
            is_relevant = binary_relevance == 'relevant'
            
            # Get numerical relevance score
            input_data = {"query": query, "document": doc.content}
            numerical_score = self.numerical_relevance_chain.invoke(input_data).relevance_score
            
            results.append(RelevanceScore(
                score=numerical_score,
                is_relevant=is_relevant
            ))
            
            self.log(f"Document {i+1} relevance: {numerical_score:.2f}, is_relevant: {is_relevant}")
            
        return results
    
    def evaluate_support(self, response: str, context: str) -> str:
        """
        Evaluate how well the response is supported by the context.
        
        Args:
            response (str): The generated response
            context (str): The context used to generate the response
            
        Returns:
            str: Support evaluation result ('Fully supported', 'Partially supported', or 'No support')
        """
        self.log("Evaluating support for response")
        input_data = {"response": response, "context": context}
        result = self.support_chain.invoke(input_data).response.strip().lower()
        self.log(f"Support evaluation: {result}")
        return result
    
    def evaluate_utility(self, query: str, response: str) -> int:
        """
        Evaluate the utility of the response.
        
        Args:
            query (str): The user's query
            response (str): The generated response
            
        Returns:
            int: Utility rating from 1 to 5
        """
        self.log("Evaluating utility of response")
        input_data = {"query": query, "response": response}
        result = self.utility_chain.invoke(input_data).response
        self.log(f"Utility evaluation: {result}/5")
        return result
    
    def determine_retrieval_strategy(self, scores: List[RelevanceScore]) -> str:
        """
        Determine the retrieval strategy based on relevance scores.
        
        Args:
            scores (List[RelevanceScore]): List of relevance scores
            
        Returns:
            str: Retrieval strategy ('kb_only', 'web_only', 'hybrid')
        """
        if not scores:
            return 'web_only'
            
        max_score = max(score.score for score in scores)
        
        if max_score < self.lower_threshold:
            return 'web_only'
        elif max_score >= self.upper_threshold:
            return 'kb_only'
        else:
            return 'hybrid'
    
    def run(self, query: str, documents: List[Document]) -> Dict:
        """
        Run evaluation on documents and determine the best strategy.
        
        Args:
            query (str): The user's query
            documents (List[Document]): List of documents to evaluate
            
        Returns:
            Dict: Dictionary containing:
                - relevance_scores: List of RelevanceScore objects
                - retrieval_strategy: Strategy to use ('kb_only', 'web_only', 'hybrid')
        """
        relevance_scores = self.evaluate_relevance(query, documents)
        retrieval_strategy = self.determine_retrieval_strategy(relevance_scores)
        self.log(f"Determined retrieval strategy: {retrieval_strategy}")
        
        return {
            'relevance_scores': relevance_scores,
            'retrieval_strategy': retrieval_strategy
        }