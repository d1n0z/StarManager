import time
from ast import literal_eval
from datetime import datetime
from typing import Any

from vkbottle_types.events.bot_events import MessageNew
from vkbottle_types.objects import MessagesMessageAttachmentType

from StarManager.core import managers
from StarManager.core.config import settings
from StarManager.core.db import pool
from StarManager.core.utils import (
    add_user_xp,
    antispam_checker,
    delete_messages,
    get_chat_name,
    get_chat_settings,
    search_id_in_message,
    get_silence,
    get_silence_allowed,
    get_user_access_level,
    get_user_ban,
    get_user_ban_info,
    get_user_last_message,
    get_user_mute,
    get_user_name,
    get_user_nickname,
    get_user_prefixes,
    get_user_premium,
    get_user_premmenu_setting,
    kick_user,
    punish,
    send_message,
    set_chat_mute,
)
from StarManager.vkbot import keyboard, messages
from StarManager.vkbot.action_handlers import action_handle
from StarManager.vkbot.add_msg_count import add_msg_counter
from StarManager.vkbot.answers_handlers import answer_handler
from StarManager.vkbot.checkers import getUChatLimit


async def message_handle(event: MessageNew) -> Any:
    if not event.object.message:
        return
    if event.object.message.action:
        return await action_handle(event)
    msg = event.object.message.text
    if event.object.message.peer_id < 2000000000:
        chat_id = event.object.message.peer_id
        for i in settings.commands.pm:
            if i in msg:
                return
        if (
            event.object.message.attachments
            and len(event.object.message.attachments) == 0
        ):
            return await send_message(chat_id, await messages.pm())
        elif (
            event.object.message.attachments
            and event.object.message.attachments[0].market
        ):
            return await send_message(
                chat_id,
                await messages.pm_market(),
                kbd=keyboard.pm_market(event.object.message.from_id),
            )
    
    uid = event.object.message.from_id
    msgtime = event.object.message.date
    chat_id = event.object.message.peer_id - 2000000000
    chat_settings = await get_chat_settings(chat_id)
    uacc = await get_user_access_level(uid, chat_id) if uid > 0 else 0

    if chat_settings["main"]["nightmode"] and (uacc <= 6):
        async with (await pool()).acquire() as conn:
            chatsetting = await conn.fetchrow(
                "select value2 from settings where chat_id=$1 and setting='nightmode'",
                chat_id,
            )
        if chatsetting and (setting := chatsetting[0]):
            setting = setting.split("-")
            now = datetime.now()
            start = datetime.strptime(setting[0], "%H:%M").replace(year=now.year)
            end = datetime.strptime(setting[1], "%H:%M").replace(year=now.year)
            if not (
                now.hour < start.hour
                or now.hour > end.hour
                or (now.hour == start.hour and now.minute < start.minute)
                or (now.hour == end.hour and now.minute >= end.minute)
            ):
                return await delete_messages(
                    event.object.message.conversation_message_id, chat_id
                )

    if event.object.message.from_id < 0:
        return
    if await answer_handler(event):
        return

    if uid in settings.service.admins:
        print(f"{uid}({chat_id}): {msg}")

    filterdata, pnt = msg.lower().replace(" ", ""), -1
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "insert into allusers (uid) values ($1) on conflict (uid) do nothing", uid
        )
        await conn.execute(
            "insert into allchats (chat_id) values ($1) on conflict (chat_id) do nothing",
            chat_id,
        )

        if any(
            i in filterdata
            for i in [
                i[0]
                for i in await conn.fetch(
                    "select filter from filters where chat_id=$1 or (owner_id=$2 and exists("
                    "select 1 from gpool where uid=$2 and chat_id=$1) and filter not in ("
                    "select filter from filterexceptions where owner_id=$2 and chat_id=$1))",
                    chat_id,
                    await conn.fetchval(
                        "select uid from accesslvl where chat_id=$1 and access_level>=7 order by "
                        "access_level, uid",
                        chat_id,
                    )
                    or uid,
                )
            ]
        ) and not await get_user_access_level(uid, chat_id):
            pnt = await conn.fetchval(
                "select punishment from filtersettings where chat_id=$1", chat_id
            )
    if pnt == -1:
        pass
    elif not pnt:
        return await delete_messages(
            event.object.message.conversation_message_id, chat_id
        )
    elif pnt == 1:
        mute_time = 315360000
        async with (await pool()).acquire() as conn:
            ms = await conn.fetchrow(
                "select last_mutes_times, last_mutes_causes, last_mutes_names, last_mutes_dates "
                "from mute where chat_id=$1 and uid=$2",
                chat_id,
                uid,
            )
        if ms is not None:
            mute_times = literal_eval(ms[0])
            mute_causes = literal_eval(ms[1])
            mute_names = literal_eval(ms[2])
            mute_dates = literal_eval(ms[3])
        else:
            mute_times, mute_causes, mute_names, mute_dates = [], [], [], []

        mute_times.append(mute_time)
        mute_causes.append("Фильтрация слов")
        mute_names.append("[club222139436|Star Manager]")
        mute_dates.append(datetime.now().strftime("%Y.%m.%d %H:%M:%S"))

        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                "update mute set mute = $1, last_mutes_times = $2, last_mutes_causes = $3, last_mutes_names = $4, "
                "last_mutes_dates = $5 where chat_id=$6 and uid=$7 returning 1",
                time.time() + mute_time,
                f"{mute_times}",
                f"{mute_causes}",
                f"{mute_names}",
                f"{mute_dates}",
                chat_id,
                uid,
            ):
                await conn.execute(
                    "insert into mute (uid, chat_id, mute, last_mutes_times, last_mutes_causes, last_mutes_names, "
                    "last_mutes_dates) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                    uid,
                    chat_id,
                    time.time() + mute_time,
                    f"{mute_times}",
                    f"{mute_causes}",
                    f"{mute_names}",
                    f"{mute_dates}",
                )

        await set_chat_mute(uid, chat_id)
        await delete_messages(event.object.message.conversation_message_id, chat_id)
        return await send_message(
            chat_id + 2000000000,
            await messages.filterpunish_mute(
                uid, await get_user_name(uid), await get_user_nickname(uid, chat_id)
            ),
        )
    else:
        ban_time = 315360000
        async with (await pool()).acquire() as conn:
            res = await conn.fetchrow(
                "select last_bans_times, last_bans_causes, last_bans_names, last_bans_dates from ban where "
                "chat_id=$1 and uid=$2",
                chat_id,
                uid,
            )
        if res is not None:
            ban_times = literal_eval(res[0])
            ban_causes = literal_eval(res[1])
            ban_names = literal_eval(res[2])
            ban_dates = literal_eval(res[3])
        else:
            ban_times, ban_causes, ban_names, ban_dates = [], [], [], []

        ban_times.append(ban_time)
        ban_causes.append("Фильтрация слов")
        ban_names.append("[club222139436|Star Manager]")
        ban_dates.append(datetime.now().strftime("%Y.%m.%d %H:%M:%S"))

        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                "update ban set ban = $1, last_bans_times = $2, last_bans_causes = $3, last_bans_names = $4, "
                "last_bans_dates = $5 where chat_id=$6 and uid=$7 returning 1",
                time.time() + ban_time,
                f"{ban_times}",
                f"{ban_causes}",
                f"{ban_names}",
                f"{ban_dates}",
                chat_id,
                uid,
            ):
                await conn.execute(
                    "insert into ban (uid, chat_id, ban, last_bans_times, last_bans_causes, last_bans_names, "
                    "last_bans_dates) values ($1, $2, $3, $4, $5, $6, $7)",
                    uid,
                    chat_id,
                    time.time() + ban_time,
                    f"{ban_times}",
                    f"{ban_causes}",
                    f"{ban_names}",
                    f"{ban_dates}",
                )

        await delete_messages(event.object.message.conversation_message_id, chat_id)
        return await send_message(
            chat_id + 2000000000,
            await messages.filterpunish_ban(
                uid, await get_user_name(uid), await get_user_nickname(uid, chat_id)
            )
            + (
                "\n❗ Пользователя не удалось кикнуть"
                if not await kick_user(uid, chat_id)
                else ""
            ),
        )

    data = event.object.message.text.split()
    if not any(
        event.object.message.text.startswith(i)
        for i in await get_user_prefixes(await get_user_premium(uid), uid)
    ) and (
        pinged := [
            i
            for i in [
                (
                    await search_id_in_message(
                        event.object.message.text, None, place=k
                    ),
                    data[k - 1],
                )
                for k in range(1, len(data) + 1)
                if not data[k - 1].isdigit()
            ]
            if i[0]
        ]
    ):
        async with (await pool()).acquire() as conn:
            if (
                await conn.fetchval(
                    "select exists(select 1 from antitag where chat_id=$1)", chat_id
                )
                and await conn.fetchval(
                    "select exists(select 1 from antitag where chat_id=$1 and uid=ANY($2))",
                    chat_id,
                    [i[0] for i in pinged],
                )
                and await delete_messages(
                    event.object.message.conversation_message_id, chat_id
                )
            ):
                return await send_message(
                    event.object.message.peer_id,
                    await messages.antitag_on(
                        uid,
                        await get_user_nickname(uid, chat_id),
                        await get_user_name(uid),
                    ),
                )
        if tonotif := [
            i
            for i in pinged
            if await get_user_premmenu_setting(i[0], "tagnotif", False)
        ]:
            for i in tonotif:
                if not await send_message(
                    i[0],
                    f"""📌 Упоминание в чате: {await get_chat_name(chat_id)}
👤 [id{uid}|{await get_user_name(uid)}] → {i[1]} 
💬 Сообщение: \"{event.object.message.text}\"""",
                ):
                    async with (await pool()).acquire() as conn:
                        await conn.execute(
                            "update premmenu set pos = $1 where uid=$2 and setting=$3",
                            0,
                            uid,
                            "tagnotif",
                        )

    if (ban := await get_user_ban(uid, chat_id)) >= time.time():
        await delete_messages(event.object.message.conversation_message_id, chat_id)
        await send_message(
            event.object.message.peer_id,
            await messages.kick_banned(
                uid,
                await get_user_name(uid),
                await get_user_nickname(uid, chat_id),
                ban,
                (await get_user_ban_info(uid, chat_id))["causes"][-1],
            ),
        )
        return await kick_user(uid, chat_id=chat_id)
    if uacc == 0 and await getUChatLimit(
        msgtime, await get_user_last_message(uid, chat_id, 0), uacc, chat_id
    ):
        return await delete_messages(
            event.object.message.conversation_message_id, chat_id
        )
    if (
        await get_silence(chat_id) and uacc not in await get_silence_allowed(chat_id)
    ) or await get_user_mute(uid, chat_id) > int(msgtime):
        return await delete_messages(
            event.object.message.conversation_message_id, chat_id
        )
    if (
        uacc == 0
        and chat_settings["main"]["disallowPings"]
        and any(
            i
            in [
                "@all",
                "@online",
                "@everyone",
                "@here",
                "@все",
                "@тут",
                "@здесь",
                "@онлайн",
            ]
            for i in event.object.message.text.replace("*", "@").lower().split()
        )
    ):
        return await delete_messages(
            event.object.message.conversation_message_id, chat_id
        )

    try:
        if (
            event.object.message.attachments
            and event.object.message.attachments[0].type
            == MessagesMessageAttachmentType.AUDIO_MESSAGE
        ):
            audio = True
        else:
            audio = False
    except Exception:
        audio = False
    try:
        if (
            event.object.message.attachments
            and event.object.message.attachments[0].type
            == MessagesMessageAttachmentType.STICKER
        ):
            if chat_settings["main"]["disallowStickers"]:
                return await delete_messages(
                    event.object.message.conversation_message_id, chat_id
                )
            sticker = True
        else:
            sticker = False
    except Exception:
        sticker = False

    if chat_settings["antispam"]["messagesPerMinute"]:
        async with (await pool()).acquire() as conn:
            if await conn.fetchval(
                "select \"value\" from settings where chat_id=$1 and setting='messagesPerMinute'",
                chat_id,
            ):
                managers.antispam.add_message(chat_id, uid, event.object.message.date)

    if uacc < 5 and (
        setting := await antispam_checker(
            chat_id, uid, event.object.message, chat_settings
        )
    ):
        async with (await pool()).acquire() as conn:
            setting = await conn.fetchrow(
                'select id, setting, "value", pos2 from settings where chat_id=$1 and setting=$2',
                chat_id,
                setting,
            )
        if punishment := await punish(uid, chat_id, setting[0]):
            if punishment != "del":
                await send_message(
                    chat_id + 2000000000,
                    await messages.antispam_punishment(
                        uid,
                        await get_user_name(uid),
                        await get_user_nickname(uid, chat_id),
                        setting[1],
                        punishment[0],
                        setting[2],
                        punishment[1] if len(punishment) > 1 else 0,
                    ),
                )
        if (
            setting[1] in settings.settings_meta.alt_to_delete
            and (
                setting[3]
                or (
                    setting[3] is None
                    and settings.settings_alt.defaults["antispam"][setting[1]]
                )
            )
        ) or (setting[1] not in settings.settings_meta.alt_to_delete and punishment):
            await delete_messages(event.object.message.conversation_message_id, chat_id)

    if chat_id == settings.service.mathgiveaways_to and msg.replace("-", "").isdigit():
        async with (await pool()).acquire() as conn:
            math = await conn.fetchrow(
                "select id, cmid, ans, xp, math from mathgiveaway where finished=false order by id desc"
            )
            if math and math[2] == int(msg):
                await conn.execute(
                    "update mathgiveaway set winner=$1, finished=true where id=$2",
                    uid,
                    math[0],
                )
                await add_user_xp(uid, math[3])
                await delete_messages(math[1], settings.service.mathgiveaways_to)
                await send_message(
                    settings.service.mathgiveaways_to + 2000000000,
                    await messages.math_winner(
                        uid,
                        await get_user_name(uid),
                        await get_user_nickname(uid, settings.service.mathgiveaways_to),
                        msg,
                        math[3],
                        math[4],
                    ),
                )
    await add_msg_counter(chat_id, uid, audio, sticker)
