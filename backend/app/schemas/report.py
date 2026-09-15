"""
Pydantic Schemas for Issue Reports
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ReportBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5)
    category: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    landmark: Optional[str] = None
    severity: str = "medium"
    priority_score: int = 50
    priority_level: Optional[str] = None
    ai_confidence: Optional[float] = Field(None, ge=0, le=1)
    recommended_action: Optional[str] = None
    reporter_name: Optional[str] = None
    reporter_contact: Optional[str] = None


class ReportCreate(ReportBase):
    image_url: Optional[str] = None
    ai_analysis: Optional[str] = None


class ReportStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(Submitted|Under Review|Assigned|In Progress|Resolved|Rejected)$")
    assigned_department: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolution_image_url: Optional[str] = None
    note: Optional[str] = Field(None, max_length=500)


class ReportStatusHistoryOut(BaseModel):
    id: int
    status: str
    note: Optional[str] = None
    updated_by_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportOut(ReportBase):
    id: int
    tracking_number: str
    status: str
    image_url: Optional[str] = None
    ai_analysis: Optional[str] = None
    reported_by_id: Optional[int] = None
    assigned_department: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolution_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportDetailOut(ReportOut):
    status_history: list[ReportStatusHistoryOut] = Field(default_factory=list)


class PublicStatusHistoryOut(BaseModel):
    status: str
    created_at: datetime


class PublicReportOut(BaseModel):
    id: int
    tracking_number: str
    category: str
    severity: str
    priority_score: int
    priority_level: Optional[str] = None
    ai_confidence: Optional[float] = None
    description: str
    recommended_action: Optional[str] = None
    image_url: Optional[str] = None
    latitude: float
    longitude: float
    address: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    status_history: list[PublicStatusHistoryOut] = Field(default_factory=list)


class AIAnalysisRequest(BaseModel):
    image_base64: Optional[str] = None
    image_url: Optional[str] = None
    category_hint: Optional[str] = None


class AIAnalysisResponse(BaseModel):
    issue_type: str
    confidence: float = Field(..., ge=0, le=1)
    severity: str
    priority: int = Field(..., ge=0, le=100)
    priority_level: str
    priority_explanation: str
    description: str
    recommended_action: str
    demo_mode: bool
    analysis_source: str
