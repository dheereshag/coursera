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
    """Verify solver parses valid JSON response from OpenRouter without reasoning when effort is None."""
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp('{"answers": [{"index": 0, "selected": ["Option A"]}]}')
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["Option A"]}
        payload = mock_post.call_args[1]["json"]
        assert payload["model"] == "deepseek/deepseek-v4.1-flash"
        assert "reasoning" not in payload


def test_solve_quiz_with_reasoning_effort() -> None:
    """Verify solver sets reasoning effort in payload when specified."""
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp('{"answers": [{"index": 0, "selected": ["Option A"]}]}')
        solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings(), effort="medium")
        assert mock_post.call_args[1]["json"]["reasoning"] == {"effort": "medium"}

        solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings(), effort="high")
        assert mock_post.call_args[1]["json"]["reasoning"] == {"effort": "high"}


def test_solve_quiz_with_explicit_model() -> None:
    """Verify solver uses explicitly passed model name."""
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp('{"answers": [{"index": 0, "selected": ["Fallback A"]}]}')
        res = solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings(), model="z-ai/glm-5.3-flash")
        assert res == {0: ["Fallback A"]}
        assert mock_post.call_args[1]["json"]["model"] == "z-ai/glm-5.3-flash"


def test_solve_quiz_retry_on_request_error() -> None:
    """Verify solver retries on RequestException and succeeds on subsequent attempt."""
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = [
            requests.RequestException("503 Service Temporarily Unavailable"),
            _mock_resp('{"answers": [{"index": 0, "selected": ["Opt B"]}]}'),
        ]
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["Opt B"]}


def test_solve_quiz_exhausted_retries_returns_empty() -> None:
    """Verify solver returns empty dict when all retries fail."""
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = requests.RequestException("Service overloaded")
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {}


def test_solve_quiz_text_answer() -> None:
    """Verify solver parses string text answer for textarea questions."""
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp('{"answers": [{"index": 0, "text": "Written response"}]}')
        assert solve_quiz_with_llm([{"index": 0, "type": "textarea"}], Settings()) == {0: ["Written response"]}


def test_solve_quiz_retry_on_api_error_payload() -> None:
    """Verify solver retries when OpenRouter returns an error dict payload."""
    resp_err = MagicMock(json=lambda: {"error": {"message": "Rate limited"}})
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = [resp_err, _mock_resp('{"answers": [{"index": 0, "selected": ["OK"]}]}')]
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["OK"]}


def test_solve_quiz_with_markdown_preamble() -> None:
    """Verify solver parses JSON wrapped in markdown fences with preamble text."""
    raw = 'Sure! Here are your answers:\n```json\n{"answers": [{"index": 0, "selected": ["Correct"]}]}\n```\nGood luck!'
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp(raw)
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["Correct"]}


def test_solve_quiz_with_think_tags() -> None:
    """Verify solver strips <think> reasoning blocks before parsing JSON."""
    raw = '<think>Analyzing question 1...\nOption A is correct.</think>\n{"answers": [{"index": 0, "selected": ["Option A"]}]}'
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp(raw)
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["Option A"]}


def test_solve_quiz_with_direct_array() -> None:
    """Verify solver parses direct JSON array responses."""
    raw = '[{"index": 0, "selected": ["Array Opt"]}]'
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp(raw)
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["Array Opt"]}


def test_solve_quiz_fallback_to_reasoning() -> None:
    """Verify solver falls back to reasoning attribute when content is empty."""
    resp = MagicMock()
    resp.json.return_value = {
        "choices": [{"message": {"content": "", "reasoning": '{"answers": [{"index": 0, "selected": ["From Reasoning"]}]}'}}]
    }
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = resp
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["From Reasoning"]}


def test_solve_quiz_retry_on_empty_choices() -> None:
    """Verify solver retries when choices is empty (IndexError) and recovers."""
    resp_empty = MagicMock(json=lambda: {"choices": []})
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = [resp_empty, _mock_resp('{"answers": [{"index": 0, "selected": ["Recovered"]}]}')]
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings()) == {0: ["Recovered"]}


def test_solve_quiz_fallback_to_fallback_model_on_error() -> None:
    """Verify solver falls back to openrouter_fallback_model when primary model fails, preserving effort."""
    resp_429 = MagicMock()
    resp_429.raise_for_status.side_effect = requests.HTTPError("429 Client Error: Too Many Requests")

    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = [
            resp_429,
            resp_429,
            _mock_resp('{"answers": [{"index": 0, "selected": ["Fallback Ans"]}]}'),
        ]
        res = solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings(openrouter_api_key="key"), effort="high")
        assert res == {0: ["Fallback Ans"]}
        models_called = [c[1]["json"]["model"] for c in mock_post.call_args_list]
        assert "deepseek/deepseek-v4.1-flash" in models_called
        assert "z-ai/glm-5.3-flash" in models_called
        assert mock_post.call_args_list[-1][1]["json"]["reasoning"] == {"effort": "high"}


def test_solve_quiz_with_mixed_text_and_image_questions() -> None:
    """Verify mixed quiz separates batch text solving and multimodal image questions, then merges."""
    cfg = Settings(openrouter_api_key="key")
    questions = [
        {"index": 0, "question": "Text Q1", "options": ["A", "B"]},
        {"index": 1, "question": "Image Q2", "options": ["C", "D"], "images": ["https://example.com/q2.png"]},
    ]
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.side_effect = [
            _mock_resp('{"answers": [{"index": 0, "selected": ["A"]}]}'),
            _mock_resp('{"answers": [{"index": 1, "selected": ["C"]}]}'),
        ]
        answers = solve_quiz_with_llm(questions, cfg)
        assert answers == {0: ["A"], 1: ["C"]}
        assert mock_post.call_count == 2
        first_payload = mock_post.call_args_list[0][1]["json"]["messages"][0]["content"]
        second_payload = mock_post.call_args_list[1][1]["json"]["messages"][0]["content"]
        assert isinstance(first_payload, str)
        assert isinstance(second_payload, list)
        assert second_payload[1] == {"type": "image_url", "image_url": {"url": "https://example.com/q2.png"}}


def test_solve_quiz_multimodal_limits_to_3_images() -> None:
    """Verify multimodal questions cap images to 3 per request."""
    cfg = Settings(openrouter_api_key="key")
    q = {
        "index": 0,
        "question": "Diagrams",
        "images": ["http://ex.com/1.png", "http://ex.com/2.png", "http://ex.com/3.png", "http://ex.com/4.png"],
    }
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp('{"answers": [{"index": 0, "selected": ["Ans"]}]}')
        res = solve_quiz_with_llm([q], cfg)
        assert res == {0: ["Ans"]}
        content = mock_post.call_args[1]["json"]["messages"][0]["content"]
        assert isinstance(content, list)
        img_blocks = [c for c in content if c["type"] == "image_url"]
        assert len(img_blocks) == 3
