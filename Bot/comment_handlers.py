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
        async with (await pool()).acquire() as conn:
            async with conn.transaction():
                if not (com := await conn.fetchval('select time from comments where uid=$1', uid)):
                    await conn.execute('insert into comments (uid, time) values ($1, $2)', uid, time.time())
                elif time.time() - com < FARM_CD:
                    return await api.wall.create_comment(
                        owner_id=-GROUP_ID, post_id=FARM_POST_ID, from_group=GROUP_ID, message=messages.farm_cd(
                            await getUserName(uid), uid, FARM_CD - (time.time() - com)),
                        reply_to_comment=event.object.id)
                else:
                    await conn.execute('update comments set time = $1 where uid=$2', time.time(), uid)
        await addUserXP(uid, 50)
        return await api.wall.create_comment(owner_id=-GROUP_ID, post_id=FARM_POST_ID, from_group=GROUP_ID,
                                             message=messages.farm(await getUserName(uid), uid),
                                             reply_to_comment=event.object.id)
    if time.time() - service_vk_api_session.method('wall.getById', {'posts': f'-{GROUP_ID}_{event.object.post_id}'}
                                                   )['items'][0]['date'] < 86400 * 7:
        async with (await pool()).acquire() as conn:
            async with conn.transaction():
                if await conn.fetchval('select exists(select 1 from newpostcomments where uid=$1 and pid=$2)',
                                       event.object.from_id, event.object.post_id):
                    return await api.wall.create_comment(
                        owner_id=-GROUP_ID, post_id=event.object.post_id, from_group=GROUP_ID,
                        message=messages.newpost_dup(await getUserName(uid), uid), reply_to_comment=event.object.id)
                await conn.execute('insert into newpostcomments (uid, pid) values ($1, $2)', uid, event.object.post_id)
        await addUserXP(uid, 250)
        return await api.wall.create_comment(
            owner_id=-GROUP_ID, post_id=event.object.post_id, from_group=GROUP_ID,
            message=messages.newpost(await getUserName(uid), uid), reply_to_comment=event.object.id)
