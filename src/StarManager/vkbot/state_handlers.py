import asyncio
import datetime
import re
import time
from ast import literal_eval
from typing import Any, Dict, Optional

import requests
from loguru import logger
from vkbottle_types.events.bot_events import MessageNew
from vkbottle_types.objects import MessagesMessageAttachmentType

from StarManager.core import managers
from StarManager.core.config import settings
from StarManager.core.db import pool
from StarManager.core.utils import (
    delete_messages,
    edit_message,
    get_user_name,
    get_user_nickname,
    get_user_premium,
    hex_to_rgb,
    is_single_emoji,
    search_id_in_message,
    send_message,
    upload_image,
    whoiscachedurl,
)
from StarManager.vkbot import keyboard, messages


async def handle_notification(
    event: MessageNew,
    queue_type: str,
    additional: Dict[str, Any],
    chat_id: int,
    uid: int,
):
    if not event.object.message:
        return

    if queue_type == "notification_text":
        name = additional["name"]
        cmid = int(additional["cmid"])
        async with (await pool()).acquire() as conn:
            notif = await conn.fetchrow(
                "update notifications set text = $1 where name=$2 and chat_id=$3 returning name, time, every, tag, status",
                event.object.message.text,
                name,
                chat_id,
            )

        await edit_message(
            await messages.notification_changed_text(name),
            event.object.message.peer_id,
            cmid,
        )
        return await send_message(
            chat_id + 2000000000,
            await messages.notification(
                notif[0],
                event.object.message.text,
                notif[1],
                notif[2],
                notif[3],
                notif[4],
            ),
            keyboard.notification(uid, notif[4], notif[0]),
        )

    if queue_type == "notification_time_change":
        ctime = event.object.message.text
        ctype = additional["type"]

        def parse_hm(s: str):
            try:
                h, m = map(int, s.split(":"))
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    raise ValueError
                return datetime.datetime.strptime(s, "%H:%M")
            except Exception:
                raise

        try:
            if ctype == "single":
                ctime_dt = parse_hm(ctime)
                nctime = datetime.datetime.now().replace(
                    hour=ctime_dt.hour, minute=ctime_dt.minute
                )
                if nctime.timestamp() < time.time():
                    nctime += datetime.timedelta(days=1)
                every = 0
            elif ctype == "everyday":
                ctime_dt = parse_hm(ctime)
                nctime = datetime.datetime.now().replace(
                    hour=ctime_dt.hour, minute=ctime_dt.minute
                )
                if nctime.timestamp() < time.time():
                    nctime += datetime.timedelta(days=1)
                every = 1440
            else:
                if int(ctime.split()[0]) < 0:
                    raise ValueError
                nctime = datetime.datetime.now() + datetime.timedelta(
                    minutes=int(ctime)
                )
                every = ctime
        except Exception:
            return await send_message(
                chat_id + 2000000000,
                await messages.notification_changing_time_error(),
            )

        name = additional["name"]
        async with (await pool()).acquire() as conn:
            notif = await conn.fetchrow(
                "update notifications set time = $1, every = $2 where name=$3 and chat_id=$4 "
                "returning name, text, time, every, tag, status",
                nctime.timestamp(),
                int(every),
                name,
                chat_id,
            )

        cmid = int(additional["cmid"])
        await edit_message(
            await messages.notification_changed_time(name),
            event.object.message.peer_id,
            cmid,
        )
        await send_message(
            chat_id + 2000000000,
            await messages.notification(*notif),
            keyboard.notification(uid, notif[5], notif[0]),
        )


