from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage

from app.services.chat_agent import normalize_content
from app.services.llm_factory import build_model


def build_playground_agent():
    return create_agent(
        model=build_model(),
    )


agent = build_playground_agent()


def get_last_ai_message(messages: list[Any]) -> AIMessage | None:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return message
    return None


async def run_playground_agent(message: str) -> str:
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=message)]},
    )
    state_messages = result.get("messages", [])
    last_ai_message = get_last_ai_message(state_messages)
    return normalize_content(last_ai_message.content if last_ai_message else "")
