"""
Models for data structures used by agents.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Document(BaseModel):
    """Represents a document with content and metadata"""
    content: str
    metadata: Dict[str, Any] = {}
    
    def preview(self, max_length: int = 200) -> str:
        """Get a preview of the document content"""
        return f"{self.content[:max_length]}..." if len(self.content) > max_length else self.content


class RelevanceScore(BaseModel):
    """Result of relevance evaluation"""
    score: float = Field(..., description="Relevance score between 0 and 1")
    is_relevant: bool = Field(..., description="Binary relevance decision")


class ReferenceLink(BaseModel):
    """Reference link to a source"""
    title: str
    url: str


class RelevantDocument(BaseModel):
    """Document deemed relevant with its score"""
    content_preview: str
    score: float
    url: str


class QueryResult(BaseModel):
    """Final result of a query"""
    final_response: str
    reference_links: List[ReferenceLink] = []
    relevant_docs: List[RelevantDocument] = []


class WebSearchResult(BaseModel):
    """Result from web search"""
    knowledge: str
    sources: List[ReferenceLink] = []