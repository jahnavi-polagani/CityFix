"""
Common Pydantic Schemas
"""
from typing import Any
from pydantic import BaseModel


class APIResponse(BaseModel):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Any = None


class ConfigResponse(BaseModel):
    app_name: str
    app_tagline: str
    app_version: str
    categories: list[str]
    departments: list[str]
    default_city: str
    default_lat: float
    default_lng: float
    default_zoom: int
