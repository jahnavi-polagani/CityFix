"""
Schemas initialization
"""
from backend.app.schemas.common import APIResponse, ConfigResponse
from backend.app.schemas.user import UserCreate, UserLogin, UserOut, Token
from backend.app.schemas.report import (
    ReportCreate,
    ReportOut,
    ReportStatusUpdate,
    AIAnalysisRequest,
    AIAnalysisResponse,
)

__all__ = [
    "APIResponse",
    "ConfigResponse",
    "UserCreate",
    "UserLogin",
    "UserOut",
    "Token",
    "ReportCreate",
    "ReportOut",
    "ReportStatusUpdate",
    "AIAnalysisRequest",
    "AIAnalysisResponse",
]
