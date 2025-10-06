import random
import re
import time
import traceback
from copy import deepcopy
from datetime import datetime

from vkbottle import KeyboardButtonColor
from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler
from vkbottle_types.objects import UsersFields

from StarManager.core import enums, managers
from StarManager.core.config import api, settings
from StarManager.core.db import pool
from StarManager.core.media.stats.stats_img import createStatsImage
from StarManager.core.utils import (
    add_user_coins,
    add_user_xp,
    chat_premium,
    delete_messages,
    get_chat_access_name,
    get_chat_settings,
    get_reg_date,
    get_rep_top,
    get_user_access_level,
    get_user_ban,
    get_user_coins,
    get_user_last_message,
    get_user_league,
    get_user_level,
    get_user_messages,
    get_user_mute,
    get_user_name,
    get_user_needed_xp,
    get_user_nickname,
    get_user_premium,
    get_user_premmenu_setting,
    get_user_premmenu_settings,
    get_user_rep,
    get_user_shop_bonuses,
    get_user_warns,
    get_user_xp,
    is_chat_admin,
    kick_user,
    messagereply,
    point_words,
    search_id_in_message,
    set_user_access_level,
    upload_image,
)
from StarManager.tgbot.bot import bot as tgbot
from StarManager.vkbot import keyboard, messages
from StarManager.vkbot.checkers import getULvlBanned
from StarManager.vkbot.rules import SearchCMD

bl = BotLabeler()


@bl.chat_message(SearchCMD("test"))
@bl.chat_message(SearchCMD("chatid"))
async def test_handler(message: Message):
    await messagereply(message, f"💬 ID данной беседы : {message.peer_id - 2000000000}")


@bl.chat_message(SearchCMD("id"))
async def id(message: Message):
    id = await search_id_in_message(message.text, message.reply_message)
    if not id:
        id = message.from_id
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )

    user = await api.users.get(user_ids=[id])
    if user[0].deactivated:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_deleted()
        )
    last_message = await get_user_last_message(id, message.peer_id - 2000000000, None)
    if isinstance(last_message, int):
        last_message = datetime.fromtimestamp(last_message).strftime("%d.%m.%Y / %H:%M")
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.id(
            id,
            await get_reg_date(id),
            await get_user_name(id),
            f"https://vk.com/id{id}",
            last_message,
        ),
    )


@bl.chat_message(SearchCMD("q"))
async def q(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id

    if await kick_user(uid, chat_id):
        await set_user_access_level(uid, chat_id, 0)
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.q(
                uid, await get_user_name(uid), await get_user_nickname(uid, chat_id)
            ),
        )
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.q_fail(
            uid, await get_user_name(uid), await get_user_nickname(uid, chat_id)
        ),
    )


@bl.chat_message(SearchCMD("premium"))
async def premium(message: Message):
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.market(),
        keyboard=keyboard.market(),
    )


@bl.chat_message(SearchCMD("top"))
async def top(message: Message):
    chat_id = message.peer_id - 2000000000
    async with (await pool()).acquire() as conn:
        msgs = await conn.fetch(
            "select uid, messages from messages where uid>0 and messages>0 and chat_id=$1 and "
            "uid=ANY($2) order by messages desc limit 10",
            chat_id,
            [
                i.member_id
                for i in (
                    await api.messages.get_conversation_members(peer_id=message.peer_id)
                ).items
            ],
        )
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.top(msgs),
        keyboard=keyboard.top(chat_id, message.from_id),
    )


