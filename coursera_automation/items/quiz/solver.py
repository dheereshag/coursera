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


def solve_quiz_with_llm(questions: list[dict[str, Any]], cfg: Settings) -> dict[int, list[str]]:
    """Solve quiz questions using Groq first with fallback to OpenRouter."""
    logger.info("Solving %d quiz question(s):\n%s", len(questions), json.dumps(questions, indent=2))
    prompt = (
        "Answer questions: 'single'=1 option, 'multiselect'=all, 'textarea'=concise written text.\n"
        "For multiple choice, 'selected' MUST contain the exact verbatim option text from 'options'.\n"
        'Respond ONLY in JSON: {"answers": [{"index": 0, "selected": ["exact option text or answer"]}]}\n\n'
        f"Questions:\n{json.dumps(questions, indent=2)}"
    )
    if cfg.groq_api_key:
        try:
            return query_groq(cfg, prompt)
        except EXC as exc:
            logger.warning("Groq solver failed: %s. Falling back to OpenRouter...", exc)
    return query_openrouter(cfg, prompt)
