import settings

start_cmd_text = 'Бот для удобного обмена ответами на дз с одноклассниками (/help)'


def get_help_cmd_text() -> str:
    cmd_help = '\n'.join(f'/{cmd.command} - {cmd.description}' for cmd in settings.commands_list)
    desc = 'Новости: @diogen_bot_news\nПо багам и предложениям писать @dimcaftv\nВ неделе 7 дней. Почаще используйте /back. Сервер за 150 рублей непредсказуемо может залагать на 10 секунд, спасибо за ожидание'
    return desc + '\n\n' + cmd_help


def get_status_text(status: bool) -> str:
    opts = ['🔴', '🟢']
    return f"Статус: {opts[status]}\n\nНовости: @diogen_bot_news\nКод: https://github.com/dimcaftv/DIOGEN_BOT"
