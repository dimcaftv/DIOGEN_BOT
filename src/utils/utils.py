from telebot.handler_backends import StatesGroup, State

from menu import menu


class BotPagesStates(StatesGroup):
    MAIN = State()
    GROUPLIST = State()
    GROUP = State()
    HOMEWORK = State()


def quick_page_markup(state, markup):
    return menu.MenuPage(state, [menu.MenuItem(*data) for data in markup])


pages = [
    quick_page_markup(BotPagesStates.MAIN, [('группы', 'groups', BotPagesStates.GROUPLIST)]),
    quick_page_markup(BotPagesStates.GROUPLIST, [('группа', 'group', BotPagesStates.GROUP),
                                                 ('назад', 'back', BotPagesStates.MAIN)]),
    quick_page_markup(BotPagesStates.GROUP, [('дз', 'hw', BotPagesStates.HOMEWORK),
                                             ('назад', 'back', BotPagesStates.GROUPLIST)]),
    quick_page_markup(BotPagesStates.HOMEWORK, [('назад', 'back', BotPagesStates.GROUP)])
]

main_menu = menu.Menu(pages)


def get_message_for_page(page: menu.MenuPage):
    return {'text': page.get_page_text(), 'reply_markup': page.get_inline_kb()}
