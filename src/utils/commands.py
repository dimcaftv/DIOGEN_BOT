from telebot import TeleBot


def register_commands(bot: TeleBot, commands):
    bot.set_my_commands(commands)
