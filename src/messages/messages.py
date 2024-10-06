import settings

start_cmd_text = 'Бот для удобного обмена ответами на дз с одноклассниками (/help)'

default_notify_template = '‼️Ответ на "{lesson_name}" {date} только что отправили в бота‼️\n@diogen_help_bot'

request_answer_template = '❔На урок "{lesson_name}" {date} попросили прислать ответ❔\n@diogen_help_bot'


def get_help_cmd_text() -> str:
    cmd_help = '\n'.join(str(cmd) for cmd in settings.commands_list)
    cmd_help += '\nИспользуй команду addchat только в группе, куда хочешь получать уведомления, настраиваемые в настройках группы'
    desc = ('Новости: @diogen_bot_news\n'
            'По багам и предложениям писать @dimcaftv\n\n'
            'Если бот сломался, напиши /start или /menu. В неделе 7 дней. Используй /back если в чате накопился мусор. Сервер за 150 рублей непредсказуемо может залагать на 10 секунд, спасибо за ожидание')
    return desc + '\n\n' + cmd_help
