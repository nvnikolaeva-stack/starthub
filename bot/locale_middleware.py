"""Пробрасывает locale (ru|en) в data для инъекции в хэндлеры."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from translations import user_locale


class LocaleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        uid: int | None = None
        lang_code: str | None = None
        if isinstance(event, Message) and event.from_user:
            uid = event.from_user.id
            lang_code = event.from_user.language_code
        elif isinstance(event, CallbackQuery) and event.from_user:
            uid = event.from_user.id
            lang_code = event.from_user.language_code
        data["locale"] = user_locale(uid, lang_code)
        return await handler(event, data)
