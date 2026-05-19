from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.schemas.documents import DocumentRenameRequest, DocumentSummary
from app.services.document_store import (
    create_document_from_upload,
    delete_document,
    get_document,
    get_document_download_path,
    list_documents,
    rename_document,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentSummary])
def get_documents() -> list[DocumentSummary]:
    return list_documents()


@router.get("/{document_id}", response_model=DocumentSummary)
def get_document_detail(document_id: str) -> DocumentSummary:
    try:
        return get_document(document_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("", response_model=DocumentSummary)
async def upload_document(
    file: UploadFile = File(...),
    display_name: str | None = Form(default=None),
) -> DocumentSummary:
    try:
        content = await file.read()
        return create_document_from_upload(
            filename=file.filename or "document.docx",
            content=content,
            display_name=display_name,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.patch("/{document_id}", response_model=DocumentSummary)
def update_document_name(document_id: str, request: DocumentRenameRequest) -> DocumentSummary:
    try:
        return rename_document(document_id, request.display_name)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/{document_id}", status_code=204)
def remove_document(document_id: str) -> None:
    try:
        delete_document(document_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    format: Literal["docx", "pdf"] = "docx",
) -> FileResponse:
    try:
        path = get_document_download_path(document_id, format)
        summary = get_document(document_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    media_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if format == "docx"
        else "application/pdf"
    )
    filename = f"{summary.display_name}.{format}"
    return FileResponse(path, media_type=media_type, filename=filename)

