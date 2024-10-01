import time
import traceback
from datetime import datetime

from Bot.checkers import getUInfBanned, getULvlBanned
from Bot.tgbot import getTGBot
from Bot.utils import getUserPremium, addUserXP, addWeeklyTask, addDailyTask, getChatName, getUserName
from config.config import TG_CHAT_ID, TG_AUDIO_THREAD_ID
from db import Messages, LastMessageDate, XP


async def add_msg_counter(chat_id, uid, audio=False) -> None:
    mst = Messages.get_or_create(uid=uid, chat_id=chat_id)[0]
    mst.messages += 1
    mst.save()
    lmt = LastMessageDate.get_or_create(uid=uid, chat_id=chat_id)[0]
    lmt.last_message = int(time.time())
    lmt.save()

    if not await getUInfBanned(uid, chat_id) or not await getULvlBanned(uid):
        return

    u_prem = await getUserPremium(uid)
    if audio:
        addxp = 5
        await addDailyTask(uid, 'sendvoice', checklvlbanned=False)
        try:
            bot = getTGBot()
            await bot.send_message(chat_id=TG_CHAT_ID, message_thread_id=TG_AUDIO_THREAD_ID,
                                   text=f'{chat_id} | {await getChatName(chat_id)} | '
                                        f'<a href="vk.com/id{uid}">{await getUserName(uid)}</a> | '
                                        f'{datetime.now().strftime("%H:%M:%S")}',
                                   disable_web_page_preview=True, parse_mode='HTML')
        except:
            traceback.print_exc()
    else:
        addxp = 2
        await addWeeklyTask(uid, 'sendmsgs', checklvlbanned=False)
        await addDailyTask(uid, 'sendmsgs', checklvlbanned=False)
    if u_prem:
        addxp *= 2

    lmt = XP.get_or_create(uid=uid, defaults={'xp': 0, 'lm': time.time()})[0]
    if time.time() - lmt.lm < 15:
        return
    lmt.lm = time.time()
    lmt.save()

    await addUserXP(uid, addxp, checklvlbanned=False)
    return
