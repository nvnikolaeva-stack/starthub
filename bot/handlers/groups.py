"""Регистрация группы в API, когда бота добавили в чат."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.enums import ChatType
from aiogram.types import ChatMemberUpdated

from group_manager import GroupManager

router = Router(name="groups")
log = logging.getLogger(__name__)


@router.my_chat_member()
async def on_bot_chat_member(event: ChatMemberUpdated, group_manager: GroupManager) -> None:
    chat = event.chat
    if not chat or chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return
    new = event.new_chat_member
    if new.status not in ("member", "administrator", "creator"):
        return
    try:
        await group_manager.get_group_id(chat.id, chat.title)
    except Exception:
        log.exception("on_bot_chat_member: register group %s", chat.id)
