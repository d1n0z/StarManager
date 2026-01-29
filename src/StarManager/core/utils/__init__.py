import asyncio
import locale
import os
import random
import re
import tempfile
import time
import traceback
import unicodedata
from ast import literal_eval
from copy import deepcopy
from datetime import date
from typing import (
    Any,
    Dict,
    Generator,
    Iterable,
    List,
    Literal,
    Optional,
    Sequence,
    TypeVar,
    Union,
)
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

from . import models

T = TypeVar("T")


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
        try:
            await conn.execute(
                "insert into usernames (uid, name, domain) values ($1, $2, $3)",
                uid,
                f"{name[0].first_name} {name[0].last_name}",
                name[0].domain or f"id{name[0].id}",
            )
        except Exception:
            pass  # i guess it's not so important
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

    from_link_id = re.search(r"vk\.(?:com|ru)/id(\d+)", message)
    from_link = re.search(r"vk\.(?:com|ru)/([a-zA-Z0-9_.]+)", message)
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
async def get_chat_name(chat_id: int, none: Any = "UNKNOWN") -> Any:
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


async def get_chat_owner(chat_id: int) -> int | bool:
    try:
        owners = await managers.access_level.get_all(
            chat_id=chat_id,
            predicate=lambda i: i.access_level >= 7 and i.custom_level_name is None,
        )
        if owners:
            return sorted(owners, key=lambda i: i.access_level)[0].uid

        async with (await pool()).acquire() as conn:
            owner = await conn.fetchval(
                "select uid from gpool where chat_id=$1",
                chat_id,
            )
        if owner:
            return owner

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


last_global_upload_failure = 0


async def upload_image(
    file: str, retry: int = 0, *, targeted_ids: Optional[List[int]] = None
) -> str | None:
    global last_global_upload_failure

    use_global = (
        last_global_upload_failure == 0
        or time.time() - last_global_upload_failure > 3600
    )
    try:
        try:
            if use_global:
                photo = await PhotoMessageUploader(api).upload(file_source=file)
            else:
                photo = await upload_image_with_targets(file, targeted_ids)
        except Exception as oe:
            if retry == 0 and use_global:
                photo = await upload_image_with_targets(file, targeted_ids)
                if photo:
                    return photo
            if use_global:
                last_global_upload_failure = time.time()
            raise oe

        if not photo:
            raise Exception
        return photo
    except Exception as e:
        if "internal server error" in str(e).lower():
            logger.debug(f"Failed to send photo: {traceback.format_exc()}")
            return
        if retry < 6 or "too many" in str(e).lower():
            await asyncio.sleep((2**retry) / 2)
            return await upload_image(file, retry + 1)
        logger.exception("Failed to send photo:")
        return


async def upload_image_with_targets(file, targeted_ids):
    async def _upload():
        return await PhotoMessageUploader(api).upload(file_source=file, peer_id=id)

    for id in targeted_ids or []:
        try:
            try:
                photo = await _upload()
            except Exception as e:
                if "too many" in str(e).lower():
                    await asyncio.sleep(3)
                    photo = await _upload()
                raise e
        except Exception:
            continue
        if photo:
            return photo
    return None


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
async def get_user_access_level(
    uid: int, chat_id: int, none: Any = 0, ignore_custom: bool = False
) -> models.SimpleAccessLevel | Any:
    res = await managers.access_level.get(uid, chat_id)
    if res is None:
        return none
    if (
        res.custom_level_name is not None
        and not await managers.custom_access_level.is_active(res.access_level, chat_id)
    ):
        return none
    acc = models.SimpleAccessLevel(
        access_level=res.access_level,
        is_custom=res.custom_level_name is not None,
    )
    if ignore_custom and acc.is_custom:
        return none
    return acc


async def get_user_last_message(
    uid: int, chat_id: int, none: Any = "Неизвестно"
) -> int | Any:
    return await managers.lastmessagedate.get_user_last_message(uid, chat_id) or none


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
    user = await managers.mute.get(uid, chat_id)
    return user.mute if user is not None else none


