"""Configuration definition for individual automation instances."""

from dataclasses import dataclass

from coursera_automation.session import SessionConfig


@dataclass
class InstanceConfig:
    """Settings for a single course automation instance."""

    email: str
    password: str
    course_url: str
    legal_name: str = ""
    headless: bool = False
    max_items: int = 50
    timeout_ms: int = 40000

    def validate(self) -> None:
        """Ensure instance configuration has required fields including legal_name."""
        if not (n := self.legal_name.strip()) or n.lower() == "your legal name":
            raise ValueError(f"Instance '{self.email}' requires a valid 'legal_name'.")

    def to_settings(self) -> SessionConfig:
        """Convert this instance configuration into a full SessionConfig object."""
        return SessionConfig(
            email=self.email,
            password=self.password,
            course_url=self.course_url,
            headless=self.headless,
            max_items=self.max_items,
            timeout_ms=self.timeout_ms,
            legal_name=self.legal_name.strip(),
        )
