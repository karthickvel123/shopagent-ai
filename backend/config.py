"""Application configuration loaded from environment variables."""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Central configuration for ShopAgent AI."""

    # Gemini
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = "gemini-3.8-flash"

    # Razorpay Test Mode
    razorpay_key_id: str = os.getenv("RAZORPAY_KEY_ID", "")
    razorpay_key_secret: str = os.getenv("RAZORPAY_KEY_SECRET", "")

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./shopagent.db")

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
