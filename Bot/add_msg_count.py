import time
from datetime import datetime

from Bot.checkers import getUInfBanned, getULvlBanned
from Bot.utils import getUserPremium, addUserXP, addWeeklyTask, addDailyTask
from config.config import CHEATING_TO, API
from db import Messages, LastMessageDate, XP


async def add_msg_counter(chat_id, uid, audio=False) -> None:
    mst = Messages.get_or_create(uid=uid, chat_id=chat_id)[0]
    mst.messages += 1
    mst.save()
    lmt = LastMessageDate.get_or_create(uid=uid, chat_id=chat_id)[0]
    lmt.last_message = int(time.time())
    lmt.save()

    lvlbanned = await getULvlBanned(uid)
    if not await getUInfBanned(uid, chat_id) or not lvlbanned:
        return

    lmt = XP.get_or_create(uid=uid, defaults={'xp': 0, 'lm': time.time()})[0]
    if time.time() - lmt.lm < 15:
        return
    lmt.lm = time.time()
    lmt.save()

    u_prem = await getUserPremium(uid)
    if audio:
        addxp = 5
        await addDailyTask(uid, 'sendvoice', lvlbanned=lvlbanned)
        await API.messages.send(
            random_id=0, chat_id=CHEATING_TO,
            message=f'{chat_id} | [id{uid}|{uid}] | {datetime.now().strftime("%H:%M:%S")}'
        )
    else:
        addxp = 2
        await addWeeklyTask(uid, 'sendmsgs', lvlbanned=lvlbanned)
        await addDailyTask(uid, 'sendmsgs', lvlbanned=lvlbanned)
    if u_prem:
        addxp *= 2

    await addUserXP(uid, addxp, lvlbanned=lvlbanned)
    return
