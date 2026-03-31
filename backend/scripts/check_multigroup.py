#!/usr/bin/env python3
"""
Скрипт проверки мультичата.
Запуск: cd backend && python3 scripts/check_multigroup.py

Требует работающий API на localhost:8000 и пакет requests:
  pip3 install requests
"""
from __future__ import annotations

import sys
from datetime import date, timedelta

import requests

BASE = "http://localhost:8000/api/v1"
PASSED = 0
FAILED = 0


def check(name: str, condition: bool, details: str = "") -> None:
    global PASSED, FAILED
    if condition:
        print(f"  OK {name}")
        PASSED += 1
    else:
        print(f"  FAIL {name} — {details}")
        FAILED += 1


def main() -> None:
    global PASSED, FAILED

    print("Проверка мультичата #алкардио\n")

    print("1. API доступен?")
    try:
        r = requests.get(f"{BASE}/events", timeout=5)
        check("API отвечает", r.status_code == 200)
    except Exception as e:
        print(f"  FAIL API недоступен: {e}")
        print("  Запусти бэкенд: cd backend && python3 -m uvicorn app.main:app --reload --port 8000")
        sys.exit(1)

    print("\n2. Создание групп")
    ra = requests.post(
        f"{BASE}/groups", json={"telegram_chat_id": -9_990_001, "name": "Test A"}
    )
    ga = ra.json()
    check("Группа A создана", ra.status_code == 200 and "id" in ga, str(ga))

    rb = requests.post(
        f"{BASE}/groups", json={"telegram_chat_id": -9_990_002, "name": "Test B"}
    )
    gb = rb.json()
    check("Группа B создана", rb.status_code == 200 and "id" in gb, str(gb))

    check("Группы разные", ga.get("id") != gb.get("id"), f"{ga} vs {gb}")

    ra2 = requests.post(
        f"{BASE}/groups", json={"telegram_chat_id": -9_990_001, "name": "Test A"}
    )
    ga2 = ra2.json()
    check("Upsert работает", ga2.get("id") == ga.get("id"), str(ga2))

    print("\n3. Создание участников")
    u1 = requests.post(
        f"{BASE}/participants",
        json={"display_name": "TestUser1", "telegram_id": 9_990_001},
    ).json()
    check("Участник 1 создан", "id" in u1)

    u2 = requests.post(
        f"{BASE}/participants",
        json={"display_name": "TestUser2", "telegram_id": 9_990_002},
    ).json()
    check("Участник 2 создан", "id" in u2)

    print("\n4. Привязка участников (ensure-member: telegram_id + display_name)")
    r = requests.post(
        f"{BASE}/groups/{ga['id']}/ensure-member",
        json={
            "telegram_id": 9_990_001,
            "display_name": "TestUser1",
            "telegram_username": None,
        },
    )
    check("User1 в группе A", r.status_code == 200)

    r = requests.post(
        f"{BASE}/groups/{ga['id']}/ensure-member",
        json={
            "telegram_id": 9_990_002,
            "display_name": "TestUser2",
            "telegram_username": None,
        },
    )
    check("User2 в группе A", r.status_code == 200)

    r = requests.post(
        f"{BASE}/groups/{gb['id']}/ensure-member",
        json={
            "telegram_id": 9_990_002,
            "display_name": "TestUser2",
            "telegram_username": None,
        },
    )
    check("User2 в группе B", r.status_code == 200)

    print("\n5. Создание стартов")
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    ea = requests.post(
        f"{BASE}/events",
        json={
            "name": "Test Race A",
            "date_start": tomorrow,
            "location": "City A",
            "sport_type": "running",
            "created_by": "test",
            "group_id": ga["id"],
        },
    ).json()
    check("Старт в группе A", "id" in ea)

    eb = requests.post(
        f"{BASE}/events",
        json={
            "name": "Test Race B",
            "date_start": tomorrow,
            "location": "City B",
            "sport_type": "triathlon",
            "created_by": "test",
            "group_id": gb["id"],
        },
    ).json()
    check("Старт в группе B", "id" in eb)

    print("\n6. Видимость стартов")
    events_a = requests.get(
        f"{BASE}/events",
        params={
            "group_id": ga["id"],
            "upcoming": "true",
            "limit": 50,
            "period": "all",
        },
    ).json()
    names_a = [e["name"] for e in events_a]
    check("Группа A: свой старт виден", "Test Race A" in names_a, str(names_a))
    check("Группа A: чужой не виден", "Test Race B" not in names_a, str(names_a))

    events_b = requests.get(
        f"{BASE}/events",
        params={
            "group_id": gb["id"],
            "upcoming": "true",
            "limit": 50,
            "period": "all",
        },
    ).json()
    names_b = [e["name"] for e in events_b]
    check("Группа B: свой старт виден", "Test Race B" in names_b, str(names_b))
    check("Группа B: чужой не виден", "Test Race A" not in names_b, str(names_b))

    events_u2 = requests.get(
        f"{BASE}/events",
        params={
            "for_telegram_id": 9_990_002,
            "upcoming": "true",
            "limit": 50,
            "period": "all",
        },
    ).json()
    names_u2 = [e["name"] for e in events_u2]
    check("User2 в личке: видит A", "Test Race A" in names_u2, str(names_u2))
    check("User2 в личке: видит B", "Test Race B" in names_u2, str(names_u2))

    events_u1 = requests.get(
        f"{BASE}/events",
        params={
            "for_telegram_id": 9_990_001,
            "upcoming": "true",
            "limit": 50,
            "period": "all",
        },
    ).json()
    names_u1 = [e["name"] for e in events_u1]
    check("User1 в личке: видит A", "Test Race A" in names_u1, str(names_u1))
    check("User1 в личке: не видит B", "Test Race B" not in names_u1, str(names_u1))

    print("\n7. Статистика")
    stats_a = requests.get(
        f"{BASE}/stats/community", params={"group_id": ga["id"]}
    ).json()
    check(
        "Статистика группы A",
        int(stats_a.get("total_events", 0)) >= 1,
        str(stats_a),
    )

    stats_all = requests.get(f"{BASE}/stats/community").json()
    check(
        "Общая статистика",
        int(stats_all.get("total_events", 0)) >= 2,
        str(stats_all),
    )

    print("\n8. Группы участника")
    groups_u2 = requests.get(f"{BASE}/participants/by-telegram/9990002/groups").json()
    check("User2 в 2 группах", len(groups_u2) >= 2, f"групп: {len(groups_u2)}")

    groups_u1 = requests.get(f"{BASE}/participants/by-telegram/9990001/groups").json()
    check("User1 в 1 группе", len(groups_u1) >= 1, f"групп: {len(groups_u1)}")

    print("\nОчистка тестовых данных")
    requests.delete(f"{BASE}/events/{ea['id']}")
    requests.delete(f"{BASE}/events/{eb['id']}")
    check("Запрос на удаление стартов отправлен", True)

    print(f"\n{'=' * 40}")
    print(f"Пройдено: {PASSED}")
    print(f"Провалено: {FAILED}")
    print(f"{'=' * 40}")

    if FAILED > 0:
        print("\nЕсть ошибки.")
        sys.exit(1)
    print("\nВсе проверки пройдены.")


if __name__ == "__main__":
    main()
