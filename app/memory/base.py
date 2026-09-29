"""Abstract base interface for memory backends."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class MemoryStore(ABC):
    """Abstract interface for episodic, semantic, and knowledge memory stores."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the active memory backend (e.g., 'hindsight', 'chroma')."""
        pass

    @abstractmethod
    async def retain(
        self,
        item_id: str,
        content: str,
        memory_type: str,  # 'incident', 'runbook', 'postmortem'
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Retain an episodic or semantic item into memory."""
        pass

    @abstractmethod
    async def recall(
        self,
        query: str,
        limit: int = 5,
        filter_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Recall relevant memories matching query with similarity scores (0.0 - 1.0)."""
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Health check to verify memory backend availability."""
        pass
