from __future__ import annotations

import html
import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from api_client import ApiClient, ApiError
from keyboards import distance_custom_keyboard, distance_pick_keyboard, join_events_keyboard
from scope import params_for_message
from translations import t
from utils import (
    OTHER_SENTINEL,
    build_distance_options,
    filter_preset_distances,
    generic_api_error,
)

router = Router(name="join")
log = logging.getLogger(__name__)


def _registration_for_telegram(ev: dict, telegram_id: int) -> dict | None:
    for r in ev.get("registrations") or []:
        tid = r.get("participant_telegram_id")
        if tid is not None and int(tid) == int(telegram_id):
            return r
    return None


async def _registered_event_ids(
    client: ApiClient, telegram_id: int
) -> frozenset[str]:
    try:
        p = await client.get_participant_by_telegram(telegram_id)
    except ApiError as e:
        if e.status == 404:
            return frozenset()
        raise
    try:
        detail = await client.get_participant_detail(str(p["id"]))
    except ApiError:
        log.exception("join participant detail")
        return frozenset()
    return frozenset(str(x["event_id"]) for x in (detail.get("events") or []))


class JoinEventFSM(StatesGroup):
    distances = State()
    distance_custom = State()


def _rebuild_join_dist_keyboard(
    data: dict, locale: str
) -> tuple[list[str], InlineKeyboardMarkup]:
    presets: list[str] = list(data.get("join_all_presets") or [])
    selected: list[str] = list(data.get("selected_distances") or [])
    opts = build_distance_options(presets, selected)
    show_done = len(selected) > 0
    return opts, distance_pick_keyboard(
        "join",
        opts,
        locale,
        show_done=show_done,
        add_navigation=False,
    )


async def _start_distances(
    message: Message, state: FSMContext, client: ApiClient, locale: str
) -> None:
    data = await state.get_data()
    sport = str(data.get("join_sport") or "")
    await state.update_data(selected_distances=[])

    try:
        res = await client.get_distances(sport)
        labels = filter_preset_distances(list(res.get("distances") or []))
    except ApiError:
        log.exception("join get_distances")
        labels = []

    if labels:
        opts, kb = _rebuild_join_dist_keyboard(
            {**data, "join_all_presets": labels, "selected_distances": []},
            locale,
        )
        await state.update_data(
            join_all_presets=labels,
            join_dist_options=opts,
        )
        await state.set_state(JoinEventFSM.distances)
        await message.answer(
            t(locale, "join_choose_dist"),
            reply_markup=kb,
        )
    else:
        await state.set_state(JoinEventFSM.distance_custom)
        await message.answer(
            t(locale, "join_enter_dist"),
            reply_markup=distance_custom_keyboard("join", locale, add_navigation=False),
        )


async def _finalize_join(
    message: Message,
    state: FSMContext,
    client: ApiClient,
    user,
    locale: str,
) -> None:
    data = await state.get_data()
    eid = str(data.get("join_event_id") or "")
    title = str(data.get("join_event_name") or t(locale, "event_word"))
    distances = list(data.get("distances") or data.get("selected_distances") or [])
    if not distances:
        await message.answer(t(locale, "need_one_distance"))
        return

    try:
        p = await client.create_participant(
            {
                "display_name": (user.full_name or t(locale, "participant_default")).strip(),
                "telegram_id": user.id,
                "telegram_username": user.username,
            }
        )
        await client.create_registration(
            {
                "event_id": eid,
                "participant_id": p["id"],
                "distances": distances,
            }
        )
    except ApiError as e:
        d = (e.detail or "").lower()
        if e.status == 400 and ("duplicate" in d or "уже" in d):
            await message.answer(t(locale, "already_joined"))
        else:
            log.warning("join registration failed: %s", e.detail)
            await message.answer(generic_api_error(locale))
        await state.clear()
        return
    except Exception:
        log.exception("join finalize")
        await message.answer(generic_api_error(locale))
        await state.clear()
        return

    await message.answer(
        t(locale, "joined_ok", name=html.escape(title)),
        parse_mode="HTML",
    )
    await state.clear()


