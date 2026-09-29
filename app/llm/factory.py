"""Factory to initialize and provide the active LLM provider."""

import logging
from typing import Optional
from app.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.groq_provider import GroqLLMProvider

logger = logging.getLogger("incident_agent.llm.factory")

_LLM_INSTANCE: Optional[BaseLLMProvider] = None
_LLM_STATUS: str = "uninitialized"


async def init_llm_provider() -> BaseLLMProvider:
    """Initialize LLM provider with fallback handling."""
    global _LLM_INSTANCE, _LLM_STATUS

    provider_name = (settings.LLM_PROVIDER or "groq").lower().strip()
    logger.info("Initializing LLM provider. Selected: %s", provider_name)

    if provider_name == "groq":
        if not settings.verify_groq_key():
            logger.warning(
                "GROQ key format invalid or not provided. Falling back to MockLLMProvider."
            )
            _LLM_INSTANCE = MockLLMProvider()
            _LLM_STATUS = "fallback_mock"
            return _LLM_INSTANCE

        groq_provider = GroqLLMProvider()
        # Test reachability
        is_reachable = await groq_provider.ping()
        if is_reachable:
            logger.info("Groq API successfully connected and responsive.")
            _LLM_INSTANCE = groq_provider
            _LLM_STATUS = "groq_active"
            return _LLM_INSTANCE
        else:
            logger.warning("Groq ping test failed. Falling back to MockLLMProvider.")
            _LLM_INSTANCE = MockLLMProvider()
            _LLM_STATUS = "fallback_mock"
            return _LLM_INSTANCE

    # Default fallback
    _LLM_INSTANCE = MockLLMProvider()
    _LLM_STATUS = "mock_active"
    return _LLM_INSTANCE


def get_llm_provider() -> BaseLLMProvider:
    """Return active LLM provider."""
    global _LLM_INSTANCE
    if _LLM_INSTANCE is None:
        _LLM_INSTANCE = MockLLMProvider()
    return _LLM_INSTANCE


def get_llm_status() -> str:
    """Return active LLM status."""
    global _LLM_STATUS
    return _LLM_STATUS


def set_llm_provider(provider: BaseLLMProvider):
    """Override LLM provider for testing."""
    global _LLM_INSTANCE, _LLM_STATUS
    _LLM_INSTANCE = provider
    _LLM_STATUS = f"test_{provider.name}"
