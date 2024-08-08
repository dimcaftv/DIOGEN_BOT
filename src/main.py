import os

from telebot import TeleBot

from database import database
from handlers import message_handlers, callback_handlers
from utils import filters, commands


def register_handlers(bot):
    message_handlers.register_handlers(bot)
    callback_handlers.register_handlers(bot)


def init_bot(bot):
    register_handlers(bot)
    filters.register_filters(bot)
    database.SimpleBotStateStorage(bot)
    bot.set_my_commands(commands.get_commads_list())


def main():
    bot = TeleBot(os.getenv('BOT_TOKEN'))
    init_bot(bot)
    bot.infinity_polling(skip_pending=True)


if __name__ == '__main__':
    main()
