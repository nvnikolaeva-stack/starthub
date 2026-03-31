#!/usr/bin/env python3
"""
Проверка фронтенда и API #алкардио через HTTP (requests), без браузера.

Ожидается: API на localhost:8000, фронтенд на 192.168.0.105:3000.

Запуск из каталога backend:
  python3 scripts/check_frontend.py

Нужен пакет: pip install requests
"""

from __future__ import annotations

import sys
from datetime import date, timedelta

import requests

FRONT = "http://192.168.0.105:3000"
API = "http://localhost:8000"

PASSED = 0
FAILED = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        print(f"  ✅ {name}")
        PASSED += 1
    else:
        msg = f" — {detail}" if detail else ""
        print(f"  ❌ {name}{msg}")
        FAILED += 1


def get(url: str, timeout: float = 15.0) -> requests.Response | None:
    try:
        return requests.get(url, timeout=timeout)
    except requests.RequestException:
        return None


def main() -> None:
    global PASSED, FAILED

    print("Проверка сайта и API (requests, без браузера)\n")

    # 1
    r1 = get(f"{API}/api/v1/events")
    check(
        "1. API: GET /api/v1/events → 200",
        r1 is not None and r1.status_code == 200,
        f"status={r1.status_code if r1 else 'нет ответа'}",
    )

    # 2
    r2 = get(f"{FRONT}/")
    check(
        "2. Фронтенд: GET / → 200",
        r2 is not None and r2.status_code == 200,
        f"status={r2.status_code if r2 else 'нет ответа'}",
    )

    # 3
    r3 = get(f"{FRONT}/add")
    check(
        "3. Фронтенд: GET /add → 200",
        r3 is not None and r3.status_code == 200,
        f"status={r3.status_code if r3 else 'нет ответа'}",
    )

    # 4
    r4 = get(f"{FRONT}/stats")
    check(
        "4. Фронтенд: GET /stats → 200",
        r4 is not None and r4.status_code == 200,
        f"status={r4.status_code if r4 else 'нет ответа'}",
    )

    # 5–9 (цепочка со стартом)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    r5 = requests.post(
        f"{API}/api/v1/events",
        json={
            "name": "check_frontend smoke",
            "date_start": tomorrow,
            "location": "Test",
            "sport_type": "running",
            "created_by": "check_frontend",
        },
        timeout=15.0,
    )
    check(
        "5. API: создать старт → 201",
        r5.status_code == 201,
        f"status={r5.status_code}",
    )

    event_id: str | None = None
    if r5.status_code == 201:
        try:
            raw = r5.json().get("id")
            event_id = str(raw) if raw is not None else None
        except ValueError:
            event_id = None

    if event_id:
        r6 = get(f"{API}/api/v1/events/{event_id}")
        check(
            "6. API: получить старт → 200",
            r6 is not None and r6.status_code == 200,
            f"status={r6.status_code if r6 else 'нет ответа'}",
        )

        r7 = get(f"{FRONT}/event/{event_id}")
        check(
            "7. Фронтенд: GET /event/{id} → 200",
            r7 is not None and r7.status_code == 200,
            f"status={r7.status_code if r7 else 'нет ответа'}",
        )

        r8 = get(f"{API}/api/v1/events/{event_id}/ical")
        cal_ok = (
            r8 is not None
            and r8.status_code == 200
            and "vcalendar" in (r8.text or "").lower()
        )
        check(
            "8. API: iCal → 200, есть VCALENDAR",
            cal_ok,
            f"status={r8.status_code if r8 else 'нет ответа'}",
        )

        r9 = requests.delete(f"{API}/api/v1/events/{event_id}", timeout=15.0)
        # В проекте по умолчанию 204; иногда допускают 200
        check(
            "9. API: удалить старт → 200",
            r9.status_code in (200, 204),
            f"status={r9.status_code}",
        )
    else:
        missing = "пропуск: старт не создан (шаг 5)"
        check("6. API: получить старт → 200", False, missing)
        check("7. Фронтенд: GET /event/{id} → 200", False, missing)
        check("8. API: iCal → 200, есть VCALENDAR", False, missing)
        check("9. API: удалить старт → 200", False, missing)

    # 10
    r10 = get(f"{API}/api/v1/events/00000000-0000-0000-0000-000000000000")
    check(
        "10. API: несуществующий UUID → 404",
        r10 is not None and r10.status_code == 404,
        f"status={r10.status_code if r10 else 'нет ответа'}",
    )

    # 11
    r11 = get(f"{API}/api/v1/events/not-a-uuid")
    check(
        "11. API: невалидный UUID → не 500",
        r11 is not None and r11.status_code != 500,
        f"status={r11.status_code if r11 else 'нет ответа'}",
    )

    # 12
    r12 = get(f"{API}/api/v1/distances/running")
    check(
        "12. API: GET /api/v1/distances/running → 200",
        r12 is not None and r12.status_code == 200,
        f"status={r12.status_code if r12 else 'нет ответа'}",
    )

    # 13
    r13 = get(f"{API}/api/v1/stats/community")
    check(
        "13. API: GET /api/v1/stats/community → 200",
        r13 is not None and r13.status_code == 200,
        f"status={r13.status_code if r13 else 'нет ответа'}",
    )

    # 14
    r14 = get(f"{API}/api/v1/groups")
    check(
        "14. API: GET /api/v1/groups → 200",
        r14 is not None and r14.status_code == 200,
        f"status={r14.status_code if r14 else 'нет ответа'}",
    )

    print(f"\n{'=' * 40}")
    print(f"Пройдено: {PASSED}")
    print(f"Провалено: {FAILED}")
    print(f"{'=' * 40}")

    if FAILED:
        sys.exit(1)


if __name__ == "__main__":
    main()
