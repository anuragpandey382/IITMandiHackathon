import sys
import os
from sentence_transformers import SentenceTransformer

# Add project root to path to allow imports from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class TextEmbedder:
    """Class for generating text embeddings using sentence transformers"""
    
    _instance = None
    
    def __new__(cls, model_name=None):
        """Singleton pattern to avoid loading model multiple times"""
        if cls._instance is None:
            cls._instance = super(TextEmbedder, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self, model_name=None):
        """
        Initialize the text embedder
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        if self.initialized:
            return
            
        if model_name is None:
            model_name = config.SENTENCE_TRANSFORMER_MODEL
        
        try:
            self.model = SentenceTransformer(model_name)
            self.initialized = True
        except Exception as e:
            print(f"Error loading sentence transformer model: {e}")
            self.model = None
            self.initialized = False
    
    def get_embedding(self, text):
        """
        Generate embedding for the given text
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector
        """
        if self.model is None:
            return None
        
        if not text:
            return None
        
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None