from __future__ import annotations

import html
import logging
import re
from datetime import date, timedelta

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import BaseFilter, Command, StateFilter
from aiogram.types import InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from api_client import ApiClient, ApiError
from translations import t
from keyboards import (
    cancel_confirm_keyboard,
    add_group_pick_keyboard,
    date_confirm_keyboard,
    date_confirm_past_keyboard,
    date_year_doubt_keyboard,
    distance_custom_keyboard,
    distance_pick_keyboard,
    duration_range_confirm_keyboard,
    duplicate_save_keyboard,
    edit_menu_keyboard,
    extras_manage_reply_keyboard,
    extras_remove_confirm_keyboard,
    extra_participants_more_keyboard,
    keep_field_keyboard,
    multi_duration_keyboard,
    nav_only_keyboard,
    preview_keyboard,
    skip_notes_keyboard,
    similar_events_keyboard,
    skip_url_keyboard,
    sport_type_keyboard,
    yes_no_keyboard,
)
from utils import (
    OTHER_SENTINEL,
    sport_title_line,
    build_distance_options,
    build_preview_text,
    date_needs_extreme_year_confirm,
    format_date_past_confirm_prompt_locale,
    format_date_recognized_prompt_locale,
    format_date_long_display,
    filter_preset_distances,
    format_range_short_dm,
    generic_api_error,
    parse_user_date,
    plural_days_locale,
    suggested_year_for_extreme,
    user_created_by,
)

router = Router(name="add_event")
log = logging.getLogger(__name__)

ADD_TEXT_PHRASES = frozenset(
    {"добавь старт", "добавить старт", "новый старт", "add"}
)

MULTIDUR_PICK = {f"add:multidur:{n}" for n in range(2, 8)}