@bl.chat_message(SearchCMD("stats"))
async def stats(message: Message):
    chat_id = message.peer_id - 2000000000

    id = await search_id_in_message(message.text, message.reply_message)
    if not id:
        id = message.from_id
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )
    reply = await messagereply(
        message, await messages.stats_loading(), disable_mentions=1
    )

    async with (await pool()).acquire() as conn:
        rewards = await conn.fetchval(
            "select exists(select 1 from rewardscollected where uid=$1 and deactivated=false)",
            message.from_id,
        )
    acc = await managers.access_level.get_access_level(message.from_id, chat_id)
    if acc < 1 and not await get_user_premium(message.from_id) and not rewards:
        id = message.from_id
    else:
        acc = await get_user_access_level(id, chat_id)
    last_message = await get_user_last_message(id, chat_id)
    if isinstance(last_message, int):
        last_message = datetime.fromtimestamp(last_message).strftime("%d.%m.%Y")
    url = (
        await api.users.get(user_ids=[id], fields=[UsersFields.PHOTO_MAX_ORIG.value])
    )[0].photo_max_orig
    if not url:
        return
    r = await api.http_client.request_content(url)
    with open(
        settings.service.path + f"src/StarManager/core/media/temp/{id}ava.jpg", "wb"
    ) as f:
        f.write(r)

    lvl_name = await get_chat_access_name(chat_id, acc)
    xp = int(await get_user_xp(id))
    lvl = await get_user_level(id) or 1
    try:
        await messagereply(
            message,
            disable_mentions=1,
            attachment=await upload_image(
                await createStatsImage(
                    await get_user_warns(id, chat_id),
                    await get_user_messages(id, chat_id),
                    id,
                    await get_user_access_level(id, chat_id),
                    await get_user_nickname(id, chat_id),
                    await get_user_coins(id),
                    last_message,
                    await get_user_premium(id),
                    min(xp, 99999999),
                    min(lvl, 999),
                    await get_user_rep(id),
                    await get_rep_top(id),
                    await get_user_name(id),
                    await get_user_mute(id, chat_id),
                    await get_user_ban(id, chat_id),
                    lvl_name or settings.lvl_names[acc],
                    await get_user_needed_xp(xp) if lvl < 999 else 0,
                    await get_user_premmenu_setting(id, "border_color", False),
                    await get_user_league(id),
                )
            ),
        )
    except Exception as e:
        if message.from_id in settings.service.devs:
            traceback.print_exc()
        if reply and reply.conversation_message_id:
            await delete_messages(reply.conversation_message_id, chat_id)
        await messagereply(
            message,
            disable_mentions=1,
            message="❌ Ошибка. Пожалуйста, попробуйте позже.",
        )
        raise e
    else:
        if reply and reply.conversation_message_id:
            await delete_messages(reply.conversation_message_id, chat_id)


@bl.chat_message(SearchCMD("help"))
async def help(message: Message):
    uid = message.from_id
    async with (await pool()).acquire() as conn:
        cmds = await conn.fetch(
            "select cmd, lvl from commandlevels where chat_id=$1",
            message.peer_id - 2000000000,
        )
    base = deepcopy(settings.commands.commands)
    for i in cmds:
        base[i[0]] = int(i[1])
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.help(cmds=base),
        keyboard=keyboard.help(uid, u_prem=await get_user_premium(uid)),
    )


@bl.chat_message(SearchCMD("bonus"))
async def bonus(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    name = await get_user_name(uid)

    async with (await pool()).acquire() as conn:
        lasttime, streak = await conn.fetchrow(
            "select time, streak from bonus where uid=$1", uid
        ) or (0, 0)
    if time.time() - lasttime < 86400:
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.bonus_time(
                uid, None, name, lasttime + 86400 - time.time()
            ),
        )

    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "update bonus set time = $1, streak=streak+1 where uid=$2 returning 1",
            time.time(),
            uid,
        ):
            await conn.execute(
                "insert into bonus (uid, time, streak) values ($1, $2, 1)",
                uid,
                time.time(),
            )

    prem = await get_user_premium(uid)
    addxp = min(100 + (50 if prem else 25) * streak, 2500 if prem else 1000)
    await add_user_xp(uid, addxp)
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.bonus(
            uid, await get_user_nickname(uid, chat_id), name, addxp, prem, streak
        ),
    )

    try:
        await tgbot.send_message(
            chat_id=settings.telegram.chat_id,
            message_thread_id=settings.telegram.bonus_thread_id,
            text=f'{uid} | <a href="vk.com/id{uid}">{await get_user_name(uid)}</a> | '
            f"Серия: {point_words(streak + 1, ('день', 'дня', 'дней'))}",
            disable_web_page_preview=True,
            parse_mode="HTML",
        )
    except Exception:
        pass


