"""Планировщик напоминаний по всем зарегистрированным группам (APScheduler, 10:00 UTC)."""

from __future__ import annotations

import logging
from datetime import date, timedelta, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils import MONTH_GEN_RU

log = logging.getLogger(__name__)


def _iso_to_date(val: Any) -> date | None:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        return date.fromisoformat(val[:10])
    return None


def last_event_day(ev: dict) -> date | None:
    """Последний день старта (для тестов и совместимости)."""
    return _iso_to_date(ev.get("date_end")) or _iso_to_date(ev.get("date_start"))


def _format_date_nominal(d: date) -> str:
    return f"{d.day} {MONTH_GEN_RU[d.month]} {d.year}"


def _event_matches_result_remind_date(ev: dict, target: date) -> bool:
    """Старт «закончился» в target: один день — date_start; несколько — date_end."""
    ds = _iso_to_date(ev.get("date_start"))
    de = _iso_to_date(ev.get("date_end"))
    if de is not None:
        return de == target
    return ds == target


def _format_distances(distances: list[Any] | None) -> str:
    if not distances:
        return "—"
    return ", ".join(str(x) for x in distances)


class ReminderScheduler:
    def __init__(self, bot: Any, api_client: Any) -> None:
        self.bot = bot
        self.api = api_client
        self._sched = AsyncIOScheduler(timezone=timezone.utc)

    def start(self) -> None:
        self._sched.add_job(
            self._tick,
            "cron",
            hour=10,
            minute=0,
            id="alkardio_reminders",
            replace_existing=True,
        )
        self._sched.start()
        log.info("Планировщик напоминаний запущен (10:00 UTC), все группы")

    async def _tick(self) -> None:
        try:
            await self.check_reminders()
        except Exception:
            log.exception("Ошибка в задаче напоминаний")

    def stop(self) -> None:
        if self._sched.running:
            self._sched.shutdown(wait=False)
            log.info("Планировщик напоминаний остановлен")

    async def check_reminders(self, today: date | None = None) -> None:
        today_d = today or date.today()
        tomorrow = today_d + timedelta(days=1)
        yesterday = today_d - timedelta(days=1)
        try:
            groups = await self.api.list_groups_api()
        except Exception:
            log.exception("check_reminders: list_groups_api")
            return
        if not groups:
            log.info("Нет зарегистрированных групп — напоминания пропущены")
            return
        for g in groups:
            raw_id = g.get("telegram_chat_id")
            gid = str(g.get("id") or "")
            if raw_id is None or not gid:
                continue
            try:
                chat_id = int(raw_id)
            except (TypeError, ValueError):
                log.warning("Некорректный telegram_chat_id в группе %r", g)
                continue
            await self.send_upcoming_reminders(chat_id, gid, tomorrow)
            await self.send_result_reminders(chat_id, gid, yesterday)

    async def send_upcoming_reminders(
        self, chat_id: int, group_id: str, target_date: date
    ) -> None:
        try:
            events = await self.api.get_group_events(
                group_id,
                {
                    "date_from": target_date.isoformat(),
                    "date_to": target_date.isoformat(),
                    "limit": 100,
                    "period": "all",
                    "upcoming": "true",
                },
            )
        except Exception:
            log.exception("send_upcoming_reminders: get_group_events")
            return

        for ev in events:
            eid = str(ev.get("id") or "")
            if not eid:
                continue
            try:
                detail = await self.api.get_event(eid)
            except Exception:
                log.exception("send_upcoming_reminders: get_event %s", eid)
                continue

            text = self._build_upcoming_message(detail)
            try:
                await self.bot.send_message(chat_id, text)
            except Exception:
                log.exception("send_upcoming_reminders: send_message")

    def _build_upcoming_message(self, detail: dict) -> str:
        name = str(detail.get("name") or "Старт")
        loc = str(detail.get("location") or "—").strip() or "—"
        ds = _iso_to_date(detail.get("date_start"))
        date_s = _format_date_nominal(ds) if ds else "—"

        lines_dist: list[str] = []
        reg_lines: list[str] = []
        for r in detail.get("registrations") or []:
            dlist = list(r.get("distances") or [])
            if dlist:
                lines_dist.extend(str(x) for x in dlist)
            pnm = str(
                r.get("participant_display_name")
                or r.get("display_name")
                or "Участник"
            )
            dist_part = _format_distances(dlist)
            reg_lines.append(f"• {pnm} ({dist_part})")

        dist_block = ", ".join(dict.fromkeys(lines_dist)) if lines_dist else "—"

        people_block = "\n".join(reg_lines) if reg_lines else "• (пока никто не записан)"

        return (
            "🏁 Завтра старт!\n\n"
            f"📌 {name}\n"
            f"📅 {date_s}\n"
            f"📍 {loc}\n"
            f"📏 {dist_block}\n\n"
            "👥 Стартуют:\n"
            f"{people_block}\n\n"
            "Удачи! 💪"
        )

    async def send_result_reminders(
        self, chat_id: int, group_id: str, target_date: date
    ) -> None:
        try:
            past_list = await self.api.get_group_events(
                group_id,
                {"upcoming": "false", "limit": 500, "period": "all"},
            )
        except Exception:
            log.exception("send_result_reminders: get_group_events")
            return

        for ev in past_list:
            if not _event_matches_result_remind_date(ev, target_date):
                continue
            eid = str(ev.get("id") or "")
            if not eid:
                continue
            try:
                detail = await self.api.get_event(eid)
            except Exception:
                log.exception("send_result_reminders: get_event %s", eid)
                continue

            regs: list = detail.get("registrations") or []
            waiting: list[str] = []
            for r in regs:
                if r.get("result_time"):
                    continue
                pnm = str(
                    r.get("participant_display_name")
                    or r.get("display_name")
                    or "Участник"
                )
                waiting.append(pnm)

            if not regs or not waiting:
                continue

            name = str(detail.get("name") or "Старт")
            body = "\n".join(f"• {n}" for n in waiting)
            text = (
                f"🏅 Как прошёл {name}?\n\n"
                "👥 Ждём результаты:\n"
                f"{body}\n\n"
                "Используйте /result чтобы добавить время и место 📊"
            )
            try:
                await self.bot.send_message(chat_id, text)
            except Exception:
                log.exception("send_result_reminders: send_message")