async def get_user_warns(uid, chat_id, none=0) -> int:
    user = await managers.warn.get(uid, chat_id)
    return user.warns if user is not None else none


async def get_user_ban(uid, chat_id, none=0) -> int:
    user = await managers.ban.get(uid, chat_id)
    return user.ban if user is not None else none


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
    ban = await managers.ban.get(uid, chat_id)
    if ban:
        return {
            "times": literal_eval(ban.last_bans_times) if ban.last_bans_times else [],
            "causes": literal_eval(ban.last_bans_causes)
            if ban.last_bans_causes
            else [],
            "names": literal_eval(ban.last_bans_names) if ban.last_bans_names else [],
            "dates": literal_eval(ban.last_bans_dates) if ban.last_bans_dates else [],
        }
    return none


async def get_user_xp(uid, none=0) -> Any | int:
    return await managers.xp.get(uid, "xp") or none


async def get_user_coins(uid, none=0) -> Any | int:
    return await managers.xp.get(uid, "coins") or none


async def get_user_league(uid, none=1) -> Any | int:
    return await managers.xp.get(uid, "league") or none


async def get_user_level(uid, none=0) -> Any | int:
    return await managers.xp.get(uid, "lvl") or none


@AsyncLRU(maxsize=0)
async def get_user_needed_xp(xp: int) -> int:
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


async def get_user_premium(uid, none=0) -> int:
    u = await managers.premium.get(uid)
    return u.time if u else none


async def get_user_premmenu_setting(uid, setting, none) -> Any:
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


async def get_user_premmenu_settings(uid) -> Dict[str, bool | None]:
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


async def get_chat_command_level(chat_id, cmd, none) -> Any:
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
    return await managers.messages.get_user_messages(uid, chat_id) or none


async def add_user_xp(uid, addxp, checklvlbanned=True) -> None:
    if checklvlbanned and (
        await managers.blocked.get(uid, "user") or await managers.lvlbanned.exists(uid)
    ):
        return
    await managers.xp.add_user_xp(uid, addxp)