async def handle_settings(
    event: MessageNew,
    queue_type: str,
    additional: Dict[str, Any],
    chat_id: int,
    uid: int,
):
    if not event.object.message:
        return

    async def change_autodelete(text: str, cmid: int, category: str):
        if not event.object.message:
            return

        if not (matches := re.findall(r"(\d+)\s*([hm])", text)):
            await edit_message(
                await messages.settings_autodelete_input_error(),
                event.object.message.peer_id,
                cmid,
                keyboard.settings_change_countable(
                    uid, category, "autodelete", onlybackbutton=True
                ),
            )
            return
        itime = 0
        for val, u in matches:
            if u == "h":
                itime += int(val) * 3600
            elif u == "m":
                itime += int(val) * 60
        if itime > 86400 or itime < 300:
            await edit_message(
                await messages.settings_autodelete_input_error(),
                event.object.message.peer_id,
                cmid,
                keyboard.settings_change_countable(
                    uid, category, "autodelete", onlybackbutton=True
                ),
            )
            return
        await managers.chat_settings.edit(chat_id, "autodelete", value=itime)
        await edit_message(
            await messages.settings_change_autodelete_done(itime),
            event.object.message.peer_id,
            cmid,
            keyboard.settings_change_countable(
                uid, category, "autodelete", onlybackbutton=True
            ),
        )

    async def change_countable(setting: str, category: str, cmid: int, text: str):
        if not event.object.message:
            return

        kb = keyboard.settings_change_countable(
            uid, category, setting, onlybackbutton=True
        )
        if setting not in settings.settings_meta.countable_multiple_arguments:
            if setting not in settings.settings_meta.countable_special_limits:
                limit = range(0, 10001)
            else:
                limit = settings.settings_meta.countable_special_limits[setting]
            if not text.isdigit() or int(text) not in limit:
                await edit_message(
                    await messages.settings_change_countable_digit_error(),
                    event.object.message.peer_id,
                    cmid,
                    kb,
                )
                return
            await managers.chat_settings.edit(chat_id, setting, value=int(text))
        else:
            if setting == "nightmode":
                try:
                    text_clean = text.replace(" ", "")
                    args = text_clean.split("-")
                    start = datetime.datetime.strptime(args[0], "%H:%M").replace(
                        year=2024
                    )
                    end = datetime.datetime.strptime(args[1], "%H:%M").replace(
                        year=2024
                    )
                    if end.hour <= start.hour:
                        end = end.replace(day=2)
                    if start.timestamp() >= end.timestamp():
                        raise ValueError
                except Exception:
                    await edit_message(
                        await messages.settings_change_countable_format_error(),
                        event.object.message.peer_id,
                        cmid,
                        kb,
                    )
                    return
                val = f"{start.hour:02d}:{start.minute:02d}-{end.hour:02d}:{end.minute:02d}"
                await managers.chat_settings.edit(chat_id, setting, value2=val)

        await edit_message(
            await messages.settings_change_countable_done(setting, text),
            event.object.message.peer_id,
            cmid,
            kb,
        )

    async def set_punishment(setting: str, category: str, cmid: int, text: str):
        if not event.object.message:
            return

        kb = keyboard.settings_change_countable(
            uid, category, setting, onlybackbutton=True
        )
        if not text.isdigit() or int(text) < 0 or int(text) >= 10000:
            await edit_message(
                await messages.settings_change_countable_digit_error(),
                event.object.message.peer_id,
                cmid,
                kb,
            )
            return
        action = additional["action"]
        pnshtime = int(text) if text != "0" else (3650 if action == "ban" else 1000000)
        await managers.chat_settings.edit(
            chat_id, setting, punishment=f"{action}|{pnshtime}"
        )
        await edit_message(
            await messages.settings_set_punishment(action, int(pnshtime)),
            event.object.message.peer_id,
            cmid,
            kb,
        )

    async def welcome_actions(subtype: str, cmid: Optional[int]):
        if not event.object.message:
            return

        async with (await pool()).acquire() as conn:
            welcome = await conn.fetchrow(
                "select msg, url, photo from welcome where chat_id=$1", chat_id
            )

        if subtype == "settings_set_welcome_text":
            if not event.object.message.text:
                return await send_message(
                    chat_id + 2000000000,
                    await messages.get(subtype + "_no_text"),
                    keyboard.settings_change_countable(
                        uid, "main", "welcome", onlybackbutton=True
                    ),
                )
            async with (await pool()).acquire() as conn:
                if not await conn.fetchval(
                    "update welcome set msg = $1 where chat_id=$2 returning 1",
                    event.object.message.text,
                    chat_id,
                ):
                    await conn.execute(
                        "insert into welcome (chat_id, msg) values ($1, $2)",
                        chat_id,
                        event.object.message.text,
                    )

        elif subtype == "settings_set_welcome_photo":
            attachment = event.object.message.attachments
            if (
                not attachment
                or attachment[0].type != MessagesMessageAttachmentType.PHOTO
                or not attachment[0].photo
                or not attachment[0].photo.sizes
                or not attachment[0].photo.sizes[-1].url
            ):
                return await send_message(
                    chat_id + 2000000000,
                    await messages.get(subtype + "_not_photo"),
                    keyboard.settings_change_countable(
                        uid, "main", "welcome", onlybackbutton=True
                    ),
                )

            r = await asyncio.to_thread(requests.get, attachment[0].photo.sizes[-1].url)
            path = f"{settings.service.path}src/StarManager/core/media/temp/{uid}welcome.jpg"
            await asyncio.to_thread(lambda: open(path, "wb").write(r.content))
            photo = await upload_image(
                path, targeted_ids=[event.object.message.peer_id, uid]
            )
            if not photo:
                return await send_message(
                    chat_id + 2000000000,
                    "⚠️ Неизвестная ошибка. Пожалуйста, попробуйте позже.",
                    keyboard.settings_change_countable(
                        uid, "main", "welcome", onlybackbutton=True
                    ),
                )
            async with (await pool()).acquire() as conn:
                if not await conn.fetchval(
                    "update welcome set photo = $1 where chat_id=$2 returning 1",
                    photo,
                    chat_id,
                ):
                    await conn.execute(
                        "insert into welcome (chat_id, photo) values ($1, $2)",
                        chat_id,
                        photo,
                    )

        elif subtype == "settings_set_welcome_url":
            if welcome and not welcome[0] and not welcome[1]:
                return await send_message(
                    chat_id + 2000000000,
                    await messages.get(subtype + "_empty_text_url"),
                    keyboard.settings_change_countable(
                        uid, "main", "welcome", onlybackbutton=True
                    ),
                )
            text_parts = event.object.message.text.split()
            if len(" ".join(text_parts[1:])) > 40:
                return await send_message(
                    chat_id + 2000000000,
                    await messages.get(subtype + "_limit_text"),
                    keyboard.settings_change_countable(
                        uid, "main", "welcome", onlybackbutton=True
                    ),
                )
            if (
                len(" ".join(text_parts[1:])) == 0
                or event.object.message.text.count("\n") > 0
            ):
                return await send_message(
                    chat_id + 2000000000,
                    await messages.settings_change_countable_format_error(),
                    keyboard.settings_change_countable(
                        uid, "main", "welcome", onlybackbutton=True
                    ),
                )
            if len(text_parts) < 2:
                return await send_message(
                    chat_id + 2000000000,
                    await messages.settings_change_countable_format_error(),
                    keyboard.settings_change_countable(
                        uid, "main", "welcome", onlybackbutton=True
                    ),
                )
            try:
                if not whoiscachedurl(text_parts[-1]):
                    raise Exception
            except Exception:
                return await send_message(
                    chat_id + 2000000000, await messages.get(subtype + "_no_url")
                )
            async with (await pool()).acquire() as conn:
                if not await conn.fetchval(
                    "update welcome set url = $1, button_label = $2 where chat_id=$3 returning 1",
                    text_parts[-1],
                    " ".join(text_parts[0:-1]),
                    chat_id,
                ):
                    await conn.execute(
                        "insert into welcome (chat_id, url, button_label) values ($1, $2, $3)",
                        chat_id,
                        text_parts[-1],
                        " ".join(text_parts[0:-1]),
                    )

        await send_message(
            chat_id + 2000000000,
            await messages.get(f"{subtype}_done"),
            keyboard.settings_change_countable(
                uid, "main", "welcome", onlybackbutton=True
            ),
        )

    if (
        queue_type == "settings_change_countable"
        and additional.get("setting") == "autodelete"
    ):
        await change_autodelete(
            event.object.message.text, additional["cmid"], additional["category"]
        )
        return

    if queue_type == "settings_change_countable":
        await change_countable(
            additional["setting"],
            additional["category"],
            additional["cmid"],
            event.object.message.text,
        )
        return

    if queue_type == "settings_set_punishment":
        await set_punishment(
            additional["setting"],
            additional["category"],
            additional["cmid"],
            event.object.message.text,
        )
        return

    if queue_type.startswith("settings_set_welcome_"):
        await welcome_actions(queue_type, additional.get("cmid"))
        return

    if queue_type == "settings_listaction":
        setting = additional["setting"]
        category = additional["category"]

        if setting == "disallowLinks":
            action = additional["action"]
            if action == "add":
                url = event.object.message.text.replace(" ", "")
                try:
                    if not whoiscachedurl(url):
                        raise
                except Exception:
                    return await send_message(
                        chat_id + 2000000000,
                        await messages.settings_change_countable_format_error(),
                        keyboard.settings_change_countable(
                            uid, category, setting, onlybackbutton=True
                        ),
                    )
                async with (await pool()).acquire() as conn:
                    if not await conn.fetchval(
                        "select exists(select 1 from antispamurlexceptions where chat_id=$1 and url=$2)",
                        chat_id,
                        url,
                    ):
                        await conn.execute(
                            "insert into antispamurlexceptions (chat_id, url) values ($1, $2)",
                            chat_id,
                            url,
                        )
                await send_message(
                    chat_id + 2000000000,
                    await messages.settings_listaction_done(setting, action, url),
                    keyboard.settings_change_countable(
                        uid, category, setting, onlybackbutton=True
                    ),
                )
                return
            elif action == "remove":
                url = (
                    event.object.message.text.replace(" ", "")
                    .replace("https://", "")
                    .replace("/", "")
                )
                async with (await pool()).acquire() as conn:
                    if not await conn.fetchval(
                        "delete from antispamurlexceptions where chat_id=$1 and url=$2 returning 1",
                        chat_id,
                        url,
                    ):
                        return await send_message(
                            chat_id + 2000000000,
                            await messages.settings_change_countable_format_error(),
                            keyboard.settings_change_countable(
                                uid, category, setting, onlybackbutton=True
                            ),
                        )
                await send_message(
                    chat_id + 2000000000,
                    await messages.settings_listaction_done(setting, action, url),
                    keyboard.settings_change_countable(
                        uid, category, setting, onlybackbutton=True
                    ),
                )
                return

        if setting == "vkLinks":
            action = additional["action"]
            url = event.object.message.text
            url = url[url.find("vk.") :]
            try:
                if "vk." not in url or not whoiscachedurl(url):
                    raise Exception
            except Exception:
                return await send_message(
                    chat_id + 2000000000,
                    await messages.settings_change_countable_format_error(),
                    keyboard.settings_change_countable(
                        uid, category, setting, onlybackbutton=True
                    ),
                )
            async with (await pool()).acquire() as conn:
                if action == "add":
                    if not await conn.fetchval(
                        "select exists(select 1 from vklinksexceptions where chat_id=$1 and url=$2)",
                        chat_id,
                        url,
                    ):
                        await conn.execute(
                            "insert into vklinksexceptions (chat_id, url) values ($1, $2)",
                            chat_id,
                            url,
                        )
                elif action == "remove":
                    if not await conn.fetchval(
                        "delete from vklinksexceptions where chat_id=$1 and url=$2 returning 1",
                        chat_id,
                        url,
                    ):
                        return await send_message(
                            chat_id + 2000000000,
                            await messages.settings_change_countable_format_error(),
                            keyboard.settings_change_countable(
                                uid, category, setting, onlybackbutton=True
                            ),
                        )
            await send_message(
                chat_id + 2000000000,
                await messages.settings_listaction_done(setting, action, url),
                keyboard.settings_change_countable(
                    uid, category, setting, onlybackbutton=True
                ),
            )
            return

        if setting == "forwardeds":
            action = additional["action"]
            exc_id = await search_id_in_message(
                event.object.message.text, event.object.message.reply_message, place=1
            )
            if not exc_id:
                return await send_message(
                    chat_id + 2000000000,
                    await messages.settings_change_countable_format_error(),
                    keyboard.settings_change_countable(
                        uid, category, setting, onlybackbutton=True
                    ),
                )
            async with (await pool()).acquire() as conn:
                if action == "add":
                    if not await conn.fetchval(
                        "select exists(select 1 from forwardedsexceptions where chat_id=$1 and exc_id=$2)",
                        chat_id,
                        exc_id,
                    ):
                        await conn.execute(
                            "insert into forwardedsexceptions (chat_id, exc_id) values ($1, $2)",
                            chat_id,
                            exc_id,
                        )
                elif action == "remove":
                    if not await conn.fetchval(
                        "delete from forwardedsexceptions where chat_id=$1 and exc_id=$2 returning 1",
                        chat_id,
                        exc_id,
                    ):
                        return await send_message(
                            chat_id + 2000000000,
                            await messages.settings_change_countable_format_error(),
                            keyboard.settings_change_countable(
                                uid, category, setting, onlybackbutton=True
                            ),
                        )
            await send_message(
                chat_id + 2000000000,
                await messages.settings_listaction_done(setting, action, exc_id),
                keyboard.settings_change_countable(
                    uid, category, setting, onlybackbutton=True
                ),
            )
            return


