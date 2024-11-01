import time

import messages
from Bot.utils import addUserXP
from config.config import FARM_POST_ID, PREMIUM_BONUS_POST_ID, PREMIUM_BONUS_DAYS, API, PREMIUM_BONUS_POST_WORKS_TIL
from db import pool


async def like_handle(event) -> None:
    pid = event.object.object_id
    if pid == FARM_POST_ID:
        uid = event.object.liker_id
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if await (await c.execute('select id from likes where uid=%s and post_id=%s', (uid, pid))).fetchone():
                    return
                await c.execute('insert into likes (uid, post_id) values (%s, %s)', (uid, pid))
                await conn.commit()
        await addUserXP(uid, 200)

    if pid == PREMIUM_BONUS_POST_ID and time.time() < PREMIUM_BONUS_POST_WORKS_TIL():
        uid = event.object.liker_id

        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                ul = await (await c.execute('select id from likes where uid=%s and post_id=%s', (uid, pid))).fetchone()
                if ul:
                    return
                await c.execute('insert into likes (uid, post_id) values (%s, %s)', (uid, pid))

                if not (await c.execute('update premium set time=time+%s where uid=%s',
                                        (PREMIUM_BONUS_DAYS * 86400, uid))).rowcount:
                    await c.execute('insert into premium (uid, time) values (%s, %s)',
                                    (uid, int(time.time() + PREMIUM_BONUS_DAYS * 86400)))
                await conn.commit()

        msg = messages.like_premium_bonus(PREMIUM_BONUS_DAYS)
        await API.messages.send(user_id=uid, message=msg, random_id=0)
