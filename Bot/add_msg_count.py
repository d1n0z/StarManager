import time
from datetime import datetime
from math import ceil

from Bot.checkers import getUInfBanned, getULvlBanned
from Bot.tgbot import tgbot
from Bot.utils import getUserPremium, addUserXP, getChatName, getUserName, chatPremium
from config.config import TG_CHAT_ID, TG_AUDIO_THREAD_ID
from db import pool


async def add_msg_counter(chat_id, uid, audio=False, sticker=False) -> bool:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update messages set messages=messages+1 where chat_id=%s and uid=%s',
                                    (chat_id, uid))).rowcount:
                await c.execute('insert into messages (uid, chat_id, messages) values (%s, %s, 1)', (uid, chat_id))
            if not (await c.execute('update lastmessagedate set last_message = %s where chat_id=%s and uid=%s',
                                    (int(time.time()), chat_id, uid))).rowcount:
                await c.execute('insert into lastmessagedate (uid, chat_id, last_message) values (%s, %s, %s)',
                                (uid, chat_id, int(time.time())))
            await conn.commit()

    if await getUInfBanned(uid, chat_id) or await getULvlBanned(uid):
        return False

    md = ("lm", 5) if not audio and not sticker else (("lvm", 20) if audio else ("lsm", 10))
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            lmt = await (await c.execute(f'select id, {md[0]} from xp where uid=%s', (uid,))).fetchone()
            if lmt and time.time() - lmt[1] < md[1]:
                return False
            elif lmt:
                await c.execute(f'update xp set {md[0]} = %s where uid=%s', (int(time.time()), uid))
            else:
                await c.execute(
                    f'insert into xp (uid, xp, lm, lvm, lsm, league) values (%(i)s, 0, %(t)s, %(t)s, %(t)s, 1)',
                    {'i': uid, 't': int(time.time())})
            await conn.commit()

    if audio:
        addxp = 4
        try:
            await tgbot.send_message(chat_id=TG_CHAT_ID, message_thread_id=TG_AUDIO_THREAD_ID,
                                     text=f'{chat_id} | {await getChatName(chat_id)} | '
                                          f'<a href="vk.com/id{uid}">{await getUserName(uid)}</a> | '
                                          f'{datetime.now().strftime("%H:%M:%S")}',
                                     disable_web_page_preview=True, parse_mode='HTML')
        except:
            pass
    elif sticker:
        addxp = 0.5
    else:
        addxp = 1
    if await getUserPremium(uid):
        addxp *= 1.5
    if await chatPremium(chat_id):
        addxp *= 1.5

    await addUserXP(uid, addxp, checklvlbanned=False)
    return True
