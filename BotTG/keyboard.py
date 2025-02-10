from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class Callback(CallbackData, prefix='cb'):
    type: str


def joingiveaway(count) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text=f'Хочу участвовать ({count})', callback_data=Callback(type='joingiveaway').pack()))

    return builder.as_markup()


def link() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='🔗 Привязать профиль', callback_data=Callback(type='link').pack()))

    return builder.as_markup()


def unlink() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='🔗 Удалить привязку', callback_data=Callback(type='unlink').pack()))
    builder.row(InlineKeyboardButton(text='👤 Пригласить друзей', callback_data=Callback(type='ref').pack()))

    return builder.as_markup()


def back():
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Назад', callback_data=Callback(type='start').pack()))

    return builder.as_markup()


def check(ref):
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Проверить подписку', callback_data=Callback(type=f'checksub_{ref}').pack()))

    return builder.as_markup()
