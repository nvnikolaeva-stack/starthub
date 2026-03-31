from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_participant(client: TestClient) -> None:
    r = client.post("/api/v1/participants", json={"display_name": "Alice Runner"})
    assert r.status_code == 201
    data = r.json()
    assert data["display_name"] == "Alice Runner"
    assert data["normalized_name"] == "alice runner"


def test_create_participant_with_telegram(client: TestClient) -> None:
    r = client.post(
        "/api/v1/participants",
        json={"display_name": "Bob", "telegram_id": 10001},
    )
    assert r.status_code == 201
    assert r.json()["telegram_id"] == 10001


def test_create_participant_duplicate_telegram_returns_same(client: TestClient) -> None:
    r1 = client.post(
        "/api/v1/participants",
        json={"display_name": "First", "telegram_id": 20002},
    )
    assert r1.status_code == 201
    id1 = r1.json()["id"]
    r2 = client.post(
        "/api/v1/participants",
        json={"display_name": "Second Name", "telegram_id": 20002},
    )
    assert r2.status_code in (200, 201)
    assert r2.json()["id"] == id1


def test_create_participant_empty_display_name(client: TestClient) -> None:
    r = client.post("/api/v1/participants", json={"display_name": ""})
    assert r.status_code == 422


def test_create_participant_whitespace_display_name(client: TestClient) -> None:
    r = client.post("/api/v1/participants", json={"display_name": "   "})
    assert r.status_code == 422
