"""Groq LLM quiz solver using OpenAI-compatible API."""

import json
import logging
from typing import Any

import requests
import tenacity as tc

from coursera_automation.config import Settings

from .json_extractor import extract_llm_json

logger = logging.getLogger(__name__)
EXC = (requests.RequestException, json.JSONDecodeError, KeyError, TypeError, ValueError, IndexError)


@tc.retry(
    stop=tc.stop_after_attempt(2), wait=tc.wait_fixed(2), retry=tc.retry_if_exception_type(EXC),
    before_sleep=tc.before_sleep_log(logger, logging.WARNING), reraise=True,
)
def _call_groq(cfg: Settings, prompt: str | list[dict[str, Any]]) -> dict[int, list[str]]:
    url = f"{cfg.groq_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {cfg.groq_api_key}", "Content-Type": "application/json"}
    model = cfg.groq_vision_model if isinstance(prompt, list) else cfg.groq_model
    tokens = 512 if isinstance(prompt, list) else 4096
    payload = {
        "model": model, "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2, "max_completion_tokens": tokens, "reasoning_effort": "high",
        "response_format": {"type": "json_object"},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code == 400:
        raise RuntimeError(f"Groq 400 Bad Request: {resp.text}")
    resp.raise_for_status()
    res_data = resp.json()
    if "error" in res_data:
        raise ValueError(f"Groq API error: {res_data['error']}")
    msg = res_data["choices"][0]["message"]
    data = extract_llm_json(msg.get("content") or msg.get("reasoning") or "")
    items = data if isinstance(data, list) else data.get("answers", [])
    ans = {it["index"]: [v] if isinstance(v := it.get("selected") or it.get("text") or it.get("answer") or [], str) else list(v) for it in items}
    if ans:
        logger.info("Parsed %d answer(s) from Groq (%s): %s", len(ans), model, ans)
        return ans
    raise ValueError(f"Empty answers in Groq payload: {msg}")


def query_groq(cfg: Settings, prompt: str | list[dict[str, Any]]) -> dict[int, list[str]]:
    """Query Groq LLM model and return parsed answers."""
    m = cfg.groq_vision_model if isinstance(prompt, list) else cfg.groq_model
    logger.info("Querying Groq (%s)...", m)
    return _call_groq(cfg, prompt)
