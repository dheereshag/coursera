"""Runtime session configuration combining instance credentials with global settings."""

from dataclasses import dataclass

from coursera_automation.config import Settings


@dataclass(frozen=True)
class SessionConfig(Settings):
    """Runtime configuration combining instance credentials with global settings."""

    email: str = ""
    password: str = ""
    course_url: str = ""
    legal_name: str = ""
    headless: bool = False
