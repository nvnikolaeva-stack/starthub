"""Команда /lang — выбор языка бота (RU/EN)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from translations import set_user_locale, t, user_locale

router = Router(name="lang")


def _lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇷🇺 Русский", callback_data="lang:set:ru"
                ),
                InlineKeyboardButton(
                    text="🇬🇧 English", callback_data="lang:set:en"
                ),
            ],
        ]
    )


@router.message(Command("lang"))
async def cmd_lang(message: Message, locale: str) -> None:
    await message.answer(t(locale, "lang_choose"), reply_markup=_lang_keyboard())


@router.callback_query(F.data.startswith("lang:set:"))
async def cb_lang_set(callback: CallbackQuery) -> None:
    if callback.data is None or callback.from_user is None:
        await callback.answer()
        return
    lang = callback.data.rsplit(":", 1)[1]
    if lang not in ("ru", "en"):
        await callback.answer()
        return
    set_user_locale(callback.from_user.id, lang)
    loc = user_locale(callback.from_user.id, callback.from_user.language_code)
    await callback.message.edit_text(
        t(loc, "lang_set_ru" if lang == "ru" else "lang_set_en"),
        reply_markup=None,
    )
    await callback.answer()
