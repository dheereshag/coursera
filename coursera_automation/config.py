"""Configuration settings for Coursera Playwright automation."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()



@dataclass(frozen=True)
class Settings:
    """Application settings and runtime credentials."""

    login_url: str = "https://www.coursera.org"
    email: str = ""
    password: str = ""
    course_url: str = ""
    headless: bool = False
    timeout_ms: int = int(os.getenv("COURSERA_TIMEOUT_MS", "40000"))
    max_items: int = int(os.getenv("COURSERA_MAX_ITEMS", "25"))
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "inclusionai/ling-3.0-flash-fin:free"
    openrouter_vision_model: str = os.getenv("OPENROUTER_VISION_MODEL", "nex-agi/nex-n2.5-mini:free")
    openrouter_fallback_models: str = os.getenv(
        "OPENROUTER_FALLBACK_MODELS",
        "dots-studio/dots-3-note-preview:free,qwen/qwen3.8-27b:free,openrouter/free",
    )
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    groq_vision_model: str = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b")
    groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    post_quiz_wait_sec: int = int(os.getenv("COURSERA_POST_QUIZ_WAIT_SEC", "180"))

    def get_openrouter_keys(self) -> list[str]:
        """Return list of parsed OpenRouter API keys for rotation."""
        return [k.strip() for k in self.openrouter_api_key.split(",") if k.strip()]


config = Settings()


