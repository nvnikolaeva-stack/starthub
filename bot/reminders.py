"""Обёртка для юнит-тестов: делегирует в ReminderScheduler."""

from __future__ import annotations

from datetime import date
from typing import Any

from scheduler import ReminderScheduler, last_event_day

__all__ = ["check_reminders", "last_event_day"]


async def check_reminders(
    bot: Any,
    api_client: Any,
    *,
    today: date | None = None,
) -> None:
    sched = ReminderScheduler(bot, api_client)
    await sched.check_reminders(today=today)
