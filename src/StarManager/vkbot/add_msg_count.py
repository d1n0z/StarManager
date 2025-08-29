import secrets
import time

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
            time.time(),
            chat_id,
            uid,
        ):
            await conn.execute(
                "insert into lastmessagedate (uid, chat_id, last_message) values ($1, $2, $3)",
                uid,
                chat_id,
                time.time(),
            )
    if await getUInfBanned(uid, chat_id) or await getULvlBanned(uid):
        return False
    md = (
        ("lm", 5)
        if not audio and not sticker
        else (("lvm", 20) if audio else ("lsm", 10))
    )
    async with (await pool()).acquire() as conn:
        lmt = await conn.fetchval(f"select {md[0]} from xp where uid=$1", uid)
        if lmt is not None and time.time() - lmt < md[1]:
            return False
        elif lmt:
            await conn.execute(
                f"update xp set {md[0]} = $1 where uid=$2", time.time(), uid
            )
        else:
            await conn.execute(
                "insert into xp (uid, xp, lm, lvm, lsm, league, lvl) values ($1, 0, $2, $2, $2, 1, 1)",
                uid,
                time.time(),
            )
        rewards = await conn.fetchval(
            "select date from rewardscollected where uid=$1 and deactivated=false", uid
        )

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
    if rewards and time.time() - rewards <= 86400 * 7:
        addxp *= 2
    if (await get_user_shop_bonuses(uid))[0] > time.time():
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
    return True
