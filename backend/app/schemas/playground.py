from pydantic import BaseModel


class PlaygroundAgentRequest(BaseModel):
    message: str


class PlaygroundAgentResponse(BaseModel):
    content: str
