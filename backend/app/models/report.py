"""
Report Model for Civic Issues
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


def generate_tracking_number() -> str:
    """Return the base report ID format; the router adds the unique sequence."""
    return "CITYFIX-000001"


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(30), unique=True, index=True, default=generate_tracking_number, nullable=False)
    submission_key = Column(String(64), unique=True, index=True, nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(80), index=True, nullable=False)
    
    # Severity & Prioritization
    severity = Column(String(20), default="medium", nullable=False)  # "low", "medium", "high", "critical"
    priority_score = Column(Integer, default=50, nullable=False)    # 1 to 100
    priority_level = Column(String(20), default="Medium", nullable=False)
    ai_confidence = Column(Float, nullable=True)
    
    # Status lifecycle: submitted -> in_review -> assigned -> in_progress -> resolved (or rejected)
    status = Column(String(30), default="submitted", index=True, nullable=False)
    
    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(255), nullable=True)
    landmark = Column(String(150), nullable=True)
    
    # Evidence & AI
    image_url = Column(String(255), nullable=True)
    ai_analysis = Column(Text, nullable=True)  # JSON formatted insights from AI Vision
    recommended_action = Column(Text, nullable=True)
    
    # User References
    reported_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reporter_name = Column(String(120), nullable=True)  # Stored for guest or quick lookup
    reporter_contact = Column(String(100), nullable=True)
    
    # Assignment & Resolution
    assigned_department = Column(String(100), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolution_image_url = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    reporter = relationship("User", back_populates="reports", foreign_keys=[reported_by_id])
    status_history = relationship("ReportStatusHistory", back_populates="report", order_by="ReportStatusHistory.created_at", cascade="all, delete-orphan")


class ReportStatusHistory(Base):
    __tablename__ = "report_status_history"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False, index=True)
    status = Column(String(30), nullable=False)
    note = Column(Text, nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    report = relationship("Report", back_populates="status_history")
    updated_by = relationship("User", foreign_keys=[updated_by_id])
