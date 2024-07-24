import time

from vkbottle_types import GroupTypes

import messages
from Bot.utils import getUserName, addUserXP
from config.config import FARM_CD, FARM_POST_ID, GROUP_ID, API
from db import Comments


async def comment_handle(event: GroupTypes.WallReplyNew) -> None:
    pid = event.object.post_id
    if pid != FARM_POST_ID:
        return
    uid = event.object.from_id
    if uid <= 0:
        return
    cid = event.object.id
    name = await getUserName(uid)

    c = Comments.get_or_create(uid=uid, defaults={'time': time.time()})[0]
    if time.time() - c.time < FARM_CD:
        msg = messages.farm_cd(name, uid, FARM_CD - (time.time() - c.time))
        await API.wall.create_comment(owner_id=-GROUP_ID, post_id=FARM_POST_ID, from_group=GROUP_ID,
                                      message=msg, reply_to_comment=cid)
        return
    c.time = time.time()
    c.save()
    await addUserXP(uid, 50)

    msg = messages.farm(name, uid)
    await API.wall.create_comment(owner_id=-GROUP_ID, post_id=FARM_POST_ID, from_group=GROUP_ID,
                                  message=msg, reply_to_comment=cid)
