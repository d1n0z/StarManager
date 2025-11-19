import asyncio
import locale
import os
import random
import re
import tempfile
import time
from ast import literal_eval
from copy import deepcopy
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Literal, Union
from urllib.parse import urlparse

import aiogram
import aiogram.exceptions
import dns.resolver
import pysafebrowsing
import requests
import urllib3
import xmltodict
from cache.async_lru import AsyncLRU
from cache.async_ttl import AsyncTTL
from loguru import logger
from memoization import cached
from multicolorcaptcha import CaptchaGenerator
from nudenet import NudeDetector
from vkbottle import PhotoMessageUploader, VKAPIError
from vkbottle.bot import Message
from vkbottle.tools.mini_types.bot.foreign_message import ForeignMessageMin
from vkbottle_types.codegen.objects import MessagesDeleteFullResponseItem
from vkbottle_types.objects import (
    MessagesForeignMessage,
    MessagesMessage,
    MessagesMessageAttachmentType,
    MessagesSendUserIdsResponseItem,
    UsersFields,
)
from yookassa import Configuration, Payment
from yookassa.payment import PaymentResponse

from StarManager.core import config, managers
from StarManager.core.config import api, settings, vk_api_session
from StarManager.core.db import pool

_hiddenalbumuid = None
_hiddenalbumlock = asyncio.Lock()


@AsyncTTL(time_to_live=300, maxsize=0)
async def get_user_name(uid: int) -> str:
    if uid < 0:
        return await get_group_name(uid)
    async with (await pool()).acquire() as conn:
        if name := await conn.fetchval("select name from usernames where uid=$1", uid):
            return name
        name = await api.users.get(user_ids=[uid], fields=[UsersFields.DOMAIN.value])  # type: ignore
        if not name:
            return "UNKNOWN"
        await conn.execute(
            "insert into usernames (uid, name, domain) values ($1, $2, $3)",
            uid,
            f"{name[0].first_name} {name[0].last_name}",
            name[0].domain or f"id{name[0].id}",
        )
        return f"{name[0].first_name} {name[0].last_name}"


async def kick_user(uid: int, chat_id: int) -> bool:
    try:
        await api.messages.remove_chat_user(chat_id=chat_id, member_id=uid)
        if (await get_chat_settings(chat_id))["main"]["deleteAccessAndNicknameOnLeave"]:
            await managers.access_level.delete(uid, chat_id)
            async with (await pool()).acquire() as conn:
                await conn.execute(
                    "delete from nickname where chat_id=$1 and uid=$2", chat_id, uid
                )
            await set_chat_mute(uid, chat_id, 0)
    except Exception:
        return False
    return True


async def delete_messages(
    cmids: int | List[int], chat_id: int
) -> bool | list[MessagesDeleteFullResponseItem]:
    try:
        return await api.messages.delete(
            group_id=settings.vk.group_id,
            delete_for_all=True,
            peer_id=chat_id + 2000000000,
            cmids=[cmids] if isinstance(cmids, int) else cmids,
        )
    except Exception:
        return False


async def search_id_in_message(
    message: str,
    reply: ForeignMessageMin | MessagesForeignMessage | None,
    place: int | None = 2,
) -> int:
    if reply:
        return reply.from_id

    if place:
        data = message.split()
        if len(data) < place:
            return 0
        message = data[place - 1]

    from_link_id = re.search(r"vk\.com/id(\d+)", message)
    from_link = re.search(r"vk\.com/([a-zA-Z0-9_.]+)", message)
    from_mention = re.search(r"\[(club|id)(\d+)\|", message)

    if from_link_id:
        return int(from_link_id.group(1))

    if from_link:
        try:
            user = await api.users.get(user_ids=[from_link.group(1)])
            return user[0].id
        except Exception:
            try:
                group = await api.groups.get_by_id(group_id=from_link.group(1))
                if group.groups:
                    return -group.groups[0].id
            except Exception:
                pass

    if from_mention:
        return (
            -int(from_mention.group(2))
            if from_mention.group(1) == "club"
            else int(from_mention.group(2))
        )

    if place is not None and message.isdigit():
        return int(message)

    return 0


async def send_message_event_answer(
    event_id: Any, user_id: int, peer_id: int, event_data: str | None = None
) -> bool:
    try:
        await api.messages.send_message_event_answer(
            event_id=event_id, user_id=user_id, peer_id=peer_id, event_data=event_data
        )
    except Exception:
        return False
    return True


async def send_message(
    peer_ids: int | List[int],
    msg: str | None = None,
    kbd: str | None = None,
    photo: str | None = None,
    disable_mentions: bool = True,
) -> list[MessagesSendUserIdsResponseItem] | int | bool:
    try:
        msgs: List[MessagesSendUserIdsResponseItem] = await api.messages.send(
            random_id=0,
            peer_ids=[peer_ids] if isinstance(peer_ids, int) else peer_ids,
            message=msg,
            keyboard=kbd,
            attachment=photo,
            disable_mentions=disable_mentions,
        )  # type: ignore
    except Exception:
        return False

    if isinstance(peer_ids, int) and peer_ids > 2000000000:
        chatid = peer_ids - 2000000000
        val, pos = await managers.chat_settings.get(
            chatid, "autodelete", ("value", "pos")
        )
        if pos and val:
            async with (await pool()).acquire() as conn:
                await conn.execute(
                    "insert into todelete (peerid, cmid, delete_at) values ($1, $2, $3)",
                    msgs[0].peer_id,
                    msgs[0].conversation_message_id,
                    time.time() + val,
                )
    return msgs