async def handle_premmenu_action(
    event: MessageNew,
    queue_type: str,
    additional: Dict[str, Any],
    chat_id: int,
    uid: int,
):
    if not event.object.message:
        return

    if queue_type == "premmenu_action_border_color":
        data = event.object.message.text
        rgb = data.replace(" ", "").split(",")
        if (
            len(rgb) == 3
            and all(255 >= int(i) >= 0 for i in rgb)
            and not data.startswith("#")
        ):
            color = "(" + ",".join(rgb) + ")"
        elif re.search(r"^#[0-9a-fA-F]{6}$", data):
            color = f"({','.join(str(i) for i in hex_to_rgb(data))})"
        else:
            return await send_message(
                chat_id + 2000000000,
                await messages.settings_change_countable_format_error(),
            )
        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                "update premmenu set value = $1 where uid=$2 and setting=$3 returning 1",
                color,
                uid,
                "border_color",
            ):
                await conn.execute(
                    "insert into premmenu (uid, setting, value) values ($1, $2, $3)",
                    uid,
                    "border_color",
                    color,
                )
        await send_message(
            chat_id + 2000000000,
            await messages.premmenu_action_complete(
                "border_color", color.replace("(", "").replace(")", "")
            ),
            keyboard.premmenu_back(uid),
        )


