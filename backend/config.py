"""
Application configuration using Pydantic BaseSettings.
All environment variables are loaded from .env and validated at startup.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Central configuration for the AI Code Review Agent backend."""

    # --- Google Gemini API ---
    GEMINI_API_KEY: str = Field(
        ...,
        description="Google Gemini API key from https://aistudio.google.com/"
    )

    # --- GitHub Integration ---
    GITHUB_WEBHOOK_SECRET: str = Field(
        ...,
        description="Secret for HMAC-SHA256 webhook signature verification"
    )
    GITHUB_TOKEN: str = Field(
        ...,
        description="GitHub Personal Access Token with repo scope"
    )

    # --- Database ---
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://codereview:codereview@db:5432/codereview",
        description="PostgreSQL async connection string"
    )

    # --- Application ---
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )
    API_PREFIX: str = Field(
        default="/api/v1",
        description="API route prefix"
    )
    APP_ENV: str = Field(
        default="development",
        description="Application environment: development, staging, production"
    )
    LOG_LEVEL: str = Field(
        default="info",
        description="Logging level"
    )

    # --- LLM Settings ---
    GEMINI_MODEL: str = Field(
        default="gemini-1.5-pro",
        description="Gemini model identifier"
    )
    GEMINI_TEMPERATURE: float = Field(
        default=0.1,
        description="LLM temperature for deterministic outputs"
    )
    GEMINI_MAX_TOKENS: int = Field(
        default=4096,
        description="Maximum output tokens per LLM call"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
