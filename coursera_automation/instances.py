"""Multi-instance configuration loader for Coursera automation sessions."""

import importlib.util
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from coursera_automation.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class InstanceConfig:
    """Settings for a single course automation instance."""

    email: str
    password: str
    course_url: str
    headless: bool = False
    max_items: int = 50
    timeout_ms: int = 40000

    def to_settings(self) -> Settings:
        """Convert this instance configuration into a full Settings object."""
        return Settings(
            email=self.email, password=self.password, course_url=self.course_url,
            headless=self.headless, max_items=self.max_items, timeout_ms=self.timeout_ms,
        )


def _load_py(p: Path) -> list[InstanceConfig]:
    spec = importlib.util.spec_from_file_location("user_instances", p)
    if not (spec and spec.loader):
        return []
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [it for it in getattr(mod, "INSTANCES", []) if isinstance(it, InstanceConfig)]


def _load_json(p: Path) -> list[InstanceConfig]:
    data = json.loads(p.read_text(encoding="utf-8"))
    return [InstanceConfig(**it) for it in data] if isinstance(data, list) else []


def load_instances(path: str = "instances.py") -> list[InstanceConfig]:
    """Load instance definitions from Python config or JSON file."""
    p = Path(path)
    if not p.exists() and path == "instances.py" and Path("instances.json").exists():
        p = Path("instances.json")
    if p.exists():
        try:
            if (insts := _load_py(p) if p.suffix == ".py" else _load_json(p)):
                logger.info("Loaded %d instance(s) from %s", len(insts), p)
                return insts
        except (json.JSONDecodeError, KeyError, TypeError, OSError, AttributeError, ImportError, ValueError) as exc:
            logger.warning("Failed to load instances from %s: %s", p, exc)
    raise ValueError(f"No valid instances could be loaded from '{path}'.")