async def handle_captcha(
    event: MessageNew, additional: Dict[str, Any], chat_id: int, uid: int
):
    if not event.object.message:
        return

    async with (await pool()).acquire() as conn:
        c = await conn.fetchval(
            "select result from captcha where chat_id=$1 and uid=$2 order by exptime desc",
            chat_id,
            uid,
        )
    if c is None:
        return
    if c.strip() != event.object.message.text.strip():
        await delete_messages(event.object.message.conversation_message_id, chat_id)
        return

    name = await get_user_name(uid)
    await send_message(
        chat_id + 2000000000,
        await messages.captcha_pass(
            uid, name, datetime.datetime.now().strftime("%H:%M:%S %Y.%m.%d")
        ),
    )

    s = await managers.chat_settings.get(chat_id, "welcome", "pos")
    async with (await pool()).acquire() as conn:
        await conn.execute(
            "delete from typequeue where chat_id=$1 and uid=$2", chat_id, uid
        )
        welcome = await conn.fetchrow(
            "select msg, url, button_label, photo from welcome where chat_id=$1",
            chat_id,
        )
        cmsgs = await conn.fetch(
            "select cmid from captcha where chat_id=$1 and uid=$2", chat_id, uid
        )
        await conn.execute(
            "delete from captcha where chat_id=$1 and uid=$2", chat_id, uid
        )
    if s and welcome:
        await send_message(
            event.object.message.peer_id,
            welcome[0].replace("%name%", f"[id{uid}|{name}]"),
            keyboard.urlbutton(welcome[1], welcome[2]),
            welcome[3],
        )
    await delete_messages([i[0] for i in cmsgs], chat_id)
    await delete_messages(event.object.message.conversation_message_id, chat_id)


