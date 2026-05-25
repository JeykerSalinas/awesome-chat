
from fastapi import APIRouter, HTTPException, UploadFile, File

from app.schemas.rag_system import TestRagSystem
from app.services.cv_agent import optimize_cv

router = APIRouter(prefix="/rag-system", tags=["rag-system"])

@router.get('')
def embedded_document () :
     return 'Hello world'


@router.post("/documents")
async def upload_pdf(file: UploadFile = File(...)):
    contents = await file.read()

     
    return {
        "filename": file.filename,
        "content_type": file.content_type
    }