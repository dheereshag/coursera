"""Configuration settings for Coursera Playwright automation."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()



@dataclass(frozen=True)
class Settings:
    """Application global settings and runtime credentials."""

    login_url: str = "https://www.coursera.org"
    timeout_ms: int = int(os.getenv("COURSERA_TIMEOUT_MS", "40000"))
    max_items: int = int(os.getenv("COURSERA_MAX_ITEMS", "25"))
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = os.getenv(
        "OPENROUTER_MODEL", "deepseek/deepseek-v4.1-flash"
    )
    openrouter_fallback_model: str = os.getenv(
        "OPENROUTER_FALLBACK_MODEL", "z-ai/glm-5.3-flash"
    )
    post_quiz_wait_sec: int = int(os.getenv("COURSERA_POST_QUIZ_WAIT_SEC", "180"))


config = Settings()