@bl.chat_message(SearchCMD("prefix"))
async def prefix(message: Message):
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.prefix(),
        keyboard=keyboard.prefix(message.from_id),
    )


@bl.chat_message(SearchCMD("cmd"))
async def cmd(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.lower().split()
    if len(data) == 2:
        try:
            cmd = data[1]
        except Exception:
            return await messagereply(
                message, disable_mentions=1, message=await messages.resetcmd_hint()
            )
        if cmd not in settings.commands.commands:
            return await messagereply(
                message,
                disable_mentions=1,
                message=await messages.resetcmd_not_found(cmd),
            )

        async with (await pool()).acquire() as conn:
            cmdn = await conn.fetchval(
                "delete from cmdnames where uid=$1 and cmd=$2 returning name", uid, cmd
            )
        if not cmdn:
            return await messagereply(
                message,
                disable_mentions=1,
                message=await messages.resetcmd_not_changed(cmd),
            )

        await messagereply(
            message,
            disable_mentions=1,
            message=await messages.resetcmd(
                uid,
                await get_user_name(uid),
                await get_user_nickname(uid, chat_id),
                cmd,
                cmdn,
            ),
        )
    elif len(data) == 3:
        try:
            cmd = data[1]
            changed = " ".join(data[2:])
        except Exception:
            return await messagereply(
                message, disable_mentions=1, message=await messages.cmd_hint()
            )
        if cmd not in settings.commands.commands:
            return await messagereply(
                message,
                disable_mentions=1,
                message=await messages.resetcmd_not_found(cmd),
            )
        if changed in settings.commands.commands:
            return await messagereply(
                message,
                disable_mentions=1,
                message=await messages.cmd_changed_in_cmds(),
            )

        async with (await pool()).acquire() as conn:
            cmdns = await conn.fetch("select cmd, name from cmdnames where uid=$1", uid)
        res = []
        for i in cmdns:
            if i[0] not in res:
                res.append(i[0])
            if changed == i[1]:
                return await messagereply(
                    message,
                    disable_mentions=1,
                    message=await messages.cmd_changed_in_users_cmds(i[0]),
                )
        if (
            not await get_user_premium(uid)
            and len(res) >= settings.leagues.cmd_bonus[await get_user_league(uid) - 1]
        ):
            return await messagereply(
                message, disable_mentions=1, message=await messages.cmd_prem(len(res))
            )

        if (
            len(re.compile(r"[a-zA-Zа-яА-Я0-9]").findall(changed)) != len(changed)
            or len(changed) > 32
        ):
            return await messagereply(
                message, disable_mentions=1, message=await messages.cmd_char_limit()
            )

        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                "update cmdnames set name = $1 where uid=$2 and cmd=$3 returning 1",
                changed,
                uid,
                cmd,
            ):
                await conn.execute(
                    "insert into cmdnames (uid, cmd, name) values ($1, $2, $3)",
                    uid,
                    cmd,
                    changed,
                )

        await messagereply(
            message,
            disable_mentions=1,
            message=await messages.cmd_set(
                uid,
                await get_user_name(uid),
                await get_user_nickname(uid, chat_id),
                cmd,
                changed,
            ),
        )
    else:
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.cmd_hint(),
            keyboard=keyboard.cmd(uid),
        )


@bl.chat_message(SearchCMD("premmenu"))
async def premmenu(message: Message):
    uid = message.from_id
    if not (prem := await get_user_premium(uid)) and await get_user_league(uid) <= 1:
        return await messagereply(
            message, disable_mentions=1, message=await messages.no_prem()
        )
    menu_settings = await get_user_premmenu_settings(uid)
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.premmenu(menu_settings, prem),
        keyboard=keyboard.premmenu(uid, menu_settings, prem),
    )


