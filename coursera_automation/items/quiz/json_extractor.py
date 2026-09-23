"""Robust JSON extraction from LLM responses with markdown fences and reasoning tags."""

import json
import re
from typing import Any


def extract_llm_json(raw: str | None) -> dict[str, Any] | list[Any]:
    """Extract and parse JSON object or array from raw text, code fences, or think blocks."""
    if not (text := (raw or "").strip()):
        raise ValueError("Empty response text from LLM")
    text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
    if (m := re.search(r"```(?:json)?\s*([{\[][\s\S]*?[}\]])\s*```", text)) or (
        m := re.search(r"[{\[][\s\S]*[}\]]", text)
    ):
        return json.loads(m.group(1) if m.lastindex else m.group(0))
    return json.loads(text)
