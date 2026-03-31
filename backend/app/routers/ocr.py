"""OCR: распознавание данных старта с изображения."""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.ocr_claude import ALLOWED_IMAGE_TYPES, recognize_event_image
from app.schemas_ocr import OCRRecognizeResponse

router = APIRouter(prefix="/ocr", tags=["ocr"])
log = logging.getLogger(__name__)


def _looks_like_image(b: bytes) -> bool:
    if len(b) < 12:
        return False
    if b.startswith(b"\xff\xd8\xff"):
        return True
    if b.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if b.startswith((b"GIF87a", b"GIF89a")):
        return True
    if b.startswith(b"RIFF") and b[8:12] == b"WEBP":
        return True
    return False


@router.post("/recognize", response_model=OCRRecognizeResponse)
async def ocr_recognize(file: UploadFile = File(...)) -> OCRRecognizeResponse:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Пустой файл")

    ct = (file.content_type or "").split(";")[0].strip().lower()
    if ct and ct not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Поддерживаются только изображения",
        )
    if not ct and not _looks_like_image(raw):
        raise HTTPException(
            status_code=400,
            detail="Поддерживаются только изображения",
        )

    try:
        parsed = recognize_event_image(raw, content_type=file.content_type)
    except Exception as e:
        log.warning("OCR failed: %s", e, exc_info=False)
        raise HTTPException(
            status_code=503,
            detail="OCR сервис недоступен",
        ) from None

    return OCRRecognizeResponse.from_parsed(parsed)
