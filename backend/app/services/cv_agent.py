from __future__ import annotations

import json
from typing import Any

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.tools import tool
from langchain_tavily import TavilyExtract

from app.core.config import settings
from app.schemas.chat import TavilyExtractPayload
from app.schemas.cv_assistant import (
    CvOptimizationRequest,
    CvOptimizationResponse,
    CvOptimizationStructuredResponse,
    SaveCvVariantInput,
)
from app.schemas.documents import DocumentSummary
from app.services.chat_agent import get_last_ai_message, normalize_content
from app.services.document_store import create_generated_variant, extract_document_blocks, get_document
from app.services.llm_factory import build_model


def build_cv_agent(
    *,
    document_id: str,
    offer_extract_capture: list[TavilyExtractPayload],
    generated_capture: list[DocumentSummary],
):
    tavily_extract_tool = TavilyExtract(
        tavily_api_key=settings.tavily_api_key,
        api_base_url=settings.tavily_base_url,
        include_images=False,
        extract_depth="advanced",
        format="markdown",
    )

    @tool("read_cv_blocks")
    def read_cv_blocks() -> str:
        """Read the editable paragraph blocks of the source CV."""
        blocks = extract_document_blocks(document_id)
        return json.dumps([block.model_dump() for block in blocks], ensure_ascii=False)

    @tool("extract_job_offer")
    async def extract_job_offer(url: str) -> str:
        """Extract the contents of a job posting URL."""
        raw_result = await tavily_extract_tool.ainvoke(
            {
                "urls": [url],
                "query": "job description responsibilities requirements qualifications tech stack",
            }
        )
        payload = TavilyExtractPayload.model_validate(raw_result)
        offer_extract_capture.append(payload)
        return payload.model_dump_json()

    @tool("save_cv_variant", args_schema=SaveCvVariantInput)
    def save_cv_variant(title: str, revisions: list[dict[str, Any]]) -> str:
        """
        Save a new generated CV version.
        Use only paragraph indices returned by read_cv_blocks.
        """
        normalized_revisions = SaveCvVariantInput(
            title=title,
            revisions=revisions,
        )
        generated_document = create_generated_variant(
            source_document_id=document_id,
            display_name=normalized_revisions.title,
            revisions=normalized_revisions.revisions,
        )
        generated_capture.append(generated_document)
        return generated_document.model_dump_json()

    return create_agent(
        model=build_model(),
        tools=[read_cv_blocks, extract_job_offer, save_cv_variant],
        response_format=ToolStrategy(schema=CvOptimizationStructuredResponse),
        system_prompt=(
            "You tailor a candidate CV to a job offer using only verified information already "
            "present in the CV. Never invent experience, responsibilities, metrics, degrees, "
            "dates, employers, or skills. You may only rewrite existing paragraph blocks to "
            "better match the job posting. Do not add or remove paragraphs. Keep the original "
            "paragraph indices and revise only the paragraphs that truly improve alignment. "
            "Your workflow is: 1) extract_job_offer, 2) read_cv_blocks, 3) decide minimal "
            "revisions, 4) save_cv_variant, 5) explain what changed and mention any gaps."
        ),
    )


async def optimize_cv(request: CvOptimizationRequest) -> CvOptimizationResponse:
    get_document(request.document_id)
    offer_extract_capture: list[TavilyExtractPayload] = []
    generated_capture: list[DocumentSummary] = []
    agent = build_cv_agent(
        document_id=request.document_id,
        offer_extract_capture=offer_extract_capture,
        generated_capture=generated_capture,
    )

    prompt = (
        f"Adapt the CV document '{request.document_id}' to the job offer at {request.job_url}. "
        "Use the tools and generate a new version of the CV. "
        "Keep claims grounded in the source document only."
    )
    if request.instructions:
        prompt += f" Additional user instructions: {request.instructions}"

    result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})

    structured_response = result.get("structured_response")
    last_ai_message = get_last_ai_message(result.get("messages", []))
    content = ""
    parsed_structured_response: CvOptimizationStructuredResponse | None = None

    if isinstance(structured_response, CvOptimizationStructuredResponse):
        parsed_structured_response = structured_response
        content = structured_response.answer.strip()

    if not content:
        content = normalize_content(last_ai_message.content if last_ai_message else "")

    return CvOptimizationResponse(
        content=content,
        generated_document=generated_capture[-1] if generated_capture else None,
        offer_extract=offer_extract_capture[-1] if offer_extract_capture else None,
        structured_response=parsed_structured_response,
    )

