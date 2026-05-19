from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class DocumentSummary(BaseModel):
    id: str
    display_name: str
    original_filename: str
    kind: Literal["uploaded", "generated"]
    source_document_id: str | None = None
    created_at: datetime
    updated_at: datetime
    available_formats: list[Literal["docx", "pdf"]]


class DocumentRenameRequest(BaseModel):
    display_name: str


class DocumentParagraphBlock(BaseModel):
    index: int
    style: str
    text: str

