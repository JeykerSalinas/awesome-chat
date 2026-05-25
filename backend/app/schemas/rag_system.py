from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl

class TestRagSystem(BaseModel):
    index: int = Field(description="Paragraph index from the source document.")
    text: str = Field(description="Replacement text for the paragraph.")