from __future__ import annotations

import logging

from api_client import ApiClient, ApiError

log = logging.getLogger(__name__)


class GroupManager:
    def __init__(self, api_client: ApiClient) -> None:
        self.api_client = api_client
        self._cache: dict[int, str] = {}

    async def get_group_id(self, chat_id: int, chat_name: str | None = None) -> str:
        if chat_id in self._cache:
            return self._cache[chat_id]
        try:
            group = await self.api_client.get_group_by_telegram(chat_id)
        except ApiError:
            log.exception("get_group_by_telegram %s", chat_id)
            raise
        if not group:
            group = await self.api_client.create_group(chat_id, chat_name)
        gid = str(group["id"])
        self._cache[chat_id] = gid
        return gid

    def forget_chat(self, chat_id: int) -> None:
        self._cache.pop(chat_id, None)
