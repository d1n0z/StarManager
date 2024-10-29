import time

from vkbottle_types import GroupTypes

import messages
from Bot.utils import getUserName, addUserXP
from config.config import FARM_CD, FARM_POST_ID, GROUP_ID, API
from db import pool


async def comment_handle(event: GroupTypes.WallReplyNew) -> None:
    pid = event.object.post_id
    if pid != FARM_POST_ID:
        return
    uid = event.object.from_id
    if uid <= 0:
        return
    cid = event.object.id
    name = await getUserName(uid)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (com := await (await c.execute('select id, time from comments where uid=%s', (uid,))).fetchone()):
                await c.execute('insert into comments (uid, time) values (%s, %s)', (uid, int(time.time())))
            elif time.time() - com[1] < FARM_CD:
                msg = messages.farm_cd(name, uid, FARM_CD - (time.time() - com.time))
                await API.wall.create_comment(owner_id=-GROUP_ID, post_id=FARM_POST_ID, from_group=GROUP_ID,
                                              message=msg, reply_to_comment=cid)
                return
            else:
                await c.execute('update comments set time = %s where uid=%s', (int(time.time()), uid))
            await conn.commit()
    await addUserXP(uid, 50)

    msg = messages.farm(name, uid)
    await API.wall.create_comment(owner_id=-GROUP_ID, post_id=FARM_POST_ID, from_group=GROUP_ID,
                                  message=msg, reply_to_comment=cid)
