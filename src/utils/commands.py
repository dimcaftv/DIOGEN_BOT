from typing import Callable

from telebot import types
from telebot.async_telebot import AsyncTeleBot


class FullCommand:
    def __init__(self, name: str, handler: Callable, help: str):
        self.name = name
        self.handler = handler
        self.help = help

    def __str__(self):
        return f'/{self.name} - {self.help}'

    def get_telebot_cmd(self):
        return types.BotCommand(self.name, self.help)


async def register_commands(bot: AsyncTeleBot, commands: list[FullCommand]):
    await bot.set_my_commands([cmd.get_telebot_cmd() for cmd in commands])
