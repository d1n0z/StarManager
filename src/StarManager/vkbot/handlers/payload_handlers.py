import asyncio
import json
import secrets
import time
from ast import literal_eval
from collections import defaultdict
from copy import deepcopy
from datetime import datetime

from vkbottle.bot import MessageEvent
from vkbottle.framework.labeler import BotLabeler
from vkbottle_types.events import GroupEventType

from StarManager.core import enums, managers, utils
from StarManager.core.config import api, settings
from StarManager.core.db import pool
from StarManager.tgbot.bot import bot as tgbot
from StarManager.vkbot import keyboard, messages
from StarManager.vkbot.checkers import getULvlBanned, haveAccess
from StarManager.vkbot.rules import SearchPayloadCMD

bl = BotLabeler()

_rps_lock = asyncio.Lock()


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["_"]))
async def empty(message: MessageEvent):
    pass


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["join", "rejoin"], checksender=False),
)
async def join(message: MessageEvent):
    payload = message.payload
    if not payload:
        return
    cmd = payload["cmd"]
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == "join" or (cmd == "rejoin" and not payload["activate"]):
        try:
            members = await api.messages.get_conversation_members(
                peer_id=chat_id + 2000000000
            )
            if not members:
                raise Exception
        except Exception:
            await utils.send_message(message.peer_id, await messages.notadmin())
            return

        bp = message.user_id
        if (
            bp not in [i.member_id for i in members.items if i.is_admin or i.is_owner]
            and await utils.get_user_access_level(bp, chat_id, ignore_custom=True) < 7
        ):
            return
        async with (await pool()).acquire() as conn:
            for m in members.items:
                if m.member_id <= 0:
                    continue
                exists = await conn.fetchval(
                    "select 1 from lastmessagedate where chat_id=$1 and uid=$2",
                    chat_id,
                    m.member_id,
                )
                if not exists:
                    await conn.execute(
                        "insert into lastmessagedate (chat_id, uid, last_message) values ($1, $2, $3)",
                        chat_id,
                        m.member_id,
                        int(time.time()),
                    )
            for i in await conn.fetch(
                "select uid from mute where chat_id=$1 and mute>$2",
                chat_id,
                time.time(),
            ):
                await utils.set_chat_mute(i[0], chat_id, 0)
            for i in await managers.access_level.delete_rows(
                await managers.access_level.get_all(chat_id=chat_id)
            ):
                await utils.set_chat_mute(i.uid, chat_id, 0)
            await conn.execute("delete from nickname where chat_id=$1", chat_id)
            await conn.execute("delete from welcome where chat_id=$1", chat_id)
            await conn.execute("delete from welcomehistory where chat_id=$1", chat_id)
            await conn.execute("delete from accessnames where chat_id=$1", chat_id)
            await conn.execute("delete from ignore where chat_id=$1", chat_id)
            await conn.execute("delete from commandlevels where chat_id=$1", chat_id)
            await conn.execute("delete from mute where chat_id=$1", chat_id)
            await conn.execute("delete from warn where chat_id=$1", chat_id)
            await conn.execute("delete from ban where chat_id=$1", chat_id)
            await conn.execute("delete from gpool where chat_id=$1", chat_id)
            await conn.execute("delete from chatgroups where chat_id=$1", chat_id)
            await conn.execute("delete from silencemode where chat_id=$1", chat_id)
            await conn.execute("delete from filters where chat_id=$1", chat_id)
            await conn.execute("delete from chatlimit where chat_id=$1", chat_id)
            await conn.execute("delete from notifications where chat_id=$1", chat_id)
            await conn.execute("delete from typequeue where chat_id=$1", chat_id)
            await conn.execute(
                "delete from antispamurlexceptions where chat_id=$1", chat_id
            )
            await conn.execute("delete from botjoineddate where chat_id=$1", chat_id)
            await conn.execute("delete from captcha where chat_id=$1", chat_id)
            await conn.execute(
                "insert into botjoineddate (chat_id, time) values ($1, $2) on conflict (chat_id) "
                "do update set time=$2",
                chat_id,
                time.time(),
            )
        await managers.chat_settings.remove(chat_id)

        await managers.access_level.edit_access_level(bp, chat_id, 7)

        if cmd == "join":
            try:
                await tgbot.send_message(
                    chat_id=settings.telegram.chat_id,
                    message_thread_id=settings.telegram.newchat_thread_id,
                    text=f"{chat_id} | {await utils.get_chat_name(chat_id)} | "
                    f"{await utils.get_chat_owner(chat_id)} | {await utils.get_chat_members(chat_id)} | "
                    f"{datetime.now().strftime('%H:%M:%S')}",
                    disable_web_page_preview=True,
                    parse_mode="HTML",
                )
            except Exception:
                pass

        await utils.edit_message(
            await messages.start(), peer_id, message.conversation_message_id
        )
        return
    elif cmd == "rejoin" and payload["activate"]:
        if await utils.get_user_access_level(
            uid, chat_id, ignore_custom=True
        ) >= 7 or uid in [
            i.member_id
            for i in (
                await api.messages.get_conversation_members(peer_id=peer_id)
            ).items
            if i.is_admin or i.is_owner
        ]:
            await utils.edit_message(
                await messages.rejoin_activate(),
                peer_id,
                message.conversation_message_id,
            )
            return


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["duel"], answer=False, checksender=False),
)
async def duel(message: MessageEvent):
    if not message.conversation_message_id or not message.payload:
        return

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    async with await managers.duel_lock.get_context(
        chat_id, message.conversation_message_id
    ) as ctx:
        if not ctx.allowed:
            await message.show_snackbar("Эта дуэль уже окончена.")
            return

        payload = message.payload
        duelcoins = int(payload["coins"])
        id = int(message.user_id)
        uid = int(payload["uid"])

        if id == uid or await getULvlBanned(id):
            await message.show_snackbar("Вы не можете участвовать в дуэли.")
            return

        coins = await utils.get_user_coins(id)
        ucoins = await utils.get_user_coins(uid)
        if coins < duelcoins:
            await message.show_snackbar("У вас недостаточно монеток.")
            return
        if ucoins < duelcoins:
            await message.show_snackbar("У вашего соперника недостаточно монеток.")
            return

        i = secrets.randbelow(2)
        winid, loseid = (id, uid) if i else (uid, id)

        com, duel_coins_com = 0, duelcoins
        has_comission = not (
            await utils.get_user_premium(winid)
            or (await utils.get_user_shop_bonuses(winid))[1] > time.time()
        )
        if has_comission:
            duel_coins_com, com = int(duelcoins / 100 * 90), 10

        edit_result = await utils.edit_message(
            await messages.duel_res(
                winid,
                await utils.get_user_name(winid),
                await utils.get_user_nickname(winid, chat_id),
                loseid,
                await utils.get_user_name(loseid),
                await utils.get_user_nickname(loseid, chat_id),
                duel_coins_com,
                has_comission,
            ),
            peer_id,
            message.conversation_message_id,
        )
        if not edit_result:
            return

        ctx.mark_used()

        await utils.add_user_coins(loseid, -duelcoins)
        await utils.add_user_coins(winid, duel_coins_com)
        await managers.event.task_progress(winid, enums.TaskCategory.win_duels, 1)

        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                "update duelwins set wins=wins+1 where uid=$1 returning 1", winid
            ):
                await conn.execute(
                    "insert into duelwins (uid, wins) values ($1, 1)", winid
                )

        await utils.send_message_event_answer(message.event_id, id, peer_id)

        uname = await utils.get_user_nickname(
            uid, chat_id
        ) or await utils.get_user_name(uid)
        name = await utils.get_user_nickname(id, chat_id) or await utils.get_user_name(
            id
        )
        try:
            await tgbot.send_message(
                chat_id=settings.telegram.chat_id,
                message_thread_id=settings.telegram.duel_thread_id,
                text=f'{"W: " if uid == winid else "L: "}<a href="vk.com/id{uid}">{uname}</a> | {"W: " if id == winid else "L: "}<a href="vk.com/id{id}">{name}</a> | {duelcoins} | {com}% | {datetime.now().strftime("%d.%m.%Y / %H:%M:%S")}',
                disable_web_page_preview=True,
                parse_mode="HTML",
            )
        except Exception:
            pass


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["premmenu"])
)
async def premmenu(message: MessageEvent):
    uid = message.user_id
    menu_settings = await utils.get_user_premmenu_settings(uid)
    prem = await utils.get_user_premium(uid)
    await utils.edit_message(
        await messages.premmenu(menu_settings, prem),
        message.peer_id,
        message.conversation_message_id,
        keyboard.premmenu(uid, menu_settings, prem),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["premmenu_turn"])
)
async def premmenu_turn(message: MessageEvent):
    uid = message.user_id
    payload = message.payload
    if not payload:
        return
    if payload["setting"] == "tagnotif" and not (
        await utils.is_messages_from_group_allowed(uid)
    ):
        await utils.edit_message(
            await messages.tagnotiferror(),
            message.peer_id,
            message.conversation_message_id,
        )
        return
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "update premmenu set pos = $1 where uid=$2 and setting=$3 returning 1",
            int(not bool(payload["pos"])),
            uid,
            payload["setting"],
        ):
            await conn.execute(
                "insert into premmenu (uid, setting, pos) values ($1, $2, $3)",
                uid,
                payload["setting"],
                int(not settings.premium_menu.default[payload["setting"]]),
            )
    prem = await utils.get_user_premium(uid)
    menu_settings = await utils.get_user_premmenu_settings(uid)
    await utils.edit_message(
        await messages.premmenu(menu_settings, prem),
        message.peer_id,
        message.conversation_message_id,
        keyboard.premmenu(uid, menu_settings, prem),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["premmenu_action"])
)
async def premmenu_action(message: MessageEvent):
    uid = message.user_id
    peer_id = message.peer_id
    if not message.payload:
        return
    setting = message.payload["setting"]

    async with (await pool()).acquire() as conn:
        if not (
            deleted := await conn.fetchval(
                "delete from premmenu where uid=$1 and setting=$2 and value is not null "
                "and value!='' returning 1",
                uid,
                setting,
            )
        ):
            await conn.execute(
                "insert into typequeue (chat_id, uid, type, additional) values ($1, $2, $3, $4)",
                peer_id - 2000000000,
                uid,
                f"premmenu_action_{setting}",
                "{}",
            )
    if deleted:
        prem = await utils.get_user_premium(uid)
        menu_settings = await utils.get_user_premmenu_settings(uid)
        await utils.edit_message(
            await messages.premmenu(menu_settings, prem),
            peer_id,
            message.conversation_message_id,
            keyboard.premmenu(uid, menu_settings, prem),
        )
        return
    await utils.edit_message(
        await messages.premmenu_action(setting),
        peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["settings_menu"])
)
async def settings_menu(message: MessageEvent):
    await utils.edit_message(
        await messages.settings_(),
        message.peer_id,
        message.conversation_message_id,
        keyboard.settings_(message.user_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["settings_menu_antispam"]),
)
async def settings_menu_antispam(message: MessageEvent):
    if not message.payload:
        return
    punishments = {
        "warn": "предупреждение",
        "kick": "исключение",
        "mute": "ограничение",
        "ban": "блокировка",
        "deletemessage": "нет",
    }
    payload = message.payload
    async with (await pool()).acquire() as conn:
        chat_settings = {
            i[0]: i[:3] + (punishments[i[3].split("|")[0]] if i[3] else None,) + i[4:]
            for i in [
                await managers.chat_settings.get(
                    *i, ("setting", "pos", "value", "punishment", "pos2")
                )
                for i in await managers.chat_settings.get_by_field(
                    chat_id=message.peer_id - 2000000000
                )
            ]
        }

    if payload["setting"] == "msgs":
        chrs, msgs = [
            chat_settings.get(i, (i, None, None, None, None))
            for i in ("maximumCharsInMessage", "messagesPerMinute")
        ]
        msgslimit, chrslimit = "не задан", "не задан"
        if val := msgs[2]:
            msgslimit = utils.pluralize_words(
                val, ("соообщение", "сообщения", "сообщений")
            )
        if val := chrs[2]:
            chrslimit = utils.pluralize_words(val, ("символ", "символа", "символов"))

        msg = f"""💬 Сообщения\nНастройте лимиты на длину и частоту сообщений.\n
1️⃣ Сообщений в минуту
• Лимит: {msgslimit}
• Наказание: {msgs[3] or "нет"}
• Удалять сообщения: {"да" if msgs[4] else "нет"}

2️⃣ Максимальная длина
• Лимит: {chrslimit}
• Наказание: {chrs[3] or "нет"}
• Удалять сообщения: {"да" if chrs[4] else "нет"}"""
        kbd = keyboard.settings_antispam_msgs(message.user_id)

    elif payload["setting"] == "spam":
        async with (await pool()).acquire() as conn:
            vklexcs = await conn.fetchval(
                "select count(*) as c from vklinksexceptions where chat_id=$1",
                message.peer_id - 2000000000,
            )
            fwdexcs = await conn.fetchval(
                "select count(*) as c from forwardedsexceptions where chat_id=$1",
                message.peer_id - 2000000000,
            )
            lnkexcs = await conn.fetchval(
                "select count(*) as c from antispamurlexceptions where chat_id=$1",
                message.peer_id - 2000000000,
            )
        vkls, fwds, lnks = [
            chat_settings.get(i, (i, None, None, None, None))
            for i in ("vkLinks", "forwardeds", "disallowLinks")
        ]
        types = fwds[2] or 0
        if isinstance(types, str):
            if types.isdigit():
                types = int(types)
            else:
                types = 0
        msg = f"""🚷 Спам-фильтры\nНастройте защиту от нежелательного контента.\n
1️⃣ Ссылки на ВК
• Статус: {"вкл." if vkls[1] else "выкл."}
• Наказание: {vkls[3] or "нет"}
• Удаление сообщений: {"да" if vkls[4] else "нет"}
• Исключения: {vklexcs} шт.

2️⃣ Пересылки
• Статус: {"вкл." if fwds[1] else "выкл."}
• Наказание: {fwds[3] or "нет"}
• Типы: {["все", "пользователи", "сообщества"][types]}
• Удаление сообщений: {"да" if fwds[4] else "нет"}
• Исключения: {fwdexcs} шт.

3️⃣ Ссылки
• Статус: {"вкл." if lnks[1] else "выкл."}
• Наказание: {lnks[3] or "нет"}
• Исключения: {lnkexcs} шт.
"""
        kbd = keyboard.settings_antispam_spam(message.user_id)
    else:
        raise Exception("Unexpected setting")

    await utils.edit_message(msg, message.peer_id, message.conversation_message_id, kbd)


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["settings", "change_setting"]),
)
async def chat_settings(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    uid = message.user_id
    peer_id = message.peer_id
    chat_id = peer_id - 2000000000
    category = payload["category"]

    if payload["cmd"] == "settings":
        chat_settings = (await utils.get_chat_settings(chat_id))[category]
        await utils.edit_message(
            await messages.settings_category(category, chat_settings, chat_id),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_category(uid, category, chat_settings),
        )
        return
    setting = payload["setting"]
    if setting in settings.settings_meta.premium and not await utils.get_user_premium(
        uid
    ):
        await utils.edit_message(
            await messages.no_prem(),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_goto(uid),
        )
        return
    chat_settings = await utils.get_chat_settings(chat_id)
    altsettings = await utils.get_chat_alt_settings(chat_id)
    if setting not in settings.settings_meta.countable:
        if setting in chat_settings[category]:
            chat_settings[category][setting] = not chat_settings[category][setting]
        else:
            altsettings[category][setting] = not altsettings[category][setting]
        await utils.turn_chat_setting(chat_id, category, setting)
        await utils.edit_message(
            await messages.settings_category(
                category, chat_settings[category], chat_id
            ),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_category(uid, category, chat_settings[category]),
        )
        return
    chatsetting = await managers.chat_settings.get(
        chat_id, setting, ("value", "value2", "punishment")
    )
    await utils.edit_message(
        await messages.settings_change_countable(
            chat_id,
            setting,
            chat_settings[category][setting],
            None if chatsetting is None else chatsetting[0],
            None if chatsetting is None else chatsetting[1],
            altsettings[category][setting]
            if (category in altsettings and setting in altsettings[category])
            else None,
            None if chatsetting is None else chatsetting[2],
        ),
        peer_id,
        message.conversation_message_id,
        keyboard.settings_change_countable(
            uid, category, setting, chat_settings, altsettings
        ),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["settings_change_countable"]),
)
async def settings_change_countable(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    uid = message.user_id
    peer_id = message.peer_id
    chat_id = peer_id - 2000000000
    action = payload["action"]
    category = payload["category"]
    setting = payload["setting"]

    if setting in settings.settings_meta.premium and not await utils.get_user_premium(
        uid
    ):
        await utils.edit_message(
            await messages.no_prem(),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_goto(uid),
        )
        return
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "delete from typequeue where chat_id=$1 and uid=$2", chat_id, uid
        )
    if action in ("turn", "turnalt"):
        chat_settings = await utils.get_chat_settings(chat_id)
        altsettings = await utils.get_chat_alt_settings(chat_id)
        if action == "turn":
            chat_settings[category][setting] = not chat_settings[category][setting]
        else:
            altsettings[category][setting] = not altsettings[category][setting]
        await utils.turn_chat_setting(
            chat_id, category, setting, alt=action == "turnalt"
        )
        chatsetting = await managers.chat_settings.get(
            chat_id, setting, ("value", "value2", "punishment", "pos", "pos2")
        )
        await utils.edit_message(
            await messages.settings_change_countable(
                chat_id,
                setting,
                chat_settings[category][setting],
                None if chatsetting is None else chatsetting[0],
                None if chatsetting is None else chatsetting[1],
                altsettings[category][setting]
                if (category in altsettings and setting in altsettings[category])
                else None,
                None if chatsetting is None else chatsetting[2],
            ),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_change_countable(
                uid, category, setting, chat_settings, altsettings
            ),
        )
        return
    if action == "set":
        if setting == "welcome":
            async with (await pool()).acquire() as conn:
                w = await conn.fetchrow(
                    "select msg, photo, url from welcome where chat_id=$1", chat_id
                )
            if w:
                await utils.edit_message(
                    await messages.settings_countable_action(
                        action, setting, w[0], w[1], w[2]
                    ),
                    peer_id,
                    message.conversation_message_id,
                    keyboard.settings_set_welcome(uid, w[0], w[1], w[2]),
                )
                return
            await utils.edit_message(
                await messages.settings_countable_action(action, setting),
                peer_id,
                message.conversation_message_id,
                keyboard.settings_set_welcome(uid, None, None, None),
            )
            return
        async with (await pool()).acquire() as conn:
            await conn.execute(
                "insert into typequeue (chat_id, uid, type, additional) values ($1, $2, $3, $4)",
                chat_id,
                uid,
                "settings_change_countable",
                "{" + f'"setting": "{setting}", "category": "{category}", "cmid": '
                f'"{message.conversation_message_id}"' + "}",
            )
        await utils.edit_message(
            await messages.settings_countable_action(action, setting),
            peer_id,
            message.conversation_message_id,
        )
        return
    elif action == "setPunishment":
        await utils.edit_message(
            await messages.settings_choose_punishment(),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_set_punishment(uid, category, setting),
        )
        return
    elif action == "setPreset":
        chatsetting = await managers.chat_settings.get(chat_id, setting, "value")
        await utils.edit_message(
            await messages.settings_set_preset(category, setting),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_set_preset(uid, category, setting, chatsetting),
        )
        return
    elif action in ("setWhitelist", "setBlacklist"):
        await utils.edit_message(
            await messages.settings_setlist(setting, action[3:-4]),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_setlist(uid, category, setting, action[3:-4]),
        )
        return


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["settings_set_preset"]),
)
async def settings_set_preset(message: MessageEvent):
    if not message.payload:
        return
    if not message.payload:
        return
    payload = message.payload
    uid = message.user_id
    peer_id = message.peer_id
    chat_id = peer_id - 2000000000
    action = payload["action"]
    category = payload["category"]
    setting = payload["setting"]
    data = payload["data"]

    if action == "setValue":
        await managers.chat_settings.edit(chat_id, setting, value=data["value"])
        await utils.edit_message(
            await messages.settings_set_preset(category, setting),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_set_preset(uid, category, setting, data["value"]),
        )
        return


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["settings_set_punishment"]),
)
async def settings_set_punishment(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    uid = message.user_id
    peer_id = message.peer_id
    chat_id = peer_id - 2000000000
    action = payload["action"]  # 'deletemessage' or 'kick' or 'mute' or 'ban'
    category = payload["category"]
    setting = payload["setting"]

    if setting in settings.settings_meta.premium and not await utils.get_user_premium(
        uid
    ):
        await utils.edit_message(
            await messages.no_prem(),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_goto(uid),
        )
        return
    if action in ["deletemessage", "kick", "", "warn"]:
        await managers.chat_settings.edit(chat_id, setting, punishment=action or None)
        await utils.edit_message(
            await messages.settings_set_punishment(action),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_change_countable(
                uid,
                category,
                setting,
                await utils.get_chat_settings(chat_id),
                await utils.get_chat_alt_settings(chat_id),
                True,
            ),
        )
        return
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "insert into typequeue (chat_id, uid, type, additional) values ($1, $2, $3, $4)",
            chat_id,
            uid,
            "settings_set_punishment",
            "{"
            + f'"setting": "{setting}", "action": "{action}", "category": "{category}", '
            f'"cmid": "{message.conversation_message_id}"' + "}",
        )
    await utils.edit_message(
        await messages.settings_set_punishment_input(action),
        peer_id,
        message.conversation_message_id,
    )
    return


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["settings_exceptionlist"]),
)
async def settings_exceptionlist(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    uid = message.user_id
    peer_id = message.peer_id
    setting = payload["setting"]

    if setting in settings.settings_meta.premium and not await utils.get_user_premium(
        uid
    ):
        await utils.edit_message(
            await messages.no_prem(),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_goto(uid),
        )
        return
    if setting == "disallowLinks":
        async with (await pool()).acquire() as conn:
            lst = await conn.fetch(
                "select url from antispamurlexceptions where chat_id=$1",
                peer_id - 2000000000,
            )
        await utils.edit_message(
            await messages.settings_exceptionlist([i[0] for i in lst]),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_change_countable(
                uid, category="antispam", setting=setting, onlybackbutton=True
            ),
        )
    if setting == "vkLinks":
        async with (await pool()).acquire() as conn:
            lst = await conn.fetch(
                "select url from vklinksexceptions where chat_id=$1",
                peer_id - 2000000000,
            )
        await utils.edit_message(
            await messages.settings_exceptionlist([i[0] for i in lst]),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_change_countable(
                uid, category="antispam", setting=setting, onlybackbutton=True
            ),
        )
    if setting == "forwardeds":
        async with (await pool()).acquire() as conn:
            lst = await conn.fetch(
                "select exc_id from forwardedsexceptions where chat_id=$1",
                peer_id - 2000000000,
            )
        await utils.edit_message(
            await messages.settings_exceptionlist(
                [
                    f"[id{i[0]}|{await utils.get_user_name(i[0]) if i[0] > 0 else await utils.get_group_name(i[0])}]"
                    for i in lst
                ]
            ),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_change_countable(
                uid, category="antispam", setting=setting, onlybackbutton=True
            ),
        )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["settings_listaction"]),
)
async def settings_listaction(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    uid = message.user_id
    peer_id = message.peer_id
    category = payload["category"]
    setting = payload["setting"]
    action = payload["action"]

    if setting in settings.settings_meta.premium and not await utils.get_user_premium(
        uid
    ):
        await utils.edit_message(
            await messages.no_prem(),
            peer_id,
            message.conversation_message_id,
            keyboard.settings_goto(uid),
        )
        return

    async with (await pool()).acquire() as conn:
        await conn.execute(
            "insert into typequeue (chat_id, uid, type, additional) values ($1, $2, $3, $4)",
            peer_id - 2000000000,
            uid,
            "settings_listaction",
            "{"
            + f'"setting": "{setting}", "category": "{category}", "action": "{action}", "type": "{payload["type"]}"'
            + "}",
        )
    await utils.edit_message(
        await messages.settings_listaction_action(setting, action),
        peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(
        [
            "settings_set_welcome_text",
            "settings_set_welcome_photo",
            "settings_set_welcome_url",
        ]
    ),
)
async def settings_set_welcome(message: MessageEvent):
    if not message.payload:
        return
    cmd = message.payload["cmd"]
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "insert into typequeue (chat_id, uid, type, additional) values ($1, $2, $3, '{}')",
            message.peer_id - 2000000000,
            message.user_id,
            cmd,
        )
    await utils.edit_message(
        await messages.get(cmd), message.peer_id, message.conversation_message_id
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(
        [
            "settings_unset_welcome_text",
            "settings_unset_welcome_photo",
            "settings_unset_welcome_url",
        ]
    ),
)
async def settings_unset_welcome(message: MessageEvent):
    if not message.payload:
        return
    cmd = message.payload["cmd"]
    peer_id = message.peer_id
    chat_id = peer_id - 2000000000

    async with (await pool()).acquire() as conn:
        welcome = await conn.fetchrow(
            "select msg, photo, url from welcome where chat_id=$1", chat_id
        )
        text = welcome[0]
        img = welcome[1]
        url = welcome[2]
        if cmd in [
            "settings_unset_welcome_text",
            "settings_unset_welcome_photo",
        ] and not (
            (text and ((img and url) or (not img and not url) or not url))
            or (img and ((text and url) or (not text and not url) or not url))
        ):
            return
        await conn.execute(
            "update welcome set msg = $1, photo = $2, url = $3 where chat_id=$4",
            None if cmd == "settings_unset_welcome_text" else text,
            None if cmd == "settings_unset_welcome_photo" else img,
            None if cmd == "settings_unset_welcome_url" else url,
            chat_id,
        )
    await utils.edit_message(
        await messages.settings_countable_action("set", "welcome"),
        peer_id,
        message.conversation_message_id,
        keyboard.settings_set_welcome(message.user_id, text, img, url),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["nicklist"])
)
async def nicklist(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    async with (await pool()).acquire() as conn:
        res = await conn.fetch(
            "select uid, nickname from nickname where chat_id=$1 and uid>0 and uid=ANY($2) and nickname is not null"
            " order by nickname",
            chat_id,
            [
                i.member_id
                for i in (
                    await api.messages.get_conversation_members(
                        peer_id=chat_id + 2000000000
                    )
                ).items
            ],
        )
    count = len(res)
    res = res[:30]
    await utils.edit_message(
        await messages.nlist(res, await api.users.get(user_ids=[i[0] for i in res])),
        peer_id,
        message.conversation_message_id,
        keyboard.nlist(message.user_id, 0, count),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["prev_page_nlist", "next_page_nlist"]),
)
async def page_nlist(message: MessageEvent):
    if not message.payload:
        return
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    page = message.payload["page"]

    members_uid = [
        i.member_id
        for i in (
            await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        ).items
    ]
    async with (await pool()).acquire() as conn:
        res = await conn.fetch(
            "select uid, nickname from nickname where chat_id=$1 and uid>0 and uid=ANY($2) and nickname is not null"
            " order by nickname",
            chat_id,
            members_uid,
        )
    if not (count := len(res)):
        return
    res = res[page * 30 : page * 30 + 30]
    await utils.edit_message(
        await messages.nlist(
            res, await api.users.get(user_ids=[i[0] for i in res]), page
        ),
        peer_id,
        message.conversation_message_id,
        keyboard.nlist(message.user_id, page, count),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["nonicklist"])
)
async def nonicklist(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    async with (await pool()).acquire() as conn:
        res = [
            i[0]
            for i in await conn.fetch(
                "select uid from nickname where chat_id=$1 and uid>0 and nickname is not null",
                chat_id,
            )
        ]
    members_uid = [
        i.member_id
        for i in (
            await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        ).items
        if i.member_id not in res
    ]
    count = len(members_uid)
    members_uid = members_uid[:30]
    await utils.edit_message(
        await messages.nnlist(await api.users.get(user_ids=members_uid)),  # type: ignore
        peer_id,
        message.conversation_message_id,
        keyboard.nnlist(message.user_id, 0, count),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["prev_page_nnlist", "next_page_nnlist"]),
)
async def page_nnlist(message: MessageEvent):
    if not message.payload:
        return
    peer_id = message.object.peer_id
    page = message.payload["page"]

    async with (await pool()).acquire() as conn:
        res = [
            i[0]
            for i in await conn.fetch(
                "select uid from nickname where chat_id=$1 and uid>0 and nickname is not null",
                peer_id - 2000000000,
            )
        ]
    members = await api.messages.get_conversation_members(peer_id=peer_id)
    members_count = len(members.items[page * 30 :])
    members = [i for i in members.items if i.member_id not in res][
        page * 30 : page * 30 + 30
    ]
    if len(members) <= 0:
        return
    await utils.edit_message(
        await messages.nnlist(
            await api.users.get(user_ids=[f"{i.member_id}" for i in members]), page
        ),
        peer_id,
        message.conversation_message_id,
        keyboard.nnlist(message.user_id, page, members_count),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["prev_page_mutelist", "next_page_mutelist"]),
)
async def page_mutelist(message: MessageEvent):
    if not message.payload:
        return
    peer_id = message.object.peer_id
    page = message.payload["page"]

    async with (await pool()).acquire() as conn:
        res = await conn.fetch(
            "select uid, chat_id, last_mutes_causes, mute, last_mutes_names from mute where chat_id=$1 and "
            "mute>$2 order by uid desc",
            peer_id - 2000000000,
            time.time(),
        )
    if not (count := len(res)):
        return
    await utils.edit_message(
        await messages.mutelist(res[page * 30 : page * 30 + 30], count),
        peer_id,
        message.conversation_message_id,
        keyboard.mutelist(message.user_id, page, count),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["prev_page_warnlist", "next_page_warnlist"]),
)
async def page_warnlist(message: MessageEvent):
    if not message.payload:
        return
    peer_id = message.object.peer_id
    page = message.payload["page"]

    async with (await pool()).acquire() as conn:
        res = await conn.fetch(
            "select uid, chat_id, last_warns_causes, warns, last_warns_names from warn where chat_id=$1 and"
            " warns>0 order by uid desc",
            peer_id - 2000000000,
        )
    if not (count := len(res)):
        return
    res = res[page * 30 : page * 30 + 30]
    await utils.edit_message(
        await messages.warnlist(res, count),
        peer_id,
        message.conversation_message_id,
        keyboard.warnlist(message.user_id, page, count),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["prev_page_banlist", "next_page_banlist"]),
)
async def page_banlist(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    peer_id = message.object.peer_id
    page = payload["page"] + (-1 if payload["cmd"].startswith("prev") else 1)

    if page < 0:
        return
    async with (await pool()).acquire() as conn:
        res = await conn.fetch(
            "select uid, chat_id, last_bans_causes, ban, last_bans_names from ban where chat_id=$1 and "
            "ban>$2 order by uid desc",
            peer_id - 2000000000,
            time.time(),
        )
    if not res:
        return
    banned_count = len(res)
    res = res[page * 30 : page * 30 + 30]
    await utils.edit_message(
        await messages.banlist(res, banned_count),
        peer_id,
        message.conversation_message_id,
        keyboard.banlist(message.user_id, page, banned_count),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(
        ["mutelist_delall", "warnlist_delall", "banlist_delall"], answer=False
    ),
)
async def punishlist_delall(message: MessageEvent):
    if not message.payload:
        return
    cmd: str = message.payload["cmd"]
    uid = message.object.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if await utils.get_user_access_level(uid, chat_id, ignore_custom=True) < 6:
        await message.show_snackbar("❌ Для данной функции требуется 6 уровень доступа")
        return
    await utils.send_message_event_answer(message.event_id, uid, peer_id)

    async with (await pool()).acquire() as conn:
        if cmd.startswith("mute"):
            uids = await conn.fetch(
                "update mute set mute=0 where chat_id=$1 returning uid", chat_id
            )
            for i in uids:
                await utils.set_chat_mute(i[0], chat_id, 0)
        elif cmd.startswith("warn"):
            await conn.execute("update warn set warns=0 where chat_id=$1", chat_id)
        elif cmd.startswith("ban"):
            await conn.execute("update ban set ban=0 where chat_id=$1", chat_id)
        else:
            raise Exception('cmd.startswith("mute" or "warn" or "ban")')
    await utils.edit_message(
        await messages.punishlist_delall_done(cmd.replace("list_delall", "")),
        peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["prev_page_statuslist", "next_page_statuslist"]),
)
async def page_statuslist(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    page = payload["page"] + (-1 if payload["cmd"].startswith("prev") else 1)

    if page < 0:
        return
    async with (await pool()).acquire() as conn:
        premium_pool = await conn.fetch(
            "select uid, time from premium where time>$1 order by time desc", time.time()
        )
    if len(premium_pool) <= 0:
        return
    premium_pool = premium_pool[page * 30 : page * 30 + 30]
    await utils.edit_message(
        await messages.statuslist(premium_pool),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.statuslist(message.user_id, page, len(premium_pool)),
    )


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["demote"]))
async def demote(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    await utils.edit_message(
        await messages.demote_yon(),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.demote_accept(message.user_id, payload["chat_id"], payload["option"]),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["demote_accept"])
)
async def demote_accept(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    option = payload["option"]

    if option == "all":
        members = await api.messages.get_conversation_members(
            peer_id=chat_id + 2000000000
        )
        for i in members.items:
            if not i.is_admin and i.member_id > 0:
                await utils.kick_user(i.member_id, chat_id)
    elif option == "lvl":
        members = await api.messages.get_conversation_members(
            peer_id=chat_id + 2000000000
        )
        kicking = []
        for i in members.items:
            if not i.is_admin and i.member_id > 0:
                acc = await utils.get_user_access_level(i.member_id, chat_id)
                if acc == 0:
                    kicking.append(i.member_id)
        for i in kicking:
            await utils.kick_user(i, chat_id)
    await utils.edit_message(
        await messages.demote_accept(
            payload["uid"] if "uid" in payload else message.user_id,
            await utils.get_user_name(uid),
            await utils.get_user_nickname(uid, chat_id),
        ),
        peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["demote_disaccept"])
)
async def demote_disaccept(message: MessageEvent):
    await utils.edit_message(
        await messages.demote_disaccept(),
        message.object.peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["giveowner_no"])
)
async def giveowner_no(message: MessageEvent):
    await utils.edit_message(
        await messages.giveowner_no(),
        message.object.peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["giveowner"])
)
async def giveowner(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    chat_id = payload["chat_id"]
    uid = payload["uid"]
    id = payload["chid"]

    await managers.access_level.delete(uid, chat_id)
    async with (await pool()).acquire() as conn:
        await conn.execute("delete from gpool where chat_id=$1", chat_id)
        await conn.execute("delete from chatgroups where chat_id=$1", chat_id)
    await utils.set_user_access_level(id, chat_id, 7)
    await utils.set_chat_mute(id, chat_id, 0)

    await utils.edit_message(
        await messages.giveowner(
            uid,
            await utils.get_user_nickname(uid, chat_id),
            await utils.get_user_name(uid),
            id,
            await utils.get_user_nickname(id, chat_id),
            await utils.get_user_name(id),
        ),
        message.object.peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["top"]))
