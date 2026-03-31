from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from translations import t

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, locale: str) -> None:
    await message.answer(t(locale, "help_full"))


@router.message(Command("help"))
async def cmd_help(message: Message, locale: str) -> None:
    await message.answer(t(locale, "help_full"))
