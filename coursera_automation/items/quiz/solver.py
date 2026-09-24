"""LLM quiz solver orchestrator: dispatches prompt to OpenRouter."""

import json
import logging
from typing import Any

from coursera_automation.config import Settings

from .openrouter_solver import query_openrouter

logger = logging.getLogger(__name__)
HEADER = (
    "Answer questions: 'single'=1 option, 'multiselect'=all, 'textarea'=concise written text.\n"
    "For multiple choice, 'selected' MUST contain the exact verbatim option text from 'options'.\n"
    'Respond ONLY in JSON: {"answers": [{"index": 0, "selected": ["exact option text or answer"]}]}\n\n'
)


def _solve_multimodal(q: dict[str, Any], cfg: Settings, model: str | None = None) -> dict[int, list[str]]:
    q_data = {k: v for k, v in q.items() if k != "images"}
    txt = f"{HEADER}Questions:\n{json.dumps([q_data], indent=2)}"
    content: list[dict[str, Any]] = [{"type": "text", "text": txt}]
    for u in q.get("images", [])[:3]:
        content.append({"type": "image_url", "image_url": {"url": u}})
    return query_openrouter(cfg, content, model=model)


def solve_quiz_with_llm(
    questions: list[dict[str, Any]], cfg: Settings, model: str | None = None
) -> dict[int, list[str]]:
    """Solve quiz questions using OpenRouter with specified model or default."""
    logger.info(
        "Solving %d quiz question(s) (model=%s):\n%s",
        len(questions),
        model or cfg.openrouter_model,
        json.dumps(questions, indent=2),
    )
    answers: dict[int, list[str]] = {}
    if text_qs := [q for q in questions if not q.get("images")]:
        prompt = f"{HEADER}Questions:\n{json.dumps(text_qs, indent=2)}"
        answers.update(query_openrouter(cfg, prompt, model=model))
    for q in [q for q in questions if q.get("images")]:
        answers.update(_solve_multimodal(q, cfg, model=model))
    return answers
