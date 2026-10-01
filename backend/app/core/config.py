import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Patient Glucose Monitoring & AI Reporting System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/patients.db"

    # LLM
    LLM_PROVIDER: str = "mock"  # openai, google, mock
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    GOOGLE_API_KEY: str = ""

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "notifications@hospital-care.org"
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "notifications@hospital-care.org"
    EMAILS_FROM_NAME: str = "Hospital Glucose Monitoring Center"
    EMAIL_ENABLED: bool = False

    # Configurable Glucose Thresholds (mg/dL)
    GLUCOSE_HYPO_THRESHOLD: float = 70.0
    GLUCOSE_NORMAL_MAX: float = 99.0
    GLUCOSE_PREDIABETES_MAX: float = 125.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
