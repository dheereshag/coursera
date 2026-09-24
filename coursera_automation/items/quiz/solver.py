"""LLM quiz solver orchestrator: queries Groq first, falling back to OpenRouter."""

import json
import logging
from typing import Any

import requests

from coursera_automation.config import Settings

from .groq_solver import query_groq
from .openrouter_solver import query_openrouter

logger = logging.getLogger(__name__)
EXC = (requests.RequestException, json.JSONDecodeError, KeyError, TypeError, ValueError, IndexError, RuntimeError)
HEADER = (
    "Answer questions: 'single'=1 option, 'multiselect'=all, 'textarea'=concise written text.\n"
    "For multiple choice, 'selected' MUST contain the exact verbatim option text from 'options'.\n"
    'Respond ONLY in JSON: {"answers": [{"index": 0, "selected": ["exact option text or answer"]}]}\n\n'
)


def _dispatch(cfg: Settings, prompt: str | list[dict[str, Any]]) -> dict[int, list[str]]:
    if cfg.groq_api_key:
        try:
            return query_groq(cfg, prompt)
        except EXC as exc:
            logger.warning("Groq solver failed: %s. Falling back to OpenRouter...", exc)
    return query_openrouter(cfg, prompt)


def _solve_multimodal(q: dict[str, Any], cfg: Settings) -> dict[int, list[str]]:
    q_data = {k: v for k, v in q.items() if k != "images"}
    txt = f"{HEADER}Questions:\n{json.dumps([q_data], indent=2)}"
    content: list[dict[str, Any]] = [{"type": "text", "text": txt}]
    for u in q.get("images", [])[:3]:
        content.append({"type": "image_url", "image_url": {"url": u}})
    return _dispatch(cfg, content)


def solve_quiz_with_llm(questions: list[dict[str, Any]], cfg: Settings) -> dict[int, list[str]]:
    """Solve quiz questions using Groq first with fallback to OpenRouter."""
    logger.info("Solving %d quiz question(s):\n%s", len(questions), json.dumps(questions, indent=2))
    answers: dict[int, list[str]] = {}
    if text_qs := [q for q in questions if not q.get("images")]:
        prompt = f"{HEADER}Questions:\n{json.dumps(text_qs, indent=2)}"
        answers.update(_dispatch(cfg, prompt))
    for q in [q for q in questions if q.get("images")]:
        answers.update(_solve_multimodal(q, cfg))
    return answers