async def edit_message(
    msg: str, peer_id: int, cmid: int | None, kb=None, attachment=None
) -> bool:
    if not cmid:
        return False
    try:
        return await api.messages.edit(
            peer_id=peer_id,
            message=msg,
            disable_mentions=True,
            conversation_message_id=cmid,
            keyboard=kb,
            attachment=attachment,
        )
    except Exception:
        return False


@AsyncTTL(time_to_live=300, maxsize=0)
async def get_chat_name(chat_id: int, none: Any = "UNKNOWN"):
    async with (await pool()).acquire() as conn:
        if name := await conn.fetchval(
            "select name from chatnames where chat_id=$1", chat_id
        ):
            return name
        try:
            chatname = await api.messages.get_conversations_by_id(
                peer_ids=[chat_id + 2000000000], group_id=settings.vk.group_id
            )
            chatname = chatname.items[0].chat_settings
            chatname = chatname.title if chatname else none
        except Exception:
            chatname = none
        await conn.execute(
            "insert into chatnames (chat_id, name) values ($1, $2)", chat_id, chatname
        )
    return chatname


@AsyncTTL(time_to_live=300, maxsize=0)
async def get_group_name(group_id: int) -> str:
    async with (await pool()).acquire() as conn:
        if name := await conn.fetchval(
            "select name from groupnames where group_id=$1", -abs(group_id)
        ):
            return name
        name = await api.groups.get_by_id(group_id=abs(group_id))
        if not name.groups:
            return "UNKNOWN"
        name = name.groups[0].name
        await conn.execute(
            "insert into groupnames (group_id, name) values ($1, $2)",
            -abs(group_id),
            name,
        )
        return name or "UNKNOWN"


@AsyncTTL(maxsize=0)
async def is_chat_admin(id: int, chat_id: int) -> bool:
    try:
        status = await api.messages.get_conversation_members(
            peer_id=chat_id + 2000000000
        )
        for i in status.items:
            if i.member_id == id and (i.is_admin or i.is_owner):
                return True
    except Exception:
        pass
    return False


@AsyncTTL(maxsize=0)
async def get_chat_owner(chat_id: int) -> int | bool:
    try:
        status = await api.messages.get_conversation_members(
            peer_id=chat_id + 2000000000
        )
        for i in status.items:
            if i.is_owner:
                return i.member_id
    except Exception:
        pass
    return False


@AsyncTTL(maxsize=0)
async def get_chat_members(chat_id: int) -> int | bool:
    try:
        status = await api.messages.get_conversation_members(
            peer_id=chat_id + 2000000000
        )
        return len(status.items)
    except Exception:
        return False


async def set_chat_mute(
    uid: int | Iterable[int], chat_id: int, mute_time: int | float | None = None
) -> Any:
    try:
        if mute_time is None or mute_time > 0:
            payload = {
                "peer_id": chat_id + 2000000000,
                "member_ids": uid,
                "action": "ro",
            }
            if mute_time is not None and mute_time < 2676000:
                payload["for"] = int(mute_time)
            return await asyncio.to_thread(
                vk_api_session.method,
                "messages.changeConversationMemberRestrictions",
                payload,
            )
        else:
            return await asyncio.to_thread(
                vk_api_session.method,
                "messages.changeConversationMemberRestrictions",
                {"peer_id": chat_id + 2000000000, "member_ids": uid, "action": "rw"},
            )
    except Exception:
        return


async def upload_image(
    file: str, uid: int | None = None, retry: int = 0
) -> str | None:
    if not uid:
        uid = await get_hidden_album_user()
    try:
        photo = await PhotoMessageUploader(api).upload(file_source=file, peer_id=uid)
        if not photo:
            raise Exception
        return photo
    except Exception as e:
        if "internal" in str(e).lower() or "access" in str(e).lower():
            async with (await pool()).acquire() as conn:
                await conn.execute(
                    "insert into hiddenalbumserverinternalerror (uid) values ($1)", uid
                )
            global _hiddenalbumuid
            _hiddenalbumuid = None
            uid = await get_hidden_album_user()
        if retry < 6 or "too many" in str(e).lower():
            await asyncio.sleep((2 ** retry) / 2)
            return await upload_image(file, uid, retry + 1)
        raise e


def _get_reg_date_sync(id: int, format: str) -> str | None:
    try:
        urlmanager = urllib3.PoolManager()
        response = urlmanager.request("GET", f"https://vk.com/foaf.php?id={id}")
        try:
            data = xmltodict.parse(response.data)
            data = (
                data["rdf:RDF"]["foaf:Person"]["ya:created"]["@dc:date"][:10]
                .replace("-", ".")
                .split(".")
            )
        except Exception:
            data = response.data.decode("latin-1")
            data = data[data.find('<ya:created dc:date="') + 21 :]
            data = data[: data.find('"')]
            data = data[: data.find("T")].replace("-", ".").split(".")

        locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")
        data = date(year=int(data[0]), month=int(data[1]), day=int(data[2]))
        return data.strftime(format)
    except Exception:
        return None


@AsyncLRU(maxsize=0)
async def get_reg_date(
    id: int, format: str = "%d %B %Y", none: Any = "Не удалось определить"
) -> str | Any:
    result = await asyncio.to_thread(_get_reg_date_sync, id, format)
    return result if result is not None else none


@AsyncTTL(time_to_live=2, maxsize=0)
async def get_user_access_level(uid: int, chat_id: int, none: Any = 0) -> int | Any:
    return await managers.access_level.get_access_level(uid, chat_id) or none


