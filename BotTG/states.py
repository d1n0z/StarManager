from aiogram.fsm.state import StatesGroup, State


class Link(StatesGroup):
    link = State()
    unlink = State()
