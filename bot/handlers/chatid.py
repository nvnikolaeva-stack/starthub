"""Команда /chatid — узнать ID группы для .env; /testreminder — тест напоминаний."""

from aiogram import Dispatcher, F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message

from scheduler import ReminderScheduler
from translations import t

router = Router(name="chatid")


@router.message(Command("testreminder"), F.chat.type == ChatType.PRIVATE)
async def cmd_testreminder(
    message: Message, dispatcher: Dispatcher, locale: str
) -> None:
    scheduler: ReminderScheduler = dispatcher["scheduler"]
    await scheduler.check_reminders()
    await message.answer(t(locale, "testreminder_ok"))


@router.message(Command("chatid"))
async def cmd_chatid(message: Message, locale: str) -> None:
    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        await message.answer(str(message.chat.id))
        return
    await message.answer(t(locale, "chatid_group_only"))