async def get_user_last_message(
    uid: int, chat_id: int, none: Any = "Неизвестно"
) -> int | Any:
    async with (await pool()).acquire() as conn:
        return (
            await conn.fetchval(
                "select last_message from lastmessagedate where chat_id=$1 and uid=$2",
                chat_id,
                uid,
            )
            or none
        )


async def get_user_nickname(uid: int, chat_id: int, none: Any = None) -> str | Any:
    async with (await pool()).acquire() as conn:
        return (
            await conn.fetchval(
                "select nickname from nickname where chat_id=$1 and uid=$2",
                chat_id,
                uid,
            )
            or none
        )


async def get_user_mute(uid, chat_id, none=0) -> int:
    async with (await pool()).acquire() as conn:
        return (
            await conn.fetchval(
                "select mute from mute where chat_id=$1 and uid=$2", chat_id, uid
            )
            or none
        )


async def get_user_warns(uid, chat_id, none=0) -> int:
    async with (await pool()).acquire() as conn:
        return (
            await conn.fetchval(
                "select warns from warn where chat_id=$1 and uid=$2", chat_id, uid
            )
            or none
        )


async def get_user_ban(uid, chat_id, none=0) -> int:
    async with (await pool()).acquire() as conn:
        return (
            await conn.fetchval(
                "select ban from ban where chat_id=$1 and uid=$2", chat_id, uid
            )
            or none
        )


async def get_chat_access_name(chat_id: int, lvl: int, none: Any = None) -> int | None:
    async with (await pool()).acquire() as conn:
        return (
            await conn.fetchval(
                "select name from accessnames where chat_id=$1 and lvl=$2", chat_id, lvl
            )
            or none
        )


async def get_user_ban_info(uid, chat_id, none=None) -> dict:
    if none is None:
        none = {"times": [], "causes": [], "names": [], "dates": []}
    async with (await pool()).acquire() as conn:
        ban = await conn.fetchrow(
            "select last_bans_times, last_bans_causes, last_bans_names, last_bans_dates "
            "from ban where chat_id=$1 and uid=$2",
            chat_id,
            uid,
        )
    if ban:
        return {
            "times": literal_eval(ban[0]),
            "causes": literal_eval(ban[1]),
            "names": literal_eval(ban[2]),
            "dates": literal_eval(ban[3]),
        }
    return none


async def get_user_xp(uid, none=0):
    return await managers.xp.get(uid, "xp") or none


async def get_user_coins(uid, none=0):
    return await managers.xp.get(uid, "coins") or none


async def get_user_league(uid, none=1):
    return await managers.xp.get(uid, "league") or none


async def get_user_level(uid, none=0):
    return await managers.xp.get(uid, "lvl") or none


@AsyncLRU(maxsize=0)
async def get_user_needed_xp(xp):
    return 1000 - xp


@AsyncTTL(time_to_live=120, maxsize=0)
async def get_xp_top(
    returnval="count", limit: int = 10, league: int = 1, users: Union[List, None] = None
) -> Dict[int, int]:
    top = await managers.xp.get_xp_top(league, users, limit)
    if returnval == "count":
        return {i[0]: k for k, i in enumerate(top, start=1)}
    elif returnval == "lvl":
        return {i[0]: i[1].lvl for i in top}
    else:
        raise Exception('returnval must be "count" or "lvl"')


@AsyncTTL(time_to_live=10, maxsize=0)
async def get_user_premium(uid, none=0) -> int:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval("select time from premium where uid=$1", uid) or none


async def get_user_premmenu_setting(uid, setting, none):
    async with (await pool()).acquire() as conn:
        res = await conn.fetchval(
            (
                "select pos from premmenu where uid=$1 and setting=$2"
                if setting in settings.premium_menu.turn
                else 'select "value" from premmenu where uid=$1 and setting=$2'
            ),
            uid,
            setting,
        )
    return res if res is not None else none


async def get_user_premmenu_settings(uid):
    user_settings = deepcopy(settings.premium_menu.default)
    async with (await pool()).acquire() as conn:
        clear_by_fire = await conn.fetchval(
            "select pos from premmenu where uid=$1 and setting=$2", uid, "clear_by_fire"
        )
        if clear_by_fire is not None:
            user_settings["clear_by_fire"] = clear_by_fire
        border_color = await conn.fetchval(
            'select "value" from premmenu where uid=$1 and setting=$2',
            uid,
            "border_color",
        )
        if border_color is not None:
            user_settings["border_color"] = border_color
        tagnotif = await conn.fetchval(
            "select pos from premmenu where uid=$1 and setting=$2", uid, "tagnotif"
        )
        if tagnotif is not None:
            user_settings["tagnotif"] = tagnotif
    return user_settings


async def get_chat_command_level(chat_id, cmd, none):
    async with (await pool()).acquire() as conn:
        return (
            await conn.fetchval(
                "select lvl from commandlevels where chat_id=$1 and cmd=$2",
                chat_id,
                cmd,
            )
            or none
        )


async def get_user_messages(uid, chat_id, none=0) -> int:
    async with (await pool()).acquire() as conn:
        return (
            await conn.fetchval(
                "select messages from messages where chat_id=$1 and uid=$2",
                chat_id,
                uid,
            )
            or none
        )


async def add_user_xp(uid, addxp, checklvlbanned=True):
    async with (await pool()).acquire() as conn:
        if checklvlbanned:
            if await conn.fetchval(
                "select exists(select 1 from lvlbanned where uid=$1)", uid
            ) or await conn.fetchval(
                "select exists(select 1 from blocked where uid=$1 and type='user')", uid
            ):
                return
    await managers.xp.add_user_xp(uid, addxp)


