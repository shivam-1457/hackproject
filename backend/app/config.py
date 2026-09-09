import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Kisan2Consumer"
    APP_ENV: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/kisan2consumer_db"

    @property
    def sqlalchemy_database_url(self) -> str:
        """Ensures Render's postgres:// format is upgraded to postgresql:// for SQLAlchemy 2.0"""
        url = self.DATABASE_URL
        if url and url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql://", 1)
        return url

    # Security
    JWT_SECRET_KEY: str = "kisan2consumer_sih2026_super_secret_jwt_key_987654321"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    EMAIL_TOKEN_EXPIRE_HOURS: int = 24

    # Email
    SMTP_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "kisan2consumerhelp@gmail.com"
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "kisan2consumerhelp@gmail.com"
    SMTP_FROM_NAME: str = "Kisan2Consumer Helpdesk"

    # Uploads
    UPLOAD_DIR: str = "uploads"

    # Frontend
    FRONTEND_URL: str = "http://127.0.0.1:5500"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5500",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8000",
        "null"
    ]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