@bl.chat_message(SearchCMD("duel"))
async def duel(message: Message):
    chat_id = message.peer_id - 2000000000

    if not (await get_chat_settings(chat_id))["entertaining"]["allowDuel"]:
        return await messagereply(
            message, disable_mentions=1, message=await messages.duel_not_allowed()
        )

    data = message.text.split()
    try:
        coins = int(data[1])
    except Exception:
        return await messagereply(
            message, disable_mentions=1, message=await messages.duel_hint()
        )

    if coins < 10 or coins > 500:
        return await messagereply(
            message, disable_mentions=1, message=await messages.duel_coins_minimum()
        )
    if len(data) != 2:
        return await messagereply(
            message, disable_mentions=1, message=await messages.duel_hint()
        )

    uid = message.from_id
    if await get_user_coins(uid) < coins:
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.not_enough_coins(
                uid, await get_user_name(uid), await get_user_nickname(uid, chat_id)
            ),
        )

    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.duel(
            uid, await get_user_name(uid), await get_user_nickname(uid, chat_id), coins
        ),
        keyboard=keyboard.duel(uid, coins),
    )


@bl.chat_message(SearchCMD("transfer"))
async def transfer(message: Message):
    chat_id = message.chat_id
    if not (await get_chat_settings(chat_id))["entertaining"]["allowTransfer"]:
        return await messagereply(message, await messages.transfer_not_allowed())
    uid = message.from_id

    id = await search_id_in_message(message.text, message.reply_message)
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.transfer_community()
        )
    if not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.transfer_hint()
        )
    if uid == id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.transfer_myself()
        )
    if await getULvlBanned(id):
        return await messagereply(
            message, disable_mentions=1, message=await messages.user_lvlbanned()
        )

    if (len(message.text.lower().split()) <= 2 and message.reply_message is None) or (
        len(message.text.lower().split()) <= 1 and message.reply_message is not None
    ):
        return await messagereply(
            message, disable_mentions=1, message=await messages.transfer_hint()
        )

    try:
        tcoins = int(message.text.split()[-1])
    except Exception:
        return await messagereply(
            message, disable_mentions=1, message=await messages.transfer_hint()
        )

    u_prem = await get_user_premium(uid)
    if (tcoins > 500 and not u_prem) or (tcoins > 1000 and u_prem) or tcoins < 50:
        return await messagereply(
            message, disable_mentions=1, message=await messages.transfer_wrong_number()
        )

    if await get_user_coins(uid) < tcoins:
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.transfer_not_enough(
                uid, await get_user_name(uid), await get_user_nickname(uid, chat_id)
            ),
        )

    async with (await pool()).acquire() as conn:
        td = sum(
            [
                i[0]
                for i in await conn.fetch(
                    "select amount from transferhistory where time>$1 and from_id=$2",
                    datetime.now().replace(hour=0, minute=0, second=0).timestamp(),
                    uid,
                )
            ]
        )
    if (td >= 500 and not u_prem) or (td >= 1000 and not u_prem):
        return await messagereply(
            message, disable_mentions=1, message=await messages.transfer_limit(u_prem)
        )

    has_comission = not (u_prem or (await get_user_shop_bonuses(uid))[1] > time.time())
    if has_comission:
        if await chat_premium(chat_id):
            comtcoins = int(tcoins / 100 * 97.5)
            com = 2.5
        else:
            comtcoins = int(tcoins / 100 * 95)
            com = 5
    else:
        comtcoins = tcoins
        com = 0

    await add_user_coins(uid, -tcoins)
    await add_user_coins(id, comtcoins)
    uname = await get_user_name(uid)
    name = await get_user_name(id)
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "insert into transferhistory (to_id, from_id, time, amount, com) VALUES ($1, $2, $3, $4, $5)",
            id,
            uid,
            time.time(),
            comtcoins,
            com,
        )
    try:
        await tgbot.send_message(
            chat_id=settings.telegram.chat_id,
            message_thread_id=settings.telegram.transfer_thread_id,
            text=f'{chat_id} | <a href="vk.com/id{uid}">{uname}</a> | '
            f'<a href="vk.com/id{id}">{name}</a> | {comtcoins} | К: {com}% | '
            f"{datetime.now().strftime('%H:%M:%S')}",
            disable_web_page_preview=True,
            parse_mode="HTML",
        )
    except Exception:
        pass
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.transfer(uid, uname, id, name, comtcoins, com),
    )


