"""Юнит-тесты парсера OCR (без вызова API)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ocr_service import parse_claude_ocr_response  # noqa: E402


def test_parse_valid_json() -> None:
    response_text = json.dumps(
        {
            "event_name": "Ironstar Sochi",
            "date": "2026-06-15",
            "distance": "Olympic",
            "sport_type": "triathlon",
            "location": "Сочи",
            "confidence": "high",
        }
    )
    out = parse_claude_ocr_response(response_text)
    assert out.get("error") is None
    assert out["event_name"] == "Ironstar Sochi"
    assert out["date"] == "2026-06-15"
    assert out["sport_type"] == "triathlon"
    assert out["confidence"] == "high"


def test_parse_markdown_wrapped_json() -> None:
    response_text = '```json\n{"event_name": "Test", "date": null}\n```'
    out = parse_claude_ocr_response(response_text)
    assert out.get("error") is None
    assert out["event_name"] == "Test"
    assert out["date"] is None


def test_parse_invalid_response() -> None:
    response_text = "I couldn't recognize the image"
    out = parse_claude_ocr_response(response_text)
    assert "error" in out
    assert isinstance(out["error"], str)


def test_parse_all_null() -> None:
    response_text = json.dumps(
        {
            "event_name": None,
            "date": None,
            "distance": None,
            "sport_type": None,
            "location": None,
            "confidence": "low",
        }
    )
    out = parse_claude_ocr_response(response_text)
    assert out.get("error") is None
    assert out["confidence"] == "low"
    assert out["event_name"] is None
