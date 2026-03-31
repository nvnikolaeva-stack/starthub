from __future__ import annotations

import uuid

from fastapi.testclient import TestClient


def test_get_ical(client: TestClient, event_base_payload: dict) -> None:
    created = client.post("/api/v1/events", json=event_base_payload).json()
    eid = created["id"]
    r = client.get(f"/api/v1/events/{eid}/ical")
    assert r.status_code == 200
    assert "text/calendar" in (r.headers.get("content-type") or "").lower()
    assert b"BEGIN:VCALENDAR" in r.content


def test_get_ical_not_found(client: TestClient) -> None:
    r = client.get(f"/api/v1/events/{uuid.uuid4()}/ical")
    assert r.status_code == 404
