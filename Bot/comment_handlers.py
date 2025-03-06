import time

from vkbottle_types import GroupTypes

import messages
from Bot.utils import getUserName, addUserXP
from config.config import FARM_CD, FARM_POST_ID, GROUP_ID, api, service_vk_api_session
from db import pool


async def comment_handle(event: GroupTypes.WallReplyNew) -> None:
    uid = event.object.from_id
    if uid <= 0:
        return
    if event.object.post_id == FARM_POST_ID:
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
        return await api.wall.create_comment(owner_id=-GROUP_ID, post_id=FARM_POST_ID, from_group=GROUP_ID,
                                             message=messages.farm(await getUserName(uid), uid),
                                             reply_to_comment=event.object.id)
    if time.time() - service_vk_api_session.method('wall.getById', {'posts': f'-{GROUP_ID}_{event.object.post_id}'}
                                                   )['items'][0]['date'] < 86400 * 7:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if await (await c.execute('select id from newpostcomments where uid=%s and pid=%s',
                                          (event.object.from_id, event.object.post_id))).fetchone():
                    return await api.wall.create_comment(
                        owner_id=-GROUP_ID, post_id=event.object.post_id, from_group=GROUP_ID,
                        message=messages.newpost_dup(await getUserName(uid), uid), reply_to_comment=event.object.id)
                await c.execute('insert into newpostcomments (uid, pid) values (%s, %s)', (uid, event.object.post_id))
                await conn.commit()
        await addUserXP(uid, 250)
        return await api.wall.create_comment(
            owner_id=-GROUP_ID, post_id=event.object.post_id, from_group=GROUP_ID,
            message=messages.newpost(await getUserName(uid), uid), reply_to_comment=event.object.id)
