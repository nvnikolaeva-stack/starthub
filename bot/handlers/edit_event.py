from __future__ import annotations

import html
import logging
from datetime import date

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from api_client import ApiClient, ApiError
from keyboards import (
    distance_custom_keyboard,
    distance_pick_keyboard,
    edit_dist_after_sport_keyboard,
    edit_field_menu_keyboard,
    edit_sport_keyboard,
    upcoming_events_pick_keyboard,
)

from scope import params_for_callback_query, params_for_message
from translations import t
from utils import (
    OTHER_SENTINEL,
    api_error_user,
    build_distance_options,
    filter_preset_distances,
    format_date_ru,
    parse_user_date,
    sport_title_line,
)

router = Router(name="edit_event")
log = logging.getLogger(__name__)

LIST_PARAMS = {"upcoming": "true", "limit": 5, "period": "all"}


class EditEventFSM(StatesGroup):
    menu = State()
    enter_name = State()
    enter_date = State()
    enter_location = State()
    enter_url = State()
    enter_notes = State()
    confirm_sport_dist = State()
    distances = State()
    distance_custom = State()


def _event_card_html(ev: dict, locale: str) -> str:
    sport = str(ev.get("sport_type", ""))
    sport_title = sport_title_line(sport, locale)
    name = html.escape(str(ev.get("name", "")))
    ds = ev.get("date_start", "")
    de = ev.get("date_end")
    dash = t(locale, "dash")
    if de:
        dates = f"{format_date_ru(ds)} — {format_date_ru(de)}"
    else:
        dates = format_date_ru(ds) if ds else dash
    loc = html.escape(str(ev.get("location", "")))
    dist_block = ""
    notes = html.escape(str(ev.get("notes") or "").strip() or dash)
    url_raw = (ev.get("url") or "").strip()
    url = html.escape(url_raw) if url_raw else dash
    regs = ev.get("registrations") or []
    if regs:
        lines = []
        for r in regs[:8]:
            dists = ", ".join(str(x) for x in (r.get("distances") or []))
            who = html.escape(str(r.get("participant_display_name", "?")))
            lines.append(
                f"• {who}: {html.escape(dists) if dists else dash}"
            )
        more = ""
        if len(regs) > 8:
            more = t(locale, "edit_regs_more", n=len(regs) - 8)
        dist_block = "\n📏 " + "\n".join(lines) + more
    return (
        t(locale, "edit_card_header")
        + f"{sport_title}\n"
        f"📌 {name}\n"
        f"📅 {dates}\n"
        f"📍 {loc}{dist_block}\n"
        f"🔗 {url}\n"
        f"📝 {notes}"
    )


async def _show_field_menu(
    message: Message,
    client: ApiClient,
    state: FSMContext,
    eid: str,
    locale: str,
    *,
    edit: bool = False,
) -> None:
    try:
        ev = await client.get_event(eid)
    except ApiError:
        txt = api_error_user(locale)
        if edit:
            await message.edit_text(txt, reply_markup=None)
        else:
            await message.answer(txt)
        return
    kb = edit_field_menu_keyboard(eid, locale)
    text = _event_card_html(ev, locale) + "\n\n" + t(locale, "what_change")
    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=kb)
    await state.set_state(EditEventFSM.menu)


async def _my_registration(
    client: ApiClient,
    event_id: str,
    telegram_id: int,
) -> dict | None:
    try:
        p = await client.get_participant_by_telegram(telegram_id)
    except ApiError as e:
        if e.status == 404:
            return None
        raise
    pid = str(p["id"])
    detail = await client.get_event(event_id)
    for r in detail.get("registrations") or []:
        if str(r.get("participant_id")) == pid:
            return r
    return None


def _rebuild_edit_dist(data: dict, locale: str) -> tuple[list[str], InlineKeyboardMarkup]:
    presets: list[str] = list(data.get("edit_all_presets") or [])
    selected: list[str] = list(data.get("selected_distances") or [])
    opts = build_distance_options(presets, selected)
    show_done = len(selected) > 0
    return opts, distance_pick_keyboard(
        "edit",
        opts,
        locale,
        show_done=show_done,
        add_navigation=False,
        edit_navigation=True,
    )


@router.message(Command("edit"))
async def cmd_edit(
    message: Message,
    state: FSMContext,
    client: ApiClient,
    locale: str,
    hub_group_id: str | None = None,
) -> None:
    await state.clear()
    try:
        events = await client.get_events(
            params_for_message(message, LIST_PARAMS, hub_group_id)
        )
    except ApiError:
        log.exception("edit list")
        await message.answer(api_error_user(locale))
        return
    if not events:
        await message.answer(t(locale, "edit_no_events"))
        return
    await message.answer(
        t(locale, "edit_which_event"),
        reply_markup=upcoming_events_pick_keyboard(events, "edit", locale),
    )


