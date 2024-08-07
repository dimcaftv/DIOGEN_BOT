import os

from telebot import TeleBot

from utils import filters, commands
from handlers import message_handlers, callback_handlers


def register_handlers(bot):
    message_handlers.register_handlers(bot)
    callback_handlers.register_handlers(bot)


def init_bot(bot):
    register_handlers(bot)
    filters.register_filters(bot)
    bot.enable_saving_states('../.state-save/states.pkl')
    bot.set_my_commands(commands.get_commads_list())


def main():
    bot = TeleBot(os.getenv('BOT_TOKEN'))
    init_bot(bot)
    bot.infinity_polling(skip_pending=True)


if __name__ == '__main__':
    main()
