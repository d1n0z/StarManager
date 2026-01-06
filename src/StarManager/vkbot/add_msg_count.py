import secrets
import time

from StarManager.core import managers
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
    await managers.messages.increment_messages(uid, chat_id)
    await managers.lastmessagedate.edit(uid, chat_id, now_ts)
    rewards = await managers.rewardscollected.get(uid)
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
    if rewards and now_ts - rewards.date <= 86400 * 7:
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
    return True
