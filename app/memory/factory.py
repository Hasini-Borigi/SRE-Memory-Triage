"""Factory for creating and managing memory stores with graceful fallback."""

import logging
from typing import Optional
from app.config import settings
from app.memory.base import MemoryStore
from app.memory.chroma import ChromaMemoryStore
from app.memory.hindsight import HindsightMemoryStore

logger = logging.getLogger("incident_agent.memory.factory")

_MEMORY_INSTANCE: Optional[MemoryStore] = None
_MEMORY_STATUS: str = "uninitialized"


async def init_memory_store() -> MemoryStore:
    """Initialize memory store based on configuration with automatic fallback."""
    global _MEMORY_INSTANCE, _MEMORY_STATUS

    preferred = (settings.MEMORY_BACKEND or "hindsight").lower().strip()
    logger.info("Initializing memory backend. Preferred: %s", preferred)

    if preferred == "hindsight":
        if not settings.verify_hindsight_key():
            logger.warning(
                "Hindsight API key verification failed. Falling back to ChromaDB."
            )
            _MEMORY_INSTANCE = ChromaMemoryStore()
            _MEMORY_STATUS = "fallback_chroma"
            return _MEMORY_INSTANCE

        hindsight_store = HindsightMemoryStore()
        # Test connectivity
        is_reachable = await hindsight_store.ping()
        if is_reachable:
            logger.info("Connected to Hindsight memory bank successfully.")
            _MEMORY_INSTANCE = hindsight_store
            _MEMORY_STATUS = "hindsight_active"
            return _MEMORY_INSTANCE
        else:
            logger.warning(
                "Hindsight bank unreachable. Gracefully falling back to ChromaDB."
            )
            _MEMORY_INSTANCE = ChromaMemoryStore()
            _MEMORY_STATUS = "fallback_chroma"
            return _MEMORY_INSTANCE

    # Default to ChromaDB
    _MEMORY_INSTANCE = ChromaMemoryStore()
    _MEMORY_STATUS = "chroma_active"
    return _MEMORY_INSTANCE


def get_memory_store() -> MemoryStore:
    """Return current memory instance or fallback Chroma instance."""
    global _MEMORY_INSTANCE
    if _MEMORY_INSTANCE is None:
        _MEMORY_INSTANCE = ChromaMemoryStore()
    return _MEMORY_INSTANCE


def get_memory_status() -> str:
    """Get active status of memory backend."""
    global _MEMORY_STATUS
    return _MEMORY_STATUS


def set_memory_store(store: MemoryStore):
    """Override memory store for testing."""
    global _MEMORY_INSTANCE, _MEMORY_STATUS
    _MEMORY_INSTANCE = store
    _MEMORY_STATUS = f"test_{store.name}"
