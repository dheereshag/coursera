"""Configuration settings for Wellfound automation."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class WellfoundConfig:
    """Wellfound automation configuration parameters."""

    email: str = field(
        default_factory=lambda: os.getenv("WELLFOUND_EMAIL", "da11@iitbbs.ac.in")
    )
    password: str = field(
        default_factory=lambda: os.getenv("WELLFOUND_PASSWORD", "Derek_20173017")
    )
    base_url: str = field(
        default_factory=lambda: os.getenv("WELLFOUND_BASE_URL", "https://wellfound.com")
    )
    login_url: str = field(
        default_factory=lambda: os.getenv("WELLFOUND_LOGIN_URL", "https://wellfound.com/login")
    )
    user_data_dir: str = field(
        default_factory=lambda: os.getenv("WELLFOUND_USER_DATA_DIR", ".browser_data/wellfound")
    )
    headless: bool = field(
        default_factory=lambda: os.getenv("WELLFOUND_HEADLESS", "false").lower() == "true"
    )
    timeout_ms: int = 15000
