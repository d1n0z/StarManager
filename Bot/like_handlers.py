from Bot.utils import addUserXP
from config.config import FARM_POST_ID
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