async def top_(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    conv_members = await api.messages.get_conversation_members(
        peer_id=peer_id,
        fields=["deactivated"],  # type: ignore
    )
    if not conv_members:
        top = []
    else:
        async with (await pool()).acquire() as conn:
            top = await conn.fetch(
                "select uid, messages from messages where uid>0 and messages>0 and chat_id=$1 and "
                "uid=ANY($2) and uid!=ALL($3) order by messages desc limit 10",
                chat_id,
                [
                    i.member_id
                    for i in (
                        await api.messages.get_conversation_members(peer_id=peer_id)
                    ).items
                ],
                [i.id for i in (conv_members.profiles or []) if i.deactivated],
            )
    await utils.edit_message(
        await messages.top(top),
        peer_id,
        message.conversation_message_id,
        keyboard.top(chat_id, message.user_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["top_leagues"])
)
async def top_leagues(message: MessageEvent):
    if not message.payload:
        return
    peer_id = message.object.peer_id
    lg = message.payload["league"]
    top = await utils.get_xp_top("lvl", league=lg)
    chattop = await utils.get_xp_top(
        "lvl",
        league=lg,
        users=[
            i.id
            for i in (
                await api.messages.get_conversation_members(
                    peer_id=peer_id,
                    fields=["deactivated"],  # type: ignore
                )
            ).profiles
            if not i.deactivated
        ],
    )
    availableleagues = [i - 1 for i in await managers.xp.get_not_empty_leagues()]
    await utils.edit_message(
        await messages.top_lvls(top, chattop),
        peer_id,
        message.conversation_message_id,
        keyboard.top_leagues(
            peer_id - 2000000000, message.user_id, lg, availableleagues
        ),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["top_duels"])
)
async def top_duels(message: MessageEvent):
    peer_id = message.object.peer_id
    async with (await pool()).acquire() as conn:
        top = await conn.fetch(
            "select uid, wins from duelwins where uid>0 order by wins desc limit 10"
        )
    top = {i[0]: i for i in top}
    users = {
        u.id: u
        for u in await api.users.get(
            user_ids=[i for i in top.keys()],
            fields=["deactivated"],  # type: ignore
        )
    }
    await utils.edit_message(
        await messages.top_duels(
            sorted(
                [
                    i
                    for uid, i in top.items()
                    if uid in users and not users[uid].deactivated
                ][:10],
                key=lambda i: i[1],
                reverse=True,
            )
        ),
        peer_id,
        message.conversation_message_id,
        keyboard.top_duels(peer_id - 2000000000, message.user_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["top_duels_in_chat"])
)
async def top_duels_in_chat(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    conv_members = await api.messages.get_conversation_members(
        peer_id=peer_id,
        fields=["deactivated"],  # type: ignore
    )
    if not conv_members:
        top = []
    else:
        async with (await pool()).acquire() as conn:
            top = await conn.fetch(
                "select uid, wins from duelwins where uid>0 and uid=ANY($1) and uid!=ALL($2) order by wins desc limit 10",
                [
                    i.member_id
                    for i in (
                        await api.messages.get_conversation_members(
                            peer_id=chat_id + 2000000000
                        )
                    ).items
                ],
                [i.id for i in (conv_members.profiles or []) if i.deactivated],
            )
    await utils.edit_message(
        await messages.top_duels(top, "в беседе"),
        peer_id,
        message.conversation_message_id,
        keyboard.top_duels_in_chat(chat_id, message.user_id),
    )


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["top_rep"]))
async def top_rep(message: MessageEvent):
    peer_id = message.object.peer_id
    async with (await pool()).acquire() as conn:
        top = await conn.fetch(
            "select uid, rep from reputation where uid>0 order by rep desc limit 10"
        )
    top = {i[0]: i for i in top}
    users = {
        u.id: u
        for u in await api.users.get(
            user_ids=[i for i in top.keys()],
            fields=["deactivated"],  # type: ignore
        )
    }
    await utils.edit_message(
        await messages.top_rep(
            sorted(
                [
                    i
                    for uid, i in top.items()
                    if uid in users and not users[uid].deactivated
                ][:10],
                key=lambda i: i[1],
                reverse=True,
            ),
            "общее | положительные",
        ),
        peer_id,
        message.conversation_message_id,
        keyboard.top_rep(peer_id - 2000000000, message.user_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["top_rep_neg"])
)
async def top_rep_neg(message: MessageEvent):
    peer_id = message.object.peer_id
    async with (await pool()).acquire() as conn:
        top = await conn.fetch(
            "select uid, rep from reputation where uid>0 order by rep limit 10"
        )
    top = {i[0]: i for i in top}
    users = {
        u.id: u
        for u in await api.users.get(
            user_ids=[i for i in top.keys()],
            fields=["deactivated"],  # type: ignore
        )
    }
    await utils.edit_message(
        await messages.top_rep(
            sorted(
                [
                    i
                    for uid, i in top.items()
                    if uid in users and not users[uid].deactivated
                ][:10],
                key=lambda i: i[1],
            ),
            "общее | отрицательные",
        ),
        peer_id,
        message.conversation_message_id,
        keyboard.top_rep_neg(peer_id - 2000000000, message.user_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["top_rep_in_chat"])
)
async def top_rep_in_chat(message: MessageEvent):
    peer_id = message.object.peer_id
    conv_members = await api.messages.get_conversation_members(
        peer_id=peer_id,
        fields=["deactivated"],  # type: ignore
    )
    if not conv_members:
        top = []
    else:
        async with (await pool()).acquire() as conn:
            top = await conn.fetch(
                "select uid, rep from reputation where uid>0 and uid=ANY($1) and uid!=ALL($2) order by rep desc limit 10",
                [
                    i.member_id
                    for i in (
                        await api.messages.get_conversation_members(peer_id=peer_id)
                    ).items
                ],
                [i.id for i in (conv_members.profiles or []) if i.deactivated],
            )
    await utils.edit_message(
        await messages.top_rep(top, "в беседе | положительные"),
        peer_id,
        message.conversation_message_id,
        keyboard.top_rep_in_chat(peer_id - 2000000000, message.user_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["top_rep_in_chat_neg"]),
)
async def top_rep_in_chat_neg(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    conv_members = await api.messages.get_conversation_members(
        peer_id=peer_id,
        fields=["deactivated"],  # type: ignore
    )
    if not conv_members:
        top = []
    else:
        async with (await pool()).acquire() as conn:
            top = await conn.fetch(
                "select uid, rep from reputation where uid>0 and uid=ANY($1) and uid!=ALL($2) order by rep limit 10",
                [
                    i.member_id
                    for i in (
                        await api.messages.get_conversation_members(
                            peer_id=chat_id + 2000000000
                        )
                    ).items
                ],
                [i.id for i in (conv_members.profiles or []) if i.deactivated],
            )
    await utils.edit_message(
        await messages.top_rep(top, "в беседе | отрицательные"),
        peer_id,
        message.conversation_message_id,
        keyboard.top_rep_in_chat_neg(peer_id - 2000000000, message.user_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["top_math"])
)
async def top_math(message: MessageEvent):
    peer_id = message.object.peer_id
    async with (await pool()).acquire() as conn:
        top = await conn.fetch(
            "select winner, count(*) as wins from mathgiveaway where winner>0 group by winner order by wins desc limit 30"
        )
    top = {i[0]: i for i in top}
    users = {
        u.id: u
        for u in await api.users.get(
            user_ids=[i for i in top.keys()],
            fields=["deactivated"],  # type: ignore
        )
    }
    await utils.edit_message(
        await messages.top_math(
            sorted(
                [
                    i
                    for uid, i in top.items()
                    if uid in users and not users[uid].deactivated
                ],
                key=lambda x: x[1],
                reverse=True,
            )[:10]
        ),
        peer_id,
        message.conversation_message_id,
        keyboard.top_math(peer_id - 2000000000, message.user_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["top_bonus"])
)
async def top_bonus(message: MessageEvent):
    peer_id = message.object.peer_id
    async with (await pool()).acquire() as conn:
        top = await conn.fetch(
            "select uid, streak from bonus order by streak desc limit 10"
        )
    top = {i[0]: i for i in top}
    users = {
        u.id: u
        for u in await api.users.get(
            user_ids=[i for i in top.keys()],
            fields=["deactivated"],  # type: ignore
        )
    }
    await utils.edit_message(
        await messages.top_bonus(
            sorted(
                [
                    i
                    for uid, i in top.items()
                    if uid in users and not users[uid].deactivated
                ][:10],
                key=lambda i: i[1],
                reverse=True,
            )
        ),
        peer_id,
        message.conversation_message_id,
        keyboard.top_bonus(peer_id - 2000000000, message.user_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["top_bonus_in_chat"])
)
async def top_bonus_in_chat(message: MessageEvent):
    peer_id = message.object.peer_id

    conv_members = await api.messages.get_conversation_members(
        peer_id=peer_id,
        fields=["deactivated"],  # type: ignore
    )
    if not conv_members:
        top = []
    else:
        async with (await pool()).acquire() as conn:
            top = await conn.fetch(
                "select uid, streak from bonus where uid=ANY($1) and uid!=ALL($2) order by streak desc limit 10",
                [
                    i.member_id
                    for i in (
                        await api.messages.get_conversation_members(peer_id=peer_id)
                    ).items
                ],
                [i.id for i in (conv_members.profiles or []) if i.deactivated],
            )
    await utils.edit_message(
        await messages.top_bonus(top),
        peer_id,
        message.conversation_message_id,
        keyboard.top_bonus_in_chat(peer_id - 2000000000, message.user_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["top_coins"])
)
async def top_coins(message: MessageEvent):
    peer_id = message.object.peer_id
    await utils.edit_message(
        await messages.top_coins(await managers.xp.get_coins_top()),
        peer_id,
        message.conversation_message_id,
        keyboard.top_coins(peer_id - 2000000000, message.user_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["top_coins_in_chat"])
)
async def top_coins_in_chat(message: MessageEvent):
    peer_id = message.object.peer_id
    conv_members = await api.messages.get_conversation_members(
        peer_id=peer_id,
        fields=["deactivated"],  # type: ignore
    )
    if not conv_members:
        top = []
    else:
        top = await managers.xp.get_coins_top(
            in_uids=[i.member_id for i in conv_members.items]
        )
    await utils.edit_message(
        await messages.top_coins(top),
        peer_id,
        message.conversation_message_id,
        keyboard.top_coins_in_chat(peer_id - 2000000000, message.user_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["resetnick_accept"])
)
async def resetnick_accept(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "delete from nickname where chat_id=$1", peer_id - 2000000000
        )
    await utils.edit_message(
        await messages.resetnick_accept(uid, await utils.get_user_name(uid)),
        peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["resetnick_disaccept"]),
)
async def resetnick_disaccept(message: MessageEvent):
    await utils.edit_message(
        await messages.resetnick_disaccept(),
        message.object.peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["resetaccess_accept"])
)
async def resetaccess_accept(message: MessageEvent):
    if not message.payload:
        return
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    lvl = int(message.payload["lvl"])
    await managers.access_level.delete_rows(
        await managers.access_level.get_all(
            chat_id, predicate=lambda i: i.access_level == lvl and i.uid != uid
        )
    )
    await utils.edit_message(
        await messages.resetaccess_accept(uid, await utils.get_user_name(uid), lvl),
        peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["resetaccess_disaccept"]),
)
async def resetaccess_disaccept(message: MessageEvent):
    if not message.payload:
        return
    await utils.edit_message(
        await messages.resetaccess_disaccept(message.payload["lvl"]),
        message.object.peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["kick_nonick"])
)
async def kick_nonick(message: MessageEvent):
    uid = message.user_id
    chat_id = message.object.peer_id - 2000000000
    async with (await pool()).acquire() as conn:
        res = [
            i[0]
            for i in await conn.fetch(
                "select uid from nickname where chat_id=$1 and uid>0 and uid!=$2 and "
                "nickname is not null",
                chat_id,
                uid,
            )
        ]
    kicked = 0
    for i in (
        await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    ).items:
        if i.member_id not in res and i.member_id > 0:
            kicked += await utils.kick_user(i.member_id, chat_id)
    await utils.send_message(
        msg=await messages.kickmenu_kick_nonick(
            uid,
            await utils.get_user_name(uid),
            await utils.get_user_nickname(uid, chat_id),
            kicked,
        ),
        peer_ids=chat_id + 2000000000,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["kick_nick"])
)
async def kick_nick(message: MessageEvent):
    uid = message.user_id
    chat_id = message.object.peer_id - 2000000000
    kicked = 0
    async with (await pool()).acquire() as conn:
        nicknamed = await conn.fetch(
            "select uid from nickname where chat_id=$1 and uid>0 and uid!=$2 and "
            "nickname is not null",
            chat_id,
            uid,
        )
    for i in nicknamed:
        kicked += await utils.kick_user(i[0], chat_id)
    await utils.send_message(
        msg=await messages.kickmenu_kick_nick(
            uid,
            await utils.get_user_name(uid),
            await utils.get_user_nickname(uid, chat_id),
            kicked,
        ),
        peer_ids=chat_id + 2000000000,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["kick_banned"])
)
async def kick_banned(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    kicked = 0
    lst = (await api.messages.get_conversation_members(peer_id=peer_id)).items
    if len(lst) > 2900:
        async with (await pool()).acquire() as conn:
            lst = await conn.fetch(
                "select uid from userjoineddate where chat_id=$1", chat_id
            )
            lst = [i[0] for i in lst]
    else:
        lst = [i.member_id for i in lst]
    lst = await api.users.get(user_ids=lst)  # type: ignore
    for i in lst:
        if i.deactivated:
            kicked += await utils.kick_user(i.id, chat_id)
    await utils.send_message(
        msg=await messages.kickmenu_kick_banned(
            uid,
            await utils.get_user_name(uid),
            await utils.get_user_nickname(uid, chat_id),
            kicked,
        ),
        peer_ids=chat_id + 2000000000,
    )


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["notif"]))
async def notif(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    peer_id = message.object.peer_id
    async with (await pool()).acquire() as conn:
        notifs = await conn.fetch(
            "select status, name from notifications where chat_id=$1 order by name desc",
            peer_id - 2000000000,
        )
    await utils.edit_message(
        await messages.notifs(notifs),
        peer_id,
        message.conversation_message_id,
        keyboard.notif_list(
            message.user_id,
            notifs,
            int(payload["page"]) if payload["cmd"] == "page" in payload else 1,
        )
        if len(notifs) > 0
        else None,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["notif_select"])
)
async def notif_select(message: MessageEvent):
    if not message.payload:
        return
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    async with (await pool()).acquire() as conn:
        notif = await conn.fetchrow(
            "select name, text, time, every, tag, status from notifications where chat_id=$1 and name=$2",
            chat_id,
            message.payload["name"],
        )
        await conn.execute(
            "delete from typequeue where uid=$1 and chat_id=$2", uid, chat_id
        )
    await utils.edit_message(
        await messages.notification(*notif),
        peer_id,
        message.conversation_message_id,
        keyboard.notification(uid, notif[5], notif[0]),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["notification_status"]),
)
async def notification_status(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    turn_to = payload["turn"]
    name = payload["name"]
    async with (await pool()).acquire() as conn:
        snotif = await conn.fetchrow(
            "select time, every from notifications where chat_id=$1 and name=$2",
            chat_id,
            name,
        )
        ntime = snotif[0]
        while ntime < time.time() and snotif[1] > 0:
            ntime += snotif[1] * 60
        snotif = await conn.fetchrow(
            "update notifications set status = $1, time = $2 where chat_id=$3 and name=$4 returning text, every, "
            "tag",
            turn_to,
            ntime,
            chat_id,
            name,
        )
    await utils.edit_message(
        await messages.notification(
            name, snotif[0], ntime, snotif[1], snotif[2], turn_to
        ),
        peer_id,
        message.conversation_message_id,
        keyboard.notification(message.user_id, turn_to, name),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["notification_text"])
)
async def notification_text(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    peer_id = message.object.peer_id
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "insert into typequeue (chat_id, uid, type, additional) values ($1, $2, $3, $4)",
            peer_id - 2000000000,
            message.user_id,
            "notification_text",
            "{"
            + f'"name": "{payload["name"]}", "cmid": "{message.conversation_message_id}"'
            + "}",
        )
    await utils.edit_message(
        await messages.notification_changing_text(),
        peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["notification_time"])
)
async def notification_time(message: MessageEvent):
    if not message.payload:
        return
    await utils.edit_message(
        await messages.notification_changing_time_choose(),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.notification_time(message.user_id, message.payload["name"]),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["notification_time_change"]),
)
async def notification_time_change(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    peer_id = message.object.peer_id
    ctype = payload["type"]
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "insert into typequeue (chat_id, uid, type, additional) values ($1, $2, $3, $4)",
            peer_id - 2000000000,
            message.user_id,
            "notification_time_change",
            "{"
            + f'"name": "{payload["name"]}", "cmid": "{message.conversation_message_id}", "type": "{ctype}"'
            + "}",
        )
    if ctype == "single":
        await utils.edit_message(
            await messages.notification_changing_time_single(),
            peer_id,
            message.conversation_message_id,
        )
    elif ctype == "everyday":
        await utils.edit_message(
            await messages.notification_changing_time_everyday(),
            peer_id,
            message.conversation_message_id,
        )
    else:
        await utils.edit_message(
            await messages.notification_changing_time_everyxmin(),
            peer_id,
            message.conversation_message_id,
        )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["notification_tag"])
)
async def notification_tag(message: MessageEvent):
    if not message.payload:
        return
    await utils.edit_message(
        await messages.notification_changing_tag_choose(),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.notification_tag(message.user_id, message.payload["name"]),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["notification_tag_change"]),
)
async def notification_tag_change(message: MessageEvent):
    if not message.payload:
        return
    peer_id = message.object.peer_id
    name = message.payload["name"]
    ctype = message.payload["type"]
    async with (await pool()).acquire() as conn:
        notif = await conn.fetchrow(
            "update notifications set tag = $1 where chat_id=$2 and name=$3 returning text, time, every, status",
            int(ctype),
            peer_id - 2000000000,
            name,
        )
    await utils.edit_message(
        await messages.notification(
            name, notif[0], notif[1], notif[2], ctype, notif[3]
        ),
        peer_id,
        message.conversation_message_id,
        keyboard.notification(message.user_id, notif[3], name),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["notification_delete"]),
)
async def notification_delete(message: MessageEvent):
    if not message.payload:
        return
    peer_id = message.object.peer_id
    name = message.payload["name"]
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "delete from notifications where chat_id=$1 and name=$2",
            peer_id - 2000000000,
            name,
        )
    await utils.edit_message(
        await messages.notification_delete(name),
        peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["listasync"])
)
async def listasync(message: MessageEvent):
    if not message.payload:
        return
    uid = message.user_id
    page = message.payload["page"]
    async with (await pool()).acquire() as conn:
        chat_ids = [
            i[0]
            for i in await conn.fetch(
                "select chat_id from gpool where uid=$1 order by id desc", uid
            )
        ]
    total = len(chat_ids)
    chat_ids = chat_ids[(page - 1) * 10 : page * 10]
    names = (
        [await utils.get_chat_name(chat_id) for chat_id in chat_ids]
        if len(chat_ids) > 0
        else []
    )
    await utils.edit_message(
        await messages.listasync(
            [{"id": i, "name": names[k]} for k, i in enumerate(chat_ids)], total
        ),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.listasync(uid, total, page),
    )


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["help"]))
async def help(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    peer_id = message.object.peer_id
    async with (await pool()).acquire() as conn:
        cmds = await conn.fetch(
            "select cmd, lvl from commandlevels where chat_id=$1", peer_id - 2000000000
        )
    base = deepcopy(settings.commands.commands)
    for i in cmds:
        try:
            base[i[0]] = int(i[1])
        except Exception:
            pass
    await utils.edit_message(
        await messages.help(payload["page"], base),
        peer_id,
        message.conversation_message_id,
        keyboard.help(message.user_id, payload["page"], payload["prem"]),
    )


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["cmdlist"]))
async def cmdlist(message: MessageEvent):
    if not message.payload:
        return
    page = message.payload["page"]
    uid = message.user_id
    async with (await pool()).acquire() as conn:
        cmdnames = {
            i[0]: i[1]
            for i in await conn.fetch(
                "select cmd, name from cmdnames where uid=$1", uid
            )
        }
    await utils.edit_message(
        await messages.cmdlist(
            dict(list(cmdnames.items())[page * 10 : (page * 10) + 10]),
            page,
            len(list(cmdnames)),
        ),
        message.peer_id,
        message.conversation_message_id,
        keyboard.cmdlist(uid, page, len(cmdnames)),
    )


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["check"]))
async def check(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    sender = payload["uid"] if "uid" in payload else message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    id = payload["id"]
    check = payload["check"]
    if check == "ban":
        async with (await pool()).acquire() as conn:
            res = await conn.fetchrow(
                "select last_bans_causes, last_bans_names, last_bans_dates, last_bans_times from ban where "
                "chat_id=$1 and uid=$2",
                chat_id,
                id,
            )
        if res is not None:
            ban_date = literal_eval(res[0])[::-1][0]
            u_bans_names = literal_eval(res[1])[::-1]
            ban_from = u_bans_names[0]
            ban_reason = literal_eval(res[2])[::-1][0]
            ban_time = literal_eval(res[3])[::-1][0]
        else:
            u_bans_names = []
            ban_date = ban_from = ban_reason = ban_time = None
        await utils.edit_message(
            await messages.check_ban(
                id,
                await utils.get_user_name(id),
                await utils.get_user_nickname(id, chat_id),
                max(await utils.get_user_ban(id, chat_id) - time.time(), 0),
                u_bans_names,
                ban_date,
                ban_from,
                ban_reason,
                ban_time,
            ),
            peer_id,
            message.conversation_message_id,
            keyboard.check_history(sender, id, "ban", len(u_bans_names)),
        )
    elif check == "mute":
        async with (await pool()).acquire() as conn:
            res = await conn.fetchrow(
                "select last_mutes_causes, last_mutes_names, last_mutes_dates, last_mutes_times from mute "
                "where chat_id=$1 and uid=$2",
                chat_id,
                id,
            )
        if res is not None:
            mute_date = literal_eval(res[0])[::-1][0]
            u_mutes_names = literal_eval(res[1])[::-1]
            mute_from = u_mutes_names[0]
            mute_reason = literal_eval(res[2])[::-1][0]
            mute_time = literal_eval(res[3])[::-1][0]
        else:
            u_mutes_names = []
            mute_date = mute_from = mute_reason = mute_time = None
        await utils.edit_message(
            await messages.check_mute(
                id,
                await utils.get_user_name(id),
                await utils.get_user_nickname(id, chat_id),
                max(await utils.get_user_mute(id, chat_id) - time.time(), 0),
                u_mutes_names,
                mute_date,
                mute_from,
                mute_reason,
                mute_time,
            ),
            peer_id,
            message.conversation_message_id,
            keyboard.check_history(sender, id, "mute", len(u_mutes_names)),
        )
    elif check == "warn":
        async with (await pool()).acquire() as conn:
            res = await conn.fetchrow(
                "select last_warns_causes, last_warns_names, last_warns_dates from warn where uid=$1 and "
                "chat_id=$2",
                id,
                chat_id,
            )
        if res is not None:
            u_warns_causes = literal_eval(res[0])[::-1]
            u_warns_names = literal_eval(res[1])[::-1]
            u_warns_dates = literal_eval(res[2])[::-1]
        else:
            u_warns_names = u_warns_causes = u_warns_dates = []
        await utils.edit_message(
            await messages.check_warn(
                id,
                await utils.get_user_name(id),
                await utils.get_user_nickname(id, chat_id),
                await utils.get_user_warns(id, chat_id),
                u_warns_names,
                u_warns_dates,
                u_warns_names,
                u_warns_causes,
            ),
            peer_id,
            message.conversation_message_id,
            keyboard.check_history(sender, id, "warn", len(u_warns_causes)),
        )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["check_menu"])
)
async def check_menu(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    id = payload["id"]
    await utils.edit_message(
        await messages.check(
            id,
            await utils.get_user_name(id),
            await utils.get_user_nickname(id, chat_id),
            max(await utils.get_user_ban(id, chat_id) - time.time(), 0),
            await utils.get_user_warns(id, chat_id),
            max(await utils.get_user_mute(id, chat_id) - time.time(), 0),
        ),
        peer_id,
        message.conversation_message_id,
        keyboard.check(uid, id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["check_history"], answer=False),
)
async def check_history(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    id = payload["id"]
    check = payload["check"]
    if not int(payload["ie"]):
        await utils.send_message_event_answer(
            message.event_id,
            uid,
            message.peer_id,
            json.dumps({"type": "show_snackbar", "text": "Нету истории"}),
        )
        return
    await utils.send_message_event_answer(message.event_id, uid, peer_id)
    if check == "ban":
        async with (await pool()).acquire() as conn:
            res = await conn.fetchrow(
                "select last_bans_causes, last_bans_names, last_bans_dates, last_bans_times from ban where "
                "chat_id=$1 and uid=$2",
                chat_id,
                id,
            )
        if res is not None:
            bans_causes = literal_eval(res[0])[::-1][:50]
            bans_names = literal_eval(res[1])[::-1][:50]
            bans_dates = literal_eval(res[2])[::-1][:50]
            bans_times = literal_eval(res[3])[::-1][:50]
        else:
            bans_causes = bans_names = bans_dates = bans_times = []
        await utils.edit_message(
            await messages.check_history_ban(
                id,
                await utils.get_user_name(id),
                await utils.get_user_nickname(id, chat_id),
                bans_dates,
                bans_names,
                bans_times,
                bans_causes,
            ),
            peer_id,
            message.conversation_message_id,
        )
    elif check == "mute":
        async with (await pool()).acquire() as conn:
            res = await conn.fetchrow(
                "select last_mutes_causes, last_mutes_names, last_mutes_dates, last_mutes_times from "
                "mute where chat_id=$1 and uid=$2",
                chat_id,
                id,
            )
        if res is not None:
            mutes_causes = literal_eval(res[0])[::-1][:50]
            mutes_names = literal_eval(res[1])[::-1][:50]
            mutes_dates = literal_eval(res[2])[::-1][:50]
            mutes_times = literal_eval(res[3])[::-1][:50]
        else:
            mutes_causes = mutes_names = mutes_dates = mutes_times = []
        await utils.edit_message(
            await messages.check_history_mute(
                id,
                await utils.get_user_name(id),
                await utils.get_user_nickname(id, chat_id),
                mutes_dates,
                mutes_names,
                mutes_times,
                mutes_causes,
            ),
            peer_id,
            message.conversation_message_id,
        )
    elif check == "warn":
        async with (await pool()).acquire() as conn:
            res = await conn.fetchrow(
                "select last_warns_causes, last_warns_names, last_warns_dates, last_warns_times from warn "
                "where chat_id=$1 and uid=$2",
                chat_id,
                id,
            )
        if res is not None:
            warns_causes = literal_eval(res[0])[::-1][:50]
            warns_names = literal_eval(res[1])[::-1][:50]
            warns_dates = literal_eval(res[2])[::-1][:50]
            warns_times = literal_eval(res[3])[::-1][:50]
        else:
            warns_causes = warns_names = warns_dates = warns_times = []
        await utils.edit_message(
            await messages.check_history_warn(
                id,
                await utils.get_user_name(id),
                await utils.get_user_nickname(id, chat_id),
                warns_dates,
                warns_names,
                warns_times,
                warns_causes,
            ),
            peer_id,
            message.conversation_message_id,
        )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["unmute", "unwarn", "unban"], answer=False, checksender=False),
)
async def unpunish(message: MessageEvent):
    if not message.payload:
        return
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    cmd = payload["cmd"]
    id = payload["id"]
    cmid = payload["cmid"]
    u_acc = await utils.get_user_access_level(uid, chat_id)
    if u_acc <= await utils.get_user_access_level(id, chat_id) or not await haveAccess(
        cmd, chat_id, uid
    ):
        await message.show_snackbar("⛔️ У вас недостаточно прав.")
        return
    await utils.send_message_event_answer(message.event_id, uid, peer_id)

    name = await utils.get_user_name(id)
    nickname = await utils.get_user_nickname(id, chat_id)
    uname = await utils.get_user_name(uid)
    unickname = await utils.get_user_nickname(uid, chat_id)
    if cmd == "unmute":
        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                "update mute set mute=0 where chat_id=$1 and uid=$2 and mute>$3 returning 1",
                chat_id,
                id,
                time.time(),
            ):
                return
        await utils.set_chat_mute(id, chat_id, 0)
        await utils.edit_message(
            await messages.unmute(uname, unickname, uid, name, nickname, id),
            peer_id,
            message.conversation_message_id,
            keyboard.deletemessages(uid, [message.conversation_message_id]),
        )
    elif cmd == "unwarn":
        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                "update warn set warns=warns-1 where chat_id=$1 and uid=$2 and warns>0 and "
                "warns<3 returning 1",
                chat_id,
                id,
            ):
                return
        await utils.edit_message(
            await messages.unwarn(uname, unickname, uid, name, nickname, id),
            peer_id,
            message.conversation_message_id,
            keyboard.deletemessages(uid, [message.conversation_message_id]),
        )
    elif cmd == "unban":
        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                "update ban set ban=0 where chat_id=$1 and uid=$2 and ban>$3 returning 1",
                chat_id,
                id,
                time.time(),
            ):
                return
        await utils.edit_message(
            await messages.unban(uname, unickname, uid, name, nickname, id),
            peer_id,
            message.conversation_message_id,
            keyboard.deletemessages(uid, [message.conversation_message_id]),
        )
    else:
        return
    await utils.delete_messages(cmid, chat_id)


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["prefix_add", "prefix_del", "prefix_list", "prefix"]),
)
async def prefix_(message: MessageEvent):
    if not message.payload:
        return
    cmd = message.payload["cmd"]
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if not await utils.get_user_premium(uid):
        await utils.edit_message(
            await messages.no_prem(), peer_id, message.conversation_message_id
        )
        return
    async with (await pool()).acquire() as conn:
        if (
            cmd == "prefix_add"
            and await conn.fetchval(
                "select count(*) as c from prefix where uid=$1", uid
            )
            > 2
        ):
            await utils.edit_message(
                await messages.addprefix_max(),
                peer_id,
                message.conversation_message_id,
                keyboard.prefix_back(uid),
            )
            return
        if cmd in ("prefix_add", "prefix_del"):
            await conn.execute(
                "insert into typequeue (chat_id, uid, type, additional) values ($1, $2, $3, $4)",
                chat_id,
                uid,
                cmd,
                '{"cmid": ' + str(message.conversation_message_id) + "}",
            )
            await utils.edit_message(
                await messages.get(cmd), peer_id, message.conversation_message_id
            )
        elif cmd == "prefix_list":
            prefixes = await conn.fetch("select prefix from prefix where uid=$1", uid)
            await utils.edit_message(
                await messages.listprefix(
                    uid,
                    await utils.get_user_name(uid),
                    await utils.get_user_nickname(uid, chat_id),
                    prefixes,
                ),
                peer_id,
                message.conversation_message_id,
                keyboard.prefix_back(uid),
            )
        else:
            await utils.edit_message(
                await messages.prefix(),
                peer_id,
                message.conversation_message_id,
                keyboard.prefix(uid),
            )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["timeout_turn"])
)
async def timeout_turn(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    async with (await pool()).acquire() as conn:
        if (
            activated := await conn.fetchval(
                "update silencemode set activated=not activated where chat_id=$1 "
                "returning activated",
                chat_id,
            )
        ) is None:
            activated = True
            await conn.execute(
                "insert into silencemode (chat_id, activated, allowed) values ($1, $2, '[]')",
                chat_id,
                activated,
            )
    if activated:
        await utils.send_message(
            peer_id,
            await messages.timeouton(
                uid,
                await utils.get_user_name(uid),
                await utils.get_user_nickname(uid, chat_id),
            ),
        )
    else:
        await utils.send_message(
            peer_id,
            await messages.timeoutoff(
                uid,
                await utils.get_user_name(uid),
                await utils.get_user_nickname(uid, chat_id),
            ),
        )
    await utils.edit_message(
        await messages.timeout(activated),
        peer_id,
        message.conversation_message_id,
        keyboard.timeout(uid, activated),
    )


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["timeout"]))
async def timeout(message: MessageEvent):
    peer_id = message.object.peer_id
    activated = await utils.get_silence(peer_id - 2000000000)
    await utils.edit_message(
        await messages.timeout(activated),
        peer_id,
        message.conversation_message_id,
        keyboard.timeout(message.user_id, activated),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["timeout_settings"])
)
async def timeout_settings(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    async with (await pool()).acquire() as conn:
        if await conn.fetchval(
            "select exists(select 1 from silencemode where chat_id=$1 and activated=true)",
            chat_id,
        ):
            return
    if message.payload:
        custom = message.payload.get("custom", False)
        page = message.payload.get("page", 0)
    else:
        custom = False
        page = 0
    await utils.edit_message(
        await messages.timeout_settings(),
        peer_id,
        message.conversation_message_id,
        keyboard.timeout_settings(
            message.user_id,
            await utils.get_silence_allowed(chat_id, custom),
            custom,
            50 if await utils.get_user_premium(message.user_id) else 10,
            page,
        ),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["timeout_settings_turn"]),
)
async def timeout_settings_turn(message: MessageEvent):
    if not message.payload:
        return
    lvl = message.payload["lvl"]
    custom = message.payload.get("custom", False)
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    async with (await pool()).acquire() as conn:
        if await conn.fetchval(
            "select exists(select 1 from silencemode where chat_id=$1 and activated=true)",
            chat_id,
        ):
            return
    allowed = sorted(await utils.get_silence_allowed(chat_id, custom))
    if lvl in allowed:
        allowed.remove(lvl)
    else:
        allowed.append(lvl)
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            f"update silencemode set allowed{'_custom' if custom else ''} = $1 where chat_id=$2 returning 1",
            f"{allowed}",
            chat_id,
        ):
            await conn.execute(
                f"insert into silencemode (chat_id, activated, allowed{'_custom' if custom else ''}) values ($1, false, $2)",
                chat_id,
                f"{allowed}",
            )
    await utils.edit_message(
        await messages.timeout_settings(),
        peer_id,
        message.conversation_message_id,
        keyboard.timeout_settings(
            message.user_id,
            allowed,
            custom,
            50 if await utils.get_user_premium(message.user_id) else 10,
            message.payload.get("page", 0),
        ),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["turnpublic"])
)
async def turnpublic(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    chat = await managers.public_chats.get_chat(chat_id)
    if chat.premium if chat else False:
        prem = "Есть"
    else:
        prem = "Отсутствует"
    if not (chat.isopen if chat else False):
        public = "Открытый"
    else:
        public = "Приватный"
    await managers.public_chats.edit_chat(
        chat_id, isopen=not chat.isopen if chat else True
    )

    async with (await pool()).acquire() as conn:
        chatgroup = (
            "Привязана"
            if await conn.fetchval(
                "select exists(select 1 from chatgroups where chat_id=$1)", chat_id
            )
            else "Не привязана"
        )
        gpool = (
            "Привязана"
            if await conn.fetchval(
                "select exists(select 1 from gpool where chat_id=$1)", chat_id
            )
            else "Не привязана"
        )
        muted = await conn.fetchval(
            "select count(*) from mute where chat_id=$1 and mute>$2",
            chat_id,
            time.time(),
        )
        banned = await conn.fetchval(
            "select count(*) from ban where chat_id=$1 and ban>$2", chat_id, time.time()
        )
        if bjd := await conn.fetchval(
            "select time from botjoineddate where chat_id=$1", chat_id
        ):
            bjd = datetime.utcfromtimestamp(bjd).strftime("%d.%m.%Y %H:%M")
        else:
            bjd = "Невозможно определить"
    members = (
        await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    ).items
    id = [i for i in members if i.is_admin and i.is_owner][0].member_id
    try:
        names = await api.users.get(user_ids=[id])
        name = f"{names[0].first_name} {names[0].last_name}"
        prefix = "id"
    except Exception:
        name = await utils.get_group_name(-int(id))
        prefix = "club"
    await utils.edit_message(
        await messages.chat(
            id,
            name,
            chat_id,
            chatgroup,
            gpool,
            public,
            muted,
            banned,
            len(members),
            bjd,
            prefix,
            await utils.get_chat_name(chat_id),
            prem,
        ),
        peer_id,
        message.conversation_message_id,
        keyboard.chat(message.user_id, public == "Открытый"),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["antitag_list"])
)
async def antitag_list(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    async with (await pool()).acquire() as conn:
        users = set(
            [
                i[0]
                for i in await conn.fetch(
                    "select uid from antitag where chat_id=$1", chat_id
                )
            ]
        )
    await utils.edit_message(
        await messages.antitag_list(users, chat_id),
        peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["import"]))
