"""
Database setup and session management using SQLAlchemy
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

# SQLite needs connect_args check_same_thread=False for multithreaded FastAPI requests
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def migrate_schema():
    """Apply small additive migrations for the existing SQLite database."""
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if "reports" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("reports")}
    additions = {
        "submission_key": "VARCHAR(64)",
        "priority_level": "VARCHAR(20) DEFAULT 'Medium'",
        "ai_confidence": "FLOAT",
        "recommended_action": "TEXT",
    }
    with engine.begin() as connection:
        for column_name, definition in additions.items():
            if column_name not in existing_columns:
                connection.execute(text(f"ALTER TABLE reports ADD COLUMN {column_name} {definition}"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_reports_submission_key ON reports (submission_key)"))

    if "report_status_history" in inspector.get_table_names():
        with engine.begin() as connection:
            connection.execute(text(
                "UPDATE reports SET status = CASE LOWER(status) "
                "WHEN 'submitted' THEN 'Submitted' WHEN 'in_review' THEN 'Under Review' "
                "WHEN 'under review' THEN 'Under Review' WHEN 'assigned' THEN 'Assigned' "
                "WHEN 'in_progress' THEN 'In Progress' WHEN 'in progress' THEN 'In Progress' "
                "WHEN 'resolved' THEN 'Resolved' WHEN 'rejected' THEN 'Rejected' ELSE 'Submitted' END"
            ))
            connection.execute(text(
                "INSERT INTO report_status_history (report_id, status, note, updated_by_id, created_at) "
                "SELECT r.id, CASE WHEN r.status IN ('Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved', 'Rejected') "
                "THEN r.status ELSE 'Submitted' END, 'Initial status recorded during migration', NULL, COALESCE(r.created_at, CURRENT_TIMESTAMP) "
                "FROM reports r WHERE NOT EXISTS (SELECT 1 FROM report_status_history h WHERE h.report_id = r.id)"
            ))


def get_db():
    """
    FastAPI dependency that yields a scoped database session.
    Automatically closes the session after request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
