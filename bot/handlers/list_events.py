from __future__ import annotations

import asyncio
import html
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from api_client import ApiClient, ApiError
from keyboards import list_filters_keyboard
from scope import params_for_message
from translations import t
from utils import format_date_ru, generic_api_error, sport_line_emoji

router = Router(name="list_events")
log = logging.getLogger(__name__)

DEFAULT_PERIOD = "all"
DEFAULT_LIMIT = 5


async def _event_block(client: ApiClient, ev: dict, locale: str) -> str:
    sport = str(ev.get("sport_type", ""))
    emo = sport_line_emoji(sport)
    title = str(ev.get("name", t(locale, "event_default")))
    gname = ev.get("group_name")
    grp_line = ""
    if gname:
        grp_line = f"👥 {html.escape(str(gname))}\n"
    ds = ev.get("date_start", "")
    loc = str(ev.get("location", ""))
    dstr = format_date_ru(ds) if ds else t(locale, "dash")
    try:
        detail = await client.get_event(str(ev["id"]))
        regs = detail.get("registrations") or []
        cnt = len(regs)
        if regs:
            ns = ", ".join(
                str(r.get("participant_display_name", ""))
                for r in regs[:5]
                if r.get("participant_display_name")
            )
            if cnt > 5:
                ns += f" (+{cnt - 5})"
            people = f"👥 {ns} ({cnt})"
        else:
            people = t(locale, "people_none_short")
    except ApiError:
        people = f"👥 {t(locale, 'dash')}"
    return f"{grp_line}{emo} <b>{title}</b>\n📅 {dstr} | 📍 {loc}\n{people}"


async def build_list_text(
    client: ApiClient, events: list[dict], locale: str
) -> str:
    if not events:
        return t(locale, "no_events_filter")
    parts = await asyncio.gather(
        *[_event_block(client, e, locale) for e in events]
    )
    return "\n\n".join(parts)


async def render_list_message(
    message: Message,
    client: ApiClient,
    *,
    period: str,
    sport: str | None,
    locale: str,
    edit: bool = False,
    hub_group_id: str | None = None,
) -> None:
    try:
        events = await client.get_events(
            params_for_message(message, _params(period, sport), hub_group_id)
        )
        text = t(locale, "upcoming_title") + await build_list_text(
            client, events, locale
        )
        kb = list_filters_keyboard(period, sport, locale)
    except ApiError:
        log.exception("list API error")
        text = generic_api_error(locale)
        kb = None

    if edit:
        if kb is not None:
            await message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        else:
            await message.edit_text(text, parse_mode="HTML", reply_markup=None)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=kb)


def _params(period: str, sport: str | None, upcoming: bool = True) -> dict:
    p: dict = {
        "upcoming": str(upcoming).lower(),
        "limit": DEFAULT_LIMIT,
        "period": period,
    }
    if sport and sport != "all":
        p["sport_type"] = sport
    return p


@router.message(Command("list"))
async def cmd_list(
    message: Message,
    client: ApiClient,
    locale: str,
    hub_group_id: str | None = None,
) -> None:
    await render_list_message(
        message,
        client,
        period=DEFAULT_PERIOD,
        sport=None,
        locale=locale,
        edit=False,
        hub_group_id=hub_group_id,
    )


@router.callback_query(F.data.startswith("list:u:"))
async def on_list_filter(
    callback: CallbackQuery,
    client: ApiClient,
    locale: str,
    hub_group_id: str | None = None,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer()
        return
    period = parts[2]
    sport_token = parts[3]
    sport: str | None = None if sport_token == "all" else sport_token
    await callback.answer()
    await render_list_message(
        callback.message,
        client,
        period=period,
        sport=sport,
        locale=locale,
        edit=True,
        hub_group_id=hub_group_id,
    )
