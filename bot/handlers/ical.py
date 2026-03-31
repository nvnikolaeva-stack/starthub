from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, Message

from api_client import ApiClient, ApiError
from keyboards import upcoming_events_pick_keyboard
from translations import t
from utils import api_error_user

router = Router(name="ical")
log = logging.getLogger(__name__)

LIST_PARAMS = {"upcoming": "true", "limit": 5, "period": "all"}


@router.message(Command("ical"))
async def cmd_ical(
    message: Message, state: FSMContext, client: ApiClient, locale: str
) -> None:
    await state.clear()
    try:
        events = await client.get_events(LIST_PARAMS)
    except ApiError:
        log.exception("ical list")
        await message.answer(api_error_user(locale))
        return
    if not events:
        await message.answer(t(locale, "ical_no_events"))
        return
    extra = [
        [
            InlineKeyboardButton(
                text=t(locale, "ical_all_my"),
                callback_data="ical:all",
            )
        ]
    ]
    await message.answer(
        t(locale, "ical_pick"),
        reply_markup=upcoming_events_pick_keyboard(
            events, "ical", locale, extra_rows=extra
        ),
    )


@router.callback_query(F.data == "ical:cancel")
async def ical_cancel(callback: CallbackQuery, state: FSMContext, locale: str) -> None:
    await state.clear()
    if callback.message:
        await callback.message.edit_text(t(locale, "canceled"), reply_markup=None)
    await callback.answer()


@router.callback_query(F.data.startswith("ical:pick:"))
async def ical_pick(
    callback: CallbackQuery,
    state: FSMContext,
    client: ApiClient,
    bot: Bot,
    locale: str,
) -> None:
    if callback.message is None or callback.from_user is None or callback.data is None:
        await callback.answer()
        return
    eid = callback.data.split(":", 2)[2]
    await callback.message.edit_text(t(locale, "ical_uploading"), reply_markup=None)
    try:
        data, filename = await client.get_event_ical_bytes(eid)
        ev = await client.get_event(eid)
    except ApiError:
        await callback.message.edit_text(api_error_user(locale))
        await callback.answer()
        return
    fn = filename or f"alkardio-{eid}.ics"
    doc = BufferedInputFile(data, filename=fn)
    await bot.send_document(
        callback.message.chat.id,
        document=doc,
        caption=t(locale, "ical_caption"),
    )
    url = (ev.get("url") or "").strip()
    if url:
        await bot.send_message(
            callback.message.chat.id, t(locale, "ical_event_url", url=url)
        )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "ical:all")
async def ical_all(
    callback: CallbackQuery,
    state: FSMContext,
    client: ApiClient,
    bot: Bot,
    locale: str,
) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    await callback.message.edit_text(t(locale, "ical_all_building"), reply_markup=None)
    try:
        data, filename = await client.get_my_ical_bytes(callback.from_user.id)
    except ApiError as e:
        if e.status == 404:
            await callback.message.edit_text(t(locale, "ical_no_profile"))
        else:
            await callback.message.edit_text(api_error_user(locale))
        await callback.answer()
        return
    fn = filename or "alkardio-my-starts.ics"
    doc = BufferedInputFile(data, filename=fn)
    await bot.send_document(
        callback.message.chat.id,
        document=doc,
        caption=t(locale, "ical_all_caption"),
    )
    await state.clear()
    await callback.answer()