@bl.chat_message(SearchCMD("start"))
async def start(message: Message):
    chat_id = message.peer_id - 2000000000
    if await get_user_access_level(
        message.from_id, chat_id
    ) >= 7 or await is_chat_admin(message.from_id, chat_id):
        await messagereply(
            message, await messages.rejoin(), keyboard=keyboard.rejoin(chat_id)
        )


@bl.chat_message(SearchCMD("anon"))
async def anon(message: Message):
    await messagereply(message, await messages.anon_not_pm(), disable_mentions=1)


@bl.chat_message(SearchCMD("deanon"))
async def deanon(message: Message):
    await messagereply(message, await messages.anon_not_pm(), disable_mentions=1)


@bl.chat_message(SearchCMD("guess"))
async def guess(message: Message):
    if not (await get_chat_settings(message.chat_id))["entertaining"]["allowGuess"]:
        return await messagereply(
            message, disable_mentions=1, message=await messages.guess_not_allowed()
        )
    data = message.text.split()
    if (
        len(data) != 3
        or not data[1].isdigit()
        or not data[2].isdigit()
        or int(data[2]) < 1
        or int(data[2]) > 5
    ):
        return await messagereply(
            message, disable_mentions=1, message=await messages.guess_hint()
        )
    if int(data[1]) < 10 or int(data[1]) > 500:
        return await messagereply(
            message, disable_mentions=1, message=await messages.guess_coins_minimum()
        )
    if await get_user_coins(message.from_id) < int(data[1]):
        return await messagereply(
            message, disable_mentions=1, message=await messages.guess_notenoughcoins()
        )
    if int(data[2]) != (num := random.randint(1, 5)):
        await add_user_coins(message.from_id, -int(data[1]))
        return await messagereply(
            message, disable_mentions=1, message=await messages.guess_lose(data[1], num)
        )
    bet = int(data[1]) * 2.5
    has_comission = not (
        await get_user_premium(message.from_id)
        or (await get_user_shop_bonuses(message.from_id))[1] > time.time()
    )
    if has_comission:
        bet = bet / 100 * 90
    await add_user_coins(message.from_id, bet)
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.guess_win(int(bet), data[2], has_comission),
    )


@bl.chat_message(SearchCMD("promo"))
async def promo(message: Message):
    data = message.text.split()
    if len(data) != 2:
        return await messagereply(
            message, disable_mentions=1, message=await messages.promo_hint()
        )
    uid = message.from_id
    async with (await pool()).acquire() as conn:
        code = await conn.fetchrow(
            "select code, date, usage, amnt, type, sub_needed from promocodes where code=$1",
            data[1],
        )
        if (
            code
            and code[5]
            and not (
                await api.groups.is_member(
                    group_id=settings.vk.group_id, user_ids=[uid]
                )
            )[0].member
        ):
            return await messagereply(
                message, disable_mentions=1, message=await messages.promo_not_member()
            )
        if code and (
            code[1]
            and time.time() > code[1]
            or (
                code[2]
                and (
                    len(
                        await conn.fetch(
                            "select id from promocodeuses where code=$1", data[1]
                        )
                    )
                    >= code[2]
                )
            )
        ):
            await conn.execute("delete from promocodes where code=$1", data[1])
            await conn.execute("delete from promocodeuses where code=$1", data[1])
            code = None
        if not code or await conn.fetchval(
            "select exists(select 1 from promocodeuses where code=$1 and uid=$2)",
            data[1],
            uid,
        ):
            return await messagereply(
                message,
                disable_mentions=1,
                message=await messages.promo_alreadyusedornotexists(
                    uid,
                    await get_user_nickname(uid, message.chat_id),
                    await get_user_name(uid),
                ),
            )
        await conn.execute(
            "insert into promocodeuses (code, uid) values ($1, $2)", data[1], uid
        )
    if code[4] == "xp":
        await add_user_xp(uid, int(code[3]))
    else:
        await add_user_coins(uid, int(code[3]))
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.promo(
            uid,
            await get_user_nickname(uid, message.chat_id),
            await get_user_name(uid),
            code[0],
            code[3],
            code[4],
        ),
    )