async def handle_prefix(
    event: MessageNew,
    queue_type: str,
    additional: Dict[str, Any],
    chat_id: int,
    uid: int,
):
    if not event.object.message:
        return

    if queue_type == "prefix_add":
        await delete_messages(additional["cmid"], chat_id)
        await delete_messages(event.object.message.conversation_message_id, chat_id)
        if len(event.object.message.text) > 2:
            await send_message(
                event.object.message.peer_id,
                await messages.addprefix_too_long(),
                keyboard.prefix_back(uid),
            )
            return
        await managers.prefixes.new_prefix(uid, event.object.message.text)
        await send_message(
            event.object.message.peer_id,
            await messages.addprefix(
                uid,
                await get_user_name(uid),
                await get_user_nickname(uid, chat_id),
                event.object.message.text,
            ),
            keyboard.prefix_back(uid),
        )
        return

    if queue_type == "prefix_del":
        await delete_messages(additional["cmid"], chat_id)
        await delete_messages(event.object.message.conversation_message_id, chat_id)
        if not await managers.prefixes.del_prefix(uid, event.object.message.text):
            await send_message(
                event.object.message.peer_id,
                await messages.delprefix_not_found(event.object.message.text),
                keyboard.prefix_back(uid),
            )
            return
        await send_message(
            event.object.message.peer_id,
            await messages.delprefix(
                uid,
                await get_user_name(uid),
                await get_user_nickname(uid, chat_id),
                event.object.message.text,
            ),
            keyboard.prefix_back(uid),
        )
        return


