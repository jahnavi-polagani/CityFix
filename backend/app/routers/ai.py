"""
AI Vision & Civic Defect Detection Router
"""
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from backend.app.schemas.report import AIAnalysisResponse
from backend.app.services.ai_service import analyze_civic_issue_image

router = APIRouter(prefix="/api/ai", tags=["AI Civic Analysis"])


@router.post("/analyze", response_model=AIAnalysisResponse)
async def analyze_image_endpoint(
    file: Optional[UploadFile] = File(None),
    category_hint: Optional[str] = Form(None)
):
    """
    Analyze civic issue image using AI vision.
    Outputs detected defect, confidence, estimated severity, priority score, and smart description.
    """
    image_bytes = None
    filename = None
    if file:
        filename = file.filename
        image_bytes = await file.read()

    try:
        analysis = analyze_civic_issue_image(
            image_bytes=image_bytes,
            filename=filename,
            category_hint=category_hint
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return AIAnalysisResponse(**analysis)
