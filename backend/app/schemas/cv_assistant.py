from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.chat import TavilyExtractPayload
from app.schemas.documents import DocumentSummary


class ParagraphRevisionInput(BaseModel):
    index: int = Field(description="Paragraph index from the source document.")
    text: str = Field(description="Replacement text for the paragraph.")


class SaveCvVariantInput(BaseModel):
    title: str = Field(description="Name for the generated CV version.")
    revisions: list[ParagraphRevisionInput] = Field(
        description="Only the paragraph blocks that should be updated.",
    )


class CvOptimizationRequest(BaseModel):
    document_id: str
    job_url: HttpUrl
    instructions: str | None = None


class CvOptimizationStructuredResponse(BaseModel):
    answer: str = Field(description="Short summary of how the CV was adapted.")
    key_adjustments: list[str] = Field(
        default_factory=list,
        description="Main non-fabricated adjustments made to the CV.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Any cautions about missing evidence or limited alignment.",
    )


class CvOptimizationResponse(BaseModel):
    content: str
    generated_document: DocumentSummary | None = None
    offer_extract: TavilyExtractPayload | None = None
    structured_response: CvOptimizationStructuredResponse | None = None