async def handle_raid_trigger(event: MessageNew, additional: Dict[str, Any]):
    if not event.object.message:
        return

    await delete_messages(additional["cmid"], event.object.message.peer_id - 2000000000)
    await delete_messages(
        event.object.message.conversation_message_id,
        event.object.message.peer_id - 2000000000,
    )
    data = event.object.message.text.split("/")
    if len(data) != 2 or any(not i.isdigit() for i in data):
        await send_message(
            event.object.message.peer_id,
            await messages.settings_change_countable_format_error(),
        )
        return
    if int(data[-1]) not in range(5, 121):
        await send_message(
            event.object.message.peer_id,
            "⚠️ Разрешённый промежуток времени - от 5 до 120 секунд.",
        )
        return
    async with (await pool()).acquire() as conn:
        raidmode = await conn.fetchrow(
            "update raidmode set limit_invites=$1, limit_seconds=$2 where chat_id=$3 returning trigger_status, limit_invites, limit_seconds",
            int(data[0]),
            int(data[1]),
            event.object.message.peer_id - 2000000000,
        )
        if raidmode is None:
            await conn.execute(
                "insert into raidmode (chat_id, trigger_status) values ($1, True)",
                event.object.message.peer_id - 2000000000,
            )
            raidmode = await conn.fetchrow(
                "select trigger_status, limit_invites, limit_seconds from raidmode where chat_id=$1",
                event.object.message.peer_id - 2000000000,
            )
    raidmode = list(raidmode)
    raidmode[1] = int(raidmode[1])
    raidmode[2] = int(raidmode[2])
    await send_message(
        event.object.message.peer_id,
        await messages.raid_settings(*raidmode),
        keyboard.raid_settings(event.object.message.from_id, raidmode[0]),
    )