class AddStartPhrase(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.chat.type != ChatType.PRIVATE:
            return False
        t = (message.text or "").strip().lower()
        return t in ADD_TEXT_PHRASES


class AddEventFSM(StatesGroup):
    pick_group = State()
    sport = State()
    name = State()
    date_start = State()
    date_year_confirm = State()
    date_confirm = State()
    multi_day = State()
    multi_duration = State()
    duration_confirm = State()
    date_end = State()
    location = State()
    distances = State()
    distance_custom = State()
    url = State()
    extra_ask = State()
    extra_name = State()
    extras_manage = State()
    notes = State()
    preview = State()
    similar_resolve = State()
    adddup_dist = State()
    adddup_custom = State()


def _combine_similar_events(exact: list, date_m: list) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for bucket in (exact, date_m):
        for ev in bucket or []:
            if not isinstance(ev, dict):
                continue
            eid = str(ev.get("id", ""))
            if eid and eid not in seen:
                seen.add(eid)
                out.append(ev)
    return out


def _format_similar_event_lines(events: list[dict], locale: str) -> str:
    blocks = []
    for ev in events:
        nm = html.escape(str(ev.get("name", "")))
        sp = html.escape(sport_title_line(str(ev.get("sport_type", "")), locale))
        loc = html.escape(str(ev.get("location", "")))
        n = int(ev.get("participants_count") or 0)
        pc = t(locale, "similar_participants_n", n=n)
        blocks.append(f"📌 <b>{nm}</b>\n   {sp} • {loc} • {pc}")
    return "\n\n".join(blocks)


async def _offer_similar_by_name(
    message: Message,
    state: FSMContext,
    client: ApiClient,
    locale: str,
    name_clean: str,
) -> bool:
    if len(name_clean) < 3:
        return False
    try:
        res = await client.search_similar_events(name=name_clean, date_str=None)
    except ApiError:
        log.exception("search_similar name")
        return False
    exact = res.get("exact_matches") or []
    if not exact:
        return False
    lines = _format_similar_event_lines(exact, locale)
    body = (
        f"{t(locale, 'similar_title_name')}\n\n{lines}\n\n"
        f"{t(locale, 'similar_footer')}"
    )
    await state.update_data(similar_resume="name")
    await state.set_state(AddEventFSM.similar_resolve)
    await message.answer(
        body,
        parse_mode="HTML",
        reply_markup=similar_events_keyboard(exact, locale),
    )
    return True


async def _offer_similar_before_location(
    message: Message,
    state: FSMContext,
    client: ApiClient,
    locale: str,
) -> bool:
    data = await state.get_data()
    ds = data.get("date_start")
    if not ds:
        return False
    nm = data.get("name")
    name_q = str(nm).strip() if nm else None
    try:
        res = await client.search_similar_events(
            name=name_q if name_q else None,
            date_str=str(ds)[:10],
        )
    except ApiError:
        log.exception("search_similar date")
        return False
    exact = res.get("exact_matches") or []
    date_m = res.get("date_matches") or []
    combined = _combine_similar_events(exact, date_m)
    if not combined:
        return False
    lines = _format_similar_event_lines(combined, locale)
    body = (
        f"{t(locale, 'similar_title_date')}\n\n{lines}\n\n"
        f"{t(locale, 'similar_footer')}"
    )
    await state.update_data(similar_resume="loc")
    await state.set_state(AddEventFSM.similar_resolve)
    await message.answer(
        body,
        parse_mode="HTML",
        reply_markup=similar_events_keyboard(combined, locale),
    )
    return True


def _rebuild_adddup_keyboard(
    data: dict, locale: str
) -> tuple[list[str], InlineKeyboardMarkup]:
    presets: list[str] = list(data.get("adddup_all_presets") or [])
    selected: list[str] = list(data.get("selected_distances") or [])
    opts = build_distance_options(presets, selected)
    show_done = len(selected) > 0
    return opts, distance_pick_keyboard(
        "adddup",
        opts,
        locale,
        show_done=show_done,
        add_navigation=False,
    )


async def _start_adddup_distances(
    message: Message,
    state: FSMContext,
    client: ApiClient,
    locale: str,
) -> None:
    data = await state.get_data()
    sport = str(data.get("adddup_sport") or "")
    await state.update_data(selected_distances=[])
    try:
        res = await client.get_distances(sport)
        labels = filter_preset_distances(list(res.get("distances") or []))
    except ApiError:
        log.exception("adddup get_distances")
        labels = []
    if labels:
        merged = {**data, "adddup_all_presets": labels, "selected_distances": []}
        opts, kb = _rebuild_adddup_keyboard(merged, locale)
        await state.update_data(
            adddup_all_presets=labels,
            adddup_dist_options=opts,
        )
        await state.set_state(AddEventFSM.adddup_dist)
        await message.answer(t(locale, "join_choose_dist"), reply_markup=kb)
    else:
        await state.set_state(AddEventFSM.adddup_custom)
        await message.answer(
            t(locale, "join_enter_dist"),
            reply_markup=distance_custom_keyboard(
                "adddup", locale, add_navigation=False
            ),
        )


async def _finalize_adddup_join(
    message: Message,
    state: FSMContext,
    client: ApiClient,
    user,
    locale: str,
) -> None:
    data = await state.get_data()
    eid = str(data.get("adddup_event_id") or "")
    title = str(data.get("adddup_event_name") or t(locale, "event_default"))
    distances = list(
        data.get("distances") or data.get("selected_distances") or []
    )
    if not distances:
        await message.answer(t(locale, "need_one_distance"))
        return
    try:
        p = await client.create_participant(
            {
                "display_name": (
                    user.full_name or t(locale, "participant_default")
                ).strip(),
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
        payload = e.payload if isinstance(e.payload, dict) else {}
        blob = (str(e.detail) + str(payload)).lower()
        if e.status == 400 and ("duplicate" in blob or "уже" in blob):
            await message.answer(t(locale, "already_joined"))
        else:
            log.warning("adddup registration failed: %s", e.detail)
            await message.answer(generic_api_error(locale))
        await state.clear()
        return
    except Exception:
        log.exception("adddup finalize")
        await message.answer(generic_api_error(locale))
        await state.clear()
        return

    await message.answer(
        t(locale, "joined_ok", name=html.escape(title)),
        parse_mode="HTML",
    )
    await state.clear()


async def _fsm_tail(state: FSMContext) -> str:
    st = await state.get_state()
    if not st:
        return ""
    return st.rsplit(":", 1)[-1]


def _extras_manage_text(names: list[str], locale: str) -> str:
    if not names:
        return t(locale, "extras_empty")
    lines = "\n".join(
        f"{i + 1}. {html.escape(str(n))}" for i, n in enumerate(names)
    )
    return t(locale, "extras_header") + lines


def _format_date_range_for_edit(ds: object, de: object, locale: str) -> str:
    if de and ds:
        d1 = date.fromisoformat(str(ds)[:10])
        d2 = date.fromisoformat(str(de)[:10])
        return f"{format_date_long_display(d1, locale)} — {format_date_long_display(d2, locale)}"
    if ds:
        d1 = date.fromisoformat(str(ds)[:10])
        return format_date_long_display(d1, locale)
    return t(locale, "dash")


def _start_date_confirm_prompt(
    d: date, locale: str
) -> tuple[str, InlineKeyboardMarkup]:
    if d < date.today():
        return (
            format_date_past_confirm_prompt_locale(d, locale),
            date_confirm_past_keyboard(locale),
        )
    return (
        format_date_recognized_prompt_locale(d, locale),
        date_confirm_keyboard(locale),
    )


async def _goto_preview(
    bot: Bot, chat_id: int, message: Message, state: FSMContext, locale: str
) -> None:
    data = await state.get_data()
    text = build_preview_text(data, locale)
    mid = data.get("preview_message_id")
    if mid:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=mid,
                text=text,
                parse_mode="HTML",
                reply_markup=preview_keyboard(locale),
            )
            await state.set_state(AddEventFSM.preview)
            return
        except Exception:
            log.debug("preview edit failed, send new")

    sent = await message.answer(
        text, parse_mode="HTML", reply_markup=preview_keyboard(locale)
    )
    await state.update_data(preview_message_id=sent.message_id)
    await state.set_state(AddEventFSM.preview)


async def _prompt_name(target: Message, state: FSMContext, locale: str) -> None:
    data = await state.get_data()
    nm = data.get("name")
    await state.set_state(AddEventFSM.name)
    if nm:
        await target.answer(
            t(
                locale,
                "current_value_prompt",
                value=html.escape(str(nm)),
            ),
            reply_markup=keep_field_keyboard("name", locale),
        )
    else:
        await target.answer(
            t(locale, "enter_name"),
            reply_markup=nav_only_keyboard(locale),
        )


async def _prompt_location_answer(
    target: Message,
    state: FSMContext,
    locale: str,
) -> None:
    data = await state.get_data()
    loc = data.get("location")
    await state.set_state(AddEventFSM.location)
    if loc:
        await target.answer(
            t(
                locale,
                "current_value_prompt",
                value=html.escape(str(loc)),
            ),
            reply_markup=keep_field_keyboard("location", locale),
        )
    else:
        await target.answer(
            t(locale, "enter_location"),
            reply_markup=nav_only_keyboard(locale),
        )


async def _start_distances_for_add(
    message: Message,
    state: FSMContext,
    client: ApiClient,
    locale: str,
) -> None:
    data = await state.get_data()
    sport = str(data.get("sport_type") or "")
    base = list(data.get("distances") or data.get("selected_distances") or [])

    try:
        res = await client.get_distances(sport)
        presets = filter_preset_distances(list(res.get("distances") or []))
    except ApiError:
        log.exception("add get_distances")
        presets = []

    await state.update_data(
        selected_distances=list(base),
        add_all_presets=presets,
    )
    opts = build_distance_options(presets, list(base))
    await state.update_data(add_dist_options=opts)
    show_done = len(base) > 0

    if opts:
        await state.set_state(AddEventFSM.distances)
        await message.answer(
            t(locale, "choose_distance"),
            reply_markup=distance_pick_keyboard(
                "add",
                opts,
                locale,
                show_done=show_done,
                add_navigation=True,
            ),
        )
    else:
        await state.set_state(AddEventFSM.distance_custom)
        await message.answer(
            t(locale, "enter_distance_comma"),
            reply_markup=distance_custom_keyboard("add", locale, add_navigation=True),
        )


async def start_add_dialog(message: Message, state: FSMContext, locale: str) -> None:
    await state.set_state(AddEventFSM.sport)
    await message.answer(
        t(locale, "choose_sport"),
        reply_markup=sport_type_keyboard("add", locale),
    )


async def _begin_add_private_flow(
    message: Message, state: FSMContext, client: ApiClient, locale: str
) -> None:
    await state.clear()
    uid = message.from_user.id if message.from_user else 0
    groups: list = []
    if uid:
        try:
            groups = await client.get_groups_for_telegram(uid)
        except ApiError:
            log.exception("get_groups_for_telegram")
            groups = []
    if len(groups) > 1:
        await state.set_state(AddEventFSM.pick_group)
        await message.answer(
            t(locale, "pick_target_group"),
            reply_markup=add_group_pick_keyboard(groups, locale),
        )
        return
    if len(groups) == 1:
        await state.update_data(target_group_id=str(groups[0]["id"]))
    await start_add_dialog(message, state, locale)


@router.callback_query(StateFilter(AddEventFSM.pick_group), F.data.startswith("add:grp:"))
async def add_pick_group_cb(
    callback: CallbackQuery, state: FSMContext, locale: str
) -> None:
    if callback.data is None or callback.message is None:
        await callback.answer()
        return
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await callback.answer()
        return
    gid = parts[2]
    await state.update_data(target_group_id=gid)
    await callback.answer()
    await start_add_dialog(callback.message, state, locale)


@router.message(Command("add"), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def add_in_group(message: Message, bot: Bot, locale: str) -> None:
    me = await bot.get_me()
    un = me.username or "this_bot"
    await message.answer(
        t(locale, "add_private_only", bot=html.escape(un)),
        parse_mode="HTML",
    )


@router.message(Command("add"), F.chat.type == ChatType.PRIVATE)
async def add_private(
    message: Message, state: FSMContext, client: ApiClient, locale: str
) -> None:
    await _begin_add_private_flow(message, state, client, locale)


@router.callback_query(F.data == "add:nav:cancel_prompt")
async def add_nav_cancel_prompt(
    callback: CallbackQuery, state: FSMContext, locale: str
) -> None:
    await callback.message.answer(
        t(locale, "cancel_flow_prompt"),
        reply_markup=cancel_confirm_keyboard(locale),
    )
    await callback.answer()


@router.callback_query(F.data == "add:cancel:yes")
async def add_cancel_yes(
    callback: CallbackQuery, state: FSMContext, locale: str
) -> None:
    await state.clear()
    await callback.message.edit_text(t(locale, "canceled"))
    await callback.answer()


@router.callback_query(F.data == "add:cancel:no")
async def add_cancel_no(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "add:nav:back")
async def add_nav_back(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    client: ApiClient,
    locale: str,
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    tail = await _fsm_tail(state)
    data = await state.get_data()

    if tail == "sport":
        await callback.answer(t(locale, "first_step"), show_alert=True)
        return

    if tail == "name":
        await state.set_state(AddEventFSM.sport)
        await callback.message.answer(
            t(locale, "choose_sport"),
            reply_markup=sport_type_keyboard("add", locale),
        )
        await callback.answer()
        return

    if tail == "date_start":
        await _prompt_name(callback.message, state, locale)
        await callback.answer()
        return

    if tail == "date_confirm":
        role = data.get("date_confirm_role")
        await state.update_data(pending_date_iso=None, date_confirm_role=None)
        if role == "start":
            await state.set_state(AddEventFSM.date_start)
            await callback.message.answer(
                t(locale, "date_prompt_short"),
                reply_markup=nav_only_keyboard(locale),
            )
        elif role == "end":
            await state.set_state(AddEventFSM.date_end)
            await callback.message.answer(
                t(locale, "enter_end_date_cap"),
                reply_markup=nav_only_keyboard(locale),
            )
        await callback.answer()
        return

    if tail == "date_year_confirm":
        await state.update_data(pending_date_iso=None, date_confirm_role=None)
        await state.set_state(AddEventFSM.date_start)
        await callback.message.answer(
            t(locale, "date_prompt_short"),
            reply_markup=nav_only_keyboard(locale),
        )
        await callback.answer()
        return

    if tail == "extras_manage":
        await state.update_data(wizard_edit=False)
        await _goto_preview(bot, callback.message.chat.id, callback.message, state, locale)
        await callback.answer()
        return

    if tail == "multi_day":
        await state.set_state(AddEventFSM.date_confirm)
        ds = date.fromisoformat(str(data["date_start"]))
        await state.update_data(
            pending_date_iso=data["date_start"],
            date_confirm_role="start",
        )
        text, kb = _start_date_confirm_prompt(ds, locale)
        await callback.message.answer(text, reply_markup=kb)
        await callback.answer()
        return

    if tail == "multi_duration":
        await state.set_state(AddEventFSM.multi_day)
        await callback.message.answer(
            t(locale, "multi_day_ask"),
            reply_markup=yes_no_keyboard("add:multi", locale),
        )
        await callback.answer()
        return

    if tail == "duration_confirm":
        await state.set_state(AddEventFSM.multi_duration)
        await callback.message.answer(
            t(locale, "how_many_days"),
            reply_markup=multi_duration_keyboard(locale),
        )
        await callback.answer()
        return

    if tail == "date_end":
        await state.set_state(AddEventFSM.multi_duration)
        await callback.message.answer(
            t(locale, "how_many_days"),
            reply_markup=multi_duration_keyboard(locale),
        )
        await callback.answer()
        return

    if tail == "location":
        if data.get("multi_day_yes"):
            await state.update_data(date_end=None)
            await state.set_state(AddEventFSM.multi_duration)
            await callback.message.answer(
                t(locale, "how_many_days"),
                reply_markup=multi_duration_keyboard(locale),
            )
        else:
            await state.set_state(AddEventFSM.multi_day)
            await callback.message.answer(
                t(locale, "multi_day_ask"),
                reply_markup=yes_no_keyboard("add:multi", locale),
            )
        await callback.answer()
        return

    if tail in ("distances", "distance_custom"):
        await _prompt_location_answer(callback.message, state, locale)
        await callback.answer()
        return

    if tail == "url":
        await _start_distances_for_add(callback.message, state, client, locale)
        await callback.answer()
        return

    if tail == "extra_ask":
        await state.set_state(AddEventFSM.url)
        await callback.message.answer(
            t(locale, "enter_link"),
            reply_markup=skip_url_keyboard(locale),
        )
        await callback.answer()
        return

    if tail == "extra_name":
        await state.set_state(AddEventFSM.extra_ask)
        await callback.message.answer(
            t(locale, "extra_ask"),
            reply_markup=yes_no_keyboard("add:extra", locale),
        )
        await callback.answer()
        return

    if tail == "notes":
        await state.set_state(AddEventFSM.extra_ask)
        await callback.message.answer(
            t(locale, "extra_ask"),
            reply_markup=yes_no_keyboard("add:extra", locale),
        )
        await callback.answer()
        return

    if tail == "preview":
        await state.set_state(AddEventFSM.notes)
        nt = data.get("notes") or ""
        dash = t(locale, "dash")
        nt_disp = html.escape(str(nt)) if nt else dash
        await callback.message.answer(
            t(locale, "notes_current", value=nt_disp),
            reply_markup=skip_notes_keyboard(locale),
        )
        await callback.answer()
        return

    await callback.answer()


@router.callback_query(F.data.regexp(r"^add:keep:(name|location|url|notes)$"))  # type: ignore[arg-type]
async def add_keep_value(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    client: ApiClient,
    locale: str) -> None:
    field = callback.data.split(":")[2]
    data = await state.get_data()
    if field == "name":
        if not data.get("name"):
            await callback.answer(t(locale, "need_name_first"), show_alert=True)
            return
        await state.set_state(AddEventFSM.date_start)
        await callback.message.answer(t(locale, "date_prompt_short"), reply_markup=nav_only_keyboard(locale))
    elif field == "location":
        if not data.get("location"):
            await callback.answer(t(locale, "need_location_first"), show_alert=True)
            return
        await _start_distances_for_add(callback.message, state, client, locale)
    elif field == "url":
        await state.set_state(AddEventFSM.extra_ask)
        await callback.message.answer(
            t(locale, "extra_ask"),
            reply_markup=yes_no_keyboard("add:extra", locale),
        )
    elif field == "notes":
        await state.update_data(wizard_edit=False)
        await _goto_preview(bot, callback.message.chat.id, callback.message, state, locale)
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.sport), F.data.startswith("add:sport:"))
async def add_sport(callback: CallbackQuery, state: FSMContext, bot: Bot, locale: str) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    new_sport = callback.data.rsplit(":", 1)[1]
    data = await state.get_data()
    prev = data.get("sport_type")

    if data.get("wizard_edit"):
        if prev is not None and prev != new_sport:
            await state.update_data(
                sport_type=new_sport,
                distances=[],
                selected_distances=[],
                wizard_edit=False,
            )
        else:
            await state.update_data(sport_type=new_sport, wizard_edit=False)
        await callback.message.edit_text(t(locale, "sport_updated"), reply_markup=None)
        await _goto_preview(bot, callback.message.chat.id, callback.message, state, locale)
        await callback.answer()
        return

    await state.update_data(sport_type=new_sport)
    await callback.message.edit_text(t(locale, "sport_chosen"), reply_markup=None)
    await _prompt_name(callback.message, state, locale)
    await callback.answer()


@router.message(StateFilter(AddEventFSM.name), F.text, F.chat.type == ChatType.PRIVATE)
async def add_name(
    message: Message, state: FSMContext, bot: Bot, client: ApiClient, locale: str
) -> None:
    name_clean = (message.text or "").strip()
    await state.update_data(name=name_clean)
    data = await state.get_data()
    if data.get("wizard_edit"):
        await state.update_data(wizard_edit=False)
        await _goto_preview(bot, message.chat.id, message, state, locale)
        return
    if await _offer_similar_by_name(message, state, client, locale, name_clean):
        return
    await state.set_state(AddEventFSM.date_start)
    await message.answer(t(locale, "date_prompt_short"), reply_markup=nav_only_keyboard(locale))


@router.message(StateFilter(AddEventFSM.date_start), F.text, F.chat.type == ChatType.PRIVATE)
async def add_date_start(message: Message, state: FSMContext, locale: str) -> None:
    raw = (message.text or "").strip()
    d = parse_user_date(raw)
    if d is None:
        await message.answer(t(locale, "date_unparseable"))
        return
    today_c = date.today()
    if d.year > today_c.year + 3:
        await message.answer(
            t(locale, "year_far", year=d.year)
        )
        return
    if d < today_c:
        await state.update_data(
            pending_date_iso=d.isoformat(),
            date_confirm_role="start",
        )
        await state.set_state(AddEventFSM.date_confirm)
        text, kb = _start_date_confirm_prompt(d, locale)
        await message.answer(text, reply_markup=kb)
        return
    if date_needs_extreme_year_confirm(d):
        hint = suggested_year_for_extreme(d)
        await state.update_data(
            pending_date_iso=d.isoformat(),
            date_confirm_role="start",
            pending_year_hint=str(hint),
        )
        await state.set_state(AddEventFSM.date_year_confirm)
        await message.answer(
            t(locale, "year_doubt", year=d.year, hint=hint),
            reply_markup=date_year_doubt_keyboard(locale),
        )
        return
    await state.update_data(
        pending_date_iso=d.isoformat(),
        date_confirm_role="start",
    )
    await state.set_state(AddEventFSM.date_confirm)
    text, kb = _start_date_confirm_prompt(d, locale)
    await message.answer(text, reply_markup=kb)


@router.callback_query(StateFilter(AddEventFSM.date_year_confirm), F.data == "add:yearok:yes")
async def add_year_ok_yes(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    if callback.message is None:
        await callback.answer()
        return
    data = await state.get_data()
    iso = str(data.get("pending_date_iso") or "")
    if not iso:
        await callback.answer(t(locale, "error_generic"), show_alert=True)
        return
    d = date.fromisoformat(iso)
    await state.set_state(AddEventFSM.date_confirm)
    text, kb = _start_date_confirm_prompt(d, locale)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.date_year_confirm), F.data == "add:yearok:no")
async def add_year_ok_no(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await state.update_data(pending_date_iso=None, date_confirm_role=None, pending_year_hint=None)
    await state.set_state(AddEventFSM.date_start)
    await callback.message.edit_text(t(locale, "date_prompt_short"), reply_markup=nav_only_keyboard(locale))
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.multi_day), F.data.startswith("add:multi:"))
async def add_multi(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    client: ApiClient,
    locale: str,
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    choice = callback.data.rsplit(":", 1)[1]
    data = await state.get_data()

    if data.get("edit_dates_mode"):
        if choice == "yes":
            await state.update_data(multi_day_yes=True)
            await state.set_state(AddEventFSM.multi_duration)
            await callback.message.edit_text(
                t(locale, "how_many_days"),
                reply_markup=multi_duration_keyboard(locale),
            )
        else:
            await state.update_data(
                date_end=None,
                edit_dates_mode=False,
                multi_day_yes=False,
            )
            await _goto_preview(bot, callback.message.chat.id, callback.message, state, locale)
        await callback.answer()
        return

    if choice == "yes":
        await state.update_data(multi_day_yes=True)
        await state.set_state(AddEventFSM.multi_duration)
        await callback.message.edit_text(
            t(locale, "how_many_days"),
            reply_markup=multi_duration_keyboard(locale),
        )
    else:
        await state.update_data(multi_day_yes=False, date_end=None)
        await callback.message.edit_text(t(locale, "one_day_goto_loc"), reply_markup=None)
        if await _offer_similar_before_location(callback.message, state, client, locale):
            await callback.answer()
            return
        await _prompt_location_answer(callback.message, state, locale)
    await callback.answer()


@router.callback_query(
    StateFilter(AddEventFSM.multi_duration),
    F.data.in_(MULTIDUR_PICK),
)
async def add_multidur_pick(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    n = int(callback.data.rsplit(":", 1)[1])
    data = await state.get_data()
    ds = date.fromisoformat(str(data["date_start"]))
    de = ds + timedelta(days=n - 1)
    await state.update_data(
        pending_duration_confirm_end=de.isoformat(),
        pending_duration_days=n,
    )
    await state.set_state(AddEventFSM.duration_confirm)
    txt = t(
        locale,
        "duration_confirm_line",
        rng=format_range_short_dm(ds, de),
        days=plural_days_locale(n, locale),
    )
    await callback.message.edit_text(
        txt,
        reply_markup=duration_range_confirm_keyboard(locale),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(AddEventFSM.multi_duration),
    F.data == "add:multidur:custom",
)
async def add_multidur_custom(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await state.update_data(multi_end_via_custom=True)
    await state.set_state(AddEventFSM.date_end)
    await callback.message.edit_text(
        t(locale, "enter_end_date_free"),
        reply_markup=None,
    )
    await callback.message.answer(
        t(locale, "reply_with_date"),
        reply_markup=nav_only_keyboard(locale),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.duration_confirm), F.data == "add:durconf:yes")
async def add_durconf_yes(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    client: ApiClient,
    locale: str,
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    data = await state.get_data()
    iso = str(data.get("pending_duration_confirm_end") or "")
    if not iso:
        await callback.answer(t(locale, "error_generic"), show_alert=True)
        return
    await state.update_data(
        date_end=iso,
        pending_duration_confirm_end=None,
        pending_duration_days=None,
    )
    data = await state.get_data()
    if data.get("edit_dates_mode"):
        await state.update_data(edit_dates_mode=False)
        await _goto_preview(bot, callback.message.chat.id, callback.message, state, locale)
        await callback.answer()
        return
    await callback.message.edit_text(t(locale, "goto_location"), reply_markup=None)
    if await _offer_similar_before_location(callback.message, state, client, locale):
        await callback.answer()
        return
    await _prompt_location_answer(callback.message, state, locale)
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.duration_confirm), F.data == "add:durconf:edit")
async def add_durconf_edit(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await state.set_state(AddEventFSM.multi_duration)
    await callback.message.edit_text(
        t(locale, "how_many_days"),
        reply_markup=multi_duration_keyboard(locale),
    )
    await callback.answer()


@router.message(StateFilter(AddEventFSM.date_end), F.text, F.chat.type == ChatType.PRIVATE)
async def add_date_end(message: Message, state: FSMContext, bot: Bot, locale: str) -> None:
    d = parse_user_date(message.text or "")
    if d is None:
        await message.answer(t(locale, "date_unparseable"))
        return
    today_c = date.today()
    if d.year > today_c.year + 3:
        await message.answer(
            t(locale, "year_far", year=d.year)
        )
        return
    data = await state.get_data()
    ds = date.fromisoformat(str(data["date_start"]))
    if d < ds:
        await message.answer(t(locale, "end_before_start"))
        return
    if d > ds + timedelta(days=7):
        await message.answer(t(locale, "end_max_week"))
        return
    await state.update_data(
        pending_date_iso=d.isoformat(),
        date_confirm_role="end",
    )
    await state.set_state(AddEventFSM.date_confirm)
    await message.answer(
        format_date_recognized_prompt_locale(d, locale),
        reply_markup=date_confirm_keyboard(locale),
    )


@router.callback_query(StateFilter(AddEventFSM.date_confirm), F.data == "add:dateconfirm:yes")
async def add_date_confirm_yes(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    client: ApiClient,
    locale: str,
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    data = await state.get_data()
    role = str(data.get("date_confirm_role") or "")
    iso = str(data.get("pending_date_iso") or "")
    if not iso or role not in ("start", "end"):
        await callback.answer(t(locale, "session_stale_add"), show_alert=True)
        return

    if role == "start":
        await state.update_data(date_start=iso, pending_date_iso=None, date_confirm_role=None)
        await state.set_state(AddEventFSM.multi_day)
        await callback.message.edit_text(
            t(locale, "multi_day_ask"),
            reply_markup=yes_no_keyboard("add:multi", locale),
        )
        await callback.answer()
        return

    await state.update_data(date_end=iso, pending_date_iso=None, date_confirm_role=None)
    await state.update_data(multi_end_via_custom=False)
    data = await state.get_data()
    if data.get("edit_dates_mode"):
        await state.update_data(edit_dates_mode=False)
        await _goto_preview(bot, callback.message.chat.id, callback.message, state, locale)
        await callback.answer()
        return
    await callback.message.edit_text(t(locale, "goto_location"), reply_markup=None)
    if await _offer_similar_before_location(callback.message, state, client, locale):
        await callback.answer()
        return
    await _prompt_location_answer(callback.message, state, locale)
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.date_confirm), F.data == "add:dateconfirm:redo")
async def add_date_confirm_redo(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    if callback.message is None:
        await callback.answer()
        return
    data = await state.get_data()
    role = str(data.get("date_confirm_role") or "")
    await state.update_data(pending_date_iso=None, date_confirm_role=None)
    if role == "start":
        await state.set_state(AddEventFSM.date_start)
        await callback.message.edit_text(t(locale, "date_prompt_short"), reply_markup=nav_only_keyboard(locale))
    elif role == "end":
        await state.set_state(AddEventFSM.date_end)
        await callback.message.edit_text(
            t(locale, "enter_end_date_cap"),
            reply_markup=nav_only_keyboard(locale),
        )
    else:
        await callback.message.edit_text(t(locale, "start_with_add"))
    await callback.answer()


@router.callback_query(
    StateFilter(AddEventFSM.similar_resolve), F.data == "add:similar:new"
)
async def similar_resolve_new(
    callback: CallbackQuery, state: FSMContext, locale: str
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    data = await state.get_data()
    resume = str(data.get("similar_resume") or "")
    await state.update_data(similar_resume=None)
    if resume == "loc":
        await _prompt_location_answer(callback.message, state, locale)
    elif resume == "name":
        await state.set_state(AddEventFSM.date_start)
        await callback.message.edit_text(
            t(locale, "date_prompt_short"), reply_markup=nav_only_keyboard(locale)
        )
    await callback.answer()


@router.callback_query(
    StateFilter(AddEventFSM.similar_resolve),
    F.data.startswith("add:similar:join:"),
)
async def similar_resolve_join(
    callback: CallbackQuery,
    state: FSMContext,
    client: ApiClient,
    locale: str,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    eid = callback.data.rsplit(":", 1)[1]
    try:
        ev = await client.get_event(eid)
    except ApiError:
        await callback.answer(t(locale, "error_generic"), show_alert=True)
        return
    await state.update_data(
        adddup_event_id=eid,
        adddup_event_name=str(ev.get("name", t(locale, "event_default"))),
        adddup_sport=str(ev.get("sport_type", "other")),
        selected_distances=[],
        similar_resume=None,
    )
    await callback.message.edit_reply_markup(reply_markup=None)
    await _start_adddup_distances(callback.message, state, client, locale)
    await callback.answer()


@router.callback_query(
    StateFilter(AddEventFSM.adddup_dist),
    F.data.startswith("adddup:dist:pick:"),
)
async def adddup_dist_pick(
    callback: CallbackQuery, state: FSMContext, locale: str
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    idx = int(callback.data.rsplit(":", 1)[1])
    data = await state.get_data()
    options: list[str] = list(data.get("adddup_dist_options") or [])
    if idx < 0 or idx >= len(options):
        await callback.answer(t(locale, "pick_error"), show_alert=True)
        return
    opt = options[idx]
    cur = list(data.get("selected_distances") or [])

    if opt == OTHER_SENTINEL:
        await state.set_state(AddEventFSM.adddup_custom)
        await callback.message.edit_text(
            t(locale, "join_ok_type_dist"), reply_markup=None
        )
        await callback.message.answer(
            t(locale, "comma_dist_hint"),
            reply_markup=distance_custom_keyboard(
                "adddup", locale, add_navigation=False
            ),
        )
        await callback.answer()
        return

    cur.append(opt)
    await state.update_data(selected_distances=cur)
    merged = {**data, "selected_distances": cur}
    opts, kb = _rebuild_adddup_keyboard(merged, locale)
    await state.update_data(adddup_dist_options=opts)
    await callback.message.edit_text(
        t(locale, "join_dist_added_pick", name=html.escape(opt)),
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(
    StateFilter(AddEventFSM.adddup_dist, AddEventFSM.adddup_custom),
    F.data == "adddup:dist:done",
)
async def adddup_dist_done(
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
    await _finalize_adddup_join(
        callback.message, state, client, callback.from_user, locale
    )


@router.message(
    StateFilter(AddEventFSM.adddup_custom), F.text, F.chat.type == ChatType.PRIVATE
)
async def adddup_dist_text(
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
    opts, kb = _rebuild_adddup_keyboard(merged, locale)
    await state.update_data(adddup_dist_options=opts)
    await state.set_state(AddEventFSM.adddup_dist)
    await message.answer(
        t(locale, "join_dist_added_more"),
        reply_markup=kb,
    )


@router.message(StateFilter(AddEventFSM.location), F.text, F.chat.type == ChatType.PRIVATE)
async def add_location(message: Message, state: FSMContext, client: ApiClient, bot: Bot, locale: str) -> None:
    await state.update_data(location=message.text.strip())
    data = await state.get_data()
    if data.get("wizard_edit"):
        await state.update_data(wizard_edit=False)
        await _goto_preview(bot, message.chat.id, message, state, locale)
        return
    await _start_distances_for_add(message, state, client, locale)


def _rebuild_dist_keyboard(
    data: dict, locale: str
) -> tuple[list[str], InlineKeyboardMarkup]:
    presets: list[str] = list(data.get("add_all_presets") or [])
    selected: list[str] = list(data.get("selected_distances") or [])
    opts = build_distance_options(presets, selected)
    show_done = len(selected) > 0
    return opts, distance_pick_keyboard(
        "add", opts, locale, show_done=show_done, add_navigation=True
    )


@router.callback_query(
    StateFilter(AddEventFSM.distances),
    F.data.startswith("add:dist:pick:"),
)
async def add_dist_pick(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    idx = int(callback.data.rsplit(":", 1)[1])
    data = await state.get_data()
    options: list[str] = list(data.get("add_dist_options") or [])
    if idx < 0 or idx >= len(options):
        await callback.answer(t(locale, "pick_error"), show_alert=True)
        return
    opt = options[idx]
    cur = list(data.get("selected_distances") or [])

    if opt == OTHER_SENTINEL:
        await state.set_state(AddEventFSM.distance_custom)
        await callback.message.edit_text(t(locale, "ok_type_distance"), reply_markup=None)
        await callback.message.answer(
            t(locale, "comma_dist_hint"),
            reply_markup=distance_custom_keyboard("add", locale, add_navigation=True),
        )
        await callback.answer()
        return

    cur.append(opt)
    await state.update_data(selected_distances=cur)
    opts, kb = _rebuild_dist_keyboard({**data, "selected_distances": cur}, locale)
    await state.update_data(add_dist_options=opts)
    await callback.message.edit_text(
        t(locale, "dist_added_line", name=html.escape(opt)),
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(
    StateFilter(AddEventFSM.distances, AddEventFSM.distance_custom),
    F.data == "add:dist:done",
)
async def add_dist_done(callback: CallbackQuery, state: FSMContext, bot: Bot, locale: str) -> None:
    if callback.message is None:
        await callback.answer()
        return
    data = await state.get_data()
    cur = list(data.get("selected_distances") or [])
    if not cur:
        await callback.answer(t(locale, "pick_distances_first"), show_alert=True)
        return
    await state.update_data(distances=cur)
    if data.get("wizard_edit"):
        await state.update_data(wizard_edit=False)
        await _goto_preview(bot, callback.message.chat.id, callback.message, state, locale)
        await callback.answer()
        return
    await state.set_state(AddEventFSM.url)
    await callback.message.edit_text(t(locale, "dist_saved"), reply_markup=None)
    await callback.message.answer(
        t(locale, "enter_link"),
        reply_markup=skip_url_keyboard(locale),
    )
    await callback.answer()


@router.message(StateFilter(AddEventFSM.distance_custom), F.text, F.chat.type == ChatType.PRIVATE)
async def add_dist_text(message: Message, state: FSMContext, locale: str) -> None:
    raw = (message.text or "").strip()
    parts = [p.strip() for p in raw.replace("\n", ",").split(",") if p.strip()]
    data = await state.get_data()
    cur = list(data.get("selected_distances") or [])
    cur.extend(parts)
    await state.update_data(selected_distances=cur)
    opts, kb = _rebuild_dist_keyboard({**data, "selected_distances": cur}, locale)
    await state.update_data(add_dist_options=opts)
    await state.set_state(AddEventFSM.distances)
    await message.answer(
        t(locale, "dist_added_short"),
        reply_markup=kb,
    )


@router.callback_query(StateFilter(AddEventFSM.extra_ask), F.data.startswith("add:extra:"))
async def add_extra_ask(callback: CallbackQuery, state: FSMContext, bot: Bot, locale: str) -> None:
    choice = callback.data.rsplit(":", 1)[1]
    data = await state.get_data()
    if choice == "yes":
        await state.update_data(extra_names=[])
        await state.set_state(AddEventFSM.extra_name)
        await callback.message.edit_text(
            t(locale, "enter_participant_name"),
            reply_markup=nav_only_keyboard(locale),
        )
    else:
        if data.get("wizard_edit"):
            await state.update_data(wizard_edit=False)
            await _goto_preview(bot, callback.message.chat.id, callback.message, state, locale)
            await callback.answer()
            return
        await state.update_data(extra_names=list(data.get("extra_names") or []))
        await state.set_state(AddEventFSM.notes)
        await callback.message.edit_text(
            t(locale, "enter_notes"),
            reply_markup=skip_notes_keyboard(locale),
        )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.extra_name), F.data == "add:extra:more")
async def add_extra_more_cb(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await callback.message.edit_text(
        t(locale, "enter_participant_name"),
        reply_markup=nav_only_keyboard(locale),
    )
    await callback.answer()


@router.message(StateFilter(AddEventFSM.extra_name), F.text, F.chat.type == ChatType.PRIVATE)
async def add_extra_name(message: Message, state: FSMContext, locale: str) -> None:
    data = await state.get_data()
    ret_ex = bool(data.get("extras_manage_return"))
    names = list(data.get("extra_names") or [])
    names.append(message.text.strip())
    await state.update_data(extra_names=names, extras_manage_return=False)
    if ret_ex:
        await state.set_state(AddEventFSM.extras_manage)
        await message.answer(
            _extras_manage_text(names, locale),
            parse_mode="HTML",
            reply_markup=extras_manage_reply_keyboard(names, locale),
        )
        return
    await message.answer(
        t(locale, "participant_added_more"),
        reply_markup=extra_participants_more_keyboard(locale),
    )


@router.callback_query(StateFilter(AddEventFSM.extras_manage), F.data == "add:exback")
async def extras_back_to_preview(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    locale: str) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await state.update_data(wizard_edit=False)
    await _goto_preview(bot, callback.message.chat.id, callback.message, state, locale)
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.extras_manage), F.data == "add:exadd")
async def extras_add_start(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await state.update_data(extras_manage_return=True)
    await state.set_state(AddEventFSM.extra_name)
    await callback.message.answer(
        t(locale, "enter_participant_name"),
        reply_markup=nav_only_keyboard(locale),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.extras_manage), F.data.startswith("add:exrm:"))
async def extras_ask_remove(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    i = int(callback.data.rsplit(":", 1)[1])
    data = await state.get_data()
    names = list(data.get("extra_names") or [])
    if i < 0 or i >= len(names):
        await callback.answer()
        return
    nm = names[i]
    await callback.message.edit_text(
        t(locale, "remove_confirm", name=html.escape(nm)),
        parse_mode="HTML",
        reply_markup=extras_remove_confirm_keyboard(i, locale),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.extras_manage), F.data == "add:excn")
async def extras_remove_cancel(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    if callback.message is None:
        await callback.answer()
        return
    data = await state.get_data()
    names = list(data.get("extra_names") or [])
    await callback.message.edit_text(
        _extras_manage_text(names, locale),
        parse_mode="HTML",
        reply_markup=extras_manage_reply_keyboard(names, locale),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.extras_manage), F.data.startswith("add:exdel:"))
async def extras_remove_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    locale: str) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    i = int(callback.data.rsplit(":", 1)[1])
    data = await state.get_data()
    names = list(data.get("extra_names") or [])
    if i < 0 or i >= len(names):
        await callback.answer()
        return
    names.pop(i)
    await state.update_data(extra_names=names)
    await callback.message.edit_text(
        _extras_manage_text(names, locale),
        parse_mode="HTML",
        reply_markup=extras_manage_reply_keyboard(names, locale),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.extra_name), F.data == "add:extra:done")
async def add_extra_done_cb(callback: CallbackQuery, state: FSMContext, bot: Bot, locale: str) -> None:
    data = await state.get_data()
    if data.get("wizard_edit"):
        await state.update_data(wizard_edit=False)
        await _goto_preview(bot, callback.message.chat.id, callback.message, state, locale)
        await callback.answer()
        return
    await state.set_state(AddEventFSM.notes)
    await callback.message.edit_text(
        t(locale, "enter_notes"),
        reply_markup=skip_notes_keyboard(locale),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.notes), F.data == "add:notes:skip")
async def add_notes_skip(callback: CallbackQuery, state: FSMContext, bot: Bot, locale: str) -> None:
    await state.update_data(notes=None)
    data = await state.get_data()
    if data.get("wizard_edit"):
        await state.update_data(wizard_edit=False)
    await _goto_preview(bot, callback.message.chat.id, callback.message, state, locale)
    await callback.answer()


@router.message(StateFilter(AddEventFSM.notes), F.text, F.chat.type == ChatType.PRIVATE)
async def add_notes_text(message: Message, state: FSMContext, bot: Bot, locale: str) -> None:
    await state.update_data(notes=message.text.strip())
    data = await state.get_data()
    if data.get("wizard_edit"):
        await state.update_data(wizard_edit=False)
    await _goto_preview(bot, message.chat.id, message, state, locale)


async def _add_save_commit(
    callback: CallbackQuery,
    state: FSMContext,
    client: ApiClient,
    locale: str,
    *,
    force_duplicate: bool = False,
) -> None:
    if callback.from_user is None or callback.message is None:
        return
    data = await state.get_data()
    try:
        author = await client.create_participant(
            {
                "display_name": (
                    callback.from_user.full_name or t(locale, "participant_default")
                ).strip(),
                "telegram_id": callback.from_user.id,
                "telegram_username": callback.from_user.username,
            }
        )
        ids: list = [author["id"]]
        for name in data.get("extra_names") or []:
            nm = str(name).strip()
            if not nm:
                continue
            p = await client.create_participant(
                {
                    "display_name": nm,
                    "telegram_id": None,
                    "telegram_username": None,
                }
            )
            ids.append(p["id"])

        payload = {
            "name": data["name"],
            "date_start": data["date_start"],
            "date_end": data.get("date_end"),
            "location": data["location"],
            "sport_type": data["sport_type"],
            "url": data.get("url"),
            "notes": data.get("notes"),
            "created_by": user_created_by(callback.from_user, locale),
        }
        tgid = data.get("target_group_id")
        if tgid:
            payload["group_id"] = str(tgid)
        ev = await client.create_event(payload, force_duplicate=force_duplicate)
        eid = ev["id"]
        dists = list(data.get("distances") or [])
        for pid in ids:
            await client.create_registration(
                {
                    "event_id": eid,
                    "participant_id": pid,
                    "distances": dists,
                }
            )
    except ApiError as e:
        pl = e.payload if isinstance(e.payload, dict) else {}
        if (
            not force_duplicate
            and e.status == 409
            and pl.get("detail") == "duplicate_event"
        ):
            eid409 = str(pl.get("existing_event_id") or "")
            await callback.message.answer(
                t(locale, "dup409_prompt"),
                reply_markup=duplicate_save_keyboard(eid409, locale),
            )
            return
        log.exception("add_save API")
        await callback.message.answer(generic_api_error(locale))
        return
    except Exception:
        log.exception("add_save")
        await callback.message.answer(generic_api_error(locale))
        return

    await state.clear()
    await callback.message.edit_text(t(locale, "event_saved"))


@router.callback_query(StateFilter(AddEventFSM.preview), F.data == "add:save")
async def add_save(
    callback: CallbackQuery, state: FSMContext, client: ApiClient, locale: str
) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return
    await _add_save_commit(
        callback, state, client, locale, force_duplicate=False
    )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.preview), F.data == "add:dup409:force")
async def add_dup409_force(
    callback: CallbackQuery, state: FSMContext, client: ApiClient, locale: str
) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return
    await _add_save_commit(
        callback, state, client, locale, force_duplicate=True
    )
    await callback.answer()


@router.callback_query(
    StateFilter(AddEventFSM.preview), F.data.startswith("add:dup409:join:")
)
async def add_dup409_join(
    callback: CallbackQuery, state: FSMContext, client: ApiClient, locale: str
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    eid = callback.data.rsplit(":", 1)[1]
    try:
        ev = await client.get_event(eid)
    except ApiError:
        await callback.answer(t(locale, "error_generic"), show_alert=True)
        return
    await state.update_data(
        adddup_event_id=eid,
        adddup_event_name=str(ev.get("name", t(locale, "event_default"))),
        adddup_sport=str(ev.get("sport_type", "other")),
        selected_distances=[],
    )
    await _start_adddup_distances(callback.message, state, client, locale)
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.preview), F.data == "add:edit:menu")
async def add_edit_menu(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    if callback.message:
        await callback.message.edit_text(
            t(locale, "what_to_change"),
            reply_markup=edit_menu_keyboard(locale),
        )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.preview), F.data == "add:edit:back")
