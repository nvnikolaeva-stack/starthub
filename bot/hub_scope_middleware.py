from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Message, TelegramObject

from api_client import ApiClient, ApiError
from group_manager import GroupManager
from translations import t, user_locale

log = logging.getLogger(__name__)


class HubScopeMiddleware(BaseMiddleware):
    """Регистрирует группу и привязывает участника; пробрасывает hub_group_id в хэндлеры."""

    def __init__(self, group_manager: GroupManager, api_client: ApiClient) -> None:
        super().__init__()
        self.group_manager = group_manager
        self.api_client = api_client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        hub_group_id: str | None = None
        msg: Message | None = None
        if isinstance(event, Message):
            msg = event
        elif isinstance(event, CallbackQuery) and event.message:
            msg = event.message

        if msg and msg.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
            try:
                hub_group_id = await self.group_manager.get_group_id(
                    msg.chat.id, msg.chat.title
                )
            except ApiError:
                log.exception("HubScope: get_group_id")
            if (
                hub_group_id
                and msg.from_user
                and not msg.from_user.is_bot
            ):
                try:
                    await self.api_client.ensure_group_member(
                        hub_group_id,
                        telegram_id=msg.from_user.id,
                        display_name=(
                            msg.from_user.full_name
                            or t(
                                user_locale(
                                    msg.from_user.id,
                                    msg.from_user.language_code,
                                ),
                                "participant_default",
                            )
                        ).strip(),
                        telegram_username=msg.from_user.username,
                    )
                except ApiError:
                    log.warning("ensure_group_member failed for chat %s", msg.chat.id)

        data["hub_group_id"] = hub_group_id
        return await handler(event, data)
