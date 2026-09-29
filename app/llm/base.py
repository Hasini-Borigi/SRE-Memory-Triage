"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseLLMProvider(ABC):
    """Abstract interface for LLM reasoning and extraction."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name ('groq', 'mock', 'gemini', 'anthropic')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier."""
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Check provider reachability."""
        pass

    @abstractmethod
    async def analyze_incident(
        self,
        incident: Dict[str, Any],
        recalled_incidents: List[Dict[str, Any]],
        available_runbooks: List[Dict[str, Any]],
        recalled_lessons: List[str],
    ) -> Dict[str, Any]:
        """Perform root cause analysis, citation of past incidents, and ranked resolution steps."""
        pass

    @abstractmethod
    async def extract_postmortem_lessons(
        self,
        content: str,
        service: str,
    ) -> Dict[str, Any]:
        """Extract structured summary, root cause, lessons learned, and action items from postmortem."""
        pass