async def import_(message: MessageEvent):
    if not message.payload:
        return
    importchatid = message.payload["importchatid"]
    if await utils.get_user_access_level(message.user_id, importchatid) < 7:
        await utils.edit_message(
            await messages.import_notowner(),
            message.object.peer_id,
            message.conversation_message_id,
        )
        return
    await utils.edit_message(
        await messages.import_(importchatid, await utils.get_chat_name(importchatid)),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.import_(message.user_id, importchatid),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["import_settings"])
)
async def import_settings(message: MessageEvent):
    if not message.payload:
        return
    importchid = message.payload["importchatid"]
    await utils.edit_message(
        await messages.import_settings(
            importchid,
            await utils.get_chat_name(importchid),
            s := await utils.get_import_settings(message.user_id, importchid),
        ),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.import_settings(message.user_id, importchid, s),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["import_turn"])
)
async def import_turn(message: MessageEvent):
    if not message.payload:
        return
    importchid = message.payload["importchatid"]
    setting = message.payload["setting"]
    await utils.turn_import_setting(importchid, message.user_id, setting)
    await utils.edit_message(
        await messages.import_settings(
            importchid,
            await utils.get_chat_name(importchid),
            s := await utils.get_import_settings(message.user_id, importchid),
        ),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.import_settings(message.user_id, importchid, s),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["import_start"])
)
async def import_start(message: MessageEvent):
    if not message.payload:
        return
    importchatid = message.payload["importchatid"]
    await utils.edit_message(
        await messages.import_start(importchatid),
        message.object.peer_id,
        message.conversation_message_id,
    )
    chatid = message.object.peer_id - 2000000000
    settings = await utils.get_import_settings(message.user_id, importchatid)
    async with (await pool()).acquire() as conn:
        if settings["sys"]:
            if i := await conn.fetchrow(
                "select activated, allowed from silencemode where chat_id=$1",
                importchatid,
            ):
                if not await conn.fetchval(
                    "update silencemode set activated = $1, allowed = $2 where chat_id=$3 "
                    "returning 1",
                    *i,
                    chatid,
                ):
                    await conn.execute(
                        "insert into silencemode (chat_id, activated, allowed) values ($1, $2, $3)",
                        chatid,
                        *i,
                    )
            for i in await conn.fetch(
                "select filter from filters where chat_id=$1", importchatid
            ):
                if not await conn.fetchval(
                    "select exists(select 1 from filters where chat_id=$1 and filter=$2)",
                    chatid,
                    *i,
                ):
                    await conn.execute(
                        "insert into filters (chat_id, filter) values ($1, $2)",
                        chatid,
                        *i,
                    )
            for i in await conn.fetch(
                "select cmd, lvl from commandlevels where chat_id=$1", importchatid
            ):
                if not await conn.fetchval(
                    "update commandlevels set lvl = $1 where chat_id=$2 and cmd=$3 returning 1",
                    i[1],
                    chatid,
                    i[0],
                ):
                    await conn.execute(
                        "insert into commandlevels (chat_id, cmd, lvl) values ($1, $2, $3)",
                        chatid,
                        *i,
                    )
            for k in await managers.chat_settings.get_by_field(chat_id=importchatid):
                i = await managers.chat_settings.get(
                    *k, ("setting", "pos", "value", "punishment", "value2", "pos2")
                )
                await managers.chat_settings.edit(
                    chatid,
                    setting=i[0],
                    pos=i[1],
                    value=i[2],
                    punishment=i[3],
                    value2=i[4],
                    pos2=i[5],
                )
            if i := await conn.fetchrow(
                "select msg, url, photo, button_label from welcome where chat_id=$1",
                importchatid,
            ):
                if not await conn.fetchval(
                    "update welcome set msg = $1, url = $2, photo = $3, button_label = $4 "
                    "where chat_id=$5 returning 1",
                    *i,
                    chatid,
                ):
                    await conn.execute(
                        "insert into welcome (chat_id, msg, url, photo, button_label) values "
                        "($1, $2, $3, $4, $5)",
                        chatid,
                        *i,
                    )
            for i in await conn.fetch(
                "select lvl, name from accessnames where chat_id=$1", importchatid
            ):
                if not await conn.fetchval(
                    "update accessnames set name = $1 where chat_id=$2 and lvl=$3 "
                    "returning 1",
                    i[1],
                    chatid,
                    i[0],
                ):
                    await conn.execute(
                        "insert into accessnames (chat_id, lvl, name) values ($1, $2, $3)",
                        chatid,
                        *i,
                    )
            for i in await conn.fetch(
                "select uid from ignore where chat_id=$1", importchatid
            ):
                if not await conn.fetchval(
                    "select exists(select 1 from ignore where chat_id=$1 and uid=$2)",
                    chatid,
                    *i,
                ):
                    await conn.execute(
                        "insert into ignore (chat_id, uid) values ($1, $2)", chatid, *i
                    )
            if i := await conn.fetchrow(
                "select time from chatlimit where chat_id=$1", importchatid
            ):
                if not await conn.fetchval(
                    "update chatlimit set time = $1 where chat_id=$2 returning 1",
                    *i,
                    chatid,
                ):
                    await conn.execute(
                        "insert into chatlimit (chat_id, time) values ($1, $2)",
                        chatid,
                        *i,
                    )
            for i in await conn.fetch(
                "select tag, every, status, time, description, text, name from notifications "
                "where chat_id=$1",
                importchatid,
            ):
                if not await conn.fetchval(
                    "update notifications set tag = $1, every = $2, status = $3, time = $4, "
                    "description = $5, text = $6 where chat_id=$7 and name=$8 returning 1",
                    *i[:-1],
                    chatid,
                    i[-1],
                ):
                    await conn.execute(
                        "insert into notifications (chat_id, tag, every, status, time, description, "
                        "text, name) values ($1, $2, $3, $4, $5, $6, $7, $8)",
                        chatid,
                        *i,
                    )
            for i in await conn.fetch(
                "select url from antispamurlexceptions where chat_id=$1", importchatid
            ):
                if not await conn.fetchval(
                    "select exists(select 1 from antispamurlexceptions where chat_id=$1 and "
                    "url=$2)",
                    chatid,
                    *i,
                ):
                    await conn.execute(
                        "insert into antispamurlexceptions (chat_id, url) values ($1, $2)",
                        chatid,
                        *i,
                    )
            for i in await conn.fetch(
                "select url from vklinksexceptions where chat_id=$1", importchatid
            ):
                if not await conn.fetchval(
                    "select exists(select 1 from vklinksexceptions where chat_id=$1 and "
                    "url=$2)",
                    chatid,
                    *i,
                ):
                    await conn.execute(
                        "insert into vklinksexceptions (chat_id, url) values ($1, $2)",
                        chatid,
                        *i,
                    )
            for i in await conn.fetch(
                "select exc_id from forwardedsexceptions where chat_id=$1", importchatid
            ):
                if not await conn.fetchval(
                    "select exists(select 1 from forwardedsexceptions where chat_id=$1 and "
                    "exc_id=$2)",
                    chatid,
                    *i,
                ):
                    await conn.execute(
                        "insert into forwardedsexceptions (chat_id, exc_id) values ($1, $2)",
                        chatid,
                        *i,
                    )
            for i in await conn.fetch(
                "select uid from antitag where chat_id=$1", importchatid
            ):
                if not await conn.fetchval(
                    "select exists(select 1 from antitag where chat_id=$1 and uid=$2)",
                    chatid,
                    *i,
                ):
                    await conn.execute(
                        "insert into antitag (chat_id, uid) values ($1, $2)", chatid, *i
                    )
            for i in await conn.fetch(
                "select uid, sys, acc, nicks, punishes, binds from importsettings where "
                "chat_id=$1",
                importchatid,
            ):
                if not await conn.fetchval(
                    "update importsettings set sys = $1, acc = $2, nicks = $3, punishes = $4, binds = $5 where "
                    "chat_id=$6 and uid=$7 returning 1",
                    *i[1:],
                    chatid,
                    i[0],
                ):
                    await conn.execute(
                        "insert into importsettings (chat_id, uid, sys, acc, nicks, punishes, binds)"
                        " values ($1, $2, $3, $4, $5, $6, $7)",
                        chatid,
                        *i,
                    )
        if settings["nicks"]:
            for i in await conn.fetch(
                "select uid, nickname from nickname where chat_id=$1", importchatid
            ):
                if not await conn.fetchval(
                    "update nickname set nickname = $1 where chat_id=$2 and uid=$3 "
                    "returning 1",
                    i[1],
                    chatid,
                    i[0],
                ):
                    await conn.execute(
                        "insert into nickname (chat_id, uid, nickname) values ($1, $2, $3)",
                        chatid,
                        *i,
                    )
        if settings["punishes"]:
            for i in await conn.fetch(
                "select uid, warns, last_warns_times, last_warns_names, last_warns_dates, "
                "last_warns_causes from warn where chat_id=$1",
                importchatid,
            ):
                if not await conn.fetchval(
                    "update warn set warns = $1, last_warns_times = $2, last_warns_names = "
                    "$3, last_warns_dates = $4, last_warns_causes = $5 where chat_id=$6 and "
                    "uid=$7 returning 1",
                    *i[1:],
                    chatid,
                    i[0],
                ):
                    await conn.execute(
                        "insert into warn (chat_id, uid, warns, last_warns_times, last_warns_names, "
                        "last_warns_dates, last_warns_causes) values ($1, $2, $3, $4, $5, $6, $7)",
                        chatid,
                        *i,
                    )
            for i in await conn.fetch(
                "select uid, ban, last_bans_times, last_bans_names, last_bans_dates, "
                "last_bans_causes from ban where chat_id=$1",
                importchatid,
            ):
                if not await conn.fetchval(
                    "update ban set ban = $1, last_bans_times = $2, last_bans_names = $3, "
                    "last_bans_dates = $4, last_bans_causes = $5 where chat_id=$6 and uid=$7"
                    " returning 1",
                    *i[1:],
                    chatid,
                    i[0],
                ):
                    await conn.execute(
                        "insert into ban (chat_id, uid, ban, last_bans_times, last_bans_names, "
                        "last_bans_dates, last_bans_causes) values ($1, $2, $3, $4, $5, $6, $7)",
                        chatid,
                        *i,
                    )
            for i in await conn.fetch(
                "select uid, mute, last_mutes_times, last_mutes_names, last_mutes_dates, "
                "last_mutes_causes from mute where chat_id=$1",
                importchatid,
            ):
                if not await conn.fetchval(
                    "update mute set mute = $1, last_mutes_times = $2, last_mutes_names = $3"
                    ", last_mutes_dates = $4, last_mutes_causes = $5 where chat_id=$6 and "
                    "uid=$7 returning 1",
                    *i[1:],
                    chatid,
                    i[0],
                ):
                    await conn.execute(
                        "insert into mute (chat_id, uid, mute, last_mutes_times, last_mutes_names, "
                        "last_mutes_dates, last_mutes_causes) values ($1, $2, $3, $4, $5, $6, $7)",
                        chatid,
                        *i,
                    )
        if settings["binds"]:
            for i in await conn.fetch(
                "select uid from gpool where chat_id=$1", importchatid
            ):
                if not await conn.fetchval(
                    "select exists(select 1 from gpool where chat_id=$1 and uid=$2)",
                    chatid,
                    *i,
                ):
                    await conn.execute(
                        "insert into gpool (chat_id, uid) values ($1, $2)", chatid, *i
                    )
            for i in await conn.fetch(
                'select uid, "group" from chatgroups where chat_id=$1', importchatid
            ):
                if not await conn.fetchval(
                    'select exists(select 1 from chatgroups where chat_id=$1 and uid=$2 and "group"=$3)',
                    chatid,
                    *i,
                ):
                    await conn.execute(
                        'insert into chatgroups (chat_id, uid, "group") values ($1, $2, $3)',
                        chatid,
                        *i,
                    )
    if settings["acc"]:
        for i in await managers.access_level.get_all(chat_id=importchatid):
            await managers.access_level.edit_access_level(i.uid, chatid, i.access_level)
    await utils.edit_message(
        await messages.import_end(importchatid),
        message.object.peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["blocklist_chats"])
)
async def blocklist_chats(message: MessageEvent):
    async with (await pool()).acquire() as conn:
        inf = await conn.fetch("select uid, reason from blocked where type='chat'")
    msg = f"⚛ Список чатов в блокировке бота (Всего:{len(inf)})\n\n"
    for chat in inf:
        msg += (
            f"➖ id {chat[0]} | {await utils.get_chat_name(chat[0])}"
            + (f" | {chat[1]}" if chat[1] else "")
            + "\n"
        )
    await utils.edit_message(
        msg,
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.blocklist_chats(message.user_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["blocklist"])
)
async def blocklist(message: MessageEvent):
    async with (await pool()).acquire() as conn:
        inf = await conn.fetch("select uid, reason from blocked where type='user'")
    msg = f"⚛ Список пользователей в блокировке бота (Всего:{len(inf)})\n\n"
    for user in inf:
        msg += (
            f"➖ [id{user[0]}|{await utils.get_user_name(user[0])}]"
            + (f" | {user[1]}" if user[1] else "")
            + "\n"
        )
    await utils.edit_message(
        msg,
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.blocklist(message.user_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["bindlist"])
)
async def bindlist(message: MessageEvent):
    if not message.payload:
        return
    page = message.payload["page"]
    group = message.payload["group"]
    async with (await pool()).acquire() as conn:
        res = await conn.fetch(
            'select "chat_id" from chatgroups where uid=$1 and "group"=$2 order by chat_id',
            message.user_id,
            group,
        )
    if not (count := len(res)):
        return
    res = res[page * 15 : page * 15 + 15]
    await utils.edit_message(
        await messages.bindlist(
            group, [(i[0], await utils.get_chat_name(i[0])) for i in res]
        ),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.bindlist(message.user_id, group, page, count),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["filter_punishments", "filter_punishments_set"]),
)
async def filterpunishments(message: MessageEvent):
    if not message.payload:
        return
    chat_id = message.peer_id - 2000000000
    async with (await pool()).acquire() as conn:
        if message.payload["cmd"].endswith("_set"):
            pnt = message.payload["set"]
            if not await conn.fetchval(
                "update filtersettings set punishment=$1 where chat_id=$2 returning 1",
                pnt,
                chat_id,
            ):
                await conn.execute(
                    "insert into filtersettings (chat_id, punishment) values ($1, $2)",
                    chat_id,
                    pnt,
                )
        else:
            pnt = (
                await conn.fetchval(
                    "select punishment from filtersettings where chat_id=$1", chat_id
                )
                or 0
            )
    await utils.edit_message(
        await messages.filter_punishments(pnt),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.filter_punishments(message.user_id, pnt),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["filter_list"])
)
async def filterlist(message: MessageEvent):
    if not message.payload:
        return
    page, chat_id = message.payload.get("page", 0), message.peer_id - 2000000000

    owners = await managers.access_level.get_all(
        chat_id=chat_id,
        predicate=lambda i: i.access_level >= 7 and i.custom_level_name is None,
    )
    if owners:
        owner_id = sorted(owners, key=lambda i: i.access_level, reverse=True)[0].uid
    else:
        owner_id = message.user_id

    async with (await pool()).acquire() as conn:
        filters = await conn.fetch(
            "select chat_id, owner_id, filter from filters where (chat_id=$1 or (owner_id=$2 and exists("
            "select 1 from gpool where uid=$2 and chat_id=$1))) and filter not in ("
            "select filter from filterexceptions where owner_id=$2 and chat_id=$1)",
            chat_id,
            owner_id,
        )
    await utils.edit_message(
        await messages.filter_list(filters[25 * page : 25 * page + 25], page),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.filter_list(message.user_id, page, len(filters)),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["filteradd"])
)
async def filteradd(message: MessageEvent):
    if not message.payload:
        return
    chat_id = message.peer_id - 2000000000

    owners = await managers.access_level.get_all(
        chat_id=chat_id,
        predicate=lambda i: i.access_level >= 7 and i.custom_level_name is None,
    )
    if owners:
        owner_id = sorted(owners, key=lambda i: i.access_level, reverse=True)[0].uid
    else:
        owner_id = message.user_id

    async with (await pool()).acquire() as conn:
        await conn.execute(
            "update filters set chat_id=null, owner_id=$1 where id=$2",
            owner_id,
            message.payload["fid"],
        )
    await utils.edit_message(
        message.payload["msg"], message.object.peer_id, message.conversation_message_id
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["filterdel"])
)
async def filterdel(message: MessageEvent):
    if not message.payload:
        return
    chat_id = message.peer_id - 2000000000

    owners = await managers.access_level.get_all(
        chat_id=chat_id,
        predicate=lambda i: i.access_level >= 7 and i.custom_level_name is None,
    )
    if owners:
        owner_id = sorted(owners, key=lambda i: i.access_level, reverse=True)[0].uid
    else:
        owner_id = message.user_id

    async with (await pool()).acquire() as conn:
        filter = await conn.fetchval(
            "delete from filters where id=$1 returning filter", message.payload["fid"]
        )
        await conn.execute(
            "delete from filterexceptions where owner_id=$1 and filter=$2",
            owner_id,
            filter,
        )
    await utils.edit_message(
        message.payload["msg"], message.object.peer_id, message.conversation_message_id
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["deletemessages"])
)
async def deletemessages(message: MessageEvent):
    if not message.payload:
        return
    await utils.delete_messages(
        message.payload["msgs"] + [message.conversation_message_id],
        message.peer_id - 2000000000,
    )


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["market"]))
async def market(message: MessageEvent):
    await utils.edit_message(
        await messages.buy(),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.buy(message.user_id),
    )


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["buy"]))
async def buy(message: MessageEvent):
    if not message.payload:
        return
    uid = message.user_id
    days = message.payload["days"]
    cost = settings.premium_cost.cost[days]
    name = (await utils.get_user_name(uid)).split()

    payment = await utils.create_payment(
        cost,
        name[-1],
        name[0],
        cost,
        uid,
        uid,
        delete_message_cmid=message.conversation_message_id,
    )
    await utils.edit_message(
        await messages.buy_order(
            payment.metadata["pid"],  # type: ignore
            uid,
            name,
            days,
            cost,
            (
                await api.utils.get_short_link(payment.confirmation.confirmation_url)  # type: ignore
            ).short_url,
        ),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.buy_order(payment.confirmation.confirmation_url),  # type: ignore
    )


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["shop_xp"]))
async def shop_xp(message: MessageEvent):
    async with (await pool()).acquire() as conn:
        limit = await conn.fetchval(
            "select limits from shop where uid=$1", message.user_id
        )
    limit = literal_eval(limit) if limit else [0, 0, 0, 0, 0]

    await utils.edit_message(
        await messages.shop_xp(await utils.get_user_coins(message.user_id), limit),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.shop_xp(message.user_id, limit),
    )


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["shop"]))
async def shop(message: MessageEvent):
    await utils.edit_message(
        await messages.shop(),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.shop(message.user_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["shop_bonuses"])
)
async def shop_bonuses(message: MessageEvent):
    async with (await pool()).acquire() as conn:
        activated_bonuses = await conn.fetchrow(
            "select exp_2x, no_comission from shop where uid=$1", message.user_id
        )
    activated_bonuses = (
        [i if i > time.time() else 0 for i in activated_bonuses]
        if activated_bonuses
        else [0, 0]
    )

    await utils.edit_message(
        await messages.shop_bonuses(await utils.get_user_coins(message.user_id)),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.shop_bonuses(message.user_id, activated_bonuses),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["shop_buy"], answer=False),
)
async def shop_buy(message: MessageEvent):
    if not message.payload:
        return
    category = message.payload["category"]
    option = message.payload["option"]
    if category == "xp":
        lot = settings.shop.xp[option]
    else:
        lot = list(settings.shop.bonuses.values())[option]
    cost = lot["cost"]

    if (user_coins := await utils.get_user_coins(message.user_id)) < cost:
        await message.show_snackbar(
            "🔴 Недостаточно монеток для покупки данного товара."
        )
        return

    if category == "xp":
        lot_limit = lot["limit"]
        async with (await pool()).acquire() as conn:
            limit_row = await conn.fetchval(
                "select limits from shop where uid=$1", message.user_id
            )
            limit = literal_eval(limit_row) if limit_row else [0, 0, 0, 0, 0]
            limit_key = list(settings.shop.xp.keys()).index(option)
            if limit[limit_key] >= lot_limit:
                await message.show_snackbar(
                    "🔴 Вы превысили суточный лимит покупки данного товара."
                )
                return
            limit[limit_key] += 1
            if limit_row:
                await conn.execute(
                    "update shop set limits=$1 where uid=$2",
                    f"{limit}",
                    message.user_id,
                )
            else:
                await conn.execute(
                    "insert into shop (uid, limits, exp_2x, no_comission) values ($1, $2, 0, 0)",
                    message.user_id,
                    f"{limit}",
                )
        lot_name = f"{option} опыта"
        await utils.add_user_coins(message.user_id, -cost)
        await utils.add_user_xp(message.user_id, option)

        await utils.edit_message(
            await messages.shop_xp(await utils.get_user_coins(message.user_id), limit),
            message.object.peer_id,
            message.conversation_message_id,
            keyboard.shop_xp(message.user_id, limit),
        )
    elif category == "bonuses":
        bonus_type = lot["type"]
        active_until = int(time.time()) + lot["active_for"]
        if bonus_type == "xp_booster":
            check_sql = "select exp_2x from shop where uid=$1"
            buy_sql = "update shop set exp_2x=$1 where uid=$2"
            buy_insert_sql = "insert into shop (uid, limits, exp_2x, no_comission) values ($1, '[0, 0, 0, 0, 0]', $2, 0)"
            activated_key = 0
        elif bonus_type == "comission_removal":
            check_sql = "select no_comission from shop where uid=$1"
            buy_sql = "update shop set no_comission=$1 where uid=$2"
            buy_insert_sql = "insert into shop (uid, limits, exp_2x, no_comission) values ($1, '[0, 0, 0, 0, 0]', 0, $2)"
            activated_key = 1
        else:
            raise Exception('type not in ("xp_booster", "comission_removal")')

        await utils.add_user_coins(message.user_id, -cost)
        async with (await pool()).acquire() as conn:
            activated_bonuses = await conn.fetchrow(
                "select exp_2x, no_comission from shop where uid=$1", message.user_id
            )
            if activated_bonuses:
                if await conn.fetchval(check_sql, message.user_id) > time.time():
                    await message.show_snackbar("🔴 У вас уже есть этот бонус.")
                    return
                await conn.execute(buy_sql, active_until, message.user_id)
            else:
                await conn.execute(buy_insert_sql, message.user_id, active_until)

        activated_bonuses = (
            [i if i > time.time() else 0 for i in activated_bonuses]
            if activated_bonuses
            else [0, 0]
        )
        activated_bonuses[activated_key] = active_until
        lot_name = lot["name"]

        await utils.edit_message(
            await messages.shop_bonuses(await utils.get_user_coins(message.user_id)),
            message.object.peer_id,
            message.conversation_message_id,
            keyboard.shop_bonuses(message.user_id, activated_bonuses),
        )
    else:
        raise Exception('category not in ("xp", "bonus")')

    category = "Опыт" if category == "xp" else "Бонус"
    user_name = await utils.get_user_name(message.user_id)
    try:
        await tgbot.send_message(
            chat_id=settings.telegram.chat_id,
            message_thread_id=settings.telegram.shop_thread_id,
            text=f'<a href="vk.com/id{message.user_id}">{user_name}</a> | {category} | {lot_name} | М: {user_coins} | П: {cost} | {datetime.now().strftime("%d.%m.%Y / %H:%M:%S")}',
            disable_web_page_preview=True,
            parse_mode="HTML",
        )
    except Exception:
        pass
    await utils.send_message(
        message.peer_id,
        f'🛍 [id{message.user_id}|{user_name}] успешно купил "{lot_name}" за {cost} монеток',
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["raid_turn"])
)
async def raid_turn(message: MessageEvent):
    async with (await pool()).acquire() as conn:
        if (
            status := await conn.fetchval(
                "update raidmode set status=not status where chat_id=$1 returning status",
                message.peer_id - 2000000000,
            )
        ) is None:
            await conn.execute(
                "insert into raidmode (chat_id, status) values ($1, True)",
                message.peer_id - 2000000000,
            )
            status = True

    await utils.edit_message(
        await messages.raid(),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.raid(message.user_id, status),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["raid_settings"])
)
async def raid_settings(message: MessageEvent):
    async with (await pool()).acquire() as conn:
        raidmode = await conn.fetchrow(
            "select trigger_status, limit_invites, limit_seconds from raidmode where chat_id=$1",
            message.peer_id - 2000000000,
        ) or [False, 5, 60]
    await utils.edit_message(
        await messages.raid_settings(*raidmode),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.raid_settings(message.user_id, raidmode[0]),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["raid_trigger_turn"])
)
async def raid_trigger_turn(message: MessageEvent):
    async with (await pool()).acquire() as conn:
        if (
            raidmode := await conn.fetchrow(
                "update raidmode set trigger_status=not status where chat_id=$1 returning trigger_status, limit_invites, limit_seconds",
                message.peer_id - 2000000000,
            )
        ) is None:
            await conn.execute(
                "insert into raidmode (chat_id, trigger_status) values ($1, True)",
                message.peer_id - 2000000000,
            )
            raidmode = list(
                await conn.fetchrow(
                    "select trigger_status, limit_invites, limit_seconds from raidmode where chat_id=$1",
                    message.peer_id - 2000000000,
                )
            )
            raidmode[0] = True

    await utils.edit_message(
        await messages.raid_settings(*raidmode),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.raid_settings(message.user_id, raidmode[0]),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["raid_trigger_set"])
)
async def raid_trigger_set(message: MessageEvent):
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "insert into typequeue (chat_id, uid, type, additional) values ($1, $2, $3, $4)",
            message.peer_id - 2000000000,
            message.user_id,
            "raid_trigger_set",
            "{" + f'"cmid": "{message.conversation_message_id}"' + "}",
        )

    await utils.edit_message(
        await messages.raid_trigger_set(),
        message.object.peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["rps"], checksender=False, answer=False),
)
async def rps(message: MessageEvent):
    if not message.payload or not message.conversation_message_id:
        return
    creator = managers.rps.get_creator_id(
        message.conversation_message_id, message.peer_id
    )
    if not creator or (
        creator == message.user_id
        or (
            message.payload["uid"] != creator
            and message.user_id != message.payload["uid"]
        )
    ):
        return
    if await utils.get_user_coins(message.user_id) < message.payload["bet"]:
        await message.show_snackbar("У вас не хватает монеток для участия.")
        return
    if await utils.get_user_coins(creator) < message.payload["bet"]:
        await message.show_snackbar("У вашего оппонента недостаточно монеток.")
        return
    await utils.edit_message(
        await messages.rps_play(
            creator,
            await utils.get_user_name(creator),
            None,
            (bet := message.payload["bet"]),
            (id := message.user_id),
            await utils.get_user_name(id),
            None,
        ),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.rps_play(f"{creator},{id}", bet),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["rps_play"], answer=False),
)
async def rps_play(message: MessageEvent):
    if not message.payload or not message.conversation_message_id:
        return

    bet = int(message.payload["bet"])

    async with _rps_lock:  # one global lock is enough for this code
        if await utils.get_user_coins(message.user_id) < bet:
            await message.show_snackbar("У вас не хватает монеток для участия.")
            return

        waiting_for_opponent = False

        creator = managers.rps.get_creator_id(
            message.conversation_message_id, message.peer_id
        )
        if creator is None:
            await message.show_snackbar(
                "⚠️ Произошла непредвиденная ошибка. Пожалуйста, попробуйте создать новую игру."
            )
            return

        picks = managers.rps.get_picks(message.conversation_message_id, message.peer_id)
        is_first_player = message.user_id == creator

        existing_pick = picks[0] if is_first_player else picks[1]
        if existing_pick is not None:
            await message.show_snackbar(
                f"Вы уже сделали выбор - {getattr(enums.RPSPick, existing_pick).value}"
            )
            return

        await managers.rps.set_pick(
            message.conversation_message_id,
            message.peer_id,
            message.payload["pick"],
            is_first_player,
            None if is_first_player else message.user_id,
        )

        picks = managers.rps.get_picks(message.conversation_message_id, message.peer_id)
        creator_pick, second_player_pick = picks
        second_player_id = managers.rps.get_second_player_id(
            message.conversation_message_id, message.peer_id
        )

        if creator_pick is None or second_player_pick is None:
            waiting_for_opponent = True
        else:
            if creator_pick == second_player_pick:
                await managers.rps.remove_game(
                    message.conversation_message_id, message.peer_id
                )
                await utils.edit_message(
                    await messages.rps_draw(bet, creator_pick),
                    message.object.peer_id,
                    message.conversation_message_id,
                )
                return

            if second_player_id is None:
                await message.show_snackbar(
                    "⚠️ Произошла непредвиденная ошибка. Пожалуйста, попробуйте создать новую игру."
                )
                return

            beats = {"r": "s", "p": "r", "s": "p"}

            if beats[creator_pick] == second_player_pick:
                winid, loseid, win_pick = creator, second_player_id, creator_pick
            else:
                winid, loseid, win_pick = second_player_id, creator, second_player_pick

            bet_w_comission, com = bet, 0
            has_comission = not (
                await utils.get_user_premium(winid)
                or (await utils.get_user_shop_bonuses(winid))[1] > time.time()
            )
            if has_comission:
                bet_w_comission, com = int(bet / 100 * 90), 10

            await utils.add_user_coins(loseid, -bet)
            await utils.add_user_coins(winid, bet_w_comission)

            await managers.rps.remove_game(
                message.conversation_message_id, message.peer_id
            )

            await utils.edit_message(
                await messages.rps_end(
                    winid,
                    await utils.get_user_name(winid),
                    None,
                    bet_w_comission,
                    win_pick,
                    com,
                ),
                message.object.peer_id,
                message.conversation_message_id,
            )

            try:
                await tgbot.send_message(
                    chat_id=settings.telegram.chat_id,
                    message_thread_id=settings.telegram.rps_thread_id,
                    text=f'{"W: " if creator == winid else "L: "}<a href="vk.com/id{creator}">{await utils.get_user_name(creator)}</a> | {"W: " if second_player_id == winid else "L: "}<a href="vk.com/id{second_player_id}">{await utils.get_user_name(second_player_id)}</a> | {bet} | {com}% | {datetime.now().strftime("%d.%m.%Y / %H:%M:%S")}',
                    disable_web_page_preview=True,
                    parse_mode="HTML",
                )
            except Exception:
                pass
            return

    if waiting_for_opponent:
        await message.show_snackbar(
            f"✅ Вы сделали выбор - {getattr(enums.RPSPick, message.payload['pick']).value}. Ожидаем оппонента..."
        )


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["chats"]))
async def chats(message: MessageEvent):
    if not message.payload:
        return
    peer_id = message.object.peer_id
    page = message.payload["page"]
    mode = enums.ChatsMode(message.payload["mode"])

    all_chats = await managers.public_chats.get_regular_chats()
    all_chats = sorted(all_chats, key=lambda x: x[1].members_count, reverse=True)
    all_chats = await managers.public_chats.get_chats_top(all_chats)
    res = (
        all_chats
        if mode == enums.ChatsMode.all
        else await managers.public_chats.sort_premium_chats(all_chats)
    )
    await utils.edit_message(
        await messages.chats(
            len(all_chats), res[page * 15 : page * 15 + 15], mode, page
        ),
        peer_id,
        message.conversation_message_id,
        keyboard.chats(message.user_id, len(res), page, mode),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["customlevel_settings"]),
)
async def customlevel_settings(message: MessageEvent):
    if not message.payload:
        return
    if message.payload.get("clear", False):
        async with (await pool()).acquire() as conn:
            await conn.execute(
                "delete from typequeue where chat_id=$1 and uid=$2",
                message.object.peer_id - 2000000000,
                message.user_id,
            )
    level = message.payload["level"]
    level = await managers.custom_access_level.get(
        level, message.object.peer_id - 2000000000
    )
    if not level:
        return
    holders = await managers.access_level.get_holders(
        message.object.peer_id - 2000000000, level.name
    )
    await utils.edit_message(
        await messages.customlevel_settings(
            level.access_level,
            level.name,
            level.emoji,
            level.status,
            len(holders),
            level.commands,
        ),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.customlevel_settings(
            message.user_id,
            level,
            (message.payload.get("pre_page", None) if message.payload else None),
        ),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["customlevel_action"])
)
async def customlevel_action(message: MessageEvent):
    if not message.payload:
        return
    chat_id = message.object.peer_id - 2000000000
    level = message.payload["level"]
    levelmenu_page = message.payload["levelmenu_page"]
    level = await managers.custom_access_level.get(level, chat_id)
    if not level:
        if message.object.conversation_message_id:
            try:
                await utils.delete_messages(
                    message.object.conversation_message_id, chat_id
                )
            except Exception:
                pass
        return
    action = message.payload["action"]

    if action == "turn":
        level.status = not level.status
        await managers.custom_access_level.edit(
            level.access_level, chat_id, status=level.status
        )
        holders = await managers.access_level.get_holders(chat_id, level.name)
        return await utils.edit_message(
            await messages.customlevel_settings(
                level.access_level,
                level.name,
                level.emoji,
                level.status,
                len(holders),
                level.commands,
            ),
            message.object.peer_id,
            message.conversation_message_id,
            keyboard.customlevel_settings(message.user_id, level, levelmenu_page),
        )
    if action == "delete":
        return await utils.edit_message(
            await messages.customlevel_delete_yon(level.name, level.access_level),
            message.object.peer_id,
            message.conversation_message_id,
            keyboard.customlevel_delete_yon(message.user_id, level.access_level),
        )
    if action == "set_commands_presets":
        return await utils.edit_message(
            await messages.customlevel_set_commands_presets(
                level.name, level.access_level
            ),
            message.object.peer_id,
            message.conversation_message_id,
            keyboard.customlevel_set_commands_presets(
                message.user_id, level.access_level
            ),
        )
    if action == "remove_all":
        return await utils.edit_message(
            await messages.customlevel_remove_all_yon(level.name, level.access_level),
            message.object.peer_id,
            message.conversation_message_id,
            keyboard.customlevel_remove_all_yon(message.user_id, level.access_level),
        )

    if action == "set_priority":
        await utils.edit_message(
            await messages.customlevel_set_priority(
                50 if await utils.get_user_premium(message.user_id) else 10
            ),
            message.object.peer_id,
            message.conversation_message_id,
            keyboard.customlevel_to_settings(
                message.user_id, level.access_level, "Назад", clear_type_queue=True
            ),
        )
    if action == "set_name":
        await utils.edit_message(
            await messages.customlevel_set_name(),
            message.object.peer_id,
            message.conversation_message_id,
            keyboard.customlevel_to_settings(
                message.user_id, level.access_level, "Назад", clear_type_queue=True
            ),
        )
    if action == "set_emoji":
        await utils.edit_message(
            await messages.customlevel_set_emoji(),
            message.object.peer_id,
            message.conversation_message_id,
            keyboard.customlevel_to_settings(
                message.user_id, level.access_level, "Назад", clear_type_queue=True
            ),
        )
    if action == "set_commands":
        await utils.edit_message(
            await messages.customlevel_set_commands(),
            message.object.peer_id,
            message.conversation_message_id,
            keyboard.customlevel_to_settings(
                message.user_id, level.access_level, "Назад", clear_type_queue=True
            ),
        )

    async with (await pool()).acquire() as conn:
        await conn.execute(
            "insert into typequeue (chat_id, uid, type, additional) values ($1, $2, $3, $4)",
            chat_id,
            message.user_id,
            f"customlevel_{action}",
            f'{{"level": {level.access_level}}}',
        )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(["customlevel_delete"])
)
async def customlevel_delete(message: MessageEvent):
    if not message.payload:
        return
    chat_id = message.object.peer_id - 2000000000
    level = message.payload["level"]
    level = await managers.custom_access_level.delete(level, chat_id)
    if level is None:
        if not message.conversation_message_id:
            return
        return await utils.delete_messages(message.conversation_message_id, chat_id)

    holders = await managers.access_level.get_holders(chat_id, level.name)
    await managers.access_level.delete_rows(holders)

    await utils.edit_message(
        await messages.customlevel_delete(level.name, level.access_level),
        message.object.peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["customlevel_remove_all"]),
)
async def customlevel_remove_all(message: MessageEvent):
    if not message.payload:
        return
    chat_id = message.object.peer_id - 2000000000
    level = message.payload["level"]
    level = await managers.custom_access_level.get(level, chat_id)
    if level is None:
        if not message.conversation_message_id:
            return
        return await utils.delete_messages(message.conversation_message_id, chat_id)

    holders = await managers.access_level.get_holders(chat_id, level.name)
    await managers.access_level.delete_rows(holders)

    await utils.edit_message(
        await messages.customlevel_remove_all(
            level.name, level.access_level, len(holders)
        ),
        message.object.peer_id,
        message.conversation_message_id,
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["customlevel_set_commands_preset"]),
)
async def customlevel_set_commands_preset(message: MessageEvent):
    if not message.payload:
        return
    chat_id = message.object.peer_id - 2000000000
    level = message.payload["level"]
    level = await managers.custom_access_level.get(level, chat_id)
    if level is None:
        if not message.conversation_message_id:
            return
        return await utils.delete_messages(message.conversation_message_id, chat_id)

    preset = message.payload["preset"]
    all_commands = defaultdict(list)
    for k, v in settings.commands.commands.items():
        all_commands[v].append(k)
    commands = []
    for k in range(0, preset + 1):
        commands.extend(all_commands[k])
    for preserved_cmd in settings.commands.custom_preserved:
        if preserved_cmd in commands:
            commands.remove(preserved_cmd)
    await managers.custom_access_level.set_preset(
        level.access_level, level.chat_id, commands
    )

    await utils.edit_message(
        await messages.customlevel_set_commands_done(
            level.name,
            level.access_level,
            commands,
            " Остальные команды были отключены.",
        ),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.customlevel_to_settings(message.user_id, level.access_level, "Назад"),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["levelmenu"]),
)
async def levelmenu(message: MessageEvent):
    if not message.payload:
        page = 0
    else:
        page = message.payload.get("page", 0)
    chat_id = message.object.peer_id - 2000000000
    levels = await managers.custom_access_level.get_all(chat_id)
    activated = [i for i in levels if i.status]
    await utils.edit_message(
        await messages.levelmenu(len(levels), len(activated)),
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.levelmenu(message.user_id, levels, page),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["staff"]),
)
async def staff(message: MessageEvent):
    if not message.payload:
        custom = False
        page = 0
    else:
        custom = message.payload.get("custom", False)
        page = message.payload.get("page", 0)
    chat_id = message.object.peer_id - 2000000000
    if not custom:
        res = await managers.access_level.get_all(
            chat_id=chat_id,
            predicate=lambda i: i.access_level < 8 and i.custom_level_name is None,
        )
        if res:
            res = sorted(res, key=lambda i: (i.access_level, i.uid), reverse=True)
        users = await api.users.get(user_ids=[i.uid for i in res if i.uid > 0])
        msg = await messages.staff(res, users, chat_id)
    else:
        levels = await managers.custom_access_level.get_all(chat_id)
        msg = await messages.staff_custom(
            sorted(levels, key=lambda i: i.access_level, reverse=True)[
                page * 10 : (page + 1) * 10
            ],
            await managers.access_level.get_all(
                chat_id=chat_id,
                predicate=lambda i: i.custom_level_name is not None,
            ),
        )

    await utils.edit_message(
        msg,
        message.object.peer_id,
        message.conversation_message_id,
        keyboard.staff(message.user_id, not custom, len(levels) if custom else 0, page),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    SearchPayloadCMD(["event_open"], answer=False),
)
async def event_open(message: MessageEvent):
    user = await managers.event.get_user(message.user_id)
    if user.event_user is None or user.event_user.has_cases == 0:
        await message.show_snackbar(
            "❄️ Вы не выполнили все задания."
        )
        return
    await utils.send_message_event_answer(
        message.event_id, message.user_id, message.peer_id
    )

    await utils.send_message(
        message.peer_id,
        await managers.event.open_case(message.user_id, message.peer_id - 2000000000),
    )