async def add_edit_back(callback: CallbackQuery, state: FSMContext, bot: Bot, locale: str) -> None:
    data = await state.get_data()
    text = build_preview_text(data, locale)
    if callback.message:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=preview_keyboard(locale),
        )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.preview), F.data == "add:edit:sport")
async def add_edit_sport(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await state.update_data(wizard_edit=True)
    data = await state.get_data()
    sp = str(data.get("sport_type") or "")
    cur = sport_title_line(sp, locale)
    await state.set_state(AddEventFSM.sport)
    await callback.message.answer(
        t(locale, "current_sport_pick", cur=html.escape(cur)),
        parse_mode="HTML",
        reply_markup=sport_type_keyboard("add", locale),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.preview), F.data == "add:edit:name")
async def add_edit_name(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await state.update_data(wizard_edit=True)
    raw_nm = (await state.get_data()).get("name")
    nm = html.escape(str(raw_nm)) if raw_nm else t(locale, "dash")
    await state.set_state(AddEventFSM.name)
    await callback.message.answer(
        t(locale, "current_name_enter", nm=nm),
        parse_mode="HTML",
        reply_markup=nav_only_keyboard(locale),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.preview), F.data == "add:edit:dates")
async def add_edit_dates(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await state.update_data(edit_dates_mode=True)
    data = await state.get_data()
    ds = data.get("date_start", "")
    de = data.get("date_end")
    cur_d = _format_date_range_for_edit(ds, de, locale)
    await state.set_state(AddEventFSM.date_start)
    await callback.message.answer(
        t(
            locale,
            "current_date_enter",
            d=html.escape(cur_d),
            prompt=t(locale, "date_prompt_short"),
        ),
        parse_mode="HTML",
        reply_markup=nav_only_keyboard(locale),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.preview), F.data == "add:edit:loc")
