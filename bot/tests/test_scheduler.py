"""Юнит-тесты планировщика напоминаний."""

from __future__ import annotations

import logging
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from reminders import check_reminders, last_event_day  # noqa: E402


def _one_group_api() -> AsyncMock:
    api = AsyncMock()
    api.list_groups_api = AsyncMock(
        return_value=[{"id": "g1", "telegram_chat_id": -100123}]
    )
    return api


@pytest.mark.asyncio
async def test_reminder_tomorrow_sends() -> None:
    today = date(2026, 6, 10)
    tomorrow = today + timedelta(days=1)
    ev = {"id": "e1", "name": "Race", "date_start": tomorrow.isoformat()}
    api = _one_group_api()
    api.get_group_events = AsyncMock(side_effect=[[ev], []])
    api.get_event = AsyncMock(
        return_value={
            "name": "Race",
            "location": "Somewhere",
            "date_start": tomorrow.isoformat(),
            "registrations": [],
        }
    )
    bot = AsyncMock()
    await check_reminders(bot, api, today=today)
    bot.send_message.assert_awaited()


@pytest.mark.asyncio
async def test_no_tomorrow_no_message() -> None:
    today = date(2026, 6, 10)
    api = _one_group_api()
    api.get_group_events = AsyncMock(side_effect=[[], []])
    bot = AsyncMock()
    await check_reminders(bot, api, today=today)
    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_yesterday_asks_result_no_result_time() -> None:
    today = date(2026, 6, 11)
    y = today - timedelta(days=1)
    ev = {"id": "e2", "name": "Past", "date_start": y.isoformat(), "date_end": None}
    api = _one_group_api()
    api.get_group_events = AsyncMock(
        side_effect=[
            [],
            [ev],
        ]
    )
    api.get_event = AsyncMock(
        return_value={
            "id": "e2",
            "name": "Past",
            "registrations": [
                {
                    "participant_id": "p1",
                    "participant_display_name": "Участник",
                    "result_time": None,
                    "distances": [],
                },
            ],
        }
    )
    bot = AsyncMock()
    await check_reminders(bot, api, today=today)
    assert bot.send_message.await_count >= 1
    args = bot.send_message.await_args_list[-1][0]
    assert "результат" in args[1].lower()


@pytest.mark.asyncio
async def test_yesterday_all_results_no_nag() -> None:
    today = date(2026, 6, 11)
    y = today - timedelta(days=1)
    ev = {"id": "e3", "name": "Done", "date_start": y.isoformat()}
    api = _one_group_api()
    api.get_group_events = AsyncMock(side_effect=[[], [ev]])
    api.get_event = AsyncMock(
        return_value={
            "id": "e3",
            "name": "Done",
            "registrations": [
                {"result_time": "3:45:00"},
            ],
        }
    )
    bot = AsyncMock()
    await check_reminders(bot, api, today=today)
    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_multiday_reminder_day_before_start() -> None:
    today = date(2026, 6, 14)
    start = date(2026, 6, 15)
    end = date(2026, 6, 17)
    ev = {
        "id": "md1",
        "name": "Camp",
        "date_start": start.isoformat(),
        "date_end": end.isoformat(),
    }
    api = _one_group_api()
    api.get_group_events = AsyncMock(side_effect=[[ev], []])
    api.get_event = AsyncMock(
        return_value={
            "name": "Camp",
            "location": "Loc",
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
            "registrations": [],
        }
    )
    bot = AsyncMock()
    await check_reminders(bot, api, today=today)
    bot.send_message.assert_awaited()


@pytest.mark.asyncio
async def test_multiday_results_after_end() -> None:
    today = date(2026, 6, 18)
    ev = {
        "id": "md2",
        "name": "Camp2",
        "date_start": "2026-06-15",
        "date_end": "2026-06-17",
    }
    assert last_event_day(ev) == date(2026, 6, 17)
    api = _one_group_api()
    api.get_group_events = AsyncMock(side_effect=[[], [ev]])
    api.get_event = AsyncMock(
        return_value={
            "id": "md2",
            "name": "Camp2",
            "registrations": [
                {
                    "participant_display_name": "Runner",
                    "result_time": None,
                    "distances": ["10k"],
                }
            ],
        }
    )
    bot = AsyncMock()
    await check_reminders(bot, api, today=today)
    bot.send_message.assert_awaited()


@pytest.mark.asyncio
async def test_no_registered_groups_skips(caplog: pytest.LogCaptureFixture) -> None:
    api = AsyncMock()
    api.list_groups_api = AsyncMock(return_value=[])
    bot = AsyncMock()
    with caplog.at_level(logging.INFO):
        await check_reminders(bot, api, today=date.today())
    bot.send_message.assert_not_awaited()
    assert any("Нет зарегистрированных групп" in (r.message or "") for r in caplog.records)
