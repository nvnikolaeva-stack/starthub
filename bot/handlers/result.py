from __future__ import annotations

import html
import logging
from datetime import date

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from api_client import ApiClient, ApiError
from keyboards import result_preview_keyboard, result_skip_place_keyboard
from translations import t
from utils import api_error_user, sport_line_emoji

router = Router(name="result")
log = logging.getLogger(__name__)


class ResultFSM(StatesGroup):
    pick_distance = State()
    enter_time = State()
    enter_place = State()
    preview = State()


def _past_entries(participant: dict) -> list[dict]:
    today = date.today()
    out: list[dict] = []
    for e in participant.get("events") or []:
        try:
            ds = e.get("date_start", "")
            if isinstance(ds, str):
                d = date.fromisoformat(ds[:10])
            else:
                continue
        except ValueError:
            continue
        if d <= today:
            out.append(e)
    out.sort(key=lambda x: str(x.get("date_start", "")), reverse=True)
    return out


def _result_events_keyboard(entries: list[dict], locale: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for e in entries[:15]:
        eid = str(e.get("event_id", ""))
        emo = sport_line_emoji(str(e.get("sport_type", "")))
        title = str(e.get("event_name", t(locale, "event_default")))[:28]
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{emo} {title}",
                    callback_data=f"res:ev:{eid}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=t(locale, "nav_cancel"), callback_data="res:cancel"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _dist_pick_keyboard(distances: list[str], locale: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for i, d in enumerate(distances):
        label = str(d)[:40]
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"res:didx:{i}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=t(locale, "nav_cancel"), callback_data="res:cancel"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("result"))
async def cmd_result(
    message: Message, state: FSMContext, client: ApiClient, locale: str
) -> None:
    await state.clear()
    if message.from_user is None:
        return
    try:
        p = await client.get_participant_by_telegram(message.from_user.id)
    except ApiError as e:
        if e.status == 404:
            await message.answer(t(locale, "result_no_past"))
            return
        await message.answer(api_error_user(locale))
        return
    try:
        detail = await client.get_participant_detail(str(p["id"]))
    except ApiError:
        await message.answer(api_error_user(locale))
        return
    past = _past_entries(detail)
    if not past:
        await message.answer(t(locale, "result_no_past"))
        return
    await message.answer(
        t(locale, "result_pick_event"),
        reply_markup=_result_events_keyboard(past, locale),
    )


@router.callback_query(F.data == "res:cancel")
async def res_cancel(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await state.clear()
    if callback.message:
        await callback.message.edit_text(t(locale, "canceled"), reply_markup=None)
    await callback.answer()


@router.callback_query(F.data.startswith("res:ev:"))
async def res_pick_event(
    callback: CallbackQuery, state: FSMContext, client: ApiClient, locale: str
) -> None:
    if callback.message is None or callback.from_user is None or callback.data is None:
        await callback.answer()
        return
    eid = callback.data.split(":", 2)[2]
    try:
        p = await client.get_participant_by_telegram(callback.from_user.id)
        detail = await client.get_participant_detail(str(p["id"]))
    except ApiError:
        await callback.answer(api_error_user(locale), show_alert=True)
        return
    reg = next(
        (x for x in (detail.get("events") or []) if str(x.get("event_id")) == eid),
        None,
    )
    if not reg:
        await callback.answer(t(locale, "result_reg_missing"), show_alert=True)
        return
    rid = str(reg["registration_id"])
    dists = list(reg.get("distances") or [])
    ename = str(reg.get("event_name", t(locale, "event_default")))
    await state.update_data(
        res_event_id=eid,
        res_registration_id=rid,
        res_event_name=ename,
        res_distances=dists,
        res_distance_label=dists[0] if len(dists) == 1 else None,
    )
    if len(dists) > 1:
        await state.set_state(ResultFSM.pick_distance)
        await callback.message.edit_text(
            t(locale, "result_which_distance"),
            reply_markup=_dist_pick_keyboard(dists, locale),
        )
    else:
        await state.set_state(ResultFSM.enter_time)
        lab = dists[0] if dists else t(locale, "dash")
        await callback.message.edit_text(
            t(locale, "result_header_dist", name=html.escape(ename), dist=html.escape(str(lab)))
            + t(locale, "result_time_prompt"),
            reply_markup=None,
        )
    await callback.answer()


@router.callback_query(StateFilter(ResultFSM.pick_distance), F.data.startswith("res:didx:"))
async def res_pick_dist(
    callback: CallbackQuery, state: FSMContext, locale: str
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    idx = int(callback.data.rsplit(":", 1)[1])
    data = await state.get_data()
    dists = list(data.get("res_distances") or [])
    if idx < 0 or idx >= len(dists):
        await callback.answer(t(locale, "result_bad_pick"), show_alert=True)
        return
    label = str(dists[idx])
    ename = str(data.get("res_event_name", ""))
    await state.update_data(res_distance_label=label)
    await state.set_state(ResultFSM.enter_time)
    await callback.message.edit_text(
        t(locale, "result_header_dist", name=html.escape(ename), dist=html.escape(label))
        + t(locale, "result_time_prompt"),
        reply_markup=None,
    )
    await callback.answer()


@router.message(StateFilter(ResultFSM.enter_time), F.text)
async def res_time_msg(message: Message, state: FSMContext, locale: str) -> None:
    text_raw = (message.text or "").strip()
    if not text_raw:
        return
    await state.update_data(res_time=text_raw)
    await state.set_state(ResultFSM.enter_place)
    await message.answer(
        t(locale, "result_place_prompt"),
        reply_markup=result_skip_place_keyboard(locale),
    )


@router.callback_query(StateFilter(ResultFSM.enter_place), F.data == "res:place:skip")
async def res_place_skip(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await state.update_data(res_place=None)
    if callback.message:
        await _show_preview(callback.message, state, locale, from_callback=True)
    await callback.answer()


@router.message(StateFilter(ResultFSM.enter_place), F.text)
async def res_place_msg(message: Message, state: FSMContext, locale: str) -> None:
    await state.update_data(res_place=(message.text or "").strip() or None)
    await _show_preview(message, state, locale, from_callback=False)


async def _show_preview(
    message: Message, state: FSMContext, locale: str, *, from_callback: bool
) -> None:
    data = await state.get_data()
    ename = str(data.get("res_event_name", ""))
    dist = str(data.get("res_distance_label") or t(locale, "dash"))
    tm = str(data.get("res_time", ""))
    pl = data.get("res_place")
    pls = str(pl) if pl else t(locale, "dash")
    text = t(
        locale,
        "result_block",
        name=html.escape(ename),
        dist=html.escape(dist),
        time=html.escape(tm),
        place=html.escape(pls),
    )
    await state.set_state(ResultFSM.preview)
    if from_callback:
        await message.edit_text(
            text, parse_mode="HTML", reply_markup=result_preview_keyboard(locale)
        )
    else:
        await message.answer(
            text, parse_mode="HTML", reply_markup=result_preview_keyboard(locale)
        )


@router.callback_query(StateFilter(ResultFSM.preview), F.data == "res:redo")
async def res_redo(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await state.set_state(ResultFSM.enter_time)
    data = await state.get_data()
    ename = str(data.get("res_event_name", ""))
    dist = str(data.get("res_distance_label") or t(locale, "dash"))
    await callback.message.edit_text(
        t(locale, "result_header_dist", name=html.escape(ename), dist=html.escape(dist))
        + t(locale, "result_time_short"),
        reply_markup=None,
    )
    await callback.answer()


@router.callback_query(StateFilter(ResultFSM.preview), F.data == "res:save")
async def res_save(
    callback: CallbackQuery,
    state: FSMContext,
    client: ApiClient,
    locale: str,
) -> None:
    if callback.message is None:
        await callback.answer()
        return
    data = await state.get_data()
    rid = str(data.get("res_registration_id") or "")
    if not rid:
        await callback.answer(t(locale, "result_session_error"), show_alert=True)
        return
    body = {
        "result_time": str(data.get("res_time") or ""),
        "result_place": data.get("res_place"),
    }
    try:
        await client.update_registration(rid, body)
    except ApiError:
        await callback.answer(api_error_user(locale), show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        t(locale, "result_saved_ok"),
        reply_markup=None,
    )
    await callback.answer()