async def add_edit_loc(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await state.update_data(wizard_edit=True)
    await _prompt_location_answer(callback.message, state, locale)
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.preview), F.data == "add:edit:dist")
async def add_edit_dist(callback: CallbackQuery, state: FSMContext, client: ApiClient, locale: str) -> None:
    data = await state.get_data()
    dists = ", ".join(str(x) for x in (data.get("distances") or [])) or t(locale, "dash")
    await state.update_data(
        wizard_edit=True,
        selected_distances=list(data.get("distances") or []),
    )
    await callback.message.answer(
        t(locale, "current_dists", dists=html.escape(dists)),
        parse_mode="HTML",
    )
    await _start_distances_for_add(callback.message, state, client, locale)
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.preview), F.data == "add:edit:url")
async def add_edit_url(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await state.update_data(wizard_edit=True)
    u = (await state.get_data()).get("url")
    cur = html.escape(str(u).strip()) if u else html.escape(t(locale, "url_not_set"))
    await state.set_state(AddEventFSM.url)
    await callback.message.answer(
        t(locale, "current_url_enter", cur=cur),
        parse_mode="HTML",
        reply_markup=skip_url_keyboard(locale),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.preview), F.data == "add:edit:extras")
async def add_edit_extras(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await state.update_data(wizard_edit=True)
    names = list((await state.get_data()).get("extra_names") or [])
    await state.set_state(AddEventFSM.extras_manage)
    await callback.message.answer(
        _extras_manage_text(names, locale),
        parse_mode="HTML",
        reply_markup=extras_manage_reply_keyboard(names, locale),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.preview), F.data == "add:edit:notes")