async def add_user_coins(
    uid, addcoins, checklvlbanned=True, addlimit=False, bonus_peer_id=0
) -> None:
    if checklvlbanned and (
        await managers.blocked.get(uid, "user") or await managers.lvlbanned.exists(uid)
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
async def get_chat_setting_value(chat_id, setting) -> Any:
    return await managers.chat_settings.get(chat_id, setting, "value")


@AsyncTTL(time_to_live=5, maxsize=0)
async def get_chat_alt_settings(chat_id) -> Dict[str, Dict[str, int]]:
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


async def set_user_access_level(
    uid, chat_id, access_level, clean: bool = False
) -> None:
    if clean:
        await managers.access_level.delete(uid, chat_id)
    await managers.access_level.edit_access_level(uid, chat_id, access_level)


async def get_silence(chat_id) -> bool:
    mode = await managers.silencemode.get(chat_id)
    return mode.activated if mode is not None else False


@AsyncTTL(time_to_live=120, maxsize=0)
async def is_chat_member(uid, chat_id) -> bool:
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


def _nsfw_detector_sync(pic_path) -> bool:
    detector = NudeDetector()
    with open(pic_path, "rb") as f:
        image_data = f.read()

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(image_data)
        temp_file_path = temp_file.name
    try:
        result = detector.detect(temp_file_path)
    except Exception:
        return False
    os.unlink(temp_file_path)
    for i in result:
        if i["class"] in settings.nsfw_categories.categories:
            if i["score"] > 0.3:
                return True
    return False


async def NSFW_detector(pic_path) -> bool:
    return await asyncio.to_thread(_nsfw_detector_sync, pic_path)


def whoiscached(text) -> bool:
    # return whois.whois(text)  # doesn't work
    try:
        if "." not in text:
            return False
        dns.resolver.resolve(text, "A")
        return True
    except Exception:
        return False


def whoiscachedurl(text) -> None | Literal[True]:
    # return whois.whois(text)  # doesn't work
    for i in text.split("/"):
        try:
            dns.resolver.resolve(i, "A")
            return True
        except Exception:
            continue


async def get_user_prefixes(u_prem, uid) -> list:
    if u_prem:
        return list(await managers.prefixes.get_all(uid)) + settings.commands.prefix
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


async def command_cooldown_check(uid: int, cmd: str) -> None | float:
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
def pluralize_days(seconds) -> str:
    res = int(int(seconds) // 86400)
    if res == 1:
        res = str(res) + " день"
    elif 1 < res < 5:
        res = str(res) + " дня"
    else:
        res = str(res) + " дней"
    return res


@cached
def pluralize_hours(seconds) -> str:
    res = int(int(seconds) // 3600)
    if res in [23, 22, 4, 3, 2]:
        res = f"{res} часа"
    elif res in [21, 1]:
        res = f"{res} час"
    else:
        res = f"{res} часов"
    return res


@cached
def pluralize_minutes(seconds) -> str:
    res = int(int(seconds) // 60)
    if res % 10 == 1 and res % 100 != 11:
        res = str(res) + " минута"
    elif 2 <= res % 10 <= 4 and (res % 100 < 10 or res % 100 >= 20):
        res = str(res) + " минуты"
    else:
        res = str(res) + " минут"
    return res


@cached
def pluralize_words(value, words) -> str:
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


def chunks(li: Sequence[T], n: int) -> Generator[Sequence[T], None, None]:
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
        mt = int(punishment[1]) * 60
        await managers.mute.mute(uid, chat_id, mt, cause)
        await set_chat_mute(uid, chat_id, mt)
        return punishment
    elif punishment[0] == "ban":
        ban_time = int(punishment[1]) * 86400
        await managers.ban.ban(uid, chat_id, ban_time, cause)
        await kick_user(uid, chat_id)
        return punishment
    elif punishment[0] == "warn":
        if await managers.warn.warn(uid, chat_id, cause) >= 3:
            await kick_user(uid, chat_id)
        return punishment
    return False


async def get_gpool(chat_id) -> Optional[List[Any]]:
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
            return None
        return chats
    except Exception:
        return None


async def get_pool(chat_id, group) -> Optional[list[Any]]:
    try:
        owners = await managers.access_level.get_all(
            chat_id=chat_id,
            predicate=lambda i: i.access_level > 6 and i.custom_level_name is None,
        )
        if len(owners) == 0:
            return None
        owner_id = sorted(owners, key=lambda i: i.access_level)[0].uid
        async with (await pool()).acquire() as conn:
            chats = [
                i[0]
                for i in await conn.fetch(
                    'select chat_id from chatgroups where "group"=$1 and uid=$2',
                    group,
                    owner_id,
                )
            ]
        if len(chats) == 0:
            return None
        return chats
    except Exception:
        return None


async def get_silence_allowed(chat_id, custom: bool = False):
    default = [7, 8] if not custom else []
    lvls = await managers.silencemode.get(chat_id)
    if lvls is None:
        return default
    if custom:
        lvls = lvls.allowed_custom
    else:
        lvls = lvls.allowed
    return literal_eval(lvls) + default


async def get_user_rep(uid):
    async with (await pool()).acquire() as conn:
        return await conn.fetchval("select rep from reputation where uid=$1", uid) or 0


async def get_rep_top(uid):
    async with (await pool()).acquire() as conn:
        top = [
            i[0]
            for i in await conn.fetch("select uid from reputation order by rep desc")
        ]
    return (top.index(uid) + 1) if uid in top else await managers.allusers.count_all()


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
    if random.choice([True, False]):
        a = random.randint(100, 1000)
        b = random.randint(100, 1000)
        return f"({a}X * {b} = {a * x * b}) → X = ?", x
    else:
        for _ in range(100):
            b = random.randint(10, 1000)
            max_k = 1000 // b
            min_k = max(2, (100 + b - 1) // b)
            if max_k >= min_k:
                k = random.randint(min_k, max_k)
                a = b * k
                if a != b:
                    return f"({a}X / {b} = {a * x // b}) → X = ?", x

        a = random.randint(100, 1000)
        divs = [d for d in range(10, min(a, 1000) + 1) if a % d == 0 and d != a]
        if divs:
            b = random.choice(divs)
            return f"({a}X / {b} = {a * x // b}) → X = ?", x

        raise RuntimeError("Не удалось сгенерировать корректную задачу деления.")


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
        payment["receipt"]["items"][0]["description"] = pluralize_words(
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


_emoji_pattern = re.compile(
    r"^("
    # 1) flags
    r"(?:[\U0001F1E6-\U0001F1FF]{2})"
    r"|"
    # 2) Keycap (number/#, * + optional VS16 + enclosing keycap)
    r"(?:[0-9#\*]\uFE0F?\u20E3)"
    r"|"
    # 3) Base unit + optional variation selector + optional skin tone, with possible ZWJ-linking
    r"(?:"
    r"["
    r"\U0001F300-\U0001F5FF"  # Misc symbols and pictographs
    r"\U0001F600-\U0001F64F"  # Emoticons
    r"\U0001F680-\U0001F6FF"  # Transport & map
    r"\U0001F700-\U0001F77F"  # Alchemical symbols (some glyphs)
    r"\U0001F780-\U0001F7FF"  # Geometric shapes extended
    r"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C / symbols
    r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    r"\U0001FA00-\U0001FA6F"  # Chess/etc and extended
    r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    r"\u2600-\u26FF"  # Misc symbols (e.g. ☀)
    r"\u2700-\u27BF"  # Dingbats (e.g. ✂)
    r"]"
    r"(?:\uFE0F)?"  # optional Variation Selector-16 (emoji presentation)
    r"(?:[\U0001F3FB-\U0001F3FF])?"  # optional skin tone modifiers
    # optional sequence: (ZWJ + (same pattern for another person/glyph))
    r"(?:\u200D(?:"
    r"["
    r"\U0001F300-\U0001F5FF"
    r"\U0001F600-\U0001F64F"
    r"\U0001F680-\U0001F6FF"
    r"\U0001F700-\U0001F77F"
    r"\U0001F780-\U0001F7FF"
    r"\U0001F800-\U0001F8FF"
    r"\U0001F900-\U0001F9FF"
    r"\U0001FA00-\U0001FA6F"
    r"\U0001FA70-\U0001FAFF"
    r"\u2600-\u26FF"
    r"\u2700-\u27BF"
    r"]"
    r"(?:\uFE0F)?"
    r"(?:[\U0001F3FB-\U0001F3FF])?"
    r"))*"
    r")"
    r")$",
    flags=re.UNICODE,
)


def is_single_emoji(s: str) -> bool:
    if not s:
        return False
    s = unicodedata.normalize("NFC", s)
    return bool(_emoji_pattern.match(s))


async def is_higher(higher_id, lower_id, chat_id):
    h_acc = await managers.access_level.get(higher_id, chat_id)
    l_acc = await managers.access_level.get(lower_id, chat_id)

    if h_acc is None:
        return False
    if l_acc is None:
        return True
    if h_acc.custom_level_name is not None:
        if l_acc.custom_level_name is not None:
            return h_acc.access_level > l_acc.access_level
        return False
    if l_acc.custom_level_name is not None:
        return True
    return h_acc.access_level > l_acc.access_level


async def set_premium_status(
    to_id: int, days: int, *, operation: Literal["add", "set"] = "set"
):
    if operation == "add":
        return await managers.premium.add_premium(to_id, days * 86400)
    return await managers.premium.set_premium(to_id, days * 86400)
