from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi.testclient import TestClient


def test_create_event_full(client: TestClient, event_base_payload: dict) -> None:
    r = client.post("/api/v1/events", json=event_base_payload)
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert data["name"] == event_base_payload["name"]


def test_create_event_missing_name(client: TestClient, event_base_payload: dict) -> None:
    body = {k: v for k, v in event_base_payload.items() if k != "name"}
    r = client.post("/api/v1/events", json=body)
    assert r.status_code == 422


def test_create_event_invalid_sport(client: TestClient, event_base_payload: dict) -> None:
    body = {**event_base_payload, "sport_type": "football"}
    r = client.post("/api/v1/events", json=body)
    assert r.status_code == 422


def test_create_multiday_within_week(client: TestClient, event_base_payload: dict) -> None:
    start = date(2026, 8, 1)
    end = start + timedelta(days=3)
    body = {
        **event_base_payload,
        "date_start": start.isoformat(),
        "date_end": end.isoformat(),
    }
    r = client.post("/api/v1/events", json=body)
    assert r.status_code == 201
    assert r.json()["date_end"] == end.isoformat()


def test_create_multiday_too_long(client: TestClient, event_base_payload: dict) -> None:
    start = date(2026, 9, 1)
    end = start + timedelta(days=10)
    body = {
        **event_base_payload,
        "date_start": start.isoformat(),
        "date_end": end.isoformat(),
    }
    r = client.post("/api/v1/events", json=body)
    assert r.status_code == 422


def test_list_events(client: TestClient, event_base_payload: dict) -> None:
    client.post("/api/v1/events", json=event_base_payload)
    r = client.get("/api/v1/events")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_events_filter_sport(client: TestClient, event_base_payload: dict) -> None:
    client.post("/api/v1/events", json=event_base_payload)
    client.post(
        "/api/v1/events",
        json={
            **event_base_payload,
            "name": "Swim",
            "sport_type": "swimming",
        },
    )
    r = client.get("/api/v1/events", params={"sport_type": "running"})
    assert r.status_code == 200
    for ev in r.json():
        assert ev["sport_type"] == "running"


def test_get_event_by_id(client: TestClient, event_base_payload: dict) -> None:
    created = client.post("/api/v1/events", json=event_base_payload).json()
    eid = created["id"]
    r = client.get(f"/api/v1/events/{eid}")
    assert r.status_code == 200
    assert r.json()["id"] == eid


def test_get_event_not_found(client: TestClient) -> None:
    r = client.get(f"/api/v1/events/{uuid.uuid4()}")
    assert r.status_code == 404


def test_get_event_invalid_uuid(client: TestClient) -> None:
    r = client.get("/api/v1/events/not-a-uuid")
    assert r.status_code == 422
    assert r.status_code != 500


def test_update_event(client: TestClient, event_base_payload: dict) -> None:
    created = client.post("/api/v1/events", json=event_base_payload).json()
    eid = created["id"]
    r = client.put(f"/api/v1/events/{eid}", json={"name": "Updated Name"})
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Name"


def test_delete_event(client: TestClient, event_base_payload: dict) -> None:
    created = client.post("/api/v1/events", json=event_base_payload).json()
    eid = created["id"]
    r = client.delete(f"/api/v1/events/{eid}")
    assert r.status_code in (200, 204)
    r2 = client.get(f"/api/v1/events/{eid}")
    assert r2.status_code == 404


def test_list_events_date_from_to_single_day(
    client: TestClient, event_base_payload: dict
) -> None:
    t0 = date.today()
    d_tom = t0 + timedelta(days=1)
    d_week = t0 + timedelta(days=7)
    d_month = t0 + timedelta(days=30)
    for nm, ds in (("A", d_tom), ("B", d_week), ("C", d_month)):
        assert (
            client.post(
                "/api/v1/events",
                json={**event_base_payload, "name": nm, "date_start": ds.isoformat()},
            ).status_code
            == 201
        )
    r = client.get(
        "/api/v1/events",
        params={
            "date_from": d_tom.isoformat(),
            "date_to": d_tom.isoformat(),
            "upcoming": "false",
            "limit": 50,
            "period": "all",
        },
    )
    assert r.status_code == 200
    names = {x["name"] for x in r.json()}
    assert names == {"A"}


def test_list_events_date_from_only_two(
    client: TestClient, event_base_payload: dict
) -> None:
    t0 = date.today()
    d_tom = t0 + timedelta(days=1)
    d_week = t0 + timedelta(days=7)
    for nm, ds in (("X", d_tom), ("Y", d_week)):
        assert (
            client.post(
                "/api/v1/events",
                json={**event_base_payload, "name": nm, "date_start": ds.isoformat()},
            ).status_code
            == 201
        )
    r = client.get(
        "/api/v1/events",
        params={
            "date_from": d_tom.isoformat(),
            "upcoming": "false",
            "limit": 50,
            "period": "all",
        },
    )
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_list_events_invalid_date_from(client: TestClient) -> None:
    r = client.get(
        "/api/v1/events",
        params={"date_from": "not-a-date", "period": "all"},
    )
    assert r.status_code == 422
    assert r.status_code != 500
