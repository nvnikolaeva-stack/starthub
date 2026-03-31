from __future__ import annotations

from fastapi.testclient import TestClient


def test_participant_stats_no_events(client: TestClient) -> None:
    p = client.post(
        "/api/v1/participants",
        json={"display_name": "Lonely"},
    ).json()
    r = client.get(f"/api/v1/stats/participant/{p['id']}")
    assert r.status_code == 200
    data = r.json()
    assert data["total_events"] == 0
    assert data["events_by_sport"] == {}


def test_participant_stats_with_events(client: TestClient) -> None:
    p = client.post(
        "/api/v1/participants",
        json={"display_name": "Active"},
    ).json()
    e1 = client.post(
        "/api/v1/events",
        json={
            "name": "E1",
            "date_start": "2026-11-01",
            "location": "A",
            "sport_type": "running",
            "created_by": "t",
        },
    ).json()
    e2 = client.post(
        "/api/v1/events",
        json={
            "name": "E2",
            "date_start": "2026-11-02",
            "location": "B",
            "sport_type": "triathlon",
            "created_by": "t",
        },
    ).json()
    for ev in (e1, e2):
        client.post(
            "/api/v1/registrations",
            json={
                "event_id": ev["id"],
                "participant_id": p["id"],
                "distances": ["Short"],
            },
        )
    r = client.get(f"/api/v1/stats/participant/{p['id']}")
    assert r.status_code == 200
    data = r.json()
    assert data["total_events"] == 2
    assert "running" in data["events_by_sport"]
    assert "triathlon" in data["events_by_sport"]


def test_community_stats(client: TestClient) -> None:
    r = client.get("/api/v1/stats/community")
    assert r.status_code == 200
    data = r.json()
    assert "total_events" in data
    assert "total_participants" in data
    assert int(data["total_events"]) >= 0
    assert int(data["total_participants"]) >= 0


def test_distances_triathlon(client: TestClient) -> None:
    r = client.get("/api/v1/distances/triathlon")
    assert r.status_code == 200
    d = r.json()["distances"]
    assert "Sprint" in d
    assert "Olympic" in d


def test_distances_swimming_empty(client: TestClient) -> None:
    r = client.get("/api/v1/distances/swimming")
    assert r.status_code == 200
    assert r.json()["distances"] == []


def test_distances_invalid_sport(client: TestClient) -> None:
    r = client.get("/api/v1/distances/invalid_sport")
    assert r.status_code in (400, 404, 422)
