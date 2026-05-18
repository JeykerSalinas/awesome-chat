from __future__ import annotations

from typing import Any, Literal

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ToolCallRequest
from langchain.agents.structured_output import ToolStrategy
from langchain.tools import tool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_tavily import TavilyExtract, TavilySearch
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.chat import (
    AssistantStructuredResponse,
    PopulationToolInput,
    TavilyExtractPayload,
    TavilyExtractToolInput,
    TavilySearchPayload,
    TavilyToolInput,
    WeatherToolInput,
)
from app.services.llm_factory import build_model
from app.state.checkpoints import checkpointer

WEATHER_HINTS = (
    "clima",
    "tiempo",
    "weather",
    "llueve",
    "lluvia",
    "temperatura",
    "sol",
    "soleado",
)

# Small in-memory data source used by the population tool.
population_by_location: dict[str, int] = {
    "caracas, venezuela": 2945000,
    "madrid, spain": 3335000,
    "madrid, españa": 3335000,
    "madrid": 3335000,
    "caracas": 2945000,
}


def normalize_content(content: Any) -> str:
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


def get_last_ai_message(messages: list[Any]) -> AIMessage | None:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return message
    return None


def message_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)

    return ""


def should_enable_weather_tool(messages: list[Any]) -> bool:
    if not messages:
        return False

    last_message = messages[-1]
    if not isinstance(last_message, HumanMessage):
        return False

    content = message_content_to_text(last_message.content).lower()
    return any(keyword in content for keyword in WEATHER_HINTS)


def build_agent(
    api_style: Literal["openai", "native"] | None,
    search_capture: list[TavilySearchPayload],
    extract_capture: list[TavilyExtractPayload],
):
    tavily_search_tool = TavilySearch(
        tavily_api_key=settings.tavily_api_key,
        api_base_url=settings.tavily_base_url,
        max_results=3,
        search_depth="basic",
        topic="general",
        include_answer=True,
        include_raw_content="markdown",
    )
    tavily_extract_tool = TavilyExtract(
        tavily_api_key=settings.tavily_api_key,
        api_base_url=settings.tavily_base_url,
        include_images=False,
        extract_depth="advanced",
        format="markdown",
    )

    @tool(
        "get_weather",
        args_schema=WeatherToolInput,
        description="Get the weather for a given city.",
    )
    async def get_weather(city: str) -> str:
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
        raw_result = await tavily_search_tool.ainvoke({"query": query})
        payload = TavilySearchPayload.model_validate(raw_result)
        search_capture.append(payload)
        return payload.model_dump_json()

    @tool(
        "tavily_extract",
        args_schema=TavilyExtractToolInput,
        description=(
            "Extract the content of one or more specific URLs. "
            "Use this after you already have target links and need the page content itself."
        ),
    )
    async def tavily_extract(
        urls: list[str],
        extract_depth: Literal["basic", "advanced"] = "basic",
        include_images: bool = False,
        query: str | None = None,
    ) -> str:
        raw_result = await tavily_extract_tool.ainvoke(
            {
                "urls": urls,
                "extract_depth": extract_depth,
                "include_images": include_images,
                "query": query,
            }
        )
        payload = TavilyExtractPayload.model_validate(raw_result)
        extract_capture.append(payload)
        return payload.model_dump_json()

    class DynamicToolMiddleware(AgentMiddleware):
        async def awrap_model_call(self, request: ModelRequest, handler):
            request_tools = list(request.tools or [])
            if not should_enable_weather_tool(request.messages):
                return await handler(request.override(tools=request_tools))

            updated = request.override(tools=[*request_tools, get_weather])
            return await handler(updated)

        async def awrap_tool_call(self, request: ToolCallRequest, handler):
            if request.tool_call["name"] == "get_weather":
                return await handler(request.override(tool=get_weather))
            return await handler(request)

    return create_agent(
        model=build_model(api_style),
        tools=[get_population, tavily_search, tavily_extract],
        middleware=[DynamicToolMiddleware()],
        system_prompt=(
            "You are a helpful assistant. "
            "Use tools when the question requires weather, population, "
            "current information from the web, or extracting content from specific URLs."
        ),
        response_format=ToolStrategy(
            schema=AssistantStructuredResponse,
            tool_message_content="Action item captured and added to meeting notes!",
        ),
        checkpointer=checkpointer,
    )


def build_agent_error_detail(error: Exception | None) -> str:
    if error is None:
        return "Error calling LangChain agent."

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


def build_chat_response(
    result: dict[str, Any],
    search_capture: list[TavilySearchPayload],
    extract_capture: list[TavilyExtractPayload],
):
    from app.schemas.chat import ChatResponse

    state_messages = result.get("messages", [])
    structured_response = result.get("structured_response")
    last_ai_message = get_last_ai_message(state_messages)
    latest_search_result = search_capture[-1] if search_capture else None
    latest_extract_result = extract_capture[-1] if extract_capture else None

    content = ""
    parsed_structured_response: AssistantStructuredResponse | None = None

    if isinstance(structured_response, AssistantStructuredResponse):
        parsed_structured_response = structured_response
        content = structured_response.answer.strip()

    if not content:
        content = normalize_content(last_ai_message.content if last_ai_message else "")
    if not content and latest_search_result and latest_search_result.answer:
        content = latest_search_result.answer

    return ChatResponse(
        content=content,
        searchResult=latest_search_result,
        extractResult=latest_extract_result,
        structuredResponse=parsed_structured_response,
    )
