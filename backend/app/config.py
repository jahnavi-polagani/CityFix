"""
Centralized Configuration for CityFix
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Project root directory (CityFix/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # Brand Identity (Single source of truth)
    APP_NAME: str = "CityFix"
    APP_TAGLINE: str = "AI-Powered Civic Issue Reporting & Resolution Platform"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Security & Tokens
    SECRET_KEY: str = "cityfix-hackathon-insecure-secret-key-replace-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite:///./cityfix.db"

    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # AI Service Configuration
    GEMINI_API_KEY: str = ""

    # Geolocation / Default Map Coordinates
    DEFAULT_CITY_NAME: str = "City Center"
    DEFAULT_LATITUDE: float = 12.9716
    DEFAULT_LONGITUDE: float = 77.5946
    DEFAULT_MAP_ZOOM: int = 13

    # Civic Categories Supported by CityFix
    ISSUE_CATEGORIES: list[str] = [
        "Pothole / Road Damage",
        "Garbage / Sanitation",
        "Broken Streetlight / Electrical",
        "Water Leakage / Drainage",
        "Fallen Tree / Greenery",
        "Traffic Signal / Signage",
        "Illegal Parking / Encroachment",
        "Public Property Vandalism",
        "Other Civic Issue",
    ]

    # City Departments
    DEPARTMENTS: list[str] = [
        "Roads & Infrastructure",
        "Solid Waste Management",
        "Electricity & Lighting",
        "Water Supply & Sewerage",
        "Parks & Recreation",
        "Traffic & Transit",
        "General Municipal Services",
    ]

    class Config:
        env_file = os.path.join(BASE_DIR, ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings singleton instance
settings = Settings()