@bl.chat_message(SearchCMD("rep"))
async def rep(message: Message):
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message, 3)
    if len(data) not in (2, 3) or data[1] not in ("+", "-") or not id or id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.rep_hint()
        )
    if id == message.from_id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.rep_myself()
        )
    members = (
        await api.messages.get_conversation_members(peer_id=message.peer_id)
    ).items
    if len(members) < 2900 and id not in [i.member_id for i in members]:
        return await messagereply(
            message, disable_mentions=1, message=await messages.rep_notinchat()
        )
    uid = message.from_id
    uprem = await get_user_premium(uid)
    async with (await pool()).acquire() as conn:
        rephistory = await conn.fetch(
            "select time from rephistory where uid=$1 and id=$2 and time>$3 order by "
            "time",
            uid,
            id,
            time.time() - 86400,
        )
        if len(rephistory) >= (3 if uprem else 1):
            return await messagereply(
                message,
                disable_mentions=1,
                message=await messages.rep_limit(uprem, rephistory[0][0]),
            )
        if not await conn.fetchval(
            f"update reputation set rep=rep {data[1]} 1 where uid=$1 returning 1", id
        ):
            await conn.execute(
                "insert into reputation (uid, rep) values ($1, $2)",
                id,
                eval(f"0{data[1]}1"),
            )
        await conn.execute(
            "insert into rephistory (uid, id, time) values ($1, $2, $3)",
            uid,
            id,
            time.time(),
        )
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.rep(
            data[1] == "+",
            uid,
            await get_user_name(uid),
            await get_user_nickname(uid, message.chat_id),
            id,
            await get_user_name(id),
            await get_user_nickname(id, message.chat_id),
            await get_user_rep(id),
            await get_rep_top(id),
        ),
    )


@bl.chat_message(SearchCMD("short"))
async def short(message: Message):
    uid = message.from_id
    if not await get_user_premium(uid):
        return await messagereply(
            message, disable_mentions=1, message=await messages.no_prem()
        )
    data = message.text.split()
    if len(data) != 2:
        return await messagereply(
            message, disable_mentions=1, message=await messages.short_hint()
        )
    try:
        shortened = await api.utils.get_short_link(url=data[1], private=False)
        if not shortened or not shortened.short_url:
            raise Exception
    except Exception:
        return await messagereply(
            message, disable_mentions=1, message=await messages.short_failed()
        )
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.short(
            shortened.short_url,
            (
                await api.utils.get_short_link(
                    f"https://vk.com/cc?act=stats&key={shortened.key}"
                )
            ).short_url,
        ),
    )


