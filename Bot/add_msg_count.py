import time
from datetime import datetime

from Bot.checkers import getUInfBanned, getULvlBanned
from Bot.tgbot import tgbot
from Bot.utils import getUserPremium, addUserXP, getChatName, getUserName, chatPremium
from config.config import TG_CHAT_ID, TG_AUDIO_THREAD_ID
from db import pool


async def add_msg_counter(chat_id, uid, audio=False, sticker=False) -> bool:
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval('update messages set messages=messages+1 where chat_id=$1 and uid=$2 '
                                   'returning 1', chat_id, uid):
            await conn.execute('insert into messages (uid, chat_id, messages) values ($1, $2, 1)', uid, chat_id)
        if not await conn.fetchval('update lastmessagedate set last_message = $1 where chat_id=$2 and uid=$3 '
                                   'returning 1', time.time(), chat_id, uid):
            await conn.execute('insert into lastmessagedate (uid, chat_id, last_message) values ($1, $2, $3)',
                               uid, chat_id, time.time())
    if await getUInfBanned(uid, chat_id) or await getULvlBanned(uid):
        return False
    md = ("lm", 5) if not audio and not sticker else (("lvm", 20) if audio else ("lsm", 10))
    async with (await pool()).acquire() as conn:
        lmt = await conn.fetchval(f'select {md[0]} from xp where uid=$1', uid)
        if lmt is not None and time.time() - lmt < md[1]:
            return False
        elif lmt:
            await conn.execute(f'update xp set {md[0]} = $1 where uid=$2', time.time(), uid)
        else:
            await conn.execute(
                f'insert into xp (uid, xp, lm, lvm, lsm, league, lvl) values ($1, 0, $2, $2, $2, 1, 1)',
                uid, time.time())

    if audio:
        addxp = 20
        # try:
        #     await tgbot.send_message(chat_id=TG_CHAT_ID, message_thread_id=TG_AUDIO_THREAD_ID,
        #                              text=f'{chat_id} | {await getChatName(chat_id)} | '
        #                                   f'<a href="vk.com/id{uid}">{await getUserName(uid)}</a> | '
        #                                   f'{datetime.now().strftime("%H:%M:%S")}',
        #                              disable_web_page_preview=True, parse_mode='HTML')
        # except:
        #     pass
    elif sticker:
        addxp = 5
    else:
        addxp = 10
    if await getUserPremium(uid):
        addxp *= 1.5
    if await chatPremium(chat_id):
        addxp *= 1.5

    await addUserXP(uid, addxp, checklvlbanned=False)
    return True
