import time

from vkbottle_types import GroupTypes

import StarManager.vkbot.messages as messages
from StarManager.core.config import api, service_vk_api_session, settings
from StarManager.core.db import pool
from StarManager.core.utils import addUserXP, getUserName


async def comment_handle(event: GroupTypes.WallReplyNew):
    uid = event.object.from_id
    if uid <= 0 or event.object.post_id is None:
        return
    if event.object.post_id == settings.service.farm_post_id:
        async with (await pool()).acquire() as conn:
            if not (
                com := await conn.fetchval(
                    "select time from comments where uid=$1", uid
                )
            ):
                await conn.execute(
                    "insert into comments (uid, time) values ($1, $2)", uid, time.time()
                )
            elif time.time() - com < 7200:
                return await api.wall.create_comment(
                    owner_id=-settings.vk.group_id,
                    post_id=settings.service.farm_post_id,
                    from_group=settings.vk.group_id,
                    message=await messages.farm_cd(
                        await getUserName(uid), uid, 7200 - (time.time() - com)
                    ),
                    reply_to_comment=event.object.id,
                )
            else:
                await conn.execute(
                    "update comments set time = $1 where uid=$2", time.time(), uid
                )
        await addUserXP(uid, 50)
        return await api.wall.create_comment(
            owner_id=-settings.vk.group_id,
            post_id=settings.service.farm_post_id,
            from_group=settings.vk.group_id,
            message=await messages.farm(await getUserName(uid), uid),
            reply_to_comment=event.object.id,
        )
    if (
        time.time()
        - service_vk_api_session.method(
            "wall.getById", {"posts": f"-{settings.vk.group_id}_{event.object.post_id}"}
        )["items"][0]["date"]
        < 86400 * 7
    ):
        async with (await pool()).acquire() as conn:
            if await conn.fetchval(
                "select exists(select 1 from newpostcomments where uid=$1 and pid=$2)",
                event.object.from_id,
                event.object.post_id,
            ):
                return await api.wall.create_comment(
                    owner_id=-settings.vk.group_id,
                    post_id=event.object.post_id,
                    from_group=settings.vk.group_id,
                    message=await messages.newpost_dup(await getUserName(uid), uid),
                    reply_to_comment=event.object.id,
                )
            await conn.execute(
                "insert into newpostcomments (uid, pid) values ($1, $2)",
                uid,
                event.object.post_id,
            )
        await addUserXP(uid, 250)
        return await api.wall.create_comment(
            owner_id=-settings.vk.group_id,
            post_id=event.object.post_id,
            from_group=settings.vk.group_id,
            message=await messages.newpost(await getUserName(uid), uid),
            reply_to_comment=event.object.id,
        )
