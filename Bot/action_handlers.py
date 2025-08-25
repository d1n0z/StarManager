import time

from vkbottle_types.events.bot_events import MessageNew

import keyboard
import messages
from Bot.utils import (
    getRaidModeActive,
    kickUser,
    getUserName,
    getUserBan,
    getUserBanInfo,
    getUserNickname,
    getChatSettings,
    sendMessage,
    getUserAccessLevel,
    deleteMessages,
    uploadImage,
    generateCaptcha,
    addUserXP,
)
from config.config import GROUP_ID, api
from db import pool


async def action_handle(event: MessageNew) -> None:
    event = event.object.message
    action = event.action
    if action.type.value not in ("chat_invite_user", "chat_kick_user"):
        return
    chat_id = event.peer_id - 2000000000
    uid = action.member_id
    if action.type.value == "chat_kick_user":
        if (await getChatSettings(chat_id))["main"]["kickLeaving"]:
            await kickUser(uid, chat_id=chat_id)
        async with (await pool()).acquire() as conn:
            await conn.execute(
                "delete from captcha where chat_id=$1 and uid=$2", chat_id, uid
            )
            await conn.execute(
                "delete from typequeue where chat_id=$1 and uid=$2 and type='captcha'",
                chat_id,
                uid,
            )
        return

    if action.type.value != "chat_invite_user":
        return
    id = event.from_id
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "insert into allusers (uid) values ($1) on conflict (uid) do nothing", id
        )
        if not await conn.fetchval(
            "update userjoineddate set time = $1 where chat_id=$2 and uid=$3 returning 1",
            time.time(),
            chat_id,
            id,
        ):
            await conn.execute(
                "insert into userjoineddate (chat_id, uid, time) values ($1, $2, $3)",
                chat_id,
                id,
                time.time(),
            )

    if uid == -GROUP_ID:
        async with (await pool()).acquire() as conn:
            if block := await conn.fetchrow(
                "select reason from blocked where uid=$1 and type='chat'", chat_id
            ):
                await sendMessage(
                    event.peer_id,
                    messages.block_chatblocked(id, block[0]),
                    keyboard.block_chatblocked(),
                )
                await api.messages.remove_chat_user(id, user_id=-GROUP_ID)
                return
            if await conn.fetchval(
                "select exists(select 1 from blacklist where uid=$1)", id
            ):
                await sendMessage(event.peer_id, messages.blocked())
                await kickUser(-GROUP_ID, chat_id=chat_id)
                return
            if not await conn.fetchval(
                "select exists(select 1 from allchats where chat_id=$1)", chat_id
            ):
                await conn.execute(
                    "insert into allchats (chat_id) values ($1)", chat_id
                )
                await sendMessage(
                    event.peer_id, messages.join(), keyboard.join(chat_id)
                )
                return
        await sendMessage(event.peer_id, messages.rejoin(), keyboard.rejoin(chat_id))
        return

    if (
        await getUserAccessLevel(id, chat_id) <= 0
        and ((await getChatSettings(chat_id))["main"]["kickInvitedByNoAccess"] or await getRaidModeActive(chat_id))
    ):
        await kickUser(uid, chat_id=chat_id)
        return

    if uid < 0:
        return
    if (ban := await getUserBan(uid, chat_id)) > time.time():
        await sendMessage(
            event.peer_id,
            messages.kick_banned(
                uid,
                await getUserName(uid),
                await getUserNickname(uid, chat_id),
                ban,
                (await getUserBanInfo(uid, chat_id))["causes"][-1],
            ),
        )
        await kickUser(uid, chat_id=chat_id)
        return
    async with (await pool()).acquire() as conn:
        if block := await conn.fetchrow(
            "select reason from blocked where uid=$1 and type='user'", uid
        ):
            await sendMessage(
                event.peer_id,
                messages.block_blockeduserinvite(uid, await getUserName(uid), block[0]),
            )
            await kickUser(uid, chat_id=chat_id)
            return

    if id:
        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                "update refferal set from_id = $1 where chat_id=$2 and uid=$3 returning 1",
                id,
                chat_id,
                uid,
            ):
                await conn.execute(
                    "insert into refferal (chat_id, uid, from_id) values ($1, $2, $3)",
                    chat_id,
                    uid,
                    id,
                )
            if (
                id
                and uid != id
                and await conn.fetchval(
                    "select exists(select 1 from referralbonus where chat_id=$1)",
                    chat_id,
                )
                and not await conn.fetchval(
                    "select exists(select 1 from referralbonushistory where chat_id=$1 and uid=$2 and from_id=$3)",
                    chat_id,
                    uid,
                    id,
                )
            ):
                await addUserXP(id, 250)
                await conn.execute(
                    "insert into referralbonushistory (chat_id, uid, from_id) values ($1, $2, $3)",
                    chat_id,
                    uid,
                    id,
                )
                await sendMessage(
                    event.peer_id,
                    messages.referralbonus(
                        id,
                        await getUserName(id),
                        await getUserNickname(id, chat_id),
                        uid,
                        await getUserName(uid),
                        await getUserNickname(uid, chat_id),
                    ),
                )
            if s := await conn.fetchrow(
                "select pos, \"value\", punishment from settings where chat_id=$1 and setting='captcha'",
                chat_id,
            ):
                if s[0] and s[1] and s[2]:
                    captcha = await generateCaptcha(uid, chat_id, s[1])
                    m = await sendMessage(
                        event.peer_id,
                        messages.captcha(uid, await getUserName(uid), s[1], s[2]),
                        photo=await uploadImage(captcha[0]),
                    )
                    if m:
                        await conn.execute(
                            "update captcha set cmid = $1 where id=$2",
                            m[0].conversation_message_id,
                            captcha[1],
                        )
                        await conn.execute(
                            'insert into typequeue (chat_id, uid, "type", additional) '
                            "values ($1, $2, 'captcha', '{}')",
                            chat_id,
                            uid,
                        )
                        return
            if s := await conn.fetchrow(
                "select pos, pos2 from settings where chat_id=$1 and setting='welcome'",
                chat_id,
            ):
                welcome = await conn.fetchrow(
                    "select msg, url, button_label, photo from welcome where chat_id=$1",
                    chat_id,
                )
                if welcome is None or not s[0]:
                    return
                u_nickname = await getUserNickname(uid, chat_id)
                m = await sendMessage(
                    event.peer_id,
                    welcome[0].replace(
                        "%name%",
                        f"[id{uid}|{await getUserName(uid) if u_nickname is None else u_nickname}]",
                    ),
                    keyboard.urlbutton(welcome[1], welcome[2]),
                    welcome[3],
                )
                if s[1]:
                    lw = await conn.fetchval(
                        "delete from welcomehistory where chat_id=$1 returning cmid",
                        chat_id,
                    )
                    await deleteMessages(lw, chat_id)
                await conn.execute(
                    "insert into welcomehistory (chat_id, time, cmid) values ($1, $2, $3) on conflict "
                    "(chat_id) do nothing",
                    chat_id,
                    time.time(),
                    m[0].conversation_message_id,
                )