async def add_user_coins(
    uid, addcoins, checklvlbanned=True, addlimit=False, bonus_peer_id=0
) -> None:
    async with (await pool()).acquire() as conn:
        if checklvlbanned:
            if await conn.fetchval(
                "select exists(select 1 from lvlbanned where uid=$1)", uid
            ) or await conn.fetchval(
                "select exists(select 1 from blocked where uid=$1 and type='user')", uid
            ):
                return
    needed_message = await managers.xp.add_user_coins(
        uid,
        addcoins,
        (u_limit := 1600 if await get_user_premium(uid) else 800),
        addlimit,
    )
    if needed_message == "bonus" and bonus_peer_id:
        await send_message(
            bonus_peer_id,
            f"🎁 [id{uid}|{await get_user_name(uid)}], вы получили +100 монеток за достижение дневного лимита в {u_limit} монеток.",
        )


@AsyncTTL(time_to_live=5, maxsize=0)
async def get_chat_settings(chat_id) -> Dict[str, Dict[str, int]]:
    chatsettings = deepcopy(settings.settings_default.defaults)
    for cat, chat in chatsettings.items():
        for setting, _ in chat.items():
            pos = await managers.chat_settings.get(chat_id, setting, "pos")
            if pos is not None:
                chatsettings[cat][setting] = pos
    return chatsettings


@AsyncTTL(time_to_live=5, maxsize=0)
async def get_chat_setting_value(chat_id, setting):
    return await managers.chat_settings.get(chat_id, setting, "value")


@AsyncTTL(time_to_live=5, maxsize=0)
async def get_chat_alt_settings(chat_id):
    chatsettings = deepcopy(settings.settings_alt.defaults)
    for cat, chat in chatsettings.items():
        for setting, _ in chat.items():
            chatsetting = await managers.chat_settings.get(chat_id, setting, "pos2")
            if chatsetting is not None:
                chatsettings[cat][setting] = chatsetting
    return chatsettings


async def turn_chat_setting(chat_id, category, setting, alt=False) -> None:
    pos = await managers.chat_settings.get(chat_id, setting, "pos2" if alt else "pos")
    await managers.chat_settings.edit(
        chat_id,
        setting,
        **{
            "pos2" if alt else "pos": not (
                (
                    settings.settings_meta.defaults[setting]["pos"]
                    if setting in settings.settings_meta.defaults
                    else settings.settings_default.defaults[category][setting]
                )
                if pos is None
                else pos
            )
        },
    )


async def set_user_access_level(uid, chat_id, access_level):
    await managers.access_level.edit_access_level(uid, chat_id, access_level)


async def get_silence(chat_id) -> bool:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval(
            "select exists(select 1 from silencemode where chat_id=$1 and activated=True)",
            chat_id,
        )


@AsyncTTL(time_to_live=120, maxsize=0)
async def is_chat_member(uid, chat_id):
    try:
        return uid in [
            i.member_id
            for i in (
                await api.messages.get_conversation_members(
                    peer_id=chat_id + 2000000000
                )
            ).items
        ]
    except Exception:
        return False


def _nsfw_detector_sync(pic_path):
    detector = NudeDetector()
    with open(pic_path, "rb") as f:
        image_data = f.read()

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(image_data)
        temp_file_path = temp_file.name
    result = detector.detect(temp_file_path)
    os.unlink(temp_file_path)
    for i in result:
        if i["class"] in settings.nsfw_categories.categories:
            if i["score"] > 0.3:
                return True
    return False


async def NSFW_detector(pic_path):
    return await asyncio.to_thread(_nsfw_detector_sync, pic_path)


def whoiscached(text):
    # return whois.whois(text)  # doesn't work
    try:
        if "." not in text:
            return False
        dns.resolver.resolve(text, "A")
        return True
    except Exception:
        return False


def whoiscachedurl(text):
    # return whois.whois(text)  # doesn't work
    for i in text.split("/"):
        try:
            dns.resolver.resolve(i, "A")
            return True
        except Exception:
            continue


async def get_user_prefixes(u_prem, uid) -> list:
    if u_prem:
        async with (await pool()).acquire() as conn:
            prefixes = await conn.fetch("select prefix from prefix where uid=$1", uid)
        return settings.commands.prefix + [i[0] for i in prefixes]
    return settings.commands.prefix


