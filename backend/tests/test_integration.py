"""
Интеграционный тест: полный флоу мультичата.

Эмулирует:
1. Два групповых чата (A и B)
2. Три пользователя (user1 в A, user2 в A и B, user3 в B)
3. Создание стартов в разных группах
4. Проверка видимости стартов
5. Проверка статистики
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient


def test_full_multigroup_flow(client: TestClient) -> None:
    # ── Шаг 1: Регистрация групп ──
    group_a = client.post(
        "/api/v1/groups",
        json={
            "telegram_chat_id": -1_001_111_111_111,
            "name": "Runners Moscow",
        },
    ).json()

    group_b = client.post(
        "/api/v1/groups",
        json={
            "telegram_chat_id": -1_002_222_222_222,
            "name": "Tri Team SPb",
        },
    ).json()

    assert group_a["id"] != group_b["id"]

    # ── Шаг 2: Регистрация участников ──
    user1 = client.post(
        "/api/v1/participants",
        json={
            "display_name": "Алексей",
            "telegram_id": 111_111,
            "telegram_username": "alex",
        },
    ).json()

    user2 = client.post(
        "/api/v1/participants",
        json={
            "display_name": "Мария",
            "telegram_id": 222_222,
            "telegram_username": "maria",
        },
    ).json()

    user3 = client.post(
        "/api/v1/participants",
        json={
            "display_name": "Петя",
            "telegram_id": 333_333,
            "telegram_username": "petya",
        },
    ).json()

    # ── Шаг 3: Привязка участников к группам (API: telegram_id + display_name) ──
    client.post(
        f"/api/v1/groups/{group_a['id']}/ensure-member",
        json={
            "telegram_id": 111_111,
            "display_name": "Алексей",
            "telegram_username": "alex",
        },
    )
    client.post(
        f"/api/v1/groups/{group_a['id']}/ensure-member",
        json={
            "telegram_id": 222_222,
            "display_name": "Мария",
            "telegram_username": "maria",
        },
    )
    client.post(
        f"/api/v1/groups/{group_b['id']}/ensure-member",
        json={
            "telegram_id": 222_222,
            "display_name": "Мария",
            "telegram_username": "maria",
        },
    )
    client.post(
        f"/api/v1/groups/{group_b['id']}/ensure-member",
        json={
            "telegram_id": 333_333,
            "display_name": "Петя",
            "telegram_username": "petya",
        },
    )

    # ── Шаг 4: Создание стартов ──
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    next_week = (date.today() + timedelta(days=7)).isoformat()

    client.post(
        "/api/v1/events",
        json={
            "name": "Moscow Marathon",
            "date_start": tomorrow,
            "location": "Москва",
            "sport_type": "running",
            "created_by": "alex",
            "group_id": group_a["id"],
        },
    )

    client.post(
        "/api/v1/events",
        json={
            "name": "Ironstar SPb",
            "date_start": next_week,
            "location": "Санкт-Петербург",
            "sport_type": "triathlon",
            "created_by": "petya",
            "group_id": group_b["id"],
        },
    )

    client.post(
        "/api/v1/events",
        json={
            "name": "Old Race",
            "date_start": tomorrow,
            "location": "Казань",
            "sport_type": "running",
            "created_by": "someone",
        },
    )

    # ── Шаг 5: Проверка видимости ──
    events_in_a = client.get(
        "/api/v1/events",
        params={
            "group_id": group_a["id"],
            "upcoming": "true",
            "limit": 50,
            "period": "all",
        },
    ).json()
    event_names_a = [e["name"] for e in events_in_a]
    assert "Moscow Marathon" in event_names_a
    assert "Ironstar SPb" not in event_names_a
    assert "Old Race" in event_names_a

    events_in_b = client.get(
        "/api/v1/events",
        params={
            "group_id": group_b["id"],
            "upcoming": "true",
            "limit": 50,
            "period": "all",
        },
    ).json()
    event_names_b = [e["name"] for e in events_in_b]
    assert "Ironstar SPb" in event_names_b
    assert "Moscow Marathon" not in event_names_b
    assert "Old Race" in event_names_b

    events_user2 = client.get(
        "/api/v1/events",
        params={
            "for_telegram_id": 222_222,
            "upcoming": "true",
            "limit": 50,
            "period": "all",
        },
    ).json()
    event_names_user2 = [e["name"] for e in events_user2]
    assert "Moscow Marathon" in event_names_user2
    assert "Ironstar SPb" in event_names_user2
    assert "Old Race" in event_names_user2

    events_user1 = client.get(
        "/api/v1/events",
        params={
            "for_telegram_id": 111_111,
            "upcoming": "true",
            "limit": 50,
            "period": "all",
        },
    ).json()
    event_names_user1 = [e["name"] for e in events_user1]
    assert "Moscow Marathon" in event_names_user1
    assert "Ironstar SPb" not in event_names_user1
    assert "Old Race" in event_names_user1

    # ── Шаг 6: Статистика ──
    stats_a = client.get(
        "/api/v1/stats/community",
        params={"group_id": group_a["id"]},
    ).json()
    assert stats_a["total_events"] == 1

    stats_b = client.get(
        "/api/v1/stats/community",
        params={"group_id": group_b["id"]},
    ).json()
    assert stats_b["total_events"] == 1

    stats_all = client.get("/api/v1/stats/community").json()
    assert stats_all["total_events"] == 3

    assert user1["telegram_id"] == 111_111
    assert user2["telegram_id"] == 222_222
    assert user3["telegram_id"] == 333_333
