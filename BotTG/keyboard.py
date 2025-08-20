from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class Callback(CallbackData, prefix="cb"):
    type: str


class ReportCallback(CallbackData, prefix="report"):
    type: str
    report_id: int


def joingiveaway(count) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=f"Хочу участвовать ({count})",
            callback_data=Callback(type="joingiveaway").pack(),
        )
    )

    return builder.as_markup()


def link() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🔗 Привязать профиль", callback_data=Callback(type="link").pack()
        )
    )

    return builder.as_markup()


def unlink() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🔗 Удалить привязку", callback_data=Callback(type="unlink").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👤 Пригласить друзей", callback_data=Callback(type="ref").pack()
        )
    )

    return builder.as_markup()


def back():
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="Назад", callback_data=Callback(type="start").pack())
    )

    return builder.as_markup()


def check(ref):
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Проверить подписку",
            callback_data=Callback(type=f"checksub_{ref}").pack(),
        )
    )

    return builder.as_markup()


def report_cancel():
    builder = InlineKeyboardBuilder()

    builder.row(
            InlineKeyboardButton(
                text='Назад',
                callback_data=Callback(type='report_cancel').pack(),
            )
        )
    return builder.as_markup()


def report(report_id):
    builder = InlineKeyboardBuilder()

    for action, label in [
        ("answer", "Ответить"),
        ("delete", "Удалить"),
        ("ban", "Заблокировать"),
    ]:
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=ReportCallback(type=action, report_id=report_id).pack(),
            )
        )
    return builder.as_markup()
