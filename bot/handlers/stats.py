from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api_client import ApiClient, ApiError
from keyboards import stats_choice_keyboard
from scope import stats_params_for_callback
from translations import t
from utils import api_error_user, sport_title_line

router = Router(name="stats")
log = logging.getLogger(__name__)


def _format_mine(stats: dict, username: str | None, locale: str) -> str:
    total = int(stats.get("total_events") or 0)
    if total == 0:
        return t(locale, "stats_empty")

    who = f"@{username}" if username else t(locale, "stats_you_anon")
    lines = [
        t(locale, "stats_header", who=who),
        "",
        t(locale, "stats_events_count", n=total),
        "",
        t(locale, "stats_by_sport"),
    ]
    by_sport = stats.get("events_by_sport") or {}
    for sport, cnt in sorted(by_sport.items(), key=lambda x: -x[1]):
        title = sport_title_line(str(sport), locale)
        lines.append(f"{title} — {cnt}")

    pr = stats.get("personal_records") or {}
    if pr:
        lines.extend(["", t(locale, "stats_personal_header")])
        for dist, tm in sorted(pr.items()):
            lines.append(f"• {dist} — {tm}")

    places = stats.get("places_history") or []
    if places:
        lines.extend(["", t(locale, "stats_places_header")])
        for item in places[:12]:
            en = str(item.get("event_name", ""))
            pl = str(item.get("result_place", ""))
            lines.append(f"• {en} — {pl}")

    return "\n".join(lines)


def _format_community(s: dict, locale: str) -> str:
    lines = [
        t(locale, "stats_team_header_line"),
        "",
        t(locale, "stats_team_total_events", n=int(s.get("total_events") or 0)),
        t(locale, "stats_team_total_people", n=int(s.get("total_participants") or 0)),
    ]
    ma = s.get("most_active_participant")
    if ma:
        name = str(ma.get("display_name", "?"))
        cnt = int(ma.get("registrations_count") or 0)
        lines.append("")
        lines.append(
            t(locale, "stats_team_most_active", name=name, count=cnt)
        )

    ps = s.get("popular_sports") or []
    if ps:
        lines.extend(["", t(locale, "stats_popular")])
        for row in ps:
            sport = str(row.get("sport_type", ""))
            cnt = int(row.get("count") or 0)
            title = sport_title_line(sport, locale)
            lines.append(f"{title} — {cnt}")

    pl = s.get("popular_locations") or []
    if pl:
        lines.extend(["", t(locale, "stats_popular_locations")])
        for row in pl[:8]:
            loc = str(row.get("location", ""))
            cnt = int(row.get("count") or 0)
            lines.append(f"• {loc} — {cnt}")

    return "\n".join(lines)


@router.message(Command("stats"))
async def cmd_stats(message: Message, state: FSMContext, locale: str) -> None:
    await state.clear()
    await message.answer(
        t(locale, "stats_which_prompt"),
        reply_markup=stats_choice_keyboard(locale),
    )


@router.callback_query(F.data == "stats:cancel")
async def stats_cancel(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await state.clear()
    if callback.message:
        await callback.message.edit_text(t(locale, "canceled"), reply_markup=None)
    await callback.answer()


@router.callback_query(F.data == "stats:mine")
async def stats_mine(
    callback: CallbackQuery, client: ApiClient, locale: str
) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    try:
        p = await client.get_participant_by_telegram(callback.from_user.id)
        st = await client.get_participant_stats(str(p["id"]))
    except ApiError as e:
        if e.status == 404:
            await callback.message.edit_text(
                t(locale, "stats_empty"),
                reply_markup=None,
            )
            await callback.answer()
            return
        log.exception("stats mine")
        await callback.message.edit_text(api_error_user(locale), reply_markup=None)
        await callback.answer()
        return
    text = _format_mine(st, callback.from_user.username, locale)
    await callback.message.edit_text(text, reply_markup=None)
    await callback.answer()


@router.callback_query(F.data == "stats:community")
async def stats_community(
    callback: CallbackQuery,
    client: ApiClient,
    locale: str,
    hub_group_id: str | None = None,
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    try:
        s = await client.get_community_stats(
            stats_params_for_callback(callback, hub_group_id)
        )
    except ApiError:
        log.exception("stats community")
        await callback.message.edit_text(api_error_user(locale), reply_markup=None)
        await callback.answer()
        return
    await callback.message.edit_text(_format_community(s, locale), reply_markup=None)
    await callback.answer()
