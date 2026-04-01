from __future__ import annotations

import json
from typing import Any

import aiohttp


class ApiError(Exception):
    def __init__(self, status: int, detail: str, payload: Any | None = None):
        self.status = status
        self.detail = detail
        self.payload = payload
        super().__init__(f"API {status}: {detail}")


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self._base = base_url.rstrip("/")
        self._session: aiohttp.ClientSession | None = None

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None

    async def _session_get(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(base_url=self._base, timeout=timeout)
        return self._session

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        session = await self._session_get()
        kwargs: dict[str, Any] = {}
        if params is not None:
            kwargs["params"] = params
        if json_body is not None:
            kwargs["json"] = json_body
        hdrs = dict(headers) if headers else None
        async with session.request(method, path, headers=hdrs, **kwargs) as resp:
            text = await resp.text()
            if resp.status >= 400:
                payload: Any = None
                if text:
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        pass
                raise ApiError(resp.status, text or resp.reason, payload)
            if not text.strip():
                return None
            ctype = resp.headers.get("Content-Type", "")
            if "application/json" in ctype:
                return json.loads(text)
            return text

    async def create_event(
        self, data: dict[str, Any], *, force_duplicate: bool = False
    ) -> dict[str, Any]:
        headers = {"X-Force-Create": "true"} if force_duplicate else None
        return await self._request(
            "POST", "/api/v1/events", json_body=data, headers=headers
        )

    async def search_similar_events(
        self, *, name: str | None = None, date_str: str | None = None
    ) -> dict[str, Any]:
        params: dict[str, str] = {}
        if name:
            params["name"] = name
        if date_str:
            params["date"] = date_str
        if not params:
            return {"exact_matches": [], "date_matches": []}
        res = await self._request(
            "GET", "/api/v1/events/search/similar", params=params
        )
        return res if isinstance(res, dict) else {}

    async def get_events(self, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        res = await self._request("GET", "/api/v1/events", params=params)
        return res if isinstance(res, list) else []

    async def get_event(self, event_id: str) -> dict[str, Any]:
        res = await self._request("GET", f"/api/v1/events/{event_id}")
        if not isinstance(res, dict):
            raise ApiError(500, "unexpected response")
        return res

    async def create_participant(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/api/v1/participants", json_body=data)

    async def create_registration(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/api/v1/registrations", json_body=data)

    async def get_distances(self, sport_type: str) -> dict[str, Any]:
        res = await self._request("GET", f"/api/v1/distances/{sport_type}")
        if not isinstance(res, dict):
            raise ApiError(500, "unexpected distances response")
        return res

    async def update_event(self, event_id: str, data: dict[str, Any]) -> dict[str, Any]:
        res = await self._request(
            "PUT", f"/api/v1/events/{event_id}", json_body=data
        )
        if not isinstance(res, dict):
            raise ApiError(500, "unexpected event update response")
        return res

    async def delete_event(self, event_id: str) -> None:
        session = await self._session_get()
        async with session.delete(f"/api/v1/events/{event_id}") as resp:
            text = await resp.text()
            if resp.status >= 400:
                payload: Any = None
                if text:
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        pass
                raise ApiError(resp.status, text or resp.reason, payload)

    async def update_registration(
        self, registration_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        res = await self._request(
            "PUT", f"/api/v1/registrations/{registration_id}", json_body=data
        )
        if not isinstance(res, dict):
            raise ApiError(500, "unexpected registration update")
        return res

    async def get_participant_by_telegram(self, telegram_id: int) -> dict[str, Any]:
        res = await self._request(
            "GET", f"/api/v1/participants/by-telegram/{telegram_id}"
        )
        if not isinstance(res, dict):
            raise ApiError(500, "unexpected participant response")
        return res

    async def get_participant_detail(self, participant_id: str) -> dict[str, Any]:
        res = await self._request("GET", f"/api/v1/participants/{participant_id}")
        if not isinstance(res, dict):
            raise ApiError(500, "unexpected participant detail")
        return res

    async def get_participant_stats(self, participant_id: str) -> dict[str, Any]:
        res = await self._request("GET", f"/api/v1/stats/participant/{participant_id}")
        if not isinstance(res, dict):
            raise ApiError(500, "unexpected stats response")
        return res

    async def get_community_stats(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        res = await self._request("GET", "/api/v1/stats/community", params=params)
        if not isinstance(res, dict):
            raise ApiError(500, "unexpected community stats")
        return res

    async def create_group(self, telegram_chat_id: int, name: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"telegram_chat_id": telegram_chat_id}
        if name:
            body["name"] = name
        return await self._request("POST", "/api/v1/groups", json_body=body)

    async def get_group_by_telegram(self, telegram_chat_id: int) -> dict[str, Any] | None:
        try:
            res = await self._request(
                "GET", f"/api/v1/groups/by-telegram/{telegram_chat_id}"
            )
            return res if isinstance(res, dict) else None
        except ApiError as e:
            if e.status == 404:
                return None
            raise

    async def list_groups_api(self) -> list[dict[str, Any]]:
        res = await self._request("GET", "/api/v1/groups")
        return res if isinstance(res, list) else []

    async def get_group_events(
        self, group_id: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        res = await self._request(
            "GET", f"/api/v1/groups/{group_id}/events", params=params
        )
        return res if isinstance(res, list) else []

    async def get_groups_for_telegram(self, telegram_id: int) -> list[dict[str, Any]]:
        res = await self._request(
            "GET", f"/api/v1/participants/by-telegram/{telegram_id}/groups"
        )
        return res if isinstance(res, list) else []

    async def ensure_group_member(
        self,
        group_id: str,
        *,
        telegram_id: int,
        display_name: str,
        telegram_username: str | None,
    ) -> dict[str, Any]:
        body = {
            "telegram_id": telegram_id,
            "display_name": display_name,
            "telegram_username": telegram_username,
        }
        return await self._request(
            "POST",
            f"/api/v1/groups/{group_id}/ensure-member",
            json_body=body,
        )

    async def get_bytes(self, path: str) -> bytes:
        session = await self._session_get()
        async with session.get(path) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise ApiError(resp.status, text or resp.reason)
            return await resp.read()

    async def get_event_ical_bytes(self, event_id: str) -> tuple[bytes, str | None]:
        session = await self._session_get()
        path = f"/api/v1/events/{event_id}/ical"
        async with session.get(path) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise ApiError(resp.status, text or resp.reason)
            data = await resp.read()
            cd = resp.headers.get("Content-Disposition", "")
            filename: str | None = None
            if 'filename="' in cd:
                filename = cd.split('filename="', 1)[-1].strip().rstrip('"')
            return data, filename

    async def get_my_ical_bytes(self, telegram_id: int) -> tuple[bytes, str | None]:
        path = f"/api/v1/participants/by-telegram/{telegram_id}/ical"
        session = await self._session_get()
        async with session.get(path) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise ApiError(resp.status, text or resp.reason)
            data = await resp.read()
            cd = resp.headers.get("Content-Disposition", "")
            filename: str | None = None
            if 'filename="' in cd:
                filename = cd.split('filename="', 1)[-1].strip().rstrip('"')
            return data, filename
