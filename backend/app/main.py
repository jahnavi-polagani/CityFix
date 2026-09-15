"""
CityFix FastAPI Main Application
"""
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import settings, BASE_DIR
from backend.app.database import engine, Base, migrate_schema
from backend.app.routers import auth_router, reports_router, ai_router, stats_router
from backend.app.routers.auth import require_user
from backend.app.models.user import User

# Ensure all database tables exist on startup
Base.metadata.create_all(bind=engine)
migrate_schema()

# Ensure upload directory exists
upload_path = os.path.join(BASE_DIR, settings.UPLOAD_DIR)
os.makedirs(upload_path, exist_ok=True)

# Frontend directories
frontend_dir = os.path.join(BASE_DIR, "frontend")
static_dir = os.path.join(frontend_dir, "static")
os.makedirs(static_dir, exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_TAGLINE,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Uploads directory for serving user-uploaded issue photos
app.mount("/uploads", StaticFiles(directory=upload_path), name="uploads")

# Mount static assets (CSS, JS, icons) if static dir exists
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include API Routers
app.include_router(auth_router)
app.include_router(reports_router)
app.include_router(ai_router)
app.include_router(stats_router)


# Health Check
@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "tagline": settings.APP_TAGLINE,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV
    }


# Centralized Brand & Application Configuration for Frontend
@app.get("/api/config", tags=["System"])
def get_public_config():
    return {
        "app_name": settings.APP_NAME,
        "app_tagline": settings.APP_TAGLINE,
        "app_version": settings.APP_VERSION,
        "categories": settings.ISSUE_CATEGORIES,
        "departments": settings.DEPARTMENTS,
        "default_city": settings.DEFAULT_CITY_NAME,
        "default_lat": settings.DEFAULT_LATITUDE,
        "default_lng": settings.DEFAULT_LONGITUDE,
        "default_zoom": settings.DEFAULT_MAP_ZOOM,
    }


# Frontend Route Handlers
@app.get("/", tags=["Frontend"])
def serve_index():
    index_file = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": f"Welcome to {settings.APP_NAME} API. Visit /docs for API documentation."}


@app.get("/report", tags=["Frontend"])
def serve_report():
    file_path = os.path.join(frontend_dir, "report.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/report-details", tags=["Frontend"])
def serve_report_details():
    file_path = os.path.join(frontend_dir, "report-details.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/public-report-details", tags=["Frontend"])
def serve_public_report_details():
    file_path = os.path.join(frontend_dir, "public-report-details.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/dashboard", tags=["Frontend"])
def serve_dashboard():
    file_path = os.path.join(frontend_dir, "dashboard.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/admin", tags=["Frontend"])
def serve_admin(user: User = Depends(require_user)):
    if user.role not in {"authority", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authority access required")
    file_path = os.path.join(frontend_dir, "admin.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/explore", tags=["Frontend"])
def serve_explore():
    file_path = os.path.join(frontend_dir, "explore.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/authority", tags=["Frontend"])
def serve_authority(user: User = Depends(require_user)):
    if user.role not in {"authority", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authority access required")
    file_path = os.path.join(frontend_dir, "authority.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/login", tags=["Frontend"])
def serve_login():
    file_path = os.path.join(frontend_dir, "login.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/about", tags=["Frontend"])
def serve_about():
    file_path = os.path.join(frontend_dir, "about.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/contact", tags=["Frontend"])
def serve_contact():
    file_path = os.path.join(frontend_dir, "contact.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/privacy", tags=["Frontend"])
def serve_privacy():
    file_path = os.path.join(frontend_dir, "privacy.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_dir, "index.html"))

