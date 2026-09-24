"""OpenRouter LLM quiz solver with model fallback chain and tenacity retries."""

import json
import logging
from typing import Any

import requests
import tenacity as tc

from coursera_automation.config import Settings

from .json_extractor import extract_llm_json

logger = logging.getLogger(__name__)
EXC = (requests.RequestException, json.JSONDecodeError, KeyError, TypeError, ValueError, IndexError)
_key_idx = 0


@tc.retry(
    stop=tc.stop_after_attempt(2), wait=tc.wait_fixed(2), retry=tc.retry_if_exception_type(EXC),
    before_sleep=tc.before_sleep_log(logger, logging.WARNING), reraise=True,
)
def _call_openrouter_model(cfg: Settings, prompt: str | list[dict[str, Any]], model: str, key: str) -> dict[int, list[str]]:
    url = f"{cfg.openrouter_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "reasoning": {"enabled": True}}
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    res_data = resp.json()
    if "error" in res_data:
        raise ValueError(f"OpenRouter API error: {res_data['error']}")
    msg = res_data["choices"][0]["message"]
    data = extract_llm_json(msg.get("content") or msg.get("reasoning") or "")
    items = data if isinstance(data, list) else data.get("answers", [])
    ans = {it["index"]: [v] if isinstance(v := it.get("selected") or it.get("text") or it.get("answer") or [], str) else list(v) for it in items}
    if ans:
        logger.info("Parsed %d answer(s) from OpenRouter (%s): %s", len(ans), model, ans)
        return ans
    raise ValueError(f"Empty answers in payload: {msg}")


def query_openrouter(cfg: Settings, prompt: str | list[dict[str, Any]]) -> dict[int, list[str]]:
    """Query OpenRouter with key rotation and fallback across candidate models."""
    global _key_idx
    keys = cfg.get_openrouter_keys() or [""]
    primary = cfg.openrouter_vision_model if isinstance(prompt, list) else cfg.openrouter_model
    models = [primary] + [m.strip() for m in cfg.openrouter_fallback_models.split(",") if m.strip() and m.strip() != primary]
    for m in models:
        for offset in range(len(keys)):
            k = keys[(_key_idx + offset) % len(keys)]
            logger.info("Querying OpenRouter (model=%s, key=...%s)...", m, k[-6:] if len(k) > 6 else "")
            try:
                ans = _call_openrouter_model(cfg, prompt, m, k)
                _key_idx = (_key_idx + offset + 1) % len(keys)
                return ans
            except EXC as exc:
                logger.warning("OpenRouter key ...%s failed on %s: %s. Rotating...", k[-6:] if len(k) > 6 else "", m, exc)
    logger.error("All OpenRouter models and keys failed after retries.")
    return {}
