"""
CityFix Application Launcher
Runs database migrations, creates upload directories, seeds demo records if empty, and boots Uvicorn server.
"""
import os
import sys

# Ensure current folder is in Python system path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.config import settings, BASE_DIR
from backend.app.database import engine, Base, SessionLocal
from backend.app.models.user import User
from backend.app.models.report import Report
from backend.app.services.auth_service import get_password_hash
import uvicorn


def seed_demo_data():
    """Seeds initial demo data (citizens, authority, sample civic reports) for hackathon presentation."""
    db = SessionLocal()
    try:
        # Check if users already exist
        if db.query(User).count() == 0:
            print("[CityFix] Seeding demo users...")
            demo_citizen = User(
                full_name="Sarah Citizen",
                email="citizen@cityfix.org",
                hashed_password=get_password_hash("password123"),
                role="citizen",
                phone="+1-555-0199"
            )
            demo_authority = User(
                full_name="Officer Marcus Vance",
                email="officer@cityfix.org",
                hashed_password=get_password_hash("admin123"),
                role="authority",
                department="Roads & Infrastructure",
                phone="+1-555-0188"
            )
            db.add_all([demo_citizen, demo_authority])
            db.commit()
            print("[CityFix] Demo users created: citizen@cityfix.org and officer@cityfix.org")

        # Check if reports already exist
        if db.query(Report).count() == 0:
            print("[CityFix] Seeding sample civic reports...")
            sample_reports = [
                Report(
                    tracking_number="CFX-2026-1001",
                    title="Deep Hazardous Pothole near MG Road Metro",
                    description="Large pothole approximately 10 inches deep on the main carriageway causing severe traffic slowdown and skid risks for bikes.",
                    category="Pothole / Road Damage",
                    severity="high",
                    priority_score=85,
                    status="in_progress",
                    latitude=12.9750,
                    longitude=77.6090,
                    address="MG Road, near Metro Pillar 142",
                    landmark="Opposite Trinity Junction",
                    assigned_department="Roads & Infrastructure",
                    reporter_name="Sarah Citizen"
                ),
                Report(
                    tracking_number="CFX-2026-1002",
                    title="Overflowing Waste Dump on 8th Main Footpath",
                    description="Municipal dustbins overflowing onto walking pavement for 3 days. Strong odor and pedestrian blockage.",
                    category="Garbage / Sanitation",
                    severity="medium",
                    priority_score=68,
                    status="submitted",
                    latitude=12.9810,
                    longitude=77.5950,
                    address="8th Main Road, Vasanth Nagar",
                    landmark="Near Community Park",
                    assigned_department="Solid Waste Management",
                    reporter_name="Concerned Resident"
                ),
                Report(
                    tracking_number="CFX-2026-1003",
                    title="Non-functional Streetlight Pole in Dark Corridor",
                    description="Two consecutive streetlight poles are dark since Monday, creating safety concerns for women and evening commuters.",
                    category="Broken Streetlight / Electrical",
                    severity="medium",
                    priority_score=72,
                    status="assigned",
                    latitude=12.9650,
                    longitude=77.5890,
                    address="Subhash Nagar 3rd Cross",
                    landmark="Beside Government High School",
                    assigned_department="Electricity & Lighting",
                    reporter_name="David R."
                ),
                Report(
                    tracking_number="CFX-2026-1004",
                    title="High-Pressure Clean Drinking Water Pipe Burst",
                    description="Drinking water main fractured, water flooding the road intersection and wasting treated water rapidly.",
                    category="Water Leakage / Drainage",
                    severity="critical",
                    priority_score=94,
                    status="in_progress",
                    latitude=12.9705,
                    longitude=77.6010,
                    address="Residency Road, Cross Junction",
                    landmark="Near State Bank Building",
                    assigned_department="Water Supply & Sewerage",
                    reporter_name="Priya Nair"
                ),
                Report(
                    tracking_number="CFX-2026-1005",
                    title="Dangerous Open Manhole on Walkway",
                    description="Manhole cover displaced during recent rain, leaving a 6-foot uncovered drain pit directly on the sidewalk.",
                    category="Pothole / Road Damage",
                    severity="critical",
                    priority_score=98,
                    status="resolved",
                    latitude=12.9680,
                    longitude=77.6150,
                    address="Old Airport Road, Ward 112",
                    landmark="In front of General Hospital",
                    assigned_department="Roads & Infrastructure",
                    resolution_notes="Heavy-duty reinforced concrete cover fitted and sealed by rapid response road crew.",
                    reporter_name="Civic Watcher"
                )
            ]
            db.add_all(sample_reports)
            db.commit()
            print(f"[CityFix] Successfully seeded {len(sample_reports)} sample reports!")
    except Exception as e:
        print(f"[CityFix] Seeding note: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    print("=" * 60)
    print(f"  Starting {settings.APP_NAME} Platform")
    print(f"  {settings.APP_TAGLINE}")
    print("=" * 60)

    # 1. Ensure upload directory exists
    uploads_dir = os.path.join(BASE_DIR, settings.UPLOAD_DIR)
    os.makedirs(uploads_dir, exist_ok=True)

    # 2. Initialize Database tables
    print("[CityFix] Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)

    # 3. Seed Demo Data
    seed_demo_data()

    # 4. Start Uvicorn Server
    print(f"[CityFix] Launching web server on http://{settings.HOST}:{settings.PORT}")
    print(f"[CityFix] Swagger API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"[CityFix] Interactive City Map & UI: http://{settings.HOST}:{settings.PORT}/")
    print("=" * 60)

    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )


if __name__ == "__main__":
    main()
