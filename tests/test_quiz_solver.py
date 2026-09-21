"""Tests for quiz solver parsing and JSON extraction."""

from unittest.mock import MagicMock, patch

from coursera_automation.config import Settings
from coursera_automation.items.quiz_solver import solve_quiz_with_llm


def test_solve_quiz_with_llm_json() -> None:
    """Verify solver parses valid JSON response from LLM."""
    chunk = MagicMock()
    chunk.choices = [MagicMock(delta=MagicMock(content='```json\n{"answers": [{"index": 0, "selected": ["Option A"]}]}\n```', reasoning_content="thinking"))]

    with patch("coursera_automation.items.quiz_solver.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = [chunk]
        mock_openai.return_value = mock_client

        cfg = Settings()
        questions = [{"index": 0, "text": "Q1?", "options": ["Option A", "Option B"]}]
        answers = solve_quiz_with_llm(questions, cfg)

        assert answers == {0: ["Option A"]}


def test_solve_quiz_multiselect() -> None:
    """Verify solver parses multiselect answers."""
    chunk = MagicMock()
    chunk.choices = [MagicMock(delta=MagicMock(content='{"answers": [{"index": 0, "selected": ["Opt A", "Opt B"]}]}', reasoning_content=None))]
    with patch("coursera_automation.items.quiz_solver.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = [chunk]
        mock_openai.return_value = mock_client
        cfg = Settings()
        questions = [{"index": 0, "text": "Q1?", "options": ["Opt A", "Opt B"], "type": "multiselect"}]
        assert solve_quiz_with_llm(questions, cfg) == {0: ["Opt A", "Opt B"]}
