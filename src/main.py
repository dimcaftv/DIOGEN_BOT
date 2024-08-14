import os

from telebot import TeleBot

import menu.utils
from app import App
from handlers import callback_handlers, message_handlers
from utils import commands, filters


def register_handlers(bot):
    message_handlers.register_handlers(bot)
    callback_handlers.register_handlers(bot)


def init_bot(bot):
    register_handlers(bot)
    filters.register_filters(bot)
    App.start(bot)
    menu.utils.set_app_menu()
    bot.set_my_commands(commands.get_commads_list())


def main():
    bot = TeleBot(os.getenv('BOT_TOKEN'))
    init_bot(bot)
    bot.infinity_polling(skip_pending=True)


if __name__ == '__main__':
    main()
