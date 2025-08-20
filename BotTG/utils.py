import re

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from loguru import logger

from config.config import TG_REPORTS_ARCHIVE_THREAD_ID, TG_REPORTS_CHAT_ID, api


async def archive_report(
    message_ids, original_text: str, action, bot: Bot, report_id, uid, answer=None
):
    new_text = original_text.split("\n")
    if action == "delete":
        action = "Удалено"
        message = (
            f"📘 Ваше обращение #{report_id} было удалено модераторами сообщества."
        )
    elif action == "ban":
        action = "Блокировка"
        message = "📘 Вы получили блокировку на отправку обращений сроком на 24 часа."
    elif action == "answer":
        action = "Закрыто"
        try:
            user_name = await api.users.get(user_ids=uid)
            user_name = f"{user_name[0].first_name} {user_name[0].last_name}"
            message = f"""📗 Обращение #{report_id}
👤 Пользователь - {user_name}\n
💬 Содержимое: {re.sub(r"<[^>]+>", "", original_text.split('Содержимое:</b> ')[-1])}
❇️ Ответ: {answer}"""
        except Exception:
            message = None

    try:
        if message:
            await api.messages.send(user_id=uid, random_id=0, message=message)
    except Exception:
        pass
    new_text.insert(3, f"➡️ Статус: {action}")
    if action == "Закрыто":
        new_text.append(f"❇️ Ответ: {answer}")
    new_text = "\n".join(new_text)
    for message_id in message_ids:
        try:
            if message_id == message_ids[-1]:
                await bot.edit_message_text(
                    chat_id=TG_REPORTS_CHAT_ID,
                    message_id=message_id,
                    text=new_text,
                    parse_mode="HTML",
                )
                await bot.copy_message(
                    chat_id=TG_REPORTS_CHAT_ID,
                    from_chat_id=TG_REPORTS_CHAT_ID,
                    message_id=message_id,
                    message_thread_id=TG_REPORTS_ARCHIVE_THREAD_ID,
                )
            else:
                await bot.copy_message(
                    chat_id=TG_REPORTS_CHAT_ID,
                    from_chat_id=TG_REPORTS_CHAT_ID,
                    message_id=message_id,
                    message_thread_id=TG_REPORTS_ARCHIVE_THREAD_ID,
                )

        except TelegramBadRequest:
            logger.exception(f"Failed to edit/copy message {message_id}")

        try:
            await bot.delete_message(chat_id=TG_REPORTS_CHAT_ID, message_id=message_id)
        except TelegramBadRequest:
            logger.exception(f"Failed to delete message {message_id}")
