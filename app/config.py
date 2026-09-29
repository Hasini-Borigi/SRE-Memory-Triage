"""Configuration module for Incident Response Agent."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger("incident_agent.config")


def mask_secret(secret: Optional[str]) -> str:
    """Safely mask secret strings so keys are never exposed in logs or UI."""
    if not secret:
        return "None"
    secret_str = str(secret).strip()
    if len(secret_str) <= 8:
        return "****"
    prefix = secret_str[:4]
    suffix = secret_str[-4:]
    return f"{prefix}****{suffix}"


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    MEMORY_BACKEND: str = "hindsight"
    HINDSIGHT_API_KEY: str = ""
    HINDSIGHT_BASE_URL: str = "https://api.hindsight.vectorize.io"
    HINDSIGHT_BANK_ID: str = "incident-response-bank"

    SQLITE_DB_PATH: str = "./data/incidents.db"
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"

    # Timeouts & Retries
    GROQ_TIMEOUT_SECONDS: float = 20.0
    GROQ_MAX_RETRIES: int = 2
    HINDSIGHT_TIMEOUT_SECONDS: float = 10.0
    HINDSIGHT_MAX_RETRIES: int = 2

    def verify_groq_key(self) -> bool:
        """Verify GROQ key format without exposing secret."""
        if not self.GROQ_API_KEY:
            return False
        clean = self.GROQ_API_KEY.strip()
        is_valid = clean.startswith("gsk_") and len(clean) >= 20
        logger.info(
            "GROQ key format check: prefix_valid=%s, length=%d (key=%s)",
            clean.startswith("gsk_"),
            len(clean),
            mask_secret(clean),
        )
        return is_valid

    def verify_hindsight_key(self) -> bool:
        """Verify Hindsight key format without exposing secret."""
        if not self.HINDSIGHT_API_KEY:
            return False
        clean = self.HINDSIGHT_API_KEY.strip()
        is_valid = clean.startswith("hsk_") and len(clean) >= 20
        logger.info(
            "Hindsight key format check: prefix_valid=%s, length=%d (key=%s)",
            clean.startswith("hsk_"),
            len(clean),
            mask_secret(clean),
        )
        return is_valid


settings = Settings()