@router.callback_query(F.data == "edit:cancel")
async def edit_cancel(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await state.clear()
    if callback.message:
        await callback.message.edit_text(t(locale, "canceled"), reply_markup=None)
    await callback.answer()


@router.callback_query(F.data == "edit:back:list")
async def edit_back_list(
    callback: CallbackQuery,
    state: FSMContext,
    client: ApiClient,
    locale: str,
    hub_group_id: str | None = None,
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await state.clear()
    try:
        events = await client.get_events(
            params_for_callback_query(callback, LIST_PARAMS, hub_group_id)
        )
    except ApiError:
        await callback.answer(api_error_user(locale), show_alert=True)
        return
    if not events:
        await callback.message.edit_text(t(locale, "edit_no_events_short"))
        await callback.answer()
        return
    await callback.message.edit_text(
        t(locale, "edit_which_event"),
        reply_markup=upcoming_events_pick_keyboard(events, "edit", locale),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit:pick:"))
async def edit_pick(
    callback: CallbackQuery, state: FSMContext, client: ApiClient, locale: str
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    eid = callback.data.split(":", 2)[2]
    try:
        ev = await client.get_event(eid)
    except ApiError:
        await callback.answer(api_error_user(locale), show_alert=True)
        return
    await state.update_data(edit_event_id=eid)
    await state.set_state(EditEventFSM.menu)
    await callback.message.edit_text(
        _event_card_html(ev, locale) + "\n\n" + t(locale, "what_change"),
        parse_mode="HTML",
        reply_markup=edit_field_menu_keyboard(eid, locale),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(EditEventFSM.menu),
    F.data.startswith("edit:field:"),
)
async def edit_choose_field(
    callback: CallbackQuery,
    state: FSMContext,
    client: ApiClient,
    locale: str,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    parts = callback.data.split(":", 3)
    if len(parts) < 4:
        await callback.answer()
        return
    eid, field_key = parts[2], parts[3]
    data = await state.get_data()
    if str(data.get("edit_event_id")) != eid:
        await callback.answer(t(locale, "session_stale_edit"), show_alert=True)
        return

    if field_key == "name":
        await state.set_state(EditEventFSM.enter_name)
        await callback.message.edit_text(
            t(locale, "enter_new_name"),
            reply_markup=None,
        )
    elif field_key == "date":
        await state.set_state(EditEventFSM.enter_date)
        await callback.message.edit_text(
            t(locale, "edit_new_date_label"),
            reply_markup=None,
        )
    elif field_key == "location":
        await state.set_state(EditEventFSM.enter_location)
        await callback.message.edit_text(
            t(locale, "new_location"),
            reply_markup=None,
        )
    elif field_key == "url":
        await state.set_state(EditEventFSM.enter_url)
        await callback.message.edit_text(
            t(locale, "new_url"),
            reply_markup=None,
        )
    elif field_key == "notes":
        await state.set_state(EditEventFSM.enter_notes)
        await callback.message.edit_text(
            t(locale, "new_notes"),
            reply_markup=None,
        )
    elif field_key == "sport":
        try:
            ev = await client.get_event(eid)
        except ApiError:
            await callback.answer(api_error_user(locale), show_alert=True)
            return
        await state.update_data(edit_sport_before=str(ev.get("sport_type", "")))
        await state.set_state(EditEventFSM.menu)
        await callback.message.edit_text(
            t(locale, "choose_sport"),
            reply_markup=edit_sport_keyboard(locale),
        )
    elif field_key == "dist":
        if callback.from_user is None:
            await callback.answer()
            return
        reg = await _my_registration(client, eid, callback.from_user.id)
        if not reg:
            await callback.answer(t(locale, "join_first"), show_alert=True)
            return
        sport = (await client.get_event(eid)).get("sport_type", "other")
        try:
            res = await client.get_distances(str(sport))
            labels = filter_preset_distances(list(res.get("distances") or []))
        except ApiError:
            labels = []
        cur = list(reg.get("distances") or [])
        await state.update_data(
            edit_registration_id=str(reg["id"]),
            edit_all_presets=labels,
            selected_distances=list(cur),
        )
        if labels:
            merged = {
                **data,
                "edit_all_presets": labels,
                "selected_distances": cur,
            }
            opts, kb = _rebuild_edit_dist(merged, locale)
            await state.update_data(edit_dist_options=opts)
            await state.set_state(EditEventFSM.distances)
            await callback.message.edit_text(
                t(locale, "pick_your_dist"),
                reply_markup=kb,
            )
        else:
            await state.set_state(EditEventFSM.distance_custom)
            await callback.message.edit_text(
                t(locale, "enter_dists_comma"),
                reply_markup=None,
            )
            await callback.message.answer(
                t(locale, "comma_values"),
                reply_markup=distance_custom_keyboard(
                    "edit", locale, add_navigation=False, edit_navigation=True
                ),
            )
    else:
        await callback.answer()
        return
    await callback.answer()


@router.callback_query(F.data == "edit:nav:field")
async def edit_nav_field(
    callback: CallbackQuery, state: FSMContext, client: ApiClient, locale: str
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    data = await state.get_data()
    eid = str(data.get("edit_event_id") or "")
    if not eid:
        await callback.answer()
        return
    await _show_field_menu(callback.message, client, state, eid, locale, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("edit:sport:pick:"))
async def edit_sport_pick(
    callback: CallbackQuery, state: FSMContext, client: ApiClient, locale: str
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    new_sport = callback.data.rsplit(":", 1)[1]
    data = await state.get_data()
    eid = str(data.get("edit_event_id") or "")
    old_sport = str(data.get("edit_sport_before") or "")
    if not eid:
        await callback.answer(t(locale, "service_down"), show_alert=True)
        return
    try:
        await client.update_event(eid, {"sport_type": new_sport})
    except ApiError:
        await callback.answer(api_error_user(locale), show_alert=True)
        return
    if new_sport != old_sport:
        await callback.message.edit_text(
            t(locale, "edit_sport_dist_warning"),
            reply_markup=edit_dist_after_sport_keyboard(locale),
        )
        await state.set_state(EditEventFSM.confirm_sport_dist)
    else:
        await _show_field_menu(callback.message, client, state, eid, locale, edit=True)
    await callback.answer()


@router.callback_query(
    StateFilter(EditEventFSM.confirm_sport_dist),
    F.data == "edit:distreset:no",
)
async def edit_distreset_no(
    callback: CallbackQuery, state: FSMContext, client: ApiClient, locale: str
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    data = await state.get_data()
    eid = str(data.get("edit_event_id") or "")
    await _show_field_menu(callback.message, client, state, eid, locale, edit=True)
    await callback.answer()


@router.callback_query(
    StateFilter(EditEventFSM.confirm_sport_dist),
    F.data == "edit:distreset:yes",
)
async def edit_distreset_yes(
    callback: CallbackQuery,
    state: FSMContext,
    client: ApiClient,
    locale: str,
) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    data = await state.get_data()
    eid = str(data.get("edit_event_id") or "")
    reg = await _my_registration(client, eid, callback.from_user.id)
    if not reg:
        await callback.answer(t(locale, "reg_not_found"), show_alert=True)
        await _show_field_menu(callback.message, client, state, eid, locale, edit=True)
        return
    ev = await client.get_event(eid)
    sport = str(ev.get("sport_type", "other"))
    try:
        res = await client.get_distances(sport)
        labels = filter_preset_distances(list(res.get("distances") or []))
    except ApiError:
        labels = []
    await state.update_data(
        edit_registration_id=str(reg["id"]),
        edit_all_presets=labels,
        selected_distances=[],
    )
    if labels:
        merged = {**data, "selected_distances": [], "edit_all_presets": labels}
        opts, kb = _rebuild_edit_dist(merged, locale)
        await state.update_data(edit_dist_options=opts)
        await state.set_state(EditEventFSM.distances)
        await callback.message.edit_text(
            t(locale, "pick_new_dists"),
            reply_markup=kb,
        )
    else:
        await state.set_state(EditEventFSM.distance_custom)
        await callback.message.edit_text(
            t(locale, "enter_dists_text"),
            reply_markup=None,
        )
        await callback.message.answer(
            t(locale, "comma_sep"),
            reply_markup=distance_custom_keyboard(
                "edit", locale, add_navigation=False, edit_navigation=True
            ),
        )
    await callback.answer()


@router.message(StateFilter(EditEventFSM.enter_name), F.text)
async def edit_name_msg(
    message: Message, state: FSMContext, client: ApiClient, locale: str
) -> None:
    eid = str((await state.get_data()).get("edit_event_id") or "")
    if not eid:
        return
    try:
        await client.update_event(eid, {"name": message.text.strip()})
    except ApiError:
        await message.answer(api_error_user(locale))
        return
    await _show_field_menu(message, client, state, eid, locale, edit=False)


@router.message(StateFilter(EditEventFSM.enter_date), F.text)
async def edit_date_msg(
    message: Message, state: FSMContext, client: ApiClient, locale: str
) -> None:
    eid = str((await state.get_data()).get("edit_event_id") or "")
    if not eid:
        return
    d = parse_user_date(message.text or "")
    if d is None:
        await message.answer(t(locale, "date_unparseable"))
        return
    if d.year > date.today().year + 3:
        await message.answer(t(locale, "year_far", year=d.year))
        return
    try:
        await client.update_event(eid, {"date_start": d.isoformat()})
    except ApiError:
        await message.answer(api_error_user(locale))
        return
    await _show_field_menu(message, client, state, eid, locale, edit=False)


@router.message(StateFilter(EditEventFSM.enter_location), F.text)
async def edit_location_msg(
    message: Message, state: FSMContext, client: ApiClient, locale: str
) -> None:
    eid = str((await state.get_data()).get("edit_event_id") or "")
    if not eid:
        return
    try:
        await client.update_event(eid, {"location": message.text.strip()})
    except ApiError:
        await message.answer(api_error_user(locale))
        return
    await _show_field_menu(message, client, state, eid, locale, edit=False)


@router.message(StateFilter(EditEventFSM.enter_url), F.text)
async def edit_url_msg(
    message: Message, state: FSMContext, client: ApiClient, locale: str
) -> None:
    eid = str((await state.get_data()).get("edit_event_id") or "")
    if not eid:
        return
    raw = message.text.strip()
    payload: dict = {"url": None if raw in ("-", "") else raw}
    try:
        await client.update_event(eid, payload)
    except ApiError:
        await message.answer(api_error_user(locale))
        return
    await _show_field_menu(message, client, state, eid, locale, edit=False)


@router.message(StateFilter(EditEventFSM.enter_notes), F.text)
async def edit_notes_msg(
    message: Message, state: FSMContext, client: ApiClient, locale: str
) -> None:
    eid = str((await state.get_data()).get("edit_event_id") or "")
    if not eid:
        return
    raw = message.text.strip()
    payload = {"notes": None if raw == "-" else raw}
    try:
        await client.update_event(eid, payload)
    except ApiError:
        await message.answer(api_error_user(locale))
        return
    await _show_field_menu(message, client, state, eid, locale, edit=False)


@router.callback_query(
    StateFilter(EditEventFSM.distances),
    F.data.startswith("edit:dist:pick:"),
)
async def edit_dist_pick(
    callback: CallbackQuery, state: FSMContext, locale: str
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    idx = int(callback.data.rsplit(":", 1)[1])
    data = await state.get_data()
    options: list[str] = list(data.get("edit_dist_options") or [])
    if idx < 0 or idx >= len(options):
        await callback.answer(t(locale, "error_generic"), show_alert=True)
        return
    opt = options[idx]
    cur = list(data.get("selected_distances") or [])
    if opt == OTHER_SENTINEL:
        await state.set_state(EditEventFSM.distance_custom)
        await callback.message.edit_text(
            t(locale, "enter_dist_text"), reply_markup=None
        )
        await callback.message.answer(
            t(locale, "comma_sep"),
            reply_markup=distance_custom_keyboard(
                "edit", locale, add_navigation=False, edit_navigation=True
            ),
        )
        await callback.answer()
        return
    cur.append(opt)
    await state.update_data(selected_distances=cur)
    merged = {**data, "selected_distances": cur}
    opts, kb = _rebuild_edit_dist(merged, locale)
    await state.update_data(edit_dist_options=opts)
    await callback.message.edit_text(
        t(locale, "edit_dist_pick_done", name=html.escape(opt)),
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data == "edit:nav:dist")
async def edit_nav_dist(
    callback: CallbackQuery, state: FSMContext, client: ApiClient, locale: str
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    data = await state.get_data()
    eid = str(data.get("edit_event_id") or "")
    if not eid:
        await callback.answer()
        return
    await state.set_state(EditEventFSM.menu)
    await _show_field_menu(callback.message, client, state, eid, locale, edit=True)
    await callback.answer()


@router.callback_query(
    StateFilter(EditEventFSM.distances, EditEventFSM.distance_custom),
    F.data == "edit:dist:done",
)
async def edit_dist_done(
    callback: CallbackQuery, state: FSMContext, client: ApiClient, locale: str
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    data = await state.get_data()
    rid = str(data.get("edit_registration_id") or "")
    cur = list(data.get("selected_distances") or [])
    eid = str(data.get("edit_event_id") or "")
    if not rid or not cur:
        await callback.answer(t(locale, "need_one_dist"), show_alert=True)
        return
    try:
        await client.update_registration(rid, {"distances": cur})
    except ApiError:
        await callback.answer(api_error_user(locale), show_alert=True)
        return
    await state.set_state(EditEventFSM.menu)
    await _show_field_menu(callback.message, client, state, eid, locale, edit=True)
    await callback.answer()


@router.message(StateFilter(EditEventFSM.distance_custom), F.text)
async def edit_dist_text(
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
    opts, kb = _rebuild_edit_dist(merged, locale)
    await state.update_data(edit_dist_options=opts)
    await state.set_state(EditEventFSM.distances)
    await message.answer(
        t(locale, "edit_dist_added_flow"),
        reply_markup=kb,
    )
