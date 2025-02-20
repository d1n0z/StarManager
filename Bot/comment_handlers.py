import time

from vkbottle_types import GroupTypes

import messages
from Bot.utils import getUserName, addUserXP
from config.config import FARM_CD, FARM_POST_ID, GROUP_ID, api
from db import pool


async def comment_handle(event: GroupTypes.WallReplyNew) -> None:
    if event.object.post_id != FARM_POST_ID:
        return
    uid = event.object.from_id
    if uid <= 0:
        return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (com := await (await c.execute('select id, time from comments where uid=%s', (uid,))).fetchone()):
                await c.execute('insert into comments (uid, time) values (%s, %s)', (uid, int(time.time())))
            elif time.time() - com[1] < FARM_CD:
                return await api.wall.create_comment(
                    owner_id=-GROUP_ID, post_id=FARM_POST_ID, from_group=GROUP_ID, message=messages.farm_cd(
                        await getUserName(uid), uid, FARM_CD - (time.time() - com[1])),
                    reply_to_comment=event.object.id)
            else:
                await c.execute('update comments set time = %s where uid=%s', (int(time.time()), uid))
            await conn.commit()
    await addUserXP(uid, 50)
    await api.wall.create_comment(owner_id=-GROUP_ID, post_id=FARM_POST_ID, from_group=GROUP_ID,
                                  message=messages.farm(await getUserName(uid), uid), reply_to_comment=event.object.id)
