"""Instance file loading from Python modules or JSON configurations."""

import importlib.util
import json
import logging
from pathlib import Path

from coursera_automation.instances.config import InstanceConfig

logger = logging.getLogger(__name__)


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
    target_path = Path(
        path
        if Path(path).exists() or path != "instances.py" or not Path("instances.json").exists()
        else "instances.json"
    )
    if target_path.exists():
        try:
            insts = _load_py(target_path) if target_path.suffix == ".py" else _load_json(target_path)
            if insts:
                logger.info("Loaded %d instance(s) from %s", len(insts), target_path)
                return insts
        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
            OSError,
            AttributeError,
            ImportError,
            ValueError,
        ) as exc:
            logger.warning("Failed to load instances from %s: %s", target_path, exc)
    raise ValueError(f"No valid instances could be loaded from '{path}'.")
