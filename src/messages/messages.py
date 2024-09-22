import settings

start_cmd_text = 'Бот для удобного обмена ответами на дз с одноклассниками (/help)'


def get_help_cmd_text() -> str:
    cmd_help = '\n'.join(str(cmd) for cmd in settings.commands_list)
    desc = ('Новости: @diogen_bot_news\n'
            'По багам и предложениям писать @dimcaftv\n\n'
            'Если бот сломался, напиши /start или /menu. В неделе 7 дней. Используй /back если в чате накопился мусор. Сервер за 150 рублей непредсказуемо может залагать на 10 секунд, спасибо за ожидание')
    return desc + '\n\n' + cmd_help


def get_status_text(status: bool) -> str:
    opts = ['🔴', '🟢']
    return (f"Статус: {opts[status]}\n\n"
            "Новости: @diogen_bot_news\n"
            "Код: https://github.com/dimcaftv/DIOGEN_BOT")
