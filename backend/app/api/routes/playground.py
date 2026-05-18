from fastapi import APIRouter

from app.schemas.playground import PlaygroundAgentRequest, PlaygroundAgentResponse
from app.services.playground_agent import run_playground_agent

router = APIRouter()


@router.post("/playground-agent", response_model=PlaygroundAgentResponse)
async def playground_agent(
    request: PlaygroundAgentRequest,
) -> PlaygroundAgentResponse:
    content = await run_playground_agent(request.message)
    return PlaygroundAgentResponse(content=content)
