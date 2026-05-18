from __future__ import annotations

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

from app.schemas.chat import ChatRequest, ChatResponse, TavilyExtractPayload, TavilySearchPayload
from app.services.chat_agent import build_agent, build_agent_error_detail, build_chat_response
from app.services.llm_factory import get_candidate_api_styles, is_api_style_fallback_error
from app.core.config import settings

router = APIRouter()


@router.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    langchain_messages = [HumanMessage(content=request.message)]
    last_error: Exception | None = None

    if settings.model_provider in {"google", "openai"}:
        candidate_api_styles: list[str | None] = [None]
    else:
        candidate_api_styles = get_candidate_api_styles()

    for api_style in candidate_api_styles:
        search_capture: list[TavilySearchPayload] = []
        extract_capture: list[TavilyExtractPayload] = []
        agent = build_agent(api_style, search_capture, extract_capture)

        try:
            result = await agent.ainvoke(
                {"messages": langchain_messages},
                config={"configurable": {"thread_id": request.thread_id}},
            )
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

        return build_chat_response(result, search_capture, extract_capture)

    raise HTTPException(status_code=502, detail=build_agent_error_detail(last_error))
