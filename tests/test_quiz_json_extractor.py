"""Tests for robust JSON extraction from LLM outputs."""

import pytest

from coursera_automation.items.quiz.json_extractor import extract_llm_json


def test_extract_llm_json_clean_dict() -> None:
    res = extract_llm_json('{"answers": [{"index": 0}]}')
    assert res == {"answers": [{"index": 0}]}


def test_extract_llm_json_code_fence() -> None:
    res = extract_llm_json('```json\n{"answers": [{"index": 1}]}\n```')
    assert res == {"answers": [{"index": 1}]}


def test_extract_llm_json_code_fence_no_lang() -> None:
    res = extract_llm_json('```\n{"answers": [{"index": 2}]}\n```')
    assert res == {"answers": [{"index": 2}]}


def test_extract_llm_json_preamble_and_postamble() -> None:
    raw = 'Here is the answer:\n```json\n{"answers": [{"index": 3}]}\n```\nHope it helps!'
    assert extract_llm_json(raw) == {"answers": [{"index": 3}]}


def test_extract_llm_json_think_tags() -> None:
    raw = '<think>I should output JSON</think>\n{"answers": [{"index": 4}]}'
    assert extract_llm_json(raw) == {"answers": [{"index": 4}]}


def test_extract_llm_json_direct_array() -> None:
    raw = '[{"index": 5, "selected": ["X"]}]'
    assert extract_llm_json(raw) == [{"index": 5, "selected": ["X"]}]


def test_extract_llm_json_empty_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Empty response"):
        extract_llm_json("")
    with pytest.raises(ValueError, match="Empty response"):
        extract_llm_json("   ")
    with pytest.raises(ValueError, match="Empty response"):
        extract_llm_json(None)


import json


def test_extract_llm_json_invalid_raises_decode_error() -> None:
    with pytest.raises(json.JSONDecodeError):
        extract_llm_json("No json here")
