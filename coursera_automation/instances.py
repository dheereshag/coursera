"""Multi-instance configuration loader for Coursera automation sessions."""

import importlib.util, json, logging
from dataclasses import dataclass
from pathlib import Path

from coursera_automation.session import SessionConfig

logger = logging.getLogger(__name__)


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
            email=self.email, password=self.password, course_url=self.course_url,
            headless=self.headless, max_items=self.max_items, timeout_ms=self.timeout_ms,
            legal_name=self.legal_name.strip(),
        )


def _load_py(p: Path) -> list[InstanceConfig]:
    if (spec := importlib.util.spec_from_file_location("user_instances", p)) and spec.loader:
        spec.loader.exec_module(mod := importlib.util.module_from_spec(spec))
        return [it for it in getattr(mod, "INSTANCES", []) if isinstance(it, InstanceConfig)]
    return []


def _load_json(p: Path) -> list[InstanceConfig]:
    data = json.loads(p.read_text(encoding="utf-8"))
    return [InstanceConfig(**it) for it in data] if isinstance(data, list) else []


def load_instances(path: str = "instances.py") -> list[InstanceConfig]:
    """Load instance definitions from Python config or JSON file."""
    p = Path(path if Path(path).exists() or path != "instances.py" or not Path("instances.json").exists() else "instances.json")
    if p.exists():
        try:
            if (insts := _load_py(p) if p.suffix == ".py" else _load_json(p)):
                logger.info("Loaded %d instance(s) from %s", len(insts), p); return insts
        except (json.JSONDecodeError, KeyError, TypeError, OSError, AttributeError, ImportError, ValueError) as exc:
            logger.warning("Failed to load instances from %s: %s", p, exc)
    raise ValueError(f"No valid instances could be loaded from '{path}'.")
