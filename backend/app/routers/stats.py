"""
Statistics and Analytics Router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database import get_db
from backend.app.models.report import Report

router = APIRouter(prefix="/api/stats", tags=["Statistics"])


@router.get("")
def get_city_stats(db: Session = Depends(get_db)):
    """Summary statistics for public transparency and authority dashboards."""
    total = db.query(Report).count()
    resolved = db.query(Report).filter(Report.status == "resolved").count()
    in_progress = db.query(Report).filter(Report.status.in_(["in_progress", "assigned"])).count()
    pending = db.query(Report).filter(Report.status.in_(["submitted", "in_review"])).count()
    critical = db.query(Report).filter(Report.severity == "critical").count()
    
    # Issues by category
    category_counts = db.query(
        Report.category, func.count(Report.id)
    ).group_by(Report.category).all()
    
    return {
        "total_reports": total,
        "resolved_reports": resolved,
        "in_progress_reports": in_progress,
        "pending_reports": pending,
        "critical_reports": critical,
        "resolution_rate": round((resolved / total * 100), 1) if total > 0 else 100.0,
        "by_category": {cat: count for cat, count in category_counts}
    }
