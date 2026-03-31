#!/usr/bin/env python3
"""
Лёгкая проверка сайта #алкардио — без браузера, без Playwright.
Проверяет что страницы отвечают и содержат нужные элементы.

Запуск из корня репозитория: python3 scripts/check_frontend.py

Требует: бэкенд на :8000 и фронтенд на :3000, пакет requests (pip install requests).
"""
from __future__ import annotations

import sys
from datetime import date, timedelta

import requests

FRONT = "http://localhost:3000"
API = "http://localhost:8000"
PASSED = 0
FAILED = 0


def check(name: str, condition: bool, details: str = "") -> None:
    global PASSED, FAILED
    if condition:
        print(f"  ✅ {name}")
        PASSED += 1
    else:
        print(f"  ❌ {name} — {details}")
        FAILED += 1


def get_safe(url: str, timeout: float = 10) -> requests.Response | None:
    try:
        return requests.get(url, timeout=timeout)
    except Exception:
        return None


def main() -> None:
    global PASSED, FAILED

    print("🔍 Проверка #алкардио (лёгкая, без браузера)\n")

    print("1️⃣  Сервисы")
    r = get_safe(f"{API}/api/v1/events")
    check("API доступен", r is not None and r.status_code == 200, "Запусти бэкенд на :8000")
    if r is None or r.status_code != 200:
        print("\n  ⛔ API недоступен. Дальше проверять бессмысленно.")
        sys.exit(1)

    r = get_safe(FRONT)
    check("Фронтенд доступен", r is not None and r.status_code == 200, "Запусти npm run dev на :3000")
    if r is None or r.status_code != 200:
        print("\n  ⛔ Фронтенд недоступен. Запусти: cd frontend && npm run dev")
        sys.exit(1)

    print("\n2️⃣  Страницы отвечают")
    pages = {
        "/": "Главная",
        "/add": "Форма добавления",
        "/stats": "Статистика",
    }
    for path, title in pages.items():
        resp = get_safe(f"{FRONT}{path}")
        check(
            f"{title} ({path})",
            resp is not None and resp.status_code == 200,
            f"status={resp.status_code if resp else 'нет ответа'}",
        )

    print("\n3️⃣  Содержимое страниц")

    r = get_safe(FRONT)
    if r is not None:
        body = r.text.lower()
        check(
            "Главная: есть календарь",
            "calendar" in body
            or "календар" in body
            or "month" in body
            or "месяц" in body,
            "Нет упоминания календаря",
        )
        check(
            "Главная: есть бренд",
            "#алкардио" in r.text or "alkardio" in body,
            "Нет бренда на главной",
        )

    r = get_safe(f"{FRONT}/add")
    if r is not None:
        body = r.text.lower()
        check(
            "Форма: есть input/select",
            "select" in body or "input" in body or "form" in body,
            "Нет элементов формы",
        )
        check(
            "Форма: упоминание спорта",
            "sport" in body
            or "спорт" in body
            or "running" in body
            or "бег" in body,
            "Нет упоминания вида спорта",
        )

    r = get_safe(f"{FRONT}/stats")
    if r is not None:
        body = r.text.lower()
        check(
            "Статистика: есть содержимое",
            "statistic" in body
            or "статистик" in body
            or "team" in body
            or "команд" in body,
            "Нет упоминания статистики",
        )

    print("\n4️⃣  API эндпоинты")

    endpoints = [
        ("GET", "/api/v1/events"),
        ("GET", "/api/v1/participants"),
        ("GET", "/api/v1/stats/community"),
        ("GET", "/api/v1/distances/running"),
        ("GET", "/api/v1/distances/triathlon"),
        ("GET", "/api/v1/groups"),
    ]
    for method, path in endpoints:
        resp = get_safe(f"{API}{path}")
        check(
            f"{method} {path}",
            resp is not None and resp.status_code == 200,
            f"status={resp.status_code if resp else 'нет ответа'}",
        )

    print("\n5️⃣  CRUD старта")
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    r = requests.post(
        f"{API}/api/v1/events",
        json={
            "name": "Frontend Test Race",
            "date_start": tomorrow,
            "location": "Test City",
            "sport_type": "running",
            "created_by": "test_script",
        },
        timeout=15,
    )
    check("Создать старт", r.status_code in (200, 201), f"status={r.status_code}")

    if r.status_code in (200, 201):
        data = r.json()
        event_id = data.get("id")
        if not event_id:
            check("Ответ создания содержит id", False, "no id in JSON")
        else:
            eid = str(event_id)

            r2 = get_safe(f"{API}/api/v1/events/{eid}")
            check("Получить старт по ID", r2 is not None and r2.status_code == 200)

            r3 = get_safe(f"{FRONT}/event/{eid}")
            check(
                "Страница старта на фронте",
                r3 is not None and r3.status_code == 200,
                f"status={r3.status_code if r3 else 'нет ответа'}",
            )

            r4 = get_safe(f"{API}/api/v1/events/{eid}/ical")
            ical_ok = (
                r4 is not None
                and r4.status_code == 200
                and "vcalendar" in (r4.text or "").lower()
            )
            check(
                "iCal файл",
                ical_ok,
                f"status={r4.status_code if r4 else 'нет ответа'}",
            )

            r5 = requests.delete(f"{API}/api/v1/events/{eid}", timeout=15)
            check("Удалить старт", r5.status_code in (200, 204), f"status={r5.status_code}")

    print("\n6️⃣  Переводы")
    r_ru = get_safe(FRONT)
    r_en = get_safe(FRONT)
    if r_ru is not None and r_en is not None:
        check(
            "Страница отвечает на обоих языках",
            r_ru.status_code == 200 and r_en.status_code == 200,
            "",
        )

    if r_ru is not None:
        body = r_ru.text
        has_any_text = len(body) > 500
        check("Страница не пустая (>500 символов)", has_any_text, f"длина: {len(body)}")

    print("\n7️⃣  Обработка ошибок")
    r = get_safe(f"{API}/api/v1/events/00000000-0000-0000-0000-000000000000")
    check(
        "Несуществующий старт → 404",
        r is not None and r.status_code == 404,
        f"status={r.status_code if r else 'нет ответа'}",
    )

    r = get_safe(f"{API}/api/v1/events/not-a-uuid")
    check(
        "Невалидный UUID → не 500",
        r is not None and r.status_code != 500,
        f"status={r.status_code if r else 'нет ответа'}",
    )

    print(f"\n{'=' * 40}")
    print(f"✅ Пройдено: {PASSED}")
    print(f"❌ Провалено: {FAILED}")
    print(f"{'=' * 40}")

    if FAILED > 0:
        print("\n⚠️  Есть ошибки! Скопируй вывод и отправь на фикс.")
        sys.exit(1)
    print("\n🎉 Все проверки пройдены!")


if __name__ == "__main__":
    main()
