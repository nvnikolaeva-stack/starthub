#!/usr/bin/env python3
"""Смоук-тесты бота (Шаг 2): компиляция, импорты, утилиты, клавиатуры, API (опционально).

Запуск из папки bot/:

    python3 test_step2_smoke.py

Проверка бэкенда: по умолчанию берётся API_URL из окружения или http://127.0.0.1:8000.
Отключить HTTP-проверку: SKIP_API=1
"""

from __future__ import annotations

import asyncio
import compileall
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _fail(msg: str) -> None:
    print("FAIL:", msg, file=sys.stderr)
    raise SystemExit(1)


def test_compile() -> None:
    if not compileall.compile_dir(str(ROOT), quiet=1):
        _fail("compileall: синтаксическая ошибка в bot/")


def test_imports() -> None:
    import api_client  # noqa: F401
    import handlers.add_event  # noqa: F401
    import handlers.delete_event  # noqa: F401
    import handlers.edit_event  # noqa: F401
    import handlers.ical  # noqa: F401
    import handlers.join_event  # noqa: F401
    import handlers.list_events  # noqa: F401
    import handlers.result  # noqa: F401
    import handlers.start  # noqa: F401
    import handlers.stats  # noqa: F401
    import keyboards  # noqa: F401
    import utils  # noqa: F401


def test_utils() -> None:
    from utils import (
        OTHER_SENTINEL,
        build_distance_options,
        build_preview_text,
        filter_preset_distances,
        parse_flexible_date,
    )

    assert filter_preset_distances(["Sprint", "Other", "other", "Прочее"]) == ["Sprint"]

    opts = build_distance_options(["A", "B", "C"], ["B"])
    assert opts == ["A", "C", OTHER_SENTINEL], opts
    assert build_distance_options([], []) == []

    d = parse_flexible_date("15.06.2026")
    if d is None:
        _fail("parse_flexible_date('15.06.2026') вернул None")
    assert d.day == 15 and d.month == 6

    prev = build_preview_text(
        {
            "sport_type": "running",
            "name": "Test",
            "date_start": "2026-06-15",
            "date_end": None,
            "location": "MSK",
            "distances": ["5 km"],
            "url": "",
            "extra_names": [],
            "notes": "",
        }
    )
    assert "Test" in prev and "Бег" in prev


def test_keyboards() -> None:
    import keyboards

    from utils import OTHER_SENTINEL

    kb = keyboards.distance_pick_keyboard(
        "add", ["x", OTHER_SENTINEL], "ru", show_done=True, add_navigation=True
    )
    if not kb.inline_keyboard:
        _fail("distance_pick_keyboard: пустая клавиатура")

    kb2 = keyboards.distance_more_done_keyboard("join", "ru")
    if not kb2.inline_keyboard:
        _fail("distance_more_done_keyboard: пустая клавиатура")


async def test_api_client() -> None:
    from api_client import ApiClient

    base = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
    client = ApiClient(base)
    try:
        events = await client.get_events(
            {"limit": 3, "upcoming": "true", "period": "all"}
        )
        assert isinstance(events, list)

        dist = await client.get_distances("running")
        assert isinstance(dist, dict) and "distances" in dist

        if events:
            ev = await client.get_event(str(events[0]["id"]))
            assert isinstance(ev, dict) and "name" in ev
    finally:
        await client.close()


def main() -> None:
    test_compile()
    test_imports()
    test_utils()
    test_keyboards()

    if os.getenv("SKIP_API", "").strip().lower() in ("1", "true", "yes"):
        print("OK (без проверки API, SKIP_API=1)")
        return

    try:
        asyncio.run(test_api_client())
    except Exception as e:
        print("WARN: проверка API пропущена или не удалась:", e, file=sys.stderr)
        print(
            "Подними бэкенд или задай API_URL; для пропуска: SKIP_API=1",
            file=sys.stderr,
        )
        raise SystemExit(2) from e

    print("OK: compile, imports, utils, keyboards, ApiClient")


if __name__ == "__main__":
    main()
