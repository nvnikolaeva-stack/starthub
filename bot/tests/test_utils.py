"""Лёгкие pytest-проверки утилит бота (без Telegram)."""

from __future__ import annotations

import sys
from pathlib import Path

# каталог bot/ в PYTHONPATH
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from datetime import date

from utils import (  # noqa: E402
    OTHER_SENTINEL,
    build_distance_options,
    filter_preset_distances,
    parse_flexible_date,
    parse_user_date,
)


def test_parse_flexible_date() -> None:
    d = parse_flexible_date("15.06.2026")
    assert d is not None
    assert d.month == 6 and d.day == 15


def test_parse_user_date_full_year() -> None:
    d = parse_user_date("03.03.2025")
    assert d is not None
    assert d == date(2025, 3, 3)


def test_parse_user_date_rejects_lone_large_number() -> None:
    assert parse_user_date("45") is None


def test_build_distance_options() -> None:
    opts = build_distance_options(["A", "B"], ["B"])
    assert opts == ["A", OTHER_SENTINEL]


def test_filter_preset_distances() -> None:
    assert filter_preset_distances(["Sprint", "other"]) == ["Sprint"]
