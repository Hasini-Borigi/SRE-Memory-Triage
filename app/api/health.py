"""Health check endpoint exposing provider and memory backend status securely."""

from fastapi import APIRouter
from app.config import settings, mask_secret
from app.models.schemas import HealthResponse
from app.llm.factory import get_llm_provider, get_llm_status
from app.memory.factory import get_memory_store, get_memory_status

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def check_health():
    """Report health and active components with strictly masked credentials."""
    llm = get_llm_provider()
    memory = get_memory_store()

    return HealthResponse(
        status="healthy",
        llm_provider=llm.name,
        llm_model=llm.model_name,
        llm_status=get_llm_status(),
        memory_backend=memory.name,
        memory_status=get_memory_status(),
        groq_configured=settings.verify_groq_key(),
        hindsight_configured=settings.verify_hindsight_key(),
        groq_key_masked=mask_secret(settings.GROQ_API_KEY),
        hindsight_key_masked=mask_secret(settings.HINDSIGHT_API_KEY),
    )
