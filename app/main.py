"""Main FastAPI application entrypoint with lifespan event handlers."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings, mask_secret
from app.models.database import Base, engine
from app.memory.factory import init_memory_store, get_memory_status
from app.llm.factory import init_llm_provider, get_llm_status
from app.api import (
    health_router,
    incidents_router,
    runbooks_router,
    postmortems_router,
    memory_router,
    analytics_router,
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("incident_agent.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan."""
    logger.info("Initializing Incident Response Agent database schema...")
    Base.metadata.create_all(bind=engine)

    logger.info(
        "Checking components: LLM=%s (key=%s), Memory=%s (key=%s)",
        settings.LLM_PROVIDER,
        mask_secret(settings.GROQ_API_KEY),
        settings.MEMORY_BACKEND,
        mask_secret(settings.HINDSIGHT_API_KEY),
    )

    # Initialize memory store with graceful fallback
    memory = await init_memory_store()
    logger.info("Active Memory Backend: %s (status: %s)", memory.name, get_memory_status())

    # Initialize LLM provider with graceful fallback
    llm = await init_llm_provider()
    logger.info("Active LLM Provider: %s (status: %s)", llm.name, get_llm_status())

    yield

    logger.info("Shutting down Incident Response Agent.")


app = FastAPI(
    title="Incident Response Agent with Memory",
    description="Autonomous SRE incident triage powered by Vectorize Hindsight and Groq Llama-3.3-70b",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router)
app.include_router(incidents_router)
app.include_router(runbooks_router)
app.include_router(postmortems_router)
app.include_router(memory_router)
app.include_router(analytics_router)


@app.get("/")
def root():
    return {
        "message": "Incident Response Agent with Memory API is active",
        "docs_url": "/docs",
        "health_url": "/health",
    }
