"""LLM quiz solver using OpenRouter reasoning model via requests and tenacity."""

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
def _query_and_parse(cfg: Settings, prompt: str, model: str) -> dict[int, list[str]]:
    """Query OpenRouter chat completion and parse answers, retrying on errors."""
    url = f"{cfg.openrouter_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {cfg.openrouter_api_key}", "Content-Type": "application/json"}
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
        logger.info("Parsed %d answer(s) from %s: %s", len(ans), model, ans)
        return ans
    raise ValueError(f"Empty answers in payload: {msg}")


def solve_quiz_with_llm(questions: list[dict[str, Any]], cfg: Settings) -> dict[int, list[str]]:
    """Query OpenRouter LLM with model fallback chain and parse JSON answers."""
    prompt = (
        "Answer questions: 'single'=1 option, 'multiselect'=all, 'textarea'=concise written text.\n"
        "For multiple choice, 'selected' MUST contain the exact verbatim option text from 'options'.\n"
        'Respond ONLY in JSON: {"answers": [{"index": 0, "selected": ["exact option text or answer"]}]}\n\n'
        f"Questions:\n{json.dumps(questions, indent=2)}"
    )
    models = [cfg.openrouter_model] + [m.strip() for m in cfg.openrouter_fallback_models.split(",") if m.strip() and m.strip() != cfg.openrouter_model]
    for m in models:
        logger.info("Querying OpenRouter (%s) with %d questions...", m, len(questions))
        try:
            return _query_and_parse(cfg, prompt, m)
        except EXC as exc:
            logger.warning("Model %s failed: %s. Trying fallback...", m, exc)
    logger.error("All OpenRouter models failed after retries.")
    return {}
