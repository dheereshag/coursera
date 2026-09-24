"""OpenRouter LLM quiz solver with single API key and tenacity retries."""

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
def _call_openrouter_model(cfg: Settings, prompt: str | list[dict[str, Any]], model: str, effort: str | None = None) -> dict[int, list[str]]:
    url = f"{cfg.openrouter_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {cfg.openrouter_api_key}", "Content-Type": "application/json"}
    payload: dict[str, Any] = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    if effort:
        payload["reasoning"] = {"effort": effort}
    resp = requests.post(url, headers=headers, json=payload, timeout=90)
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


def query_openrouter(cfg: Settings, prompt: str | list[dict[str, Any]], model: str | None = None, effort: str | None = None) -> dict[int, list[str]]:
    """Query OpenRouter with single key using specified model and reasoning effort."""
    target_model = model or cfg.openrouter_model
    logger.info("Querying OpenRouter (model=%s, effort=%s)...", target_model, effort)
    try:
        return _call_openrouter_model(cfg, prompt, target_model, effort=effort)
    except EXC as exc:
        logger.warning("OpenRouter model %s failed: %s.", target_model, exc)
        if target_model != cfg.openrouter_fallback_model:
            logger.info("Retrying with API fallback model: %s...", cfg.openrouter_fallback_model)
            try:
                return _call_openrouter_model(cfg, prompt, cfg.openrouter_fallback_model, effort=effort)
            except EXC as err:
                logger.error("Fallback model %s also failed: %s.", cfg.openrouter_fallback_model, err)
    return {}