@router.message(Command("join"))
async def cmd_join(
    message: Message,
    client: ApiClient,
    state: FSMContext,
    locale: str,
    hub_group_id: str | None = None,
) -> None:
    await state.clear()
    try:
        events = await client.get_events(
            params_for_message(
                message,
                {"upcoming": "true", "limit": 5, "period": "all"},
                hub_group_id,
            )
        )
    except ApiError:
        log.exception("join list")
        await message.answer(generic_api_error(locale))
        return

    if not events:
        await message.answer(t(locale, "no_upcoming"))
        return

    registered: frozenset[str] = frozenset()
    uid = message.from_user.id if message.from_user else 0
    if uid:
        try:
            registered = await _registered_event_ids(client, uid)
        except ApiError:
            log.exception("join registered_event_ids")
            await message.answer(generic_api_error(locale))
            return

    await message.answer(
        t(locale, "join_pick_header"),
        reply_markup=join_events_keyboard(
            events, locale, registered_event_ids=registered
        ),
    )


@router.callback_query(F.data == "join:cancel")
async def join_cancel(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await state.clear()
    if callback.message:
        await callback.message.edit_text(t(locale, "canceled"))
    await callback.answer()


@router.callback_query(F.data.startswith("join:pick:"))
async def join_pick(
    callback: CallbackQuery, state: FSMContext, client: ApiClient, locale: str
) -> None:
    if callback.message is None or callback.from_user is None or callback.data is None:
        await callback.answer()
        return
    eid = callback.data.split(":", 2)[2]
    try:
        ev = await client.get_event(eid)
    except ApiError:
        await callback.answer(t(locale, "join_load_fail"), show_alert=True)
        return

    reg = _registration_for_telegram(ev, callback.from_user.id)
    if reg is not None:
        await state.clear()
        await callback.answer()
        dists = list(reg.get("distances") or [])
        dist_html = (
            ", ".join(html.escape(str(x)) for x in dists)
            if dists
            else t(locale, "dash")
        )
        await callback.message.answer(
            t(locale, "join_already_registered_dists", dists=dist_html),
            parse_mode="HTML",
        )
        return

    await state.update_data(
        join_event_id=eid,
        join_event_name=str(ev.get("name", t(locale, "event_default"))),
        join_sport=str(ev.get("sport_type", "other")),
    )
    await callback.answer()
    await _start_distances(callback.message, state, client, locale)


@router.callback_query(
    StateFilter(JoinEventFSM.distances),
    F.data.startswith("join:dist:pick:"),
)
async def join_dist_pick(
    callback: CallbackQuery, state: FSMContext, locale: str
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    idx = int(callback.data.rsplit(":", 1)[1])
    data = await state.get_data()
    options: list[str] = list(data.get("join_dist_options") or [])
    if idx < 0 or idx >= len(options):
        await callback.answer(t(locale, "pick_error"), show_alert=True)
        return
    opt = options[idx]
    cur = list(data.get("selected_distances") or [])

    if opt == OTHER_SENTINEL:
        await state.set_state(JoinEventFSM.distance_custom)
        await callback.message.edit_text(
            t(locale, "join_ok_type_dist"), reply_markup=None
        )
        await callback.message.answer(
            t(locale, "comma_dist_hint"),
            reply_markup=distance_custom_keyboard("join", locale, add_navigation=False),
        )
        await callback.answer()
        return

    cur.append(opt)
    await state.update_data(selected_distances=cur)
    merged = {**data, "selected_distances": cur}
    opts, kb = _rebuild_join_dist_keyboard(merged, locale)
    await state.update_data(join_dist_options=opts)
    await callback.message.edit_text(
        t(locale, "join_dist_added_pick", name=html.escape(opt)),
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(
    StateFilter(JoinEventFSM.distances, JoinEventFSM.distance_custom),
    F.data == "join:dist:done",
)
async def join_dist_done(
    callback: CallbackQuery, state: FSMContext, client: ApiClient, locale: str
) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    data = await state.get_data()
    distances = list(data.get("selected_distances") or [])
    if not distances:
        await callback.answer(t(locale, "pick_distances_first"), show_alert=True)
        return
    await state.update_data(distances=distances)
    await callback.answer()
    await _finalize_join(callback.message, state, client, callback.from_user, locale)


@router.message(StateFilter(JoinEventFSM.distance_custom), F.text)
async def join_dist_text(
    message: Message, state: FSMContext, locale: str
) -> None:
    raw = (message.text or "").strip()
    if not raw:
        return
    parts = [p.strip() for p in raw.replace("\n", ",").split(",") if p.strip()]
    data = await state.get_data()
    cur = list(data.get("selected_distances") or [])
    cur.extend(parts)
    await state.update_data(selected_distances=cur)
    merged = {**data, "selected_distances": cur}
    opts, kb = _rebuild_join_dist_keyboard(merged, locale)
    await state.update_data(join_dist_options=opts)
    await state.set_state(JoinEventFSM.distances)
    await message.answer(
        t(locale, "join_dist_added_more"),
        reply_markup=kb,
    )
