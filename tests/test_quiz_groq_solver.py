"""Tests for Groq LLM solver."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from coursera_automation.config import Settings
from coursera_automation.items.quiz.groq_solver import query_groq


def _mock_groq_resp(content_text: str) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {
        "choices": [{"message": {"content": content_text}}],
    }
    return resp


def test_query_groq_success() -> None:
    """Verify query_groq formats request correctly and parses JSON answers."""
    cfg = Settings(groq_api_key="test-groq-key", groq_model="openai/gpt-oss-120b")
    with patch("coursera_automation.items.quiz.groq_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_groq_resp('{"answers": [{"index": 0, "selected": ["Option 1"]}]}')
        answers = query_groq(cfg, "Prompt")
        assert answers == {0: ["Option 1"]}

        call_args = mock_post.call_args
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-groq-key"
        assert call_args[1]["json"]["model"] == "openai/gpt-oss-120b"
        assert call_args[1]["json"]["reasoning_effort"] == "low"
        assert call_args[1]["json"]["max_completion_tokens"] == 4096


def test_query_groq_retry_on_error() -> None:
    """Verify query_groq retries on RequestException and succeeds."""
    cfg = Settings(groq_api_key="test-groq-key")
    with patch("coursera_automation.items.quiz.groq_solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = [
            requests.RequestException("Rate limited"),
            _mock_groq_resp('{"answers": [{"index": 0, "selected": ["Recovered"]}]}'),
        ]
        answers = query_groq(cfg, "Prompt")
        assert answers == {0: ["Recovered"]}


def test_query_groq_empty_answers_raises() -> None:
    """Verify query_groq raises ValueError on empty answers payload."""
    cfg = Settings(groq_api_key="test-groq-key")
    with patch("coursera_automation.items.quiz.groq_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_groq_resp('{"answers": []}')
        with pytest.raises(ValueError, match="Empty answers"):
            query_groq(cfg, "Prompt")


def test_query_groq_400_raises_runtime_error_without_retry() -> None:
    """Verify query_groq immediately raises RuntimeError on 400 Bad Request without retrying."""
    cfg = Settings(groq_api_key="test-groq-key")
    resp_400 = MagicMock(status_code=400, text='{"error":"json_validate_failed"}')
    with patch("coursera_automation.items.quiz.groq_solver.requests.post", return_value=resp_400) as mock_post:
        with pytest.raises(RuntimeError, match="Groq 400 Bad Request"):
            query_groq(cfg, "Prompt")
        assert mock_post.call_count == 1

