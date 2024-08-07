from telebot import types

commands_list = [
    types.BotCommand('start', 'запуск бота'),
    types.BotCommand('help', 'показать помощь')
]


def get_commads_list():
    return commands_list
