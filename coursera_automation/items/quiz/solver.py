"""LLM quiz solver using OpenRouter reasoning model via requests and tenacity."""

import json
import logging
import re
from typing import Any

import requests
import tenacity as tc

from coursera_automation.config import Settings

logger = logging.getLogger(__name__)
EXC = (requests.RequestException, json.JSONDecodeError, KeyError, TypeError, ValueError)


@tc.retry(
    stop=tc.stop_after_attempt(3),
    wait=tc.wait_exponential(multiplier=1, min=2, max=10),
    retry=tc.retry_if_exception_type(EXC),
    before_sleep=tc.before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _query_and_parse(cfg: Settings, prompt: str) -> dict[int, list[str]]:
    """Query OpenRouter chat completion and parse answers, retrying on errors."""
    url = f"{cfg.openrouter_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {cfg.openrouter_api_key}", "Content-Type": "application/json"}
    payload = {"model": cfg.openrouter_model, "messages": [{"role": "user", "content": prompt}], "reasoning": {"enabled": True}}
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    res_data = resp.json()
    if "error" in res_data:
        raise ValueError(f"OpenRouter API error: {res_data['error']}")
    raw = res_data["choices"][0]["message"]["content"]
    data = json.loads(re.sub(r"```json|```", "", raw).strip())
    ans = {
        it["index"]: [v] if isinstance(v := it.get("selected") or it.get("text") or it.get("answer") or [], str) else list(v)
        for it in data.get("answers", [])
    }
    if ans:
        logger.info("Parsed %d answer(s): %s", len(ans), ans)
        return ans
    raise ValueError(f"Empty answers in payload: {raw}")


def solve_quiz_with_llm(questions: list[dict[str, Any]], cfg: Settings) -> dict[int, list[str]]:
    """Query OpenRouter LLM with tenacity retry backoff and parse JSON answers."""
    prompt = (
        "Answer questions: 'single'=1 option, 'multiselect'=all, 'textarea'=concise written text.\n"
        'Respond ONLY in JSON: {"answers": [{"index": 0, "selected": ["option or text"]}]}\n\n'
        f"Questions:\n{json.dumps(questions, indent=2)}"
    )
    logger.info("Querying OpenRouter (%s) with %d questions...", cfg.openrouter_model, len(questions))
    try:
        return _query_and_parse(cfg, prompt)
    except EXC as exc:
        logger.error("LLM solver failed after retries: %s", exc)
        return {}