async def add_edit_notes(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await state.update_data(wizard_edit=True)
    nt = (await state.get_data()).get("notes")
    cur = html.escape(str(nt).strip()) if nt else html.escape(t(locale, "notes_not_set"))
    await state.set_state(AddEventFSM.notes)
    await callback.message.answer(
        t(locale, "current_notes_enter", cur=cur),
        parse_mode="HTML",
        reply_markup=skip_notes_keyboard(locale),
    )
    await callback.answer()


@router.callback_query(StateFilter(AddEventFSM.url), F.data == "add:url:skip")
async def add_url_skip(callback: CallbackQuery, state: FSMContext, bot: Bot, locale: str) -> None:
    await state.update_data(url=None)
    data = await state.get_data()
    if data.get("wizard_edit"):
        await state.update_data(wizard_edit=False)
        await _goto_preview(bot, callback.message.chat.id, callback.message, state, locale)
        await callback.answer()
        return
    await state.set_state(AddEventFSM.extra_ask)
    await callback.message.edit_text(
        t(locale, "extra_ask"),
        reply_markup=yes_no_keyboard("add:extra", locale),
    )
    await callback.answer()


@router.message(StateFilter(AddEventFSM.url), F.text, F.chat.type == ChatType.PRIVATE)
async def add_url_text(message: Message, state: FSMContext, bot: Bot, locale: str) -> None:
    raw = (message.text or "").strip()
    if raw and not re.match(r"^https?://", raw, re.I):
        raw = "https://" + raw
    await state.update_data(url=raw or None)
    data = await state.get_data()
    if data.get("wizard_edit"):
        await state.update_data(wizard_edit=False)
        await _goto_preview(bot, message.chat.id, message, state, locale)
        return
    await state.set_state(AddEventFSM.extra_ask)
    await message.answer(
        t(locale, "extra_ask"),
        reply_markup=yes_no_keyboard("add:extra", locale),
    )


@router.message(StateFilter(None), AddStartPhrase())
async def add_phrase_start(message: Message, state: FSMContext, client: ApiClient, locale: str) -> None:
    await _begin_add_private_flow(message, state, client, locale)
