"""Tests for quiz solver parsing, JSON extraction, and tenacity retries."""

from unittest.mock import MagicMock, patch

import requests

from coursera_automation.config import Settings
from coursera_automation.items.quiz.solver import solve_quiz_with_llm


def _mock_resp(content: str) -> MagicMock:
    """Create mock requests response with json payload."""
    resp = MagicMock()
    resp.json.return_value = {"choices": [{"message": {"content": content}}]}
    return resp


def test_solve_quiz_with_llm_json() -> None:
    """Verify solver parses valid JSON response from OpenRouter."""
    with patch("coursera_automation.items.quiz.solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp('{"answers": [{"index": 0, "selected": ["Option A"]}]}')
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["Option A"]}
        payload = mock_post.call_args[1]["json"]
        assert payload["model"] == "inclusionai/ling-3.0-flash-fin:free" and payload["reasoning"] == {"enabled": True}


def test_solve_quiz_retry_on_request_error() -> None:
    """Verify solver retries on RequestException and succeeds on subsequent attempt."""
    with patch("coursera_automation.items.quiz.solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = [
            requests.RequestException("503 Service Temporarily Unavailable"),
            _mock_resp('{"answers": [{"index": 0, "selected": ["Opt B"]}]}'),
        ]
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["Opt B"]}


def test_solve_quiz_exhausted_retries_returns_empty() -> None:
    """Verify solver returns empty dict when all retries fail."""
    with patch("coursera_automation.items.quiz.solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = requests.RequestException("Service overloaded")
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {}


def test_solve_quiz_text_answer() -> None:
    """Verify solver parses string text answer for textarea questions."""
    with patch("coursera_automation.items.quiz.solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp('{"answers": [{"index": 0, "text": "Written response"}]}')
        assert solve_quiz_with_llm([{"index": 0, "type": "textarea"}], Settings()) == {0: ["Written response"]}


def test_solve_quiz_retry_on_api_error_payload() -> None:
    """Verify solver retries when OpenRouter returns an error dict payload."""
    resp_err = MagicMock(json=lambda: {"error": {"message": "Rate limited"}})
    with patch("coursera_automation.items.quiz.solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = [resp_err, _mock_resp('{"answers": [{"index": 0, "selected": ["OK"]}]}')]
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["OK"]}


def test_solve_quiz_with_markdown_preamble() -> None:
    """Verify solver parses JSON wrapped in markdown fences with preamble text."""
    raw = 'Sure! Here are your answers:\n```json\n{"answers": [{"index": 0, "selected": ["Correct"]}]}\n```\nGood luck!'
    with patch("coursera_automation.items.quiz.solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp(raw)
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["Correct"]}


def test_solve_quiz_with_think_tags() -> None:
    """Verify solver strips <think> reasoning blocks before parsing JSON."""
    raw = '<think>Analyzing question 1...\nOption A is correct.</think>\n{"answers": [{"index": 0, "selected": ["Option A"]}]}'
    with patch("coursera_automation.items.quiz.solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp(raw)
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["Option A"]}


def test_solve_quiz_with_direct_array() -> None:
    """Verify solver parses direct JSON array responses."""
    raw = '[{"index": 0, "selected": ["Array Opt"]}]'
    with patch("coursera_automation.items.quiz.solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp(raw)
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["Array Opt"]}


def test_solve_quiz_fallback_to_reasoning() -> None:
    """Verify solver falls back to reasoning attribute when content is empty."""
    resp = MagicMock()
    resp.json.return_value = {
        "choices": [{"message": {"content": "", "reasoning": '{"answers": [{"index": 0, "selected": ["From Reasoning"]}]}'}}]
    }
    with patch("coursera_automation.items.quiz.solver.requests.post") as mock_post:
        mock_post.return_value = resp
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["From Reasoning"]}


def test_solve_quiz_retry_on_empty_choices() -> None:
    """Verify solver retries when choices is empty (IndexError) and recovers."""
    resp_empty = MagicMock(json=lambda: {"choices": []})
    with patch("coursera_automation.items.quiz.solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = [resp_empty, _mock_resp('{"answers": [{"index": 0, "selected": ["Recovered"]}]}')]
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["Recovered"]}
