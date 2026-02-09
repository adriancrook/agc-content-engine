"""
Base agent interface - all agents follow this pattern
Pure functions: article in, result out
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class AgentResult:
    """Standardized agent output"""
    success: bool
    data: Dict[str, Any]  # Fields to update in article
    cost: float = 0.0     # Track API costs
    tokens: int = 0       # Track token usage
    error: str = None     # Error message if failed


class BaseAgent(ABC):
    """All agents implement this interface"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @abstractmethod
    async def run(self, article) -> AgentResult:
        """
        Process article and return result
        Pure function - no side effects, no database access

        Args:
            article: Article model instance with current state

        Returns:
            AgentResult with data to update article
        """
        pass

    def _format_error(self, error: Exception) -> str:
        """Format error for logging"""
        return f"{type(error).__name__}: {str(error)}"
