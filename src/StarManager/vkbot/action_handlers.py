from datetime import datetime
import time

from vkbottle_types.events.bot_events import MessageNew

from StarManager.core import managers, utils
from StarManager.core.config import api, settings
from StarManager.core.db import pool
from StarManager.vkbot import keyboard, messages


async def action_handle(message: MessageNew) -> None:
    event = message.object.message
    if event is None or (action := event.action) is None:
        return
    chat_id = event.peer_id - 2000000000
    chat_settings = await utils.get_chat_settings(chat_id)
    if action.type.value == "chat_invite_user_by_link" and (
        await utils.get_raid_mode_active(chat_id)
        or chat_settings["main"]["kickInvitedByLink"]
    ):
        if await utils.kick_user(event.from_id, chat_id=chat_id):
            await utils.send_message(
                event.peer_id,
                f"⛔️ [id{event.from_id}|{await utils.get_user_name(event.from_id)}], был(-a) исключен(-на) из беседы. Вход по пригласительным ссылкам в беседе отключен.",
            )
        return

    if (uid := action.member_id) is None:
        return

    if action.type.value in ("chat_invite_user_by_link", "chat_invite_user"):
        if chat_id in settings.service.too_old_last_seen_in:
            user = (await api.users.get(user_ids=uid, fields=["last_seen"]))[0]  # type: ignore
            cutoff = datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            if (
                user.last_seen
                and user.last_seen.time
                and user.last_seen.time <= cutoff.timestamp()
            ):
                await utils.kick_user(uid, chat_id)
                await utils.send_message(
                    event.peer_id,
                    f"🔴 Пользователь [id{uid}|{await utils.get_user_name(uid)}] не соответствует критериям беседы и его нельзя добавить в беседу.",
                )
                return
        async with (await pool()).acquire() as conn:
            raidmode = await conn.fetchrow(
                "select trigger_status, limit_invites, limit_seconds, status from raidmode where chat_id=$1",
                chat_id,
            )
        if raidmode and raidmode[0] and not raidmode[3]:
            managers.raid.add_user_id(action.type.value, chat_id, uid)
            if len(
                to_kick := managers.raid.get_users(
                    action.type.value, chat_id, raidmode[2]
                ).keys()
            ) >= raidmode[1] and (
                action.type.value != "chat_invite_user"
                or await utils.get_user_access_level(uid, chat_id) == 0
            ):
                await utils.send_message(
                    event.peer_id,
                    "❗️ Активирована защита от рейдов, все новые участники чата будут кикнуты. Для отключения напишите команду /raid",
                )
                async with (await pool()).acquire() as conn:
                    await conn.execute(
                        "update raidmode set status=true where chat_id=$1", chat_id
                    )
                for user_id in to_kick:
                    await utils.kick_user(user_id, chat_id)
                return

    if action.type.value not in ("chat_invite_user", "chat_kick_user"):
        return

    if action.type.value == "chat_kick_user":
        if chat_settings["main"]["kickLeaving"]:
            await utils.kick_user(uid, chat_id=chat_id)
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

    if uid == -settings.vk.group_id:
        async with (await pool()).acquire() as conn:
            if block := await conn.fetchrow(
                "select reason from blocked where uid=$1 and type='chat'", chat_id
            ):
                await utils.send_message(
                    event.peer_id,
                    await messages.block_chatblocked(id, block[0]),
                    keyboard.block_chatblocked(),
                )
                await api.messages.remove_chat_user(id, user_id=-settings.vk.group_id)
                return
            if await conn.fetchval(
                "select exists(select 1 from blacklist where uid=$1)", id
            ):
                await utils.send_message(event.peer_id, await messages.blocked())
                await utils.kick_user(-settings.vk.group_id, chat_id=chat_id)
                return
            if not await conn.fetchval(
                "select exists(select 1 from allchats where chat_id=$1)", chat_id
            ):
                await conn.execute(
                    "insert into allchats (chat_id) values ($1)", chat_id
                )
                await utils.send_message(
                    event.peer_id, await messages.join(), keyboard.join(chat_id)
                )
                return
        await utils.send_message(
            event.peer_id, await messages.rejoin(), keyboard.rejoin(chat_id)
        )
        return

    if await utils.get_user_access_level(id, chat_id) == 0 and (
        chat_settings["main"]["kickInvitedByNoAccess"]
        or await utils.get_raid_mode_active(chat_id)
    ):
        await utils.kick_user(uid, chat_id=chat_id)
        return

    if uid < 0:
        return
    if (ban := await utils.get_user_ban(uid, chat_id)) > time.time():
        await utils.send_message(
            event.peer_id,
            await messages.kick_banned(
                uid,
                await utils.get_user_name(uid),
                await utils.get_user_nickname(uid, chat_id),
                ban,
                (await utils.get_user_ban_info(uid, chat_id))["causes"][-1],
            ),
        )
        await utils.kick_user(uid, chat_id=chat_id)
        return
    async with (await pool()).acquire() as conn:
        if block := await conn.fetchrow(
            "select reason from blocked where uid=$1 and type='user'", uid
        ):
            await utils.send_message(
                event.peer_id,
                await messages.block_blockeduserinvite(
                    uid, await utils.get_user_name(uid), block[0]
                ),
            )
            await utils.kick_user(uid, chat_id=chat_id)
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
                await utils.add_user_xp(id, 250)
                await conn.execute(
                    "insert into referralbonushistory (chat_id, uid, from_id) values ($1, $2, $3)",
                    chat_id,
                    uid,
                    id,
                )
                await utils.send_message(
                    event.peer_id,
                    await messages.referralbonus(
                        id,
                        await utils.get_user_name(id),
                        await utils.get_user_nickname(id, chat_id),
                        uid,
                        await utils.get_user_name(uid),
                        await utils.get_user_nickname(uid, chat_id),
                    ),
                )
            if s := await conn.fetchrow(
                "select pos, \"value\", punishment from settings where chat_id=$1 and setting='captcha'",
                chat_id,
            ):
                if s[0] and s[1] and s[2]:
                    captcha = await utils.generate_captcha(uid, chat_id, s[1])
                    m = await utils.send_message(
                        event.peer_id,
                        await messages.captcha(
                            uid, await utils.get_user_name(uid), s[1], s[2]
                        ),
                        photo=await utils.upload_image(captcha[0]),
                    )
                    if m and not isinstance(m, (int, bool)):
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
                u_nickname = await utils.get_user_nickname(uid, chat_id)
                m = await utils.send_message(
                    event.peer_id,
                    (
                        welcome[0].replace(
                            "%name%",
                            f"[id{uid}|{await utils.get_user_name(uid) if u_nickname is None else u_nickname}]",
                        )
                    )
                    if welcome[0]
                    else None,
                    keyboard.urlbutton(welcome[1], welcome[2]),
                    welcome[3],
                )
                if s[1]:
                    lw = await conn.fetchval(
                        "delete from welcomehistory where chat_id=$1 returning cmid",
                        chat_id,
                    )
                    await utils.delete_messages(lw, chat_id)
                if m and not isinstance(m, (int, bool)):
                    await conn.execute(
                        "insert into welcomehistory (chat_id, time, cmid) values ($1, $2, $3) on conflict "
                        "(chat_id) do nothing",
                        chat_id,
                        time.time(),
                        m[0].conversation_message_id,
                    )