async def antispam_checker(
    chat_id, uid, message: MessagesMessage, chat_settings
) -> str | Literal[False]:
    if chat_settings["antispam"]["messagesPerMinute"]:
        setting = await managers.chat_settings.get(
            chat_id, "messagesPerMinute", "value"
        )
        if setting is not None and managers.antispam.get_count(chat_id, uid) >= setting:
            return "messagesPerMinute"

    if chat_settings["antispam"]["maximumCharsInMessage"]:
        setting = await managers.chat_settings.get(
            chat_id, "maximumCharsInMessage", "value"
        )
        if setting is not None and len(message.text) >= setting:
            return "maximumCharsInMessage"
    if chat_settings["antispam"]["disallowLinks"] and not any(
        message.text.startswith(i)
        for i in await get_user_prefixes(await get_user_premium(uid), uid)
    ):
        data = message.text.split()
        async with (await pool()).acquire() as conn:
            for i in data:
                for y in i.split("/"):
                    if (
                        "." not in y
                        or y in ["vk.com", "vk.ru", "star-manager.ru"]
                        or not whoiscached(y)
                    ):
                        continue
                    if not await conn.fetchval(
                        "select exists(select 1 from antispamurlexceptions where chat_id=$1"
                        " and url=$2)",
                        chat_id,
                        y.replace("https://", "").replace("/", ""),
                    ):
                        return "disallowLinks"
    if chat_settings["antispam"]["disallowNSFW"] and message.attachments is not None:
        for i in message.attachments:
            if (
                i.type != MessagesMessageAttachmentType.PHOTO
                or i.photo is None
                or i.photo.sizes is None
            ):
                continue
            photo = i.photo.sizes[2]
            for y in i.photo.sizes:
                if y.width > photo.width:
                    photo = y
            if not photo or not photo.url:
                continue

            def download_and_save():
                r = requests.get(photo.url)  # type: ignore
                filename = (
                    settings.service.path
                    + f"src/StarManager/core/media/temp/{time.time()}.jpg"
                )
                with open(filename, "wb") as f:
                    f.write(r.content)
                return filename

            filename = await asyncio.to_thread(download_and_save)
            isNSFW = await NSFW_detector(filename)
            if isNSFW:
                return "disallowNSFW"
    if chat_settings["antispam"]["vkLinks"]:
        data = message.text.split()
        async with (await pool()).acquire() as conn:
            for i in data:
                if not any(domain in i for domain in ("vk.com", "vk.ru")):
                    continue
                if not await conn.fetchval(
                    "select exists(select 1 from vklinksexceptions where chat_id=$1"
                    " and url=$2)",
                    chat_id,
                    i[i.find("vk.") :],
                ):
                    return "vkLinks"
    if chat_settings["antispam"]["forwardeds"] and (
        message.fwd_messages or message.attachments
    ):
        msgs = []
        if message.attachments:
            msgs.append(message.attachments)
        if message.fwd_messages is not None:
            stack = message.fwd_messages.copy()
            while stack:
                msg = stack.pop()
                if msg.attachments:
                    msgs.append(msg.attachments)
                    if hasattr(msg, "fwd_messages") and msg.fwd_messages:
                        stack.extend(msg.fwd_messages)
        async with (await pool()).acquire() as conn:
            for i in msgs:
                for atchmnt in i:
                    if not hasattr(atchmnt, "wall") or not atchmnt.wall:
                        continue
                    if not await conn.fetchval(
                        "select exists(select 1 from forwardedsexceptions where chat_id=$1 and exc_id=$2)",
                        chat_id,
                        atchmnt.wall.owner_id,
                    ):
                        return "forwardeds"
    return False


async def command_cooldown_check(uid: int, cmd: str):
    if not (
        cd := (
            settings.commands.cooldown.get(cmd, 0)
            / (2 if await get_user_premium(uid) else 1)
        )
    ):
        return None
    if (
        last_command := managers.commands_cooldown.get_user_time(uid, cmd)
    ) > time.time() - cd:
        return last_command

    managers.commands_cooldown.set(uid, cmd)
    return None


