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
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp('{"answers": [{"index": 0, "selected": ["Option A"]}]}')
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings(groq_api_key="")) == {0: ["Option A"]}
        payload = mock_post.call_args[1]["json"]
        assert payload["model"] == "dots-studio/dots-3-note-preview:free" and payload["reasoning"] == {"enabled": True}


def test_solve_quiz_retry_on_request_error() -> None:
    """Verify solver retries on RequestException and succeeds on subsequent attempt."""
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = [
            requests.RequestException("503 Service Temporarily Unavailable"),
            _mock_resp('{"answers": [{"index": 0, "selected": ["Opt B"]}]}'),
        ]
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings(groq_api_key="")) == {0: ["Opt B"]}


def test_solve_quiz_exhausted_retries_returns_empty() -> None:
    """Verify solver returns empty dict when all retries fail."""
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = requests.RequestException("Service overloaded")
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings(groq_api_key="")) == {}


def test_solve_quiz_text_answer() -> None:
    """Verify solver parses string text answer for textarea questions."""
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp('{"answers": [{"index": 0, "text": "Written response"}]}')
        assert solve_quiz_with_llm([{"index": 0, "type": "textarea"}], Settings(groq_api_key="")) == {0: ["Written response"]}


def test_solve_quiz_retry_on_api_error_payload() -> None:
    """Verify solver retries when OpenRouter returns an error dict payload."""
    resp_err = MagicMock(json=lambda: {"error": {"message": "Rate limited"}})
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = [resp_err, _mock_resp('{"answers": [{"index": 0, "selected": ["OK"]}]}')]
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings(groq_api_key="")) == {0: ["OK"]}


def test_solve_quiz_with_markdown_preamble() -> None:
    """Verify solver parses JSON wrapped in markdown fences with preamble text."""
    raw = 'Sure! Here are your answers:\n```json\n{"answers": [{"index": 0, "selected": ["Correct"]}]}\n```\nGood luck!'
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp(raw)
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings(groq_api_key="")) == {0: ["Correct"]}


def test_solve_quiz_with_think_tags() -> None:
    """Verify solver strips <think> reasoning blocks before parsing JSON."""
    raw = '<think>Analyzing question 1...\nOption A is correct.</think>\n{"answers": [{"index": 0, "selected": ["Option A"]}]}'
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp(raw)
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings(groq_api_key="")) == {0: ["Option A"]}


def test_solve_quiz_with_direct_array() -> None:
    """Verify solver parses direct JSON array responses."""
    raw = '[{"index": 0, "selected": ["Array Opt"]}]'
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp(raw)
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings(groq_api_key="")) == {0: ["Array Opt"]}


def test_solve_quiz_fallback_to_reasoning() -> None:
    """Verify solver falls back to reasoning attribute when content is empty."""
    resp = MagicMock()
    resp.json.return_value = {
        "choices": [{"message": {"content": "", "reasoning": '{"answers": [{"index": 0, "selected": ["From Reasoning"]}]}'}}]
    }
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = resp
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings(groq_api_key="")) == {0: ["From Reasoning"]}


def test_solve_quiz_retry_on_empty_choices() -> None:
    """Verify solver retries when choices is empty (IndexError) and recovers."""
    resp_empty = MagicMock(json=lambda: {"choices": []})
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = [resp_empty, _mock_resp('{"answers": [{"index": 0, "selected": ["Recovered"]}]}')]
        assert solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings(groq_api_key="")) == {0: ["Recovered"]}


def test_solve_quiz_fallback_to_second_model_on_429() -> None:
    """Verify solver falls back to nex-agi model when primary hits 429."""
    resp_429 = MagicMock()
    resp_429.raise_for_status.side_effect = requests.HTTPError("429 Client Error: Too Many Requests")

    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = [
            resp_429,
            resp_429,
            _mock_resp('{"answers": [{"index": 0, "selected": ["Fallback 1 Ans"]}]}'),
        ]
        res = solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings(groq_api_key="", openrouter_api_key="single-key"))
        assert res == {0: ["Fallback 1 Ans"]}
        models_called = [call[1]["json"]["model"] for call in mock_post.call_args_list]
        assert "dots-studio/dots-3-note-preview:free" in models_called
        assert "nex-agi/nex-n2.5-mini:free" in models_called


def test_solve_quiz_fallback_to_third_model_on_429() -> None:
    """Verify solver falls back to openrouter/free when primary and secondary both hit 429."""
    resp_429 = MagicMock()
    resp_429.raise_for_status.side_effect = requests.HTTPError("429 Client Error: Too Many Requests")

    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = [
            resp_429,
            resp_429,
            resp_429,
            resp_429,
            _mock_resp('{"answers": [{"index": 0, "selected": ["Third Ans"]}]}'),
        ]
        res = solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], Settings(groq_api_key="", openrouter_api_key="single-key"))
        assert res == {0: ["Third Ans"]}
        models_called = [call[1]["json"]["model"] for call in mock_post.call_args_list]
        assert "dots-studio/dots-3-note-preview:free" in models_called
        assert "nex-agi/nex-n2.5-mini:free" in models_called
        assert "openrouter/free" in models_called