async def handle_customlevel(
    event: MessageNew,
    queue_type: str,
    additional: Dict[str, int],
    chat_id: int,
    uid: int,
    queue_id: int,
):
    if not event.object.message:
        return

    level = additional["level"]
    level = await managers.custom_access_level.get(level, chat_id)
    if not level:
        return

    if queue_type.endswith("set_priority"):
        limit = 50 if await get_user_premium(uid) else 10
        try:
            priority = int(event.object.message.text)
            if priority not in range(1, limit + 1):
                raise Exception
        except Exception:
            return await send_message(
                event.object.message.peer_id,
                await messages.customlevel_set_priority(limit),
                keyboard.customlevel_to_settings(
                    uid, level.access_level, "Назад", clear_type_queue=True
                ),
            )
        if priority != level.access_level:
            await managers.custom_access_level.edit_access_level(
                level.access_level, chat_id, priority
            )
        await send_message(
            event.object.message.peer_id,
            await messages.customlevel_set_priority_done(level.name, priority),
            keyboard.customlevel_to_settings(
                uid, priority, "Назад", clear_type_queue=True
            ),
        )
    if queue_type.endswith("set_name"):
        name = event.object.message.text.strip()
        if len(name) > 32:
            return await send_message(
                event.object.message.peer_id,
                f"{await messages.createlevel_char_limit()}\n{await messages.customlevel_set_name()}",
                keyboard.customlevel_to_settings(
                    uid, level.access_level, "Назад", clear_type_queue=True
                ),
            )
        if (
            await managers.custom_access_level.get_by_name(
                name, event.object.message.peer_id - 2000000000
            )
            is not None
        ):
            return await send_message(
                event.object.message.peer_id,
                f"{await messages.createlevel_name_already_exists(name)}\n{await messages.customlevel_set_name()}",
                keyboard.customlevel_to_settings(
                    uid, level.access_level, "Назад", clear_type_queue=True
                ),
            )
        if chars := re.findall(
            r"[^a-zA-Zа-яА-ЯёЁ0-9 ~!@#$%^&*()_+\-={}|;:'\",.<>?\/]", name
        ):
            return await send_message(
                event.object.message.peer_id,
                f"""{await messages.createlevel_name_forbidden_chars(", ".join([f'"{i}"' for i in set(chars)]))}\n{await messages.customlevel_set_name()}""",
                keyboard.customlevel_to_settings(
                    uid, level.access_level, "Назад", clear_type_queue=True
                ),
            )
        await managers.custom_access_level.edit(
            level.access_level, event.object.message.peer_id - 2000000000, name=name
        )
        await managers.access_level.edit_custom_level_name(
            event.object.message.peer_id - 2000000000, level.access_level, name
        )
        await send_message(
            event.object.message.peer_id,
            await messages.customlevel_set_name_done(level.name, name),
            keyboard.customlevel_to_settings(
                uid, level.access_level, "Назад", clear_type_queue=True
            ),
        )
    if queue_type.endswith("set_emoji"):
        emoji = event.object.message.text.strip()
        if not is_single_emoji(emoji):
            return await send_message(
                event.object.message.peer_id,
                await messages.customlevel_set_emoji(),
                keyboard.customlevel_to_settings(
                    uid, level.access_level, "Назад", clear_type_queue=True
                ),
            )
        await managers.custom_access_level.edit(
            level.access_level, event.object.message.peer_id - 2000000000, emoji=emoji
        )
        await send_message(
            event.object.message.peer_id,
            await messages.customlevel_set_emoji_done(level.name, emoji),
            keyboard.customlevel_to_settings(
                uid, level.access_level, "Назад", clear_type_queue=True
            ),
        )
    if queue_type.endswith("set_commands"):
        message = event.object.message.text.rstrip(".")
        commands = re.split(r",\s*|\s+", message)
        commands = [c for c in commands if c]
        bad_input = [
            c
            for c in commands
            if settings.commands.commands.get(c, 8) == 8
            or c in settings.commands.custom_preserved
        ]
        if not commands or bad_input:
            msg = await messages.customlevel_set_commands()
            if bad_input:
                msg = f"""⚠️ Неверно указаны команды: {", ".join([f'"{c}"' for c in bad_input])}\n{msg}"""
            return await send_message(
                event.object.message.peer_id,
                msg,
                keyboard.customlevel_to_settings(
                    uid, level.access_level, "Назад", clear_type_queue=True
                ),
            )
        await managers.custom_access_level.set_preset(
            level.access_level, event.object.message.peer_id - 2000000000, commands
        )
        await send_message(
            event.object.message.peer_id,
            await messages.customlevel_set_commands_done(
                level.name, level.access_level, commands
            ),
            keyboard.customlevel_to_settings(
                uid, level.access_level, "Назад", clear_type_queue=True
            ),
        )

    async with (await pool()).acquire() as conn:
        await conn.execute("delete from typequeue where id=$1", queue_id)


async def route_queue(event: MessageNew):
    if event.object.message is None:
        return

    uid = event.object.message.from_id
    chat_id = event.object.message.peer_id - 2000000000

    async with (
        (await pool()).acquire() as conn
    ):  # LAME database states TODO: create a manager or use vkbottle fsm(?)
        queue = await conn.fetchrow(
            'select id, chat_id, uid, "type", additional from typequeue where chat_id=$1 and uid=$2',
            chat_id,
            uid,
        )
        if not queue:
            return False
        if queue[3] not in ("captcha",) and not queue[3].startswith("customlevel_"):
            await conn.execute("delete from typequeue where id=$1", queue[0])

    additional = literal_eval(queue[4])
    qtype: str = queue[3]

    try:
        if qtype.startswith("notification_"):
            return await handle_notification(event, qtype, additional, chat_id, uid)

        if qtype.startswith("settings_"):
            return await handle_settings(event, qtype, additional, chat_id, uid)

        if qtype.startswith("premmenu_action_"):
            return await handle_premmenu_action(event, qtype, additional, chat_id, uid)

        if qtype == "captcha":
            return await handle_captcha(event, additional, chat_id, uid)

        if qtype.startswith("prefix"):
            return await handle_prefix(event, qtype, additional, chat_id, uid)

        if qtype == "raid_trigger_set":
            return await handle_raid_trigger(event, additional)

        if qtype.startswith("customlevel_"):
            return await handle_customlevel(
                event, qtype, additional, chat_id, uid, queue[0]
            )
    except Exception:
        logger.exception("TypeQueue error:")
        return


async def answer_handler(event: MessageNew):
    return await route_queue(event)
