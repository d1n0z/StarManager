import time

import messages
from Bot.utils import addUserXP
from config.config import FARM_POST_ID, PREMIUM_BONUS_POST_ID, PREMIUM_BONUS_DAYS, API, PREMIUM_BONUS_POST_WORKS_TIL
from db import Likes, Premium


async def like_handle(event) -> None:
    pid = event.object.object_id
    if pid == FARM_POST_ID:
        uid = event.object.liker_id
        Likes.get_or_create(uid=uid, pid=pid)
        await addUserXP(uid, 200)

    if pid == PREMIUM_BONUS_POST_ID and time.time() < PREMIUM_BONUS_POST_WORKS_TIL():
        uid = event.object.liker_id

        ul = Likes.get_or_none(uid=uid, post_id=pid)
        if ul is not None:
            return
        Likes.create(uid=uid, post_id=pid)

        pr = Premium.get_or_create(uid=uid, defaults={'time': 0})[0]
        last_time = pr.time - int(time.time())
        if last_time <= 0:
            last_time = 0
        pr.time = time.time() + (PREMIUM_BONUS_DAYS * 86400) + last_time

        msg = messages.like_premium_bonus(PREMIUM_BONUS_DAYS)
        await API.messages.send(user_id=uid, message=msg, random_id=0)