def test_solve_quiz_uses_groq_primary() -> None:
    """Verify solver uses Groq when groq_api_key is present and succeeds."""
    cfg = Settings(groq_api_key="groq-key")
    with (
        patch("coursera_automation.items.quiz.solver.query_groq", return_value={0: ["Groq Ans"]}) as mock_groq,
        patch("coursera_automation.items.quiz.solver.query_openrouter") as mock_or,
    ):
        res = solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], cfg)
        assert res == {0: ["Groq Ans"]}
        mock_groq.assert_called_once()
        mock_or.assert_not_called()


def test_solve_quiz_groq_fails_falls_back_to_openrouter() -> None:
    """Verify solver falls back to OpenRouter when Groq query fails."""
    cfg = Settings(groq_api_key="groq-key")
    with (
        patch("coursera_automation.items.quiz.solver.query_groq", side_effect=RuntimeError("Groq down")),
        patch("coursera_automation.items.quiz.solver.query_openrouter", return_value={0: ["OR Ans"]}) as mock_or,
    ):
        res = solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], cfg)
        assert res == {0: ["OR Ans"]}
        mock_or.assert_called_once()


def test_solve_quiz_openrouter_key_rotation_on_429() -> None:
    """Verify that when key 1 hits 429, openrouter rotates to key 2 on the same model."""
    resp_429 = MagicMock()
    resp_429.raise_for_status.side_effect = requests.HTTPError("429 Client Error: Too Many Requests")

    cfg = Settings(groq_api_key="", openrouter_api_key="key-alpha,key-beta")
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post, patch("tenacity.nap.time.sleep"):
        mock_post.side_effect = [
            resp_429,
            resp_429,
            _mock_resp('{"answers": [{"index": 0, "selected": ["Key Beta Ans"]}]}'),
        ]
        res = solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], cfg)
        assert res == {0: ["Key Beta Ans"]}
        auth_headers = [call[1]["headers"]["Authorization"] for call in mock_post.call_args_list]
        assert "Bearer key-alpha" in auth_headers
        assert "Bearer key-beta" in auth_headers


def test_solve_quiz_openrouter_key_round_robin() -> None:
    """Verify consecutive OpenRouter queries cycle keys round-robin."""
    cfg = Settings(groq_api_key="", openrouter_api_key="key-1,key-2,key-3")
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp('{"answers": [{"index": 0, "selected": ["Ans"]}]}')
        solve_quiz_with_llm([{"index": 0, "text": "Q1?"}], cfg)
        solve_quiz_with_llm([{"index": 0, "text": "Q2?"}], cfg)
        auth_headers = [call[1]["headers"]["Authorization"] for call in mock_post.call_args_list]
        assert len(auth_headers) == 2
        assert auth_headers[0] != auth_headers[1]


def test_solve_quiz_with_mixed_text_and_image_questions() -> None:
    """Verify mixed quiz separates batch text solving and multimodal image questions, then merges."""
    cfg = Settings(groq_api_key="groq-key")
    questions = [
        {"index": 0, "question": "Text Q1", "options": ["A", "B"]},
        {"index": 1, "question": "Image Q2", "options": ["C", "D"], "images": ["https://example.com/q2.png"]},
    ]
    with patch("coursera_automation.items.quiz.solver.query_groq") as mock_groq:
        mock_groq.side_effect = [
            {0: ["A"]},
            {1: ["C"]},
        ]
        answers = solve_quiz_with_llm(questions, cfg)
        assert answers == {0: ["A"], 1: ["C"]}
        assert mock_groq.call_count == 2
        first_call_prompt = mock_groq.call_args_list[0][0][1]
        second_call_prompt = mock_groq.call_args_list[1][0][1]
        assert isinstance(first_call_prompt, str)
        assert isinstance(second_call_prompt, list)
        assert second_call_prompt[1] == {"type": "image_url", "image_url": {"url": "https://example.com/q2.png"}}


def test_solve_quiz_multimodal_limits_to_3_images() -> None:
    """Verify multimodal questions cap images to 3 per request."""
    cfg = Settings(groq_api_key="groq-key")
    q = {
        "index": 0,
        "question": "Diagrams",
        "images": ["http://ex.com/1.png", "http://ex.com/2.png", "http://ex.com/3.png", "http://ex.com/4.png"],
    }
    with patch("coursera_automation.items.quiz.solver.query_groq", return_value={0: ["Ans"]}) as mock_groq:
        res = solve_quiz_with_llm([q], cfg)
        assert res == {0: ["Ans"]}
        content = mock_groq.call_args[0][1]
        assert isinstance(content, list)
        img_blocks = [c for c in content if c["type"] == "image_url"]
        assert len(img_blocks) == 3


def test_solve_quiz_multimodal_openrouter_uses_vision_model() -> None:
    """Verify multimodal query routes to openrouter_vision_model when Groq is not configured."""
    cfg = Settings(groq_api_key="", openrouter_api_key="or-key", openrouter_vision_model="nex-agi/nex-n2.5-mini:free")
    q = {"index": 0, "question": "Diagram", "images": ["http://ex.com/1.png"]}
    with patch("coursera_automation.items.quiz.openrouter_solver.requests.post") as mock_post:
        mock_post.return_value = _mock_resp('{"answers": [{"index": 0, "selected": ["Vision Res"]}]}')
        res = solve_quiz_with_llm([q], cfg)
        assert res == {0: ["Vision Res"]}
        assert mock_post.call_args[1]["json"]["model"] == "nex-agi/nex-n2.5-mini:free"





