"""Вызов Anthropic для распознавания старта по скриншоту."""

from __future__ import annotations

import base64
import logging
import os

from app.ocr_json import parse_claude_ocr_response

log = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = frozenset(
    {"image/jpeg", "image/png", "image/gif", "image/webp"}
)

_OCR_SYSTEM = (
    "Ты извлекаешь данные о спортивном старте с изображения (афиша, сайт). "
    "Ответь ТОЛЬКО одним JSON-объектом без пояснений, с полями:\n"
    "event_name (string|null), date (YYYY-MM-DD|null), distance (string|null), "
    "sport_type (string|null), location (string|null), confidence (low|medium|high)."
)


def _image_media_type_declared(content_type: str | None) -> str:
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct in ALLOWED_IMAGE_TYPES:
        return ct
    return "image/jpeg"


def recognize_event_image(
    image_bytes: bytes,
    *,
    content_type: str | None,
) -> dict:
    """
    Вызывает Claude Vision. При сбое API бросает исключение (ловится в роутере).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("missing API key")

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    media = _image_media_type_declared(content_type)
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")

    msg = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system=_OCR_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media,
                            "data": b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Извлеки данные старта в JSON по схеме выше.",
                    },
                ],
            }
        ],
    )
    text_parts: list[str] = []
    for block in msg.content:
        if hasattr(block, "text"):
            text_parts.append(block.text)
    merged = "\n".join(text_parts)
    parsed = parse_claude_ocr_response(merged)
    if "error" in parsed and len(parsed) == 2 and "raw_preview" in parsed:
        log.debug("OCR parse issue: %s", parsed)
    return parsed
