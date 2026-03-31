"""Тесты групп и мультичат-фильтрации API."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient


TG_A = -1001234567890
TG_B = -1009876543210
TG_C = -1005555555555
TG_MISSING = -9999999999


def _tomorrow_iso() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


def _next_week_iso() -> str:
    return (date.today() + timedelta(days=7)).isoformat()


# ===== CRUD групп =====


def test_create_group(client: TestClient) -> None:
    r = client.post(
        "/api/v1/groups",
        json={"telegram_chat_id": TG_A, "name": "Test Group"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["telegram_chat_id"] == TG_A
    assert data.get("name") == "Test Group"


def test_create_same_group_upsert(client: TestClient) -> None:
    r1 = client.post("/api/v1/groups", json={"telegram_chat_id": TG_A, "name": "Test Group"})
    assert r1.status_code == 200
    id1 = r1.json()["id"]
    r2 = client.post("/api/v1/groups", json={"telegram_chat_id": TG_A, "name": "Test Group"})
    assert r2.status_code == 200
    assert r2.json()["id"] == id1


def test_get_group_by_telegram(client: TestClient) -> None:
    client.post("/api/v1/groups", json={"telegram_chat_id": TG_A, "name": "Test Group"})
    r = client.get(f"/api/v1/groups/by-telegram/{TG_A}")
    assert r.status_code == 200
    data = r.json()
    assert data["telegram_chat_id"] == TG_A


def test_get_group_by_telegram_not_found(client: TestClient) -> None:
    r = client.get(f"/api/v1/groups/by-telegram/{TG_MISSING}")
    assert r.status_code == 404


def test_list_all_groups(client: TestClient) -> None:
    client.post("/api/v1/groups", json={"telegram_chat_id": TG_A, "name": "G1"})
    client.post("/api/v1/groups", json={"telegram_chat_id": TG_B, "name": "G2"})
    r = client.get("/api/v1/groups")
    assert r.status_code == 200
    lst = r.json()
    assert len(lst) == 2
    tgs = {g["telegram_chat_id"] for g in lst}
    assert TG_A in tgs and TG_B in tgs


# ===== События привязанные к группам =====


def test_create_event_with_group_id(client: TestClient) -> None:
    g = client.post("/api/v1/groups", json={"telegram_chat_id": TG_A, "name": "G"}).json()
    gid = g["id"]
    r = client.post(
        "/api/v1/events",
        json={
            "name": "Grouped",
            "date_start": _next_week_iso(),
            "location": "X",
            "sport_type": "running",
            "created_by": "t",
            "group_id": gid,
        },
    )
    assert r.status_code == 201
    assert r.json()["group_id"] == gid


def test_create_event_without_group_id(client: TestClient) -> None:
    r = client.post(
        "/api/v1/events",
        json={
            "name": "Legacy",
            "date_start": _next_week_iso(),
            "location": "Y",
            "sport_type": "running",
            "created_by": "t",
        },
    )
    assert r.status_code == 201
    assert r.json().get("group_id") is None


def test_list_events_filtered_by_group_id(client: TestClient) -> None:
    ga = client.post("/api/v1/groups", json={"telegram_chat_id": TG_A, "name": "A"}).json()
    gb = client.post("/api/v1/groups", json={"telegram_chat_id": TG_B, "name": "B"}).json()
    ds = _next_week_iso()
    client.post(
        "/api/v1/events",
        json={
            "name": "In A",
            "date_start": ds,
            "location": "L",
            "sport_type": "running",
            "created_by": "t",
            "group_id": ga["id"],
        },
    )
    client.post(
        "/api/v1/events",
        json={
            "name": "In B",
            "date_start": ds,
            "location": "L",
            "sport_type": "running",
            "created_by": "t",
            "group_id": gb["id"],
        },
    )
    r = client.get(
        "/api/v1/events",
        params={"group_id": ga["id"], "upcoming": "true", "limit": 50, "period": "all"},
    )
    assert r.status_code == 200
    names = {e["name"] for e in r.json()}
    assert "In A" in names
    assert "In B" not in names


def test_list_events_without_filter_returns_all(client: TestClient) -> None:
    ga = client.post("/api/v1/groups", json={"telegram_chat_id": TG_A, "name": "A"}).json()
    gb = client.post("/api/v1/groups", json={"telegram_chat_id": TG_B, "name": "B"}).json()
    ds = _next_week_iso()
    client.post(
        "/api/v1/events",
        json={
            "name": "Ev A",
            "date_start": ds,
            "location": "L",
            "sport_type": "running",
            "created_by": "t",
            "group_id": ga["id"],
        },
    )
    client.post(
        "/api/v1/events",
        json={
            "name": "Ev B",
            "date_start": ds,
            "location": "L",
            "sport_type": "running",
            "created_by": "t",
            "group_id": gb["id"],
        },
    )
    r = client.get(
        "/api/v1/events",
        params={"upcoming": "true", "limit": 50, "period": "all"},
    )
    assert r.status_code == 200
    names = {e["name"] for e in r.json()}
    assert names == {"Ev A", "Ev B"}


def test_list_events_for_telegram_id(client: TestClient) -> None:
    ga = client.post("/api/v1/groups", json={"telegram_chat_id": TG_A, "name": "A"}).json()
    gb = client.post("/api/v1/groups", json={"telegram_chat_id": TG_B, "name": "B"}).json()
    tg_user = 777_001
    client.post(
        "/api/v1/groups/{}/ensure-member".format(ga["id"]),
        json={
            "telegram_id": tg_user,
            "display_name": "Member",
            "telegram_username": "mem",
        },
    )
    ds = _next_week_iso()
    client.post(
        "/api/v1/events",
        json={
            "name": "Only A",
            "date_start": ds,
            "location": "L",
            "sport_type": "running",
            "created_by": "t",
            "group_id": ga["id"],
        },
    )
    client.post(
        "/api/v1/events",
        json={
            "name": "Only B",
            "date_start": ds,
            "location": "L",
            "sport_type": "running",
            "created_by": "t",
            "group_id": gb["id"],
        },
    )
    r = client.get(
        "/api/v1/events",
        params={
            "for_telegram_id": tg_user,
            "upcoming": "true",
            "limit": 50,
            "period": "all",
        },
    )
    assert r.status_code == 200
    names = {e["name"] for e in r.json()}
    assert "Only A" in names
    assert "Only B" not in names


# ===== Статистика по группам =====


def test_community_stats_for_group(client: TestClient) -> None:
    ga = client.post("/api/v1/groups", json={"telegram_chat_id": TG_A, "name": "A"}).json()
    gb = client.post("/api/v1/groups", json={"telegram_chat_id": TG_B, "name": "B"}).json()
    ds = _next_week_iso()
    for i in range(3):
        client.post(
            "/api/v1/events",
            json={
                "name": f"A{i}",
                "date_start": ds,
                "location": "L",
                "sport_type": "running",
                "created_by": "t",
                "group_id": ga["id"],
            },
        )
    client.post(
        "/api/v1/events",
        json={
            "name": "Blone",
            "date_start": ds,
            "location": "L",
            "sport_type": "running",
            "created_by": "t",
            "group_id": gb["id"],
        },
    )
    r = client.get("/api/v1/stats/community", params={"group_id": ga["id"]})
    assert r.status_code == 200
    assert r.json()["total_events"] == 3


def test_community_stats_all(client: TestClient) -> None:
    ga = client.post("/api/v1/groups", json={"telegram_chat_id": TG_A, "name": "A"}).json()
    gb = client.post("/api/v1/groups", json={"telegram_chat_id": TG_B, "name": "B"}).json()
    ds = _next_week_iso()
    for i in range(3):
        client.post(
            "/api/v1/events",
            json={
                "name": f"S{i}",
                "date_start": ds,
                "location": "L",
                "sport_type": "running",
                "created_by": "t",
                "group_id": ga["id"],
            },
        )
    client.post(
        "/api/v1/events",
        json={
            "name": "S3",
            "date_start": ds,
            "location": "L",
            "sport_type": "running",
            "created_by": "t",
            "group_id": gb["id"],
        },
    )
    r = client.get("/api/v1/stats/community")
    assert r.status_code == 200
    assert r.json()["total_events"] == 4


# ===== Участники и группы =====


def test_ensure_member_links_participant(client: TestClient) -> None:
    g = client.post("/api/v1/groups", json={"telegram_chat_id": TG_A, "name": "G"}).json()
    tg = 888_001
    r = client.post(
        f"/api/v1/groups/{g['id']}/ensure-member",
        json={
            "telegram_id": tg,
            "display_name": "Пользователь",
            "telegram_username": "usr",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("telegram_id") == tg


def test_group_participants_list(client: TestClient) -> None:
    g = client.post("/api/v1/groups", json={"telegram_chat_id": TG_A, "name": "G"}).json()
    tg = 888_002
    client.post(
        f"/api/v1/groups/{g['id']}/ensure-member",
        json={
            "telegram_id": tg,
            "display_name": "Listed",
            "telegram_username": None,
        },
    )
    r = client.get(f"/api/v1/groups/{g['id']}/participants")
    assert r.status_code == 200
    ids = {p["telegram_id"] for p in r.json()}
    assert tg in ids


def test_participant_groups_by_telegram(client: TestClient) -> None:
    g = client.post("/api/v1/groups", json={"telegram_chat_id": TG_A, "name": "MyG"}).json()
    tg = 888_003
    client.post(
        f"/api/v1/groups/{g['id']}/ensure-member",
        json={
            "telegram_id": tg,
            "display_name": "With groups",
            "telegram_username": "wg",
        },
    )
    r = client.get(f"/api/v1/participants/by-telegram/{tg}/groups")
    assert r.status_code == 200
    gids = {x["id"] for x in r.json()}
    assert g["id"] in gids


# ===== Напоминания (эндпоинт строгого списка группы) =====


def test_group_events_tomorrow_for_reminders(client: TestClient) -> None:
    """Старт в группе A на завтра — в списке /groups/A/events за этот день ровно один."""
    ga = client.post("/api/v1/groups", json={"telegram_chat_id": TG_A, "name": "A"}).json()
    client.post("/api/v1/groups", json={"telegram_chat_id": TG_B, "name": "B"})
    tom = _tomorrow_iso()
    client.post(
        "/api/v1/events",
        json={
            "name": "Rem A",
            "date_start": tom,
            "location": "L",
            "sport_type": "running",
            "created_by": "t",
            "group_id": ga["id"],
        },
    )
    r_a = client.get(
        f"/api/v1/groups/{ga['id']}/events",
        params={
            "date_from": tom,
            "date_to": tom,
            "upcoming": "true",
            "limit": 50,
            "period": "all",
        },
    )
    assert r_a.status_code == 200
    assert len(r_a.json()) == 1
    assert r_a.json()[0]["name"] == "Rem A"


def test_other_group_events_not_in_group_b_tomorrow(client: TestClient) -> None:
    """Старт только в группе A — в /groups/B/events на завтра пусто."""
    ga = client.post("/api/v1/groups", json={"telegram_chat_id": TG_C, "name": "CA"}).json()
    gb = client.post("/api/v1/groups", json={"telegram_chat_id": TG_B, "name": "CB"}).json()
    tom = _tomorrow_iso()
    client.post(
        "/api/v1/events",
        json={
            "name": "OnlyForA",
            "date_start": tom,
            "location": "L",
            "sport_type": "running",
            "created_by": "t",
            "group_id": ga["id"],
        },
    )
    r = client.get(
        f"/api/v1/groups/{gb['id']}/events",
        params={
            "date_from": tom,
            "date_to": tom,
            "upcoming": "true",
            "limit": 50,
            "period": "all",
        },
    )
    assert r.status_code == 200
    assert r.json() == []
