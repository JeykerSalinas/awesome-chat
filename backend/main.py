from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from pydantic import AliasChoices, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# `BASE_DIR` points to the `backend/` folder.
# We use it to locate files like `.env` without depending on the directory
# from which the server is started.
BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    # This defines a class. It does not create an object yet.
    # `BaseSettings` is a Pydantic class specialized for configuration.
    # It reads environment variables, validates them, and exposes them
    # as typed Python attributes when we later instantiate `Settings()`.
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
app = FastAPI(title="Lovely Chat Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessageIn(BaseModel):
    # Pydantic model for one chat message coming from the frontend.
    # FastAPI validates request JSON against this schema automatically.
    role: Literal["user", "assistant"]
    content: str


class TavilySearchResultItem(BaseModel):
    # Pydantic model for a single Tavily source entry.
    url: str
    title: str
    content: str
    score: float | None = None
    raw_content: str | None = None


class TavilySearchPayload(BaseModel):
    # Pydantic model for the full Tavily response that the frontend renders.
    # Defining the class creates the schema.
    # Calling `TavilySearchPayload(...)` or `.model_validate(...)` creates instances.
    query: str
    answer: str | None = None
    response_time: float | None = None
    request_id: str | None = None
    results: list[TavilySearchResultItem]
    follow_up_questions: list[str] | None = None
    images: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    # Request body for POST /chat.
    messages: list[ChatMessageIn]


class ChatResponse(BaseModel):
    # Response body returned to the frontend.
    content: str
    searchResult: TavilySearchPayload | None = None


class WeatherToolInput(BaseModel):
    city: str


class PopulationToolInput(BaseModel):
    location: str


class TavilyToolInput(BaseModel):
    query: str


# Small in-memory data source used by the population tool.
population_by_location: dict[str, int] = {
    "caracas, venezuela": 2945000,
    "madrid, spain": 3335000,
    "madrid, españa": 3335000,
    "madrid": 3335000,
    "caracas": 2945000,
}


def normalize_content(content: Any) -> str:
    # Model output can be plain text or a list of structured content blocks.
    # We normalize both shapes into a single plain string for the frontend.
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts).strip()

    return ""


def to_langchain_messages(history: list[ChatMessageIn]) -> list[HumanMessage | AIMessage]:
    # Convert incoming API messages into LangChain message objects.
    # We instantiate `HumanMessage` / `AIMessage` so the agent receives the
    # conversation in the format LangChain expects internally.
    converted_messages: list[HumanMessage | AIMessage] = []
    for message in history:
        if message.role == "user":
            converted_messages.append(HumanMessage(content=message.content))
        else:
            converted_messages.append(AIMessage(content=message.content))
    return converted_messages


def get_last_ai_message(messages: list[Any]) -> AIMessage | None:
    # After the agent finishes, LangChain returns state that includes a full
    # message history. We walk backward and pick the last assistant message.
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return message
    return None


def build_ollama_openai_compatible_base_url() -> str:
    # Ollama's OpenAI-compatible API usually lives under `/v1`.
    # If the configured URL already ends with `/v1`, we reuse it as-is.
    base_url = settings.ollama_base_url.rstrip("/")
    if base_url.endswith("/v1"):
        return base_url
    return f"{base_url}/v1"


def build_ollama_model(api_style: Literal["openai", "native"]) -> ChatOpenAI | ChatOllama:
    # Model factory for Ollama.
    # `ChatOpenAI` here is used against Ollama's OpenAI-compatible API.
    # `ChatOllama` uses Ollama's native API directly.
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


def get_candidate_api_styles() -> list[Literal["openai", "native"]]:
    # This decides which LangChain model wrapper we try.
    # In `auto` mode we prefer the OpenAI-compatible path first because your
    # local setup already showed a 404 on the native `/api/chat` route.
    if settings.ollama_api_style == "openai":
        return ["openai"]
    if settings.ollama_api_style == "native":
        return ["native"]
    return ["openai", "native"]


