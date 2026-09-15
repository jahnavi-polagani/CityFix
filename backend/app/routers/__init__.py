"""
Routers initialization
"""
from backend.app.routers.auth import router as auth_router
from backend.app.routers.reports import router as reports_router
from backend.app.routers.ai import router as ai_router
from backend.app.routers.stats import router as stats_router

__all__ = ["auth_router", "reports_router", "ai_router", "stats_router"]
