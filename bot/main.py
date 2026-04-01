from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeDefault,
    TelegramObject,
)

from api_client import ApiClient
from config import API_URL, BOT_TOKEN
from group_manager import GroupManager
from handlers import (
    add_event,
    chatid,
    delete_event,
    edit_event,
    groups as groups_handler,
    ical,
    join_event,
    lang as lang_handler,
    list_events,
    result,
    start,
    stats,
)
from hub_scope_middleware import HubScopeMiddleware
from locale_middleware import LocaleMiddleware
from scheduler import ReminderScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


class ApiClientMiddleware(BaseMiddleware):
    def __init__(self, client: ApiClient) -> None:
        super().__init__()
        self.client = client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["client"] = self.client
        return await handler(event, data)


class SchedulerMiddleware(BaseMiddleware):
    """Пробрасывает ReminderScheduler в хэндлеры (kwargs `scheduler`)."""

    def __init__(self, scheduler: ReminderScheduler) -> None:
        super().__init__()
        self.scheduler = scheduler

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["scheduler"] = self.scheduler
        return await handler(event, data)


async def _run() -> None:
    client = ApiClient(API_URL)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(LocaleMiddleware())
    dp.update.middleware(ApiClientMiddleware(client))

    group_manager = GroupManager(client)
    dp["group_manager"] = group_manager
    dp.update.middleware(HubScopeMiddleware(group_manager, client))

    reminder_scheduler = ReminderScheduler(bot, client)
    reminder_scheduler.start()

    dp["scheduler"] = reminder_scheduler
    dp.update.middleware(SchedulerMiddleware(reminder_scheduler))

    dp.include_router(groups_handler.router)
    dp.include_router(lang_handler.router)
    dp.include_router(start.router)
    dp.include_router(list_events.router)
    dp.include_router(join_event.router)
    dp.include_router(edit_event.router)
    dp.include_router(delete_event.router)
    dp.include_router(result.router)
    dp.include_router(stats.router)
    dp.include_router(ical.router)
    dp.include_router(add_event.router)
    # /testreminder и /chatid — последними, чтобы команды точно доходили до хэндлера
    dp.include_router(chatid.router)

    # Меню команд: в личке Telegram показывает /edit; в группах клиент всегда
    # дописывает @bot к пунктам меню — это поведение клиента, его нельзя убрать API.
    # Поэтому полный список только для private; в группах и для админов — пусто
    # (команды всё равно работают, если набрать вручную, например /edit).
    _commands: list[BotCommand] = [
        BotCommand(command="add", description="Добавить новый старт"),
        BotCommand(command="list", description="Ближайшие старты"),
        BotCommand(command="join", description="Присоединиться к старту"),
        BotCommand(command="edit", description="Редактировать старт"),
        BotCommand(command="delete", description="Удалить старт"),
        BotCommand(command="result", description="Внести результат"),
        BotCommand(command="stats", description="Статистика"),
        BotCommand(command="ical", description="Скачать .ics файл"),
        BotCommand(command="help", description="Справка / Help"),
        BotCommand(command="lang", description="Язык / Language"),
        BotCommand(
            command="chatid",
            description="Узнать ID чата (для напоминаний)",
        ),
        BotCommand(
            command="testreminder",
            description="Тест напоминаний (отладка)",
        ),
    ]
    for _scope in (
        BotCommandScopeDefault(),
        BotCommandScopeAllPrivateChats(),
        BotCommandScopeAllGroupChats(),
        BotCommandScopeAllChatAdministrators(),
    ):
        await bot.delete_my_commands(_scope)
    await bot.set_my_commands(_commands, BotCommandScopeAllPrivateChats())
    await bot.set_my_commands([], BotCommandScopeAllGroupChats())
    await bot.set_my_commands([], BotCommandScopeAllChatAdministrators())

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        reminder_scheduler.stop()
        await client.close()
        await bot.session.close()


def main() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(_run())


if __name__ == "__main__":
    main()