@bl.chat_message(SearchCMD("rewards"))
async def rewards(message: Message):
    uid = message.from_id
    if not await api.groups.is_member(group_id=settings.vk.group_id, user_id=uid):
        return await messagereply(
            message,
            disable_mentions=1,
            keyboard=keyboard.urlbutton(
                f"https://vk.com/club{settings.vk.group_id}",
                "Подписаться",
                KeyboardButtonColor.POSITIVE,
            ),
            message=await messages.rewards_unsubbed(
                uid,
                await get_user_name(uid),
                await get_user_nickname(uid, message.chat_id),
            ),
        )
    async with (await pool()).acquire() as conn:
        collected = await conn.fetchrow(
            "select deactivated, date from rewardscollected where uid=$1", uid
        )
        if collected:
            if collected[0]:
                await conn.fetchrow(
                    "update rewardscollected set deactivated=false where uid=$1", uid
                )
                return await messagereply(
                    message,
                    disable_mentions=1,
                    message=await messages.rewards_activated(
                        uid,
                        await get_user_name(uid),
                        await get_user_nickname(uid, message.chat_id),
                        collected[1],
                        7,
                    ),
                )
            return await messagereply(
                message,
                disable_mentions=1,
                message=await messages.rewards_collected(
                    uid,
                    await get_user_name(uid),
                    await get_user_nickname(uid, message.chat_id),
                    datetime.fromtimestamp(collected[1]).strftime("%d.%m.%Y"),
                ),
            )
        await conn.execute(
            "insert into rewardscollected (uid, date, deactivated) values ($1, $2, false)",
            uid,
            int(time.time()),
        )
    await add_user_xp(uid, 10000)
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.rewards(
            uid,
            await get_user_name(uid),
            await get_user_nickname(uid, message.chat_id),
            time.time(),
            7,
            10000,
        ),
    )


@bl.chat_message(SearchCMD("shop"))
async def shop(message: Message):
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.shop(),
        keyboard=keyboard.shop(message.from_id),
    )


@bl.chat_message(SearchCMD("rps"))
async def rps(message: Message):
    data = message.text.split()
    if len(data) == 3:
        id = await search_id_in_message(message.text, message.reply_message, 3)
    else:
        id = 0

    if len(data) not in (2, 3) or not data[1].isdigit() or (len(data) == 3 and id <= 0):
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.rps_hint(),
        )
    bet = int(data[1])
    if bet not in range(25, 1001):
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.rps_bet_limit(),
        )
    if bet > await get_user_coins(message.from_id):
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.rps_not_enough_coins(),
        )
    if id and bet > await get_user_coins(id):
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.rps_not_enough_coins(),
        )
    msg = await messagereply(
        message,
        disable_mentions=1,
        message=await messages.rps(
            message.from_id,
            await get_user_name(message.from_id),
            None,
            bet,
            *(
                (
                    id,
                    await get_user_name(id),
                    None,
                )
                if id
                else (None,)
            ),
        ),
        keyboard=keyboard.rps(message.from_id, bet, id),
    )
    if not msg.conversation_message_id:
        return
    await managers.rps.add_game(
        msg.conversation_message_id, message.peer_id, time.time(), message.from_id
    )


@bl.chat_message(SearchCMD("up"))
async def up(message: Message):
    if not (await get_chat_settings(message.peer_id - 2000000000))["entertaining"][
        "allowChats"
    ]:
        return await messagereply(
            message, disable_mentions=1, message=await messages.chats_not_allowed()
        )
    up_res, remaining = await managers.public_chats.do_up(
        message.chat_id,
        message.from_id,
        message.date if hasattr(message, "date") and message.date else None,
    )
    if not up_res:
        if remaining is not None:
            return await messagereply(
                message,
                disable_mentions=1,
                message=await messages.up_cooldown(remaining),
            )
        else:
            return await messagereply(
                message,
                disable_mentions=1,
                message=await messages.up_chat_is_not_premium(),
            )
    await messagereply(message, disable_mentions=1, message=await messages.up())


@bl.chat_message(SearchCMD("chats"))
async def chats(message: Message):
    if not (await get_chat_settings(message.peer_id - 2000000000))["entertaining"][
        "allowChats"
    ]:
        return await messagereply(
            message, disable_mentions=1, message=await messages.chats_not_allowed()
        )

    chats = await managers.public_chats.get_sorted_premium_chats()
    res = await managers.public_chats.get_chats_top(chats[:15])
    await messagereply(
        message,
        await messages.chats(
            (total_chats := await managers.public_chats.count_regular_chats()),
            res,
            enums.ChatsMode.premium,
        ),
        keyboard=keyboard.chats(
            message.from_id, total_chats, 0, enums.ChatsMode.premium
        ),
        disable_mentions=1,
    )
