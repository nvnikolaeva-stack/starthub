"""Разбор JSON из ответа Claude (OCR)."""

from __future__ import annotations

import json
import re
from typing import Any

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.I)


def parse_claude_ocr_response(response_text: str) -> dict[str, Any]:
    """
    Достаёт JSON из текста модели. При ошибке возвращает dict с ключом error (без исключений).
    """
    raw = (response_text or "").strip()
    if not raw:
        return {"error": "empty response"}

    m = _JSON_FENCE.search(raw)
    if m:
        raw = m.group(1).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "invalid_json", "raw_preview": raw[:200]}

    if not isinstance(data, dict):
        return {"error": "not_a_object"}

    out: dict[str, Any] = {}
    for key in (
        "event_name",
        "date",
        "distance",
        "sport_type",
        "location",
        "confidence",
    ):
        if key in data:
            out[key] = data[key]
    return out
