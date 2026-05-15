from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# `BASE_DIR` points to the `backend/` folder.
# We use it to locate files like `.env` without depending on the directory
# from which the server is started.
BASE_DIR = Path(__file__).resolve().parents[2]
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]
LOCALHOST_ORIGIN_REGEX = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", BASE_DIR.parent / "frontend" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    model_provider: Literal["google", "openai", "ollama"] = Field(
        default="google",
        validation_alias=AliasChoices("MODEL_PROVIDER"),
    )
    google_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_API_KEY"),
    )
    google_model: str = Field(
        default="gemini-2.5-flash-lite",
        validation_alias=AliasChoices("GOOGLE_MODEL"),
    )
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY"),
    )
    openai_model: str = Field(
        default="gpt-4.1-mini",
        validation_alias=AliasChoices("OPENAI_MODEL"),
    )
    openai_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_BASE_URL"),
    )
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434",
        validation_alias=AliasChoices("OLLAMA_BASE_URL"),
    )
    ollama_model: str = Field(
        default="qwen2.5:7b",
        validation_alias=AliasChoices("OLLAMA_MODEL"),
    )
    ollama_api_style: Literal["auto", "openai", "native"] = Field(
        default="auto",
        validation_alias=AliasChoices("OLLAMA_API_STYLE"),
    )
    tavily_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("TAVILY_API_KEY", "VITE_TAVILY_API_KEY"),
    )
    tavily_base_url: str = Field(
        default="https://api.tavily.com",
        validation_alias=AliasChoices("TAVILY_BASE_URL"),
    )


settings = Settings()
