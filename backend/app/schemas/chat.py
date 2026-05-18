from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, BaseModel, Field


class ChatMessageIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    thread_id: str = Field(validation_alias=AliasChoices("thread_id", "threadId"))
    message: str


class TavilySearchResultItem(BaseModel):
    url: str
    title: str
    content: str
    score: float | None = None
    raw_content: str | None = None


class TavilySearchPayload(BaseModel):
    query: str
    answer: str | None = None
    response_time: float | None = None
    request_id: str | None = None
    results: list[TavilySearchResultItem]
    follow_up_questions: list[str] | None = None
    images: list[str] = Field(default_factory=list)


class TavilyExtractResultItem(BaseModel):
    url: str
    raw_content: str | None = None
    images: list[str] = Field(default_factory=list)
    favicon: str | None = None


class TavilyExtractFailedResultItem(BaseModel):
    url: str
    error: str | None = None


class TavilyExtractPayload(BaseModel):
    results: list[TavilyExtractResultItem]
    failed_results: list[TavilyExtractFailedResultItem] = Field(default_factory=list)
    response_time: float | None = None


class AssistantStructuredResponse(BaseModel):
    answer: str = Field(description="Respuesta final para mostrar al usuario.")
    needs_clarification: bool = Field(
        default=False,
        description="True si faltan datos para responder bien.",
    )
    suggested_title: str | None = Field(
        default=None,
        description="Resumen corto de la respuesta en 2-5 palabras.",
    )


class ChatResponse(BaseModel):
    content: str
    searchResult: TavilySearchPayload | None = None
    extractResult: TavilyExtractPayload | None = None
    structuredResponse: AssistantStructuredResponse | None = None


class WeatherToolInput(BaseModel):
    city: str


class PopulationToolInput(BaseModel):
    location: str


class TavilyToolInput(BaseModel):
    query: str


class TavilyExtractToolInput(BaseModel):
    urls: list[str]
    extract_depth: Literal["basic", "advanced"] = "basic"
    include_images: bool = False
    query: str | None = None
