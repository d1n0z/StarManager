import secrets
import time

from StarManager.core import enums, managers
from StarManager.core.db import pool
from StarManager.core.utils import (
    add_user_coins,
    add_user_xp,
    chat_premium,
    get_user_premium,
    get_user_shop_bonuses,
)
from StarManager.vkbot.checkers import getUInfBanned, getULvlBanned


async def add_msg_counter(chat_id, uid, audio=False, sticker=False) -> bool:
    now_ts = int(time.time())
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "update messages set messages=messages+1 where chat_id=$1 and uid=$2 "
            "returning 1",
            chat_id,
            uid,
        ):
            await conn.execute(
                "insert into messages (uid, chat_id, messages) values ($1, $2, 1)",
                uid,
                chat_id,
            )
        if not await conn.fetchval(
            "update lastmessagedate set last_message = $1 where chat_id=$2 and uid=$3 "
            "returning 1",
            now_ts,
            chat_id,
            uid,
        ):
            await conn.execute(
                "insert into lastmessagedate (uid, chat_id, last_message) values ($1, $2, $3)",
                uid,
                chat_id,
                now_ts,
            )
        rewards = await conn.fetchval(
            "select date from rewardscollected where uid=$1 and deactivated=false", uid
        )
    if await getUInfBanned(uid, chat_id) or await getULvlBanned(uid):
        return False

    md = (
        ("lm", 5)
        if not audio and not sticker
        else (("lvm", 20) if audio else ("lsm", 10))
    )
    lmt = await managers.xp.get(uid, md[0])
    if lmt is not None and now_ts - lmt < md[1]:
        return False
    elif lmt:
        await managers.xp.edit(uid, **{md[0]: now_ts})
    else:
        await managers.xp.edit(uid, lm=now_ts, lvm=now_ts, lsm=now_ts)

    if audio:
        addxp, addcoins = 20, 5
    elif sticker:
        addxp, addcoins = 5, 0
    else:
        addxp, addcoins = 10, 2
    if await get_user_premium(uid):
        addxp *= 2
    if await chat_premium(chat_id):
        addxp *= 1.5
    if rewards and now_ts - rewards <= 86400 * 7:
        addxp *= 2
    if (await get_user_shop_bonuses(uid))[0] > now_ts:
        addxp *= 2

    rannum = secrets.randbelow(100)
    if addcoins and rannum < 40:
        await add_user_coins(
            uid,
            addcoins,
            checklvlbanned=False,
            addlimit=True,
            bonus_peer_id=chat_id + 2000000000,
        )
    await add_user_xp(uid, addxp, checklvlbanned=False)
    await managers.event.task_progress(uid, enums.TaskCategory.send_messages, 1)
    return True