def build_agent(
    api_style: Literal["openai", "native"] | None,
    search_capture: list[TavilySearchPayload],
):
    # We build the LangChain tools here so they can capture request-scoped state.
    # `search_capture` is a mutable list used to keep the latest Tavily payload
    # for the frontend without relying on globals shared across requests.
    tavily_search_tool = TavilySearch(
        tavily_api_key=settings.tavily_api_key,
        api_base_url=settings.tavily_base_url,
        max_results=3,
        search_depth="basic",
        topic="general",
        include_answer=True,
        include_raw_content="markdown",
    )

    @tool(
        "get_weather",
        args_schema=WeatherToolInput,
        description="Get the weather for a given city.",
    )
    async def get_weather(city: str) -> str:
        # LangChain will validate the arguments using `WeatherToolInput`
        # before this function is called.
        return f"No tengo acceso a clima en tiempo real. Respuesta mock para {city}: 22°C y soleado."

    @tool(
        "GetPopulation",
        args_schema=PopulationToolInput,
        description="Get the current population in a given location.",
    )
    async def get_population(location: str) -> str:
        normalized_location = location.strip().lower()
        population = population_by_location.get(normalized_location)
        if not population:
            return f"No tengo población registrada para {location}."

        return (
            f"La población estimada de {location} es "
            f"{population:,.0f}".replace(",", ".")
            + " habitantes."
        )

    @tool(
        "tavily_search",
        args_schema=TavilyToolInput,
        description="Search the web for current information and trusted sources.",
    )
    async def tavily_search(query: str) -> str:
        # We still use LangChain for the search itself, not raw HTTP.
        raw_result = await tavily_search_tool.ainvoke({"query": query})
        payload = TavilySearchPayload.model_validate(raw_result)
        search_capture.append(payload)
        return payload.model_dump_json()

    return create_agent(
        model=build_model(api_style),
        tools=[get_weather, get_population, tavily_search],
        system_prompt=(
            "You are a helpful assistant. "
            "Use tools when the question requires weather, population, "
            "or current information from the web."
        ),
    )


def is_api_style_fallback_error(error: Exception) -> bool:
    # We only want to try the second LangChain model wrapper when the first one
    # fails because the backend endpoint shape does not match.
    error_message = str(error)
    return (
        "404" in error_message
        or "/api/chat" in error_message
        or "/v1/chat/completions" in error_message
    )


def build_agent_error_detail(error: Exception) -> str:
    error_message = str(error)

    if settings.model_provider == "google" and "GOOGLE_API_KEY is required" in error_message:
        return (
            "Google is selected as the model provider, but GOOGLE_API_KEY is missing. "
            "Set GOOGLE_API_KEY in backend/.env."
        )

    if settings.model_provider == "openai" and "OPENAI_API_KEY is required" in error_message:
        return (
            "OpenAI is selected as the model provider, but OPENAI_API_KEY is missing. "
            "Set OPENAI_API_KEY in backend/.env."
        )

    if "not found" in error_message and settings.ollama_model in error_message:
        return (
            f"Ollama is reachable at {settings.ollama_base_url}, but the configured model "
            f"'{settings.ollama_model}' is not available. Pull that model in Ollama or set "
            "OLLAMA_MODEL in backend/.env or frontend/.env to a model you already have."
        )

    return f"Error calling LangChain agent: {error}"


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    langchain_messages = to_langchain_messages(request.messages)
    last_error: Exception | None = None

    if settings.model_provider in {"google", "openai"}:
        candidate_api_styles: list[Literal["openai", "native"] | None] = [None]
    else:
        candidate_api_styles = get_candidate_api_styles()

    for api_style in candidate_api_styles:
        search_capture: list[TavilySearchPayload] = []
        agent = build_agent(api_style, search_capture)

        try:
            # `ainvoke` runs the full LangChain agent loop:
            # model -> tool calls -> tool execution -> model -> final answer
            result = await agent.ainvoke({"messages": langchain_messages})
        except Exception as error:  # noqa: BLE001
            last_error = error
            if (
                settings.model_provider == "ollama"
                and api_style is not None
                and is_api_style_fallback_error(error)
                and api_style != get_candidate_api_styles()[-1]
            ):
                continue
            break

        state_messages = result.get("messages", [])
        last_ai_message = get_last_ai_message(state_messages)
        latest_search_result = search_capture[-1] if search_capture else None

        content = normalize_content(last_ai_message.content if last_ai_message else "")
        if not content and latest_search_result and latest_search_result.answer:
            content = latest_search_result.answer

        return ChatResponse(content=content, searchResult=latest_search_result)

    raise HTTPException(status_code=502, detail=build_agent_error_detail(last_error))
