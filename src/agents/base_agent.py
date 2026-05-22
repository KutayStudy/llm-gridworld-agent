"""Base agent interface for GridWorld agents."""
from abc import ABC, abstractmethod
from src.actions import Action

class BaseAgent(ABC):
    """Parent class for all agents that act in the GridWorld environment."""
    @abstractmethod
    def choose_action(self, observation: dict) -> Action:
        """Choose the next action based on the current observation."""
        pass