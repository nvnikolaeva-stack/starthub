"""Схема ответа OCR API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class OCRRecognizeResponse(BaseModel):
    event_name: str | None = None
    date: str | None = None
    distance: str | None = None
    sport_type: str | None = None
    location: str | None = None
    confidence: str | None = None
    error: str | None = None

    @classmethod
    def from_parsed(cls, data: dict[str, Any]) -> "OCRRecognizeResponse":
        return cls(
            event_name=data.get("event_name"),
            date=data.get("date"),
            distance=data.get("distance"),
            sport_type=data.get("sport_type"),
            location=data.get("location"),
            confidence=data.get("confidence"),
            error=data.get("error"),
        )
