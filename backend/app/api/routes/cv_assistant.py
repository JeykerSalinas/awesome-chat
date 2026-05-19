from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.cv_assistant import CvOptimizationRequest, CvOptimizationResponse
from app.services.cv_agent import optimize_cv

router = APIRouter(prefix="/cv-assistant", tags=["cv-assistant"])


@router.post("/optimize", response_model=CvOptimizationResponse)
async def optimize_cv_for_job(request: CvOptimizationRequest) -> CvOptimizationResponse:
    try:
        return await optimize_cv(request)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Error optimizing CV: {error}") from error

