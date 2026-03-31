from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models


def _event(client: TestClient) -> dict:
    return client.post(
        "/api/v1/events",
        json={
            "name": "Reg Test Event",
            "date_start": "2026-10-01",
            "location": "X",
            "sport_type": "triathlon",
            "created_by": "pytest",
        },
    ).json()


def _participant(client: TestClient) -> dict:
    return client.post(
        "/api/v1/participants",
        json={"display_name": "P1"},
    ).json()


def test_create_registration(client: TestClient) -> None:
    ev = _event(client)
    p = _participant(client)
    r = client.post(
        "/api/v1/registrations",
        json={
            "event_id": ev["id"],
            "participant_id": p["id"],
            "distances": ["Olympic"],
        },
    )
    assert r.status_code == 201
    assert r.json()["distances"] == ["Olympic"]


def test_duplicate_registration(client: TestClient) -> None:
    ev = _event(client)
    p = _participant(client)
    body = {
        "event_id": ev["id"],
        "participant_id": p["id"],
        "distances": ["Sprint"],
    }
    r1 = client.post("/api/v1/registrations", json=body)
    assert r1.status_code == 201
    r2 = client.post("/api/v1/registrations", json=body)
    assert r2.status_code in (400, 409)
    assert r2.status_code != 500


def test_update_registration_result(client: TestClient) -> None:
    ev = _event(client)
    p = _participant(client)
    reg = client.post(
        "/api/v1/registrations",
        json={
            "event_id": ev["id"],
            "participant_id": p["id"],
            "distances": ["Olympic"],
        },
    ).json()
    rid = reg["id"]
    r = client.put(
        f"/api/v1/registrations/{rid}",
        json={"result_time": "2:15:30", "result_place": "15/120"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["result_time"] == "2:15:30"
    assert data["result_place"] == "15/120"


def test_delete_registration(client: TestClient) -> None:
    ev = _event(client)
    p = _participant(client)
    reg = client.post(
        "/api/v1/registrations",
        json={
            "event_id": ev["id"],
            "participant_id": p["id"],
            "distances": ["Olympic"],
        },
    ).json()
    rid = reg["id"]
    r = client.delete(f"/api/v1/registrations/{rid}")
    assert r.status_code in (200, 204)
    r2 = client.delete(f"/api/v1/registrations/{rid}")
    assert r2.status_code == 404


def test_delete_event_cascades_registrations(
    client: TestClient,
    db_session: Session,
) -> None:
    ev = _event(client)
    p = _participant(client)
    eid = uuid.UUID(ev["id"])
    client.post(
        "/api/v1/registrations",
        json={
            "event_id": ev["id"],
            "participant_id": p["id"],
            "distances": ["Olympic"],
        },
    )
    r = client.delete(f"/api/v1/events/{ev['id']}")
    assert r.status_code in (200, 204)
    db_session.expire_all()
    n = (
        db_session.query(models.Registration)
        .filter(models.Registration.event_id == eid)
        .count()
    )
    assert n == 0
