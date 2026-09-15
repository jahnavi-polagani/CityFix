"""
Reports Router - Issue Submission, Listing, Tracking, and Authority Management
"""
import os
import json
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Form
from sqlalchemy.orm import Session
from backend.app.config import settings, BASE_DIR
from backend.app.database import get_db
from backend.app.models.report import Report, ReportStatusHistory, generate_tracking_number
from backend.app.models.user import User
from backend.app.schemas.report import PublicReportOut, ReportCreate, ReportOut, ReportDetailOut, ReportStatusUpdate
from backend.app.routers.auth import get_current_user, require_user

router = APIRouter(prefix="/api/reports", tags=["Reports"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_CATEGORIES = {"Pothole", "Garbage", "Broken Streetlight", "Overflowing Drain", "Road Damage", "Water Leakage", "Damaged Footpath", "Traffic Signal Problem", "Other"}


def _priority_level(score: int) -> str:
    if score <= 25:
        return "Low"
    if score <= 50:
        return "Medium"
    if score <= 75:
        return "High"
    return "Critical"


def _next_report_id(db: Session) -> str:
    next_number = (db.query(Report.id).order_by(Report.id.desc()).first() or (0,))[0] + 1
    candidate = f"CITYFIX-{next_number:06d}"
    while db.query(Report).filter(Report.tracking_number == candidate).first():
        next_number += 1
        candidate = f"CITYFIX-{next_number:06d}"
    return candidate


async def _store_validated_image(file: UploadFile) -> tuple[str, str]:
    if not file or not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An issue image is required.")
    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image format. Use JPG, JPEG, PNG, or WEBP.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded image is empty.")
    if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"Image must be smaller than {settings.MAX_UPLOAD_SIZE_MB} MB.")
    try:
        from PIL import Image
        import io
        with Image.open(io.BytesIO(contents)) as image:
            image.verify()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is not a valid image.") from exc

    upload_dir = os.path.join(BASE_DIR, settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as image_file:
        image_file.write(contents)
    return f"/uploads/{filename}", file_path


def _require_management_user(user: User = Depends(require_user)) -> User:
    if user.role not in {"authority", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authority access required")
    return user


@router.post("/upload", response_model=dict)
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file for issue verification."""
    image_url, _ = await _store_validated_image(file)
    return {
        "success": True,
        "image_url": image_url,
        "filename": image_url.rsplit("/", 1)[-1]
    }


@router.post("/submit", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def submit_report(
    file: UploadFile = File(...),
    issue_type: str = Form(...),
    confidence: float = Form(...),
    severity: str = Form(...),
    priority: int = Form(...),
    description: str = Form(...),
    recommended_action: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    address: Optional[str] = Form(None),
    demo_mode: bool = Form(False),
    submission_key: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    """Validate, store, and persist a complete citizen report."""
    if issue_type not in SUPPORTED_CATEGORIES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported issue category.")
    if not 0 <= confidence <= 1:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="AI confidence must be between 0 and 1.")
    if severity.upper() not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid severity.")
    if not 0 <= priority <= 100:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Priority must be between 0 and 100.")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid location coordinates.")
    if not description.strip() or not recommended_action.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="AI analysis details are required.")
    if submission_key:
        existing = db.query(Report).filter(Report.submission_key == submission_key, Report.reported_by_id == current_user.id).first()
        if existing:
            return existing

    image_url, image_path = await _store_validated_image(file)
    tracking_number = _next_report_id(db)
    analysis = {
        "issue_type": issue_type,
        "confidence": confidence,
        "severity": severity.upper(),
        "priority": priority,
        "description": description,
        "recommended_action": recommended_action,
        "demo_mode": demo_mode,
    }
    new_report = Report(
        tracking_number=tracking_number,
        submission_key=submission_key,
        title=f"{issue_type} reported via CityFix",
        description=description,
        category=issue_type,
        severity=severity.upper(),
        priority_score=priority,
        priority_level=_priority_level(priority),
        ai_confidence=confidence,
        recommended_action=recommended_action,
        latitude=latitude,
        longitude=longitude,
        address=address,
        image_url=image_url,
        ai_analysis=json.dumps(analysis),
        reported_by_id=current_user.id,
        reporter_name=current_user.full_name,
        reporter_contact=current_user.email,
        status="Submitted",
    )
    try:
        db.add(new_report)
        db.flush()
        db.add(ReportStatusHistory(report_id=new_report.id, status="Submitted", note="Report submitted by citizen", updated_by_id=current_user.id))
        db.commit()
        db.refresh(new_report)
    except Exception as exc:
        db.rollback()
        if os.path.exists(image_path):
            os.remove(image_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="We could not save the report. Please try again.") from exc
    return new_report


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def create_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    """Submit a new civic issue report."""
    tracking_no = generate_tracking_number()
    # Check uniqueness
    while db.query(Report).filter(Report.tracking_number == tracking_no).first():
        tracking_no = generate_tracking_number()
    
    new_report = Report(
        tracking_number=tracking_no,
        title=report_in.title,
        description=report_in.description,
        category=report_in.category,
        severity=report_in.severity,
        priority_score=report_in.priority_score,
        priority_level=report_in.priority_level or _priority_level(report_in.priority_score),
        ai_confidence=report_in.ai_confidence,
        recommended_action=report_in.recommended_action,
        latitude=report_in.latitude,
        longitude=report_in.longitude,
        address=report_in.address,
        landmark=report_in.landmark,
        image_url=report_in.image_url,
        ai_analysis=report_in.ai_analysis,
        reported_by_id=current_user.id,
        reporter_name=current_user.full_name,
        reporter_contact=current_user.email,
        status="Submitted"
    )
    db.add(new_report)
    db.flush()
    db.add(ReportStatusHistory(report_id=new_report.id, status="Submitted", note="Report submitted", updated_by_id=current_user.id))
    db.commit()
    db.refresh(new_report)
    return new_report


@router.get("/admin/all", response_model=List[ReportOut])
def list_admin_reports(
    limit: int = Query(200, le=500),
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    issue_type: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(_require_management_user)
):
    query = db.query(Report)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter((Report.tracking_number.ilike(term)) | (Report.category.ilike(term)) | (Report.address.ilike(term)))
    if status_filter and status_filter != "All":
        query = query.filter(Report.status == status_filter)
    if priority and priority != "All":
        query = query.filter(Report.priority_level == priority)
    if issue_type and issue_type != "All":
        query = query.filter(Report.category == issue_type)
    if severity and severity != "All":
        query = query.filter(Report.severity == severity)
    return query.order_by(Report.created_at.desc()).limit(limit).all()


@router.get("/admin/summary", response_model=dict)
def admin_summary(
    db: Session = Depends(get_db),
    user: User = Depends(_require_management_user)
):
    reports = db.query(Report).all()
    statuses = ["Submitted", "Under Review", "Assigned", "In Progress", "Resolved", "Rejected"]
    priorities = ["Critical", "High", "Medium", "Low"]
    categories = sorted(SUPPORTED_CATEGORIES)
    return {
        "total": len(reports),
        "new": sum(report.status == "Submitted" for report in reports),
        "statuses": {value: sum(report.status == value for report in reports) for value in statuses},
        "priorities": {value: sum(report.priority_level == value for report in reports) for value in priorities},
        "high_critical": sum(report.priority_level in {"High", "Critical"} or report.severity in {"HIGH", "CRITICAL"} for report in reports),
        "categories": {value: sum(report.category == value for report in reports) for value in categories},
    }


def _public_report(report: Report) -> dict:
    return {
        "id": report.id,
        "tracking_number": report.tracking_number,
        "category": report.category,
        "severity": report.severity,
        "priority_score": report.priority_score,
        "priority_level": report.priority_level,
        "ai_confidence": report.ai_confidence,
        "description": report.description,
        "recommended_action": report.recommended_action,
        "image_url": report.image_url,
        "latitude": report.latitude,
        "longitude": report.longitude,
        "address": report.address,
        "status": report.status,
        "created_at": report.created_at,
        "updated_at": report.updated_at,
        "status_history": [{"status": entry.status, "created_at": entry.created_at} for entry in report.status_history],
    }


@router.get("/public", response_model=List[PublicReportOut])
def list_public_reports(
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(200, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Return safe, read-only civic report data for the public Explore view."""
    query = db.query(Report)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter((Report.tracking_number.ilike(term)) | (Report.category.ilike(term)) | (Report.address.ilike(term)))
    if status_filter and status_filter != "All":
        query = query.filter(Report.status == status_filter)
    if priority and priority != "All":
        query = query.filter(Report.priority_level == priority)
    if category and category != "All":
        query = query.filter(Report.category == category)
    if severity and severity != "All":
        query = query.filter(Report.severity == severity)
    reports = query.order_by(Report.created_at.desc()).offset(offset).limit(limit).all()
    return [_public_report(report) for report in reports]


@router.get("/public/{identifier}", response_model=PublicReportOut)
def get_public_report(identifier: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.tracking_number == identifier.upper()).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public report not found")
    return _public_report(report)


@router.get("", response_model=List[ReportOut])
def list_reports(
    status: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Explore civic issues with interactive filters."""
    query = db.query(Report)
    
    if status and status != "all":
        query = query.filter(Report.status == status)
    if category and category != "all":
        query = query.filter(Report.category == category)
    if severity and severity != "all":
        query = query.filter(Report.severity == severity)
    if department and department != "all":
        query = query.filter(Report.assigned_department == department)
    if search:
        query = query.filter(
            (Report.title.ilike(f"%{search}%")) |
            (Report.description.ilike(f"%{search}%")) |
            (Report.tracking_number.ilike(f"%{search}%")) |
            (Report.address.ilike(f"%{search}%"))
        )
        
    query = query.order_by(Report.priority_score.desc(), Report.created_at.desc())
    return query.offset(offset).limit(limit).all()


@router.get("/my-reports", response_model=List[ReportOut])
def list_my_reports(
    db: Session = Depends(get_db),
    user: User = Depends(require_user)
):
    """Retrieve reports submitted by the logged-in citizen."""
    return db.query(Report).filter(Report.reported_by_id == user.id).order_by(Report.created_at.desc()).all()


@router.get("/mine/{identifier}", response_model=ReportDetailOut)
def get_my_report(
    identifier: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user)
):
    """Return a report only when it belongs to the authenticated citizen."""
    query = db.query(Report).filter(Report.reported_by_id == user.id)
    report = query.filter(Report.id == int(identifier)).first() if identifier.isdigit() else query.filter(Report.tracking_number == identifier.upper()).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


@router.get("/{identifier}", response_model=ReportDetailOut)
def get_report_by_id_or_tracking(
    identifier: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user)
):
    """Get a report only when it belongs to the user or the user manages reports."""
    report = None
    if identifier.isdigit():
        report = db.query(Report).filter(Report.id == int(identifier)).first()
    if not report:
        report = db.query(Report).filter(Report.tracking_number == identifier.upper()).first()
    
    if not report or (user.role not in {"authority", "admin"} and report.reported_by_id != user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    return report


@router.patch("/{report_id}/status", response_model=ReportOut)
def update_report_status(
    report_id: int,
    update_data: ReportStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(_require_management_user)
):
    """Update report status, department assignment, or resolution notes (Authority action)."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    
    previous_status = report.status
    if previous_status == update_data.status:
        if update_data.note:
            db.add(ReportStatusHistory(report_id=report.id, status=previous_status, note=update_data.note, updated_by_id=user.id))
            db.commit()
            db.refresh(report)
        return report

    report.status = update_data.status
    if update_data.assigned_department is not None:
        report.assigned_department = update_data.assigned_department
    if update_data.resolution_notes is not None:
        report.resolution_notes = update_data.resolution_notes
    if update_data.resolution_image_url is not None:
        report.resolution_image_url = update_data.resolution_image_url
        
    if update_data.status == "Resolved":
        report.resolved_at = datetime.utcnow()
        
    report.updated_at = datetime.utcnow()
    db.add(ReportStatusHistory(report_id=report.id, status=update_data.status, note=update_data.note, updated_by_id=user.id))
    db.commit()
    db.refresh(report)
    return report
