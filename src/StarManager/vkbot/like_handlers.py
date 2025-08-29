from StarManager.core.utils import add_user_xp
from StarManager.core.config import settings
from StarManager.core.db import pool


async def like_handle(event) -> None:
    pid = event.object.object_id
    if pid == settings.service.farm_post_id:
        uid = event.object.liker_id
        async with (await pool()).acquire() as conn:
            if await conn.fetchval(
                "select exists(select id from likes where uid=$1 and post_id=$2)",
                uid,
                pid,
            ):
                return
            await conn.execute(
                "insert into likes (uid, post_id) values ($1, $2)", uid, pid
            )
        await add_user_xp(uid, 200)
