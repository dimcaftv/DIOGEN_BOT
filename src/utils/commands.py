from telebot.async_telebot import AsyncTeleBot


async def register_commands(bot: AsyncTeleBot, commands):
    await bot.set_my_commands(commands)
