"""Configuration settings for Coursera Playwright automation."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()



@dataclass(frozen=True)
class Settings:
    """Application settings and runtime credentials."""

    login_url: str = os.getenv(
        "COURSERA_LOGIN_URL", "https://www.coursera.org"
    )
    course_url: str = os.getenv(
        "COURSERA_COURSE_URL",
        "https://www.coursera.org/specializations/generative-ai-for-software-developers",
    )
    email: str = os.getenv("COURSERA_EMAIL", "24bai70310@cuchd.in")
    password: str = os.getenv("COURSERA_PASSWORD", "Lakshya.24AI")
    headless: bool = os.getenv("COURSERA_HEADLESS", "false").lower() == "true"
    timeout_ms: int = int(os.getenv("COURSERA_TIMEOUT_MS", "40000"))
    max_items: int = int(os.getenv("COURSERA_MAX_ITEMS", "25"))
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )
    openrouter_model: str = os.getenv(
        "OPENROUTER_MODEL", "inclusionai/ling-3.0-flash-fin:free"
    )
    post_quiz_wait_sec: int = int(os.getenv("COURSERA_POST_QUIZ_WAIT_SEC", "180"))


config = Settings()


