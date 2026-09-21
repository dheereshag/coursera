"""Multi-instance configuration loader for Coursera automation sessions."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from coursera_automation.config import Settings, config

logger = logging.getLogger(__name__)


@dataclass
class InstanceConfig:
    """Settings for a single course automation instance."""

    email: str
    password: str
    course_url: str
    headless: bool = False
    max_items: int = 50
    timeout_ms: int = 15000

    def to_settings(self) -> Settings:
        """Convert this instance configuration into a full Settings object."""
        return Settings(
            email=self.email,
            password=self.password,
            course_url=self.course_url,
            headless=self.headless,
            max_items=self.max_items,
            timeout_ms=self.timeout_ms,
        )


def load_instances(path: str = "instances.json") -> list[InstanceConfig]:
    """Load instance definitions from JSON, or fallback to default Settings."""
    p = Path(path)
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                instances = [InstanceConfig(**item) for item in data]
                logger.info("Loaded %d instances from %s", len(instances), path)
                return instances
        except (json.JSONDecodeError, KeyError, TypeError, OSError) as exc:
            logger.warning("Failed to load %s (%s). Using defaults.", path, exc)

    logger.info("Using default single instance configuration.")
    return [
        InstanceConfig(
            email=config.email, password=config.password,
            course_url=config.course_url, headless=config.headless,
            max_items=config.max_items, timeout_ms=config.timeout_ms,
        )
    ]