@cached
def point_days(seconds):
    res = int(int(seconds) // 86400)
    if res == 1:
        res = str(res) + " день"
    elif 1 < res < 5:
        res = str(res) + " дня"
    else:
        res = str(res) + " дней"
    return res


@cached
def point_hours(seconds):
    res = int(int(seconds) // 3600)
    if res in [23, 22, 4, 3, 2]:
        res = f"{res} часа"
    elif res in [21, 1]:
        res = f"{res} час"
    else:
        res = f"{res} часов"
    return res


@cached
def point_minutes(seconds):
    res = int(int(seconds) // 60)
    if res % 10 == 1 and res % 100 != 11:
        res = str(res) + " минута"
    elif 2 <= res % 10 <= 4 and (res % 100 < 10 or res % 100 >= 20):
        res = str(res) + " минуты"
    else:
        res = str(res) + " минут"
    return res


@cached
def point_words(value, words):
    """
    :param value
    :param words: e.g. (минута, минуты, минут)
    :return:
    """
    if value % 10 == 1 and value % 100 != 11:
        res = str(value) + f" {words[0]}"
    elif 2 <= value % 10 <= 4 and (value % 100 < 10 or value % 100 >= 20):
        res = str(value) + f" {words[1]}"
    else:
        res = str(value) + f" {words[2]}"
    return res


def chunks(li, n):
    for i in range(0, len(li), n):
        yield li[i : i + n]


async def get_user_rep_banned(uid) -> bool:
    async with (await pool()).acquire() as conn:
        if (
            t := await conn.fetchval("select time from reportban where uid=$1", uid)
        ) and (not t or time.time() < t):
            return True
        return False


async def generate_captcha(uid, chat_id, exp):
    def gen_captcha():
        gen = CaptchaGenerator()
        image = gen.gen_math_captcha_image(difficult_level=2, multicolor=True)
        name = f"{settings.service.path}src/StarManager/core/media/temp/captcha{uid}_{chat_id}.png"
        image.image.save(name, "png")
        return name, str(image.equation_result)

    name, result = await asyncio.to_thread(gen_captcha)
    async with (await pool()).acquire() as conn:
        c = await conn.fetchval(
            "insert into captcha (chat_id, uid, exptime, result) values ($1, $2, $3, $4) returning id",
            chat_id,
            uid,
            time.time() + exp * 60,
            result,
        )
    return name, c


async def punish(uid, chat_id, setting_id):
    key = await managers.chat_settings.get_by_id(setting_id)
    setting, name = await managers.chat_settings.get(*key, ("punishment", "setting"))
    if setting is None:
        return False
    punishment = list(setting.split("|"))
    if punishment[0] == "deletemessage":
        return "del"
    if punishment[0] == "kick":
        await kick_user(uid, chat_id)
        return punishment

    if name in settings.settings_meta.positions["antispam"]:
        cause = (
            "Анти-спам (#AS"
            + str(
                list(settings.settings_meta.positions["antispam"].keys()).index(name)
                + 1
            )
            + ")"
        )
    else:
        cause = "Нарушение правил беседы."

    if punishment[0] == "mute":
        async with (await pool()).acquire() as conn:
            ms = await conn.fetchrow(
                "select last_mutes_times, last_mutes_causes, last_mutes_names, last_mutes_dates from mute where "
                "chat_id=$1 and uid=$2",
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

        mute_date = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        mute_time = int(punishment[1]) * 60
        mute_times.append(mute_time)
        mute_causes.append(cause)
        mute_names.append(f"[club{-settings.vk.group_id}|Star Manager]")
        mute_dates.append(mute_date)

        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                "update mute set mute = $1, last_mutes_times = $2, last_mutes_causes = $3, "
                "last_mutes_names = $4, last_mutes_dates = $5 where chat_id=$6 and uid=$7 returning 1",
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

        await set_chat_mute(uid, chat_id, mute_time)
        return punishment
    elif punishment[0] == "ban":
        ban_date = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
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

        ban_time = int(punishment[1]) * 86400
        ban_times.append(ban_time)
        ban_causes.append(cause)
        ban_names.append(f"[club{-settings.vk.group_id}|Star Manager]")
        ban_dates.append(ban_date)

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

        await kick_user(uid, chat_id)
        return punishment
    elif punishment[0] == "warn":
        async with (await pool()).acquire() as conn:
            res = await conn.fetchrow(
                "select warns, last_warns_times, last_warns_causes, last_warns_names, "
                "last_warns_dates from warn where chat_id=$1 and uid=$2",
                chat_id,
                uid,
            )
        if res is not None:
            warns = res[0] + 1
            warn_times = literal_eval(res[1])
            warn_causes = literal_eval(res[2])
            warn_names = literal_eval(res[3])
            warn_dates = literal_eval(res[4])
        else:
            warns = 1
            warn_times, warn_causes, warn_names, warn_dates = [], [], [], []
        warn_times.append(0)
        warn_causes.append(cause)
        warn_names.append(f"[club{-settings.vk.group_id}|Star Manager]")
        warn_dates.append(datetime.now().strftime("%Y.%m.%d %H:%M:%S"))

        if warns >= 3:
            warns = 0
            await kick_user(uid, chat_id)

        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                "update warn set warns = $1, last_warns_times = $2, last_warns_causes = $3, last_warns_names = $4, "
                "last_warns_dates = $5 where chat_id=$6 and uid=$7 returning 1",
                warns,
                f"{warn_times}",
                f"{warn_causes}",
                f"{warn_names}",
                f"{warn_dates}",
                chat_id,
                uid,
            ):
                await conn.execute(
                    "insert into warn (uid, chat_id, warns, last_warns_times, last_warns_causes, last_warns_names, "
                    "last_warns_dates) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                    uid,
                    chat_id,
                    warns,
                    f"{warn_times}",
                    f"{warn_causes}",
                    f"{warn_names}",
                    f"{warn_dates}",
                )
        return punishment
    return False


async def get_gpool(chat_id) -> List[Any] | Literal[False]:
    try:
        async with (await pool()).acquire() as conn:
            chats = [
                i[0]
                for i in await conn.fetch(
                    "select chat_id from gpool where uid=(select uid from gpool where chat_id=$1)",
                    chat_id,
                )
            ]
        if len(chats) == 0:
            raise Exception
        return chats
    except Exception:
        return False


async def get_pool(chat_id, group) -> list[Any] | Literal[False]:
    try:
        async with (await pool()).acquire() as conn:
            chats = [
                i[0]
                for i in await conn.fetch(
                    'select chat_id from chatgroups where "group"=$1 and uid='
                    "(select uid from accesslvl where accesslvl.chat_id=$2 and access_level>6 "
                    "order by access_level limit 1)",
                    group,
                    chat_id,
                )
            ]
        if len(chats) == 0:
            raise Exception
        return chats
    except Exception:
        return False


async def get_silence_allowed(chat_id):
    async with (await pool()).acquire() as conn:
        lvls = await conn.fetchval(
            "select allowed from silencemode where chat_id=$1", chat_id
        )
    if lvls is not None:
        return literal_eval(lvls) + [7, 8]
    return [7, 8]


async def get_user_rep(uid):
    async with (await pool()).acquire() as conn:
        return await conn.fetchval("select rep from reputation where uid=$1", uid) or 0


async def get_rep_top(uid):
    async with (await pool()).acquire() as conn:
        top = [
            i[0]
            for i in await conn.fetch("select uid from reputation order by rep desc")
        ]
        allu = await conn.fetchval("select count(*) as c from allusers")
    return (top.index(uid) + 1) if uid in top else allu


@cached
def hex_to_rgb(value):
    value = value.lstrip("#")
    lv = len(value)
    return tuple(int(value[i : i + lv // 3], 16) for i in range(0, lv, lv // 3))


async def chat_premium(chat_id, none=False):
    chat = await managers.public_chats.get_chat(chat_id)
    return none if not chat else chat.premium


@AsyncTTL(time_to_live=300, maxsize=0)
async def is_messages_from_group_allowed(uid):
    return (
        await api.messages.is_messages_from_group_allowed(
            group_id=settings.vk.group_id, user_id=uid
        )
    ).is_allowed


async def get_hidden_album_user():
    global _hiddenalbumuid
    async with _hiddenalbumlock:
        if _hiddenalbumuid:
            return _hiddenalbumuid

        async with (await pool()).acquire() as conn:
            last_uid_row = await conn.fetchrow(
                "select uid from allusers where is_last_hidden_album=true limit 1"
            )
            if last_uid_row:
                last_uid = last_uid_row[0]
                if (
                    await api.messages.is_messages_from_group_allowed(
                        group_id=settings.vk.group_id, user_id=last_uid
                    )
                ).is_allowed:
                    _hiddenalbumuid = last_uid
                    return _hiddenalbumuid

            await conn.execute(
                "update allusers set is_last_hidden_album=false where is_last_hidden_album=true"
            )

            excluded = [
                i[0]
                for i in await conn.fetch(
                    "select uid from hiddenalbumserverinternalerror"
                )
            ]
            userspool = await conn.fetch(
                "select uid from allusers where not uid=ANY($1) and uid>0", excluded
            )

        for user in userspool:
            uid = user[0]
            if (
                await api.messages.is_messages_from_group_allowed(
                    group_id=settings.vk.group_id, user_id=uid
                )
            ).is_allowed:
                _hiddenalbumuid = uid
                async with (await pool()).acquire() as conn:
                    await conn.execute("update allusers set is_last_hidden_album=false")
                    await conn.execute(
                        "update allusers set is_last_hidden_album=true where uid=$1",
                        uid,
                    )
                return _hiddenalbumuid

            await asyncio.sleep(0.51)


async def get_import_settings(uid, chat_id):
    async with (await pool()).acquire() as conn:
        if s := await conn.fetchrow(
            "select sys, acc, nicks, punishes, binds from importsettings where uid=$1 and "
            "chat_id=$2",
            uid,
            chat_id,
        ):
            return {
                "sys": s[0],
                "acc": s[1],
                "nicks": s[2],
                "punishes": s[3],
                "binds": s[4],
            }
        return settings.import_settings.default


async def turn_import_setting(chat_id, uid, setting):
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "update importsettings set "
            + setting
            + "=not "
            + setting
            + " where chat_id=$1 and uid=$2 returning 1",
            chat_id,
            uid,
        ):
            defaults = settings.import_settings.default.copy()
            defaults[setting] = not defaults[setting]
            await conn.execute(
                "insert into importsettings (uid, chat_id, sys, acc, nicks, punishes, binds) values ($1, $2, $3, $4"
                ", $5, $6, $7)",
                uid,
                chat_id,
                defaults["sys"],
                defaults["acc"],
                defaults["nicks"],
                defaults["punishes"],
                defaults["binds"],
            )


@cached
def scan_url_for_malware(url):
    try:
        url = requests.get(url, allow_redirects=True, timeout=2).url
    except requests.RequestException:
        return []
    sb = pysafebrowsing.SafeBrowsing(key=settings.google.token)
    sb = sb.lookup_url(url)
    return sb["threats"] if "threats" in sb and sb["threats"] else []


@cached
def scan_url_for_redirect(url):
    try:
        response = requests.get(url, allow_redirects=False, timeout=2)
        return (
            response.headers.get("Location")
            if 300 <= response.status_code < 400
            else None
        )
    except requests.RequestException:
        return None


@cached
def scan_url_is_shortened(url):
    try:
        response = requests.get(url, allow_redirects=True, timeout=2)
        return (
            response.url
            if (
                urlparse(response.url).netloc.replace("www.", "")
                != urlparse(url).netloc.replace("www.", "")
            )
            else False
        )
    except requests.RequestException:
        return False


def generate_easy_problem():
    a, op, b = random.randint(10, 99), random.choice(["+", "-"]), random.randint(10, 99)
    return f"{a} {op} {b} = ?", (a + b) if op == "+" else (a - b)


def generate_medium_problem():
    x = random.randint(1, 33)
    a = random.randint(10, 499)
    b = random.randint(10, 499)
    op = random.choice(["+", "-"])
    if op == "+":
        c = a * x + b
    else:
        c = a * x - b
    return f"({a}X {op} {b} = {c}) → X = ?", x


def generate_hard_problem():
    x = random.randint(12, 199)
    if random.randint(0, 1):
        a, b = random.randint(100, 1000), random.randint(100, 1000)
        return f"({a}X * {b} = {a * x * b}) → X = ?", x
    else:
        a = random.randint(100, 1000)
        b = random.randint(10, 1000)
        while a % b != 0 or a == b:
            b = random.randint(10, 1000)
        return f"({a}X / {b} = {int(a * x / b)}) → X = ?", x


async def messagereply(
    protectedmessage: Message, *args, **kwargs
) -> MessagesSendUserIdsResponseItem | None:
    try:
        msg = await protectedmessage.reply(*args, **kwargs)
        if msg.peer_id > 2000000000:
            chatid = msg.peer_id - 2000000000
            val, pos = await managers.chat_settings.get(
                chatid, "autodelete", ("value", "pos")
            )
            if pos and val:
                async with (await pool()).acquire() as conn:
                    await conn.execute(
                        "insert into todelete (peerid, cmid, delete_at) values ($1, $2, $3)",
                        msg.peer_id,
                        msg.conversation_message_id,
                        time.time() + val,
                    )
        return msg
    except VKAPIError[100]:
        pass
    except Exception as exc:
        raise Exception("Failed to reply to message") from exc


async def create_payment(
    cost,
    first_name,
    last_name,
    origcost,
    from_id,
    to_id,
    promo=None,
    chat_id=None,
    coins=None,
    email=None,
    delete_message_cmid=None,
) -> PaymentResponse:
    async with (await pool()).acquire() as conn:
        order_id = await conn.fetchval(
            "select id from payments order by id desc limit 1"
        )
        order_id = 1 if order_id is None else (order_id + 1)
        await conn.execute(
            "insert into payments (id, uid, success) values ($1, $2, $3)",
            order_id,
            to_id,
            0,
        )
    payment = {
        "amount": {"value": str(cost) + ".00", "currency": "RUB"},
        "receipt": {
            "customer": {
                "full_name": f"{last_name} {first_name}",
                "email": config.sitedata["email"],
            },
            "items": [
                {
                    "amount": {"value": str(cost) + ".00", "currency": "RUB"},
                    "vat_code": 1,
                    "quantity": 1,
                }
            ],
        },
        "metadata": {
            "pid": order_id,
            "origcost": origcost,
        },
        "merchant_customer_id": from_id,
        "confirmation": {
            "type": "redirect",
            "locale": "ru_RU",
            "return_url": "https://vk.com/star_manager",
        },
    }
    if coins:
        payment["receipt"]["items"][0]["description"] = point_words(
            coins, ("монетка", "монетки", "монеток")
        )
        payment["metadata"]["coins"] = coins
    elif chat_id:
        payment["receipt"]["items"][0]["description"] = "Premium-беседа"
        payment["metadata"]["chat_id"] = chat_id
    else:
        payment["receipt"]["items"][0]["description"] = "Premium-статус"

    if promo and promo[1]:
        payment["metadata"]["personal"] = promo[2]

    if to_id != from_id:
        payment["metadata"]["gift"] = to_id

    if email:
        payment["receipt"]["customer"]["email"] = email
        payment["receipt"]["email"] = email

    if delete_message_cmid:
        payment["metadata"]["del_cmid"] = delete_message_cmid

    Configuration.account_id = settings.yookassa.merchant_id
    Configuration.secret_key = settings.yookassa.token
    return Payment.create(payment)


async def get_user_shop_bonuses(uid):
    async with (await pool()).acquire() as conn:
        return (
            await conn.fetchrow(
                "select exp_2x, no_comission from shop where uid=$1", uid
            )
        ) or [0, 0]


async def get_raid_mode_active(chat_id):
    async with (await pool()).acquire() as conn:
        return bool(
            await conn.fetchval("select status from raidmode where chat_id=$1", chat_id)
        )


async def archive_report(
    message_ids,
    user: aiogram.types.user.User,
    original_text: str,
    action,
    bot: aiogram.Bot,
    report_id,
    uid,
    answer=None,
):
    new_text = original_text.split("\n")
    if action == "delete":
        action = "Удалено"
        message = (
            f"📘 Ваше обращение #{report_id} было удалено модераторами сообщества."
        )
    elif action == "ban":
        action = "Блокировка"
        message = "📘 Вы получили блокировку на отправку обращений сроком на 24 часа."
    elif action == "answer":
        action = "Закрыто"
        try:
            user_name = await api.users.get(user_ids=uid)
            user_name = f"{user_name[0].first_name} {user_name[0].last_name}"
            message = f"""📗 Обращение #{report_id}
👤 Пользователь - {user_name}\n
💬 Содержимое: {re.sub(r"<[^>]+>", "", original_text.split("Содержимое:</b> ")[-1])}
❇️ Ответ: {answer}"""
        except Exception:
            message = None

    try:
        if message:
            await api.messages.send(user_id=uid, random_id=0, message=message)
    except Exception:
        pass
    new_text.insert(
        2,
        f'🛂 Ответил: <a href="tg://user?id={user.id}">{f"@{user.username}" if user.username else (user.full_name or user.id)}</a>',
    )
    new_text.insert(4, f"➡️ Статус: {action}")
    if action == "Закрыто":
        new_text.append(f"❇️ Ответ: {answer}")
    new_text = "\n".join(new_text)
    for message_id in message_ids:
        try:
            if message_id == message_ids[-1]:
                await bot.edit_message_text(
                    chat_id=settings.telegram.reports_chat_id,
                    message_id=message_id,
                    text=new_text,
                    parse_mode="HTML",
                )
                await bot.copy_message(
                    chat_id=settings.telegram.reports_chat_id,
                    from_chat_id=settings.telegram.reports_chat_id,
                    message_id=message_id,
                    message_thread_id=settings.telegram.reports_archive_thread_id,
                )
            else:
                await bot.copy_message(
                    chat_id=settings.telegram.reports_chat_id,
                    from_chat_id=settings.telegram.reports_chat_id,
                    message_id=message_id,
                    message_thread_id=settings.telegram.reports_archive_thread_id,
                )

        except aiogram.exceptions.TelegramBadRequest:
            logger.exception(f"Failed to edit/copy message {message_id}")

        try:
            await bot.delete_message(
                chat_id=settings.telegram.reports_chat_id, message_id=message_id
            )
        except aiogram.exceptions.TelegramBadRequest:
            logger.exception(f"Failed to delete message {message_id}")


def number_to_emoji(n: int) -> str:
    if n == 10:
        return "🔟"
    mapping = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
    return "".join(mapping[int(d)] for d in str(n))
