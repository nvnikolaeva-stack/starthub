"""Тесты OCR. С реальным ANTHROPIC_API_KEY тест по изображению не пропускается."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

ANTHROPIC_KEY_SET = os.getenv("ANTHROPIC_API_KEY") is not None


def _minimal_png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
        b"\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def test_ocr_recognize_without_file(client: TestClient) -> None:
    r = client.post("/api/v1/ocr/recognize")
    assert r.status_code == 422
    assert r.status_code != 500


def test_ocr_recognize_invalid_txt(client: TestClient) -> None:
    r = client.post(
        "/api/v1/ocr/recognize",
        files={"file": ("x.txt", b"not an image", "text/plain")},
    )
    assert r.status_code == 400
    assert "изображения" in (r.json().get("detail") or "").lower()


def test_ocr_recognize_empty_file(client: TestClient) -> None:
    r = client.post(
        "/api/v1/ocr/recognize",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert r.status_code == 400
    assert r.status_code != 500


def test_ocr_recognize_bad_api_key(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-invalid-not-real")
    r = client.post(
        "/api/v1/ocr/recognize",
        files={"file": ("t.png", _minimal_png(), "image/png")},
    )
    assert r.status_code == 503
    detail = r.json().get("detail", "")
    assert "OCR сервис недоступен" in str(detail)
    assert "traceback" not in r.text.lower()


@pytest.mark.skipif(
    not ANTHROPIC_KEY_SET,
    reason="ANTHROPIC_API_KEY not set",
)
def test_ocr_recognize_real_image(client: TestClient) -> None:
    pillow = pytest.importorskip("PIL", reason="Pillow not installed")
    from io import BytesIO

    img = pillow.Image.new("RGB", (200, 80), color=(255, 255, 255))
    buf = BytesIO()
    img.save(buf, format="PNG")
    png = buf.getvalue()

    r = client.post(
        "/api/v1/ocr/recognize",
        files={"file": ("shot.png", png, "image/png")},
    )
    assert r.status_code == 200
    data = r.json()
    for key in (
        "event_name",
        "date",
        "distance",
        "sport_type",
        "location",
        "confidence",
    ):
        assert key in data
