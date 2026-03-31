from __future__ import annotations

import html
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api_client import ApiClient, ApiError
from keyboards import delete_confirm_keyboard, upcoming_events_pick_keyboard
from scope import params_for_message
from translations import t
from utils import api_error_user

router = Router(name="delete_event")
log = logging.getLogger(__name__)

LIST_PARAMS = {"upcoming": "true", "limit": 5, "period": "all"}


@router.message(Command("delete"))
async def cmd_delete(
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
        log.exception("delete list")
        await message.answer(api_error_user(locale))
        return
    if not events:
        await message.answer(t(locale, "delete_no_events"))
        return
    await message.answer(
        t(locale, "delete_which"),
        reply_markup=upcoming_events_pick_keyboard(events, "del", locale),
    )


@router.callback_query(F.data == "del:cancel")
async def del_cancel(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await state.clear()
    if callback.message:
        await callback.message.edit_text(t(locale, "canceled"), reply_markup=None)
    await callback.answer()


@router.callback_query(F.data.startswith("del:pick:"))
async def del_pick(
    callback: CallbackQuery, client: ApiClient, locale: str
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    eid = callback.data.split(":", 2)[2]
    try:
        detail = await client.get_event(eid)
    except ApiError:
        await callback.answer(api_error_user(locale), show_alert=True)
        return
    cnt = len(detail.get("registrations") or [])
    title = str(detail.get("name", t(locale, "event_default")))
    text = t(
        locale,
        "delete_warn",
        title=html.escape(title),
        count=cnt,
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=delete_confirm_keyboard(eid, locale),
    )
    await callback.answer()


@router.callback_query(F.data == "del:no")
async def del_no(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await state.clear()
    if callback.message:
        await callback.message.edit_text(
            t(locale, "delete_canceled"), reply_markup=None
        )
    await callback.answer()


@router.callback_query(F.data.startswith("del:yes:"))
async def del_yes(
    callback: CallbackQuery, state: FSMContext, client: ApiClient, locale: str
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    eid = callback.data.split(":", 2)[2]
    await state.clear()
    try:
        await client.delete_event(eid)
    except ApiError:
        await callback.message.edit_text(api_error_user(locale), reply_markup=None)
        await callback.answer()
        return
    await callback.message.edit_text(t(locale, "event_deleted"), reply_markup=None)
    await callback.answer()
