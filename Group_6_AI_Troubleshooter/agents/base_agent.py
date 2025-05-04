"""
Base Agent class that all specialized agents will inherit from.
"""
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Base class for all agents in the RAG system"""
    
    def __init__(self, name):
        """
        Initialize a base agent.
        
        Args:
            name (str): Name of the agent
        """
        self.name = name
        
    @abstractmethod
    def run(self, *args, **kwargs):
        """
        Run the agent's main functionality.
        
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
            
        Returns:
            Any: Result of the agent's execution
        """
        pass
    
    def log(self, message):
        """
        Log a message from this agent.
        
        Args:
            message (str): Message to log
        """
        print(f"[{self.name}] {message}")