from __future__ import annotations

from typing import Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.config import settings


def build_ollama_openai_compatible_base_url() -> str:
    base_url = settings.ollama_base_url.rstrip("/")
    if base_url.endswith("/v1"):
        return base_url
    return f"{base_url}/v1"


def get_candidate_api_styles() -> list[Literal["openai", "native"]]:
    if settings.ollama_api_style == "openai":
        return ["openai"]
    if settings.ollama_api_style == "native":
        return ["native"]
    return ["openai", "native"]


def build_ollama_model(api_style: Literal["openai", "native"]) -> ChatOpenAI | ChatOllama:
    if api_style == "openai":
        return ChatOpenAI(
            model=settings.ollama_model,
            base_url=build_ollama_openai_compatible_base_url(),
            api_key="ollama",
            temperature=0,
        )

    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0,
    )


def build_model(
    api_style: Literal["openai", "native"] | None = None,
) -> ChatGoogleGenerativeAI | ChatOpenAI | ChatOllama:
    if settings.model_provider == "google":
        if not settings.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY is required when MODEL_PROVIDER=google."
            )

        return ChatGoogleGenerativeAI(
            model=settings.google_model,
            google_api_key=settings.google_api_key,
            temperature=0,
        )

    if settings.model_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when MODEL_PROVIDER=openai."
            )

        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0,
        )

    if api_style is None:
        api_style = get_candidate_api_styles()[0]

    return build_ollama_model(api_style)


def is_api_style_fallback_error(error: Exception) -> bool:
    error_message = str(error)
    return (
        "404" in error_message
        or "/api/chat" in error_message
        or "/v1/chat/completions" in error_message
    )
