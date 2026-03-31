"""Параметры API для фильтрации стартов по группе или личке пользователя."""

from __future__ import annotations

from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Message


def merge_events_params(
    base: dict,
    chat,
    *,
    hub_group_id: str | None,
    from_user_id: int | None,
) -> dict:
    p = {**base}
    if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        if hub_group_id:
            p["group_id"] = hub_group_id
    elif from_user_id is not None:
        p["for_telegram_id"] = from_user_id
    return p


def merge_community_stats_params(
    chat,
    *,
    hub_group_id: str | None,
    from_user_id: int | None,
) -> dict:
    if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP) and hub_group_id:
        return {"group_id": hub_group_id}
    if from_user_id is not None:
        return {"for_telegram_id": from_user_id}
    return {}


def params_for_message(message: Message, base: dict, hub_group_id: str | None) -> dict:
    uid = message.from_user.id if message.from_user else None
    return merge_events_params(base, message.chat, hub_group_id=hub_group_id, from_user_id=uid)


def params_for_callback_query(
    callback: CallbackQuery, base: dict, hub_group_id: str | None
) -> dict:
    if callback.message is None:
        return {**base}
    uid = callback.from_user.id if callback.from_user else None
    return merge_events_params(
        base, callback.message.chat, hub_group_id=hub_group_id, from_user_id=uid
    )


def stats_params_for_callback(
    callback: CallbackQuery, hub_group_id: str | None
) -> dict:
    if callback.message is None:
        return {}
    uid = callback.from_user.id if callback.from_user else None
    return merge_community_stats_params(
        callback.message.chat, hub_group_id=hub_group_id, from_user_id=uid
    )
