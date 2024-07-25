import time
from datetime import datetime

from Bot.checkers import getUInfBanned, getULvlBanned
from Bot.utils import getUserMessages, getUserPremium, addUserXP, addWeeklyTask, addDailyTask, getUserName
from config.config import CHEATING_TO, API
from db import Messages, LastMessageDate, XP


async def add_msg_counter(chat_id, uid, audio=False, addownerxp=0) -> None:
    msgs = await getUserMessages(uid, chat_id)
    msgs += 1
    mst = Messages.get_or_create(uid=uid, chat_id=chat_id)[0]
    mst.messages = msgs
    mst.save()

    lmt = LastMessageDate.get_or_create(uid=uid, chat_id=chat_id)[0]
    lmt.last_message = int(time.time())
    lmt.save()

    if not await getUInfBanned(uid, chat_id) or not await getULvlBanned(uid):
        return

    u_prem = await getUserPremium(uid)
    if audio:
        addxp = 5
        await addDailyTask(uid, 'sendvoice')
        await API.messages.send(
            random_id=0, chat_id=CHEATING_TO,
            message=f'{chat_id} | [id{uid}|{await getUserName(uid)}] | {datetime.now().strftime("%H:%M:%S")}'
        )
    else:
        addxp = 2
        await addWeeklyTask(uid, 'sendmsgs')
        await addDailyTask(uid, 'sendmsgs')
    if u_prem:
        addxp *= 2
    if addownerxp != 0:
        addxp = addownerxp

    lmt = XP.get_or_create(uid=uid, defaults={'xp': 0, 'lm': time.time()})[0]
    if time.time() - lmt.lm < 15:
        return
    lmt.lm = time.time()
    lmt.save()

    await addUserXP(uid, addxp)
    return
