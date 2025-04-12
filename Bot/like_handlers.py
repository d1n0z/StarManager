from Bot.utils import addUserXP
from config.config import FARM_POST_ID
from db import pool


async def like_handle(event) -> None:
    pid = event.object.object_id
    if pid == FARM_POST_ID:
        uid = event.object.liker_id
        async with (await pool()).acquire() as conn:
            if await conn.fetchval('select exists(select id from likes where uid=$1 and post_id=$2)', uid, pid):
                return
            await conn.execute('insert into likes (uid, post_id) values ($1, $2)', uid, pid)
        await addUserXP(uid, 200)
