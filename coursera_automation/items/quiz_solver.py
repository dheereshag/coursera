"""LLM-based quiz question solver using NVIDIA Nemotron via OpenAI SDK."""

import json
import logging
import re
from typing import Any

from openai import OpenAI, OpenAIError

from coursera_automation.config import Settings

logger = logging.getLogger(__name__)


def solve_quiz_with_llm(questions: list[dict[str, Any]], cfg: Settings) -> dict[int, list[str]]:
    """Query NVIDIA LLM with questions and parse selected answer options."""
    client = OpenAI(base_url=cfg.nvidia_base_url, api_key=cfg.nvidia_api_key)
    prompt = (
        "Answer these quiz questions. For 'single', choose 1 option. For 'multiselect', choose all.\n"
        'Respond ONLY in JSON: {"answers": [{"index": 0, "selected": ["option text"]}]}\n\n'
        f"Questions:\n{json.dumps(questions, indent=2)}"
    )
    logger.info("Querying LLM (%s) with %d questions...", cfg.nvidia_model, len(questions))
    try:
        completion = client.chat.completions.create(
            model=cfg.nvidia_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            top_p=0.95,
            max_tokens=16384,
            extra_body={"chat_template_kwargs": {"enable_thinking": True}},
            stream=True,
        )
        parts, reasoning = [], []
        for chunk in completion:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if r := getattr(delta, "reasoning_content", None):
                reasoning.append(r)
            if delta.content:
                parts.append(delta.content)
        if reasoning:
            logger.info("LLM reasoning: %s", "".join(reasoning))
        raw = "".join(parts)
    except OpenAIError as exc:
        logger.error("LLM API call failed: %s", exc)
        return {}

    logger.info("Raw LLM response:\n%s", raw)
    clean = re.sub(r"```json|```", "", raw).strip()
    try:
        data = json.loads(clean)
        ans = {it["index"]: it.get("selected", []) for it in data.get("answers", [])}
        logger.info("Parsed %d answer(s): %s", len(ans), ans)
        return ans
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as err:
        logger.warning("Failed parsing LLM answer: %s. Raw: %s", err, raw)
        return {}
