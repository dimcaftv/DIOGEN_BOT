import settings

start_cmd_text = 'Легендарный бот для обмена дз с одноклассниками (/help)'


def get_help_cmd_text():
    return '\n'.join(f'/{cmd.command} - {cmd.description}' for cmd in settings.commands_list)
