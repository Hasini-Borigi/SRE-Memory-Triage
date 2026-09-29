"""Tests for LLM and Memory fallback logic and secret masking."""

import pytest
from app.config import Settings, mask_secret, settings
from app.llm.groq_provider import GroqLLMProvider
from app.llm.factory import init_llm_provider, get_llm_status
from app.memory.chroma import ChromaMemoryStore
from app.memory.factory import init_memory_store, get_memory_status


def test_secret_masking():
    """Verify secrets are masked and never exposed in full."""
    raw_groq = "gsk_test_mock_secret_key_string_12345678"
    masked = mask_secret(raw_groq)
    assert masked.startswith("gsk_")
    assert "****" in masked
    assert raw_groq not in masked

    raw_hsk = "hsk_test_mock_secret_key_string_12345678"
    masked_hsk = mask_secret(raw_hsk)
    assert masked_hsk.startswith("hsk_")
    assert "****" in masked_hsk
    assert raw_hsk not in masked_hsk


def test_settings_key_verification():
    """Verify prefix and length validation logic."""
    test_settings = Settings(
        GROQ_API_KEY="gsk_mock_test_key_sample_1234567890",
        HINDSIGHT_API_KEY="hsk_mock_test_key_sample_1234567890",
    )
    assert test_settings.verify_groq_key() is True
    assert test_settings.verify_hindsight_key() is True

    bad_settings = Settings(
        GROQ_API_KEY="invalid_key",
        HINDSIGHT_API_KEY="invalid_key",
    )
    assert bad_settings.verify_groq_key() is False
    assert bad_settings.verify_hindsight_key() is False


@pytest.mark.asyncio
async def test_llm_fallback_on_unconfigured_groq():
    """Verify that unconfigured Groq (api_key='') falls back to MockLLMProvider cleanly."""
    groq = GroqLLMProvider(api_key="")
    assert groq._client is None

    result = await groq.analyze_incident(
        incident={
            "id": "INC-TEST-FB-UNCONF",
            "title": "Database connection drop",
            "service": "postgres-primary",
            "severity": "SEV1",
            "symptoms": "Connections dropped",
        },
        recalled_incidents=[{
            "incident_id": "INC-1001",
            "title": "Postgres pool exhaustion",
            "service": "postgres-primary",
            "root_cause": "Pool saturation",
            "runbook_id": "RB-001",
            "score": 0.90,
        }],
        available_runbooks=[{
            "id": "RB-001",
            "title": "Pool Recovery",
            "steps": ["Step 1", "Step 2"],
        }],
        recalled_lessons=[],
    )

    assert "probable_root_cause" in result
    assert result["confidence"] > 0.5
    assert len(result["ranked_resolution_steps"]) > 0


@pytest.mark.asyncio
async def test_llm_fallback_on_unreachable_groq():
    """Verify that if Groq fails or is unconfigured, MockLLMProvider handles analysis smoothly."""
    # Initialize Groq provider with invalid key
    groq = GroqLLMProvider(api_key="gsk_invalid_fake_key_1234567890")
    
    # Analyze incident should not crash but return mock response
    result = await groq.analyze_incident(
        incident={
            "id": "INC-TEST-FB",
            "title": "Database connection drop",
            "service": "postgres-primary",
            "severity": "SEV1",
            "symptoms": "Connections dropped",
        },
        recalled_incidents=[{
            "incident_id": "INC-1001",
            "title": "Postgres pool exhaustion",
            "service": "postgres-primary",
            "root_cause": "Pool saturation",
            "runbook_id": "RB-001",
            "score": 0.90,
        }],
        available_runbooks=[{
            "id": "RB-001",
            "title": "Pool Recovery",
            "steps": ["Step 1", "Step 2"],
        }],
        recalled_lessons=[],
    )

    assert "probable_root_cause" in result
    assert result["confidence"] > 0.5
    assert len(result["ranked_resolution_steps"]) > 0


@pytest.mark.asyncio
async def test_factory_fallback_on_invalid_keys():
    """Verify factory-level graceful degradation to Mock LLM and ChromaDB on invalid keys."""
    orig_groq = settings.GROQ_API_KEY
    orig_hsk = settings.HINDSIGHT_API_KEY
    try:
        settings.GROQ_API_KEY = "invalid_key"
        settings.HINDSIGHT_API_KEY = "invalid_key"

        llm = await init_llm_provider()
        assert llm.name == "mock"
        assert get_llm_status() == "fallback_mock"

        memory = await init_memory_store()
        assert memory.name == "chroma"
        assert get_memory_status() == "fallback_chroma"
    finally:
        settings.GROQ_API_KEY = orig_groq
        settings.HINDSIGHT_API_KEY = orig_hsk


@pytest.mark.asyncio
async def test_memory_fallback_chroma_ping(tmp_path):
    """Verify Chroma memory store initializes and pings successfully using isolated temp dir."""
    chroma = ChromaMemoryStore(persist_dir=str(tmp_path / "chroma_test"))
    is_live = await chroma.ping()
    assert is_live is True
    assert chroma.name == "chroma"
