import json
import random
import string
import time
from datetime import datetime

from aiogram.types import InputMediaPhoto
from loguru import logger
from vkbottle.framework.labeler import BotLabeler
from vkbottle_types import GroupTypes
from vkbottle_types.events import GroupEventType

from StarManager.tgbot import bot as tgbot
from StarManager.tgbot import keyboard as tgkeyboard
from StarManager.vkbot import keyboard, messages
from StarManager.vkbot.rules import SearchPMCMD
from StarManager.core.utils import (
    get_chat_name,
    get_chat_settings,
    get_user_rep_banned,
    get_user_name,
    get_user_nickname,
    get_user_premium,
    is_chat_member,
    send_message,
    whoiscached,
)
from StarManager.core.config import settings, api
from StarManager.core.db import pool

bl = BotLabeler()


@bl.raw_event(
    GroupEventType.MESSAGE_NEW,
    GroupTypes.MessageNew,
    SearchPMCMD("anon"),
    blocking=False,
)
async def anon(event: GroupTypes.MessageNew):
    message = event.object.message
    if not message:
        return
    uid = message.from_id
    if not await get_user_premium(uid):
        return
    data = message.text.split()
    if len(data) < 3 or not data[1].isdigit():
        await send_message(message.peer_id, await messages.anon_help())
        return
    chatid = int(data[1])
    if not (await get_chat_settings(chatid))["entertaining"]["allowAnon"]:
        await send_message(message.peer_id, await messages.anon_not_allowed())
        return
    try:
        await api.messages.get_conversations_by_id(
            peer_ids=[chatid + 2000000000], group_id=settings.vk.group_id
        )
    except Exception:
        await send_message(message.peer_id, await messages.anon_chat_does_not_exist())
        return
    for i in data:
        for y in i.split("/"):
            if not whoiscached(y):
                continue
            await send_message(message.peer_id, await messages.anon_link())
            return
    if message.attachments and len(message.attachments) > 0:
        await send_message(message.peer_id, await messages.anon_attachments())
        return
    if not await is_chat_member(uid, chatid):
        await send_message(message.peer_id, await messages.anon_not_member())
        return
    date = datetime.now().replace(hour=0, minute=0, second=0)
    async with (await pool()).acquire() as conn:
        if (
            cnt := await conn.fetchval(
                "select count(*) as c from anonmessages where fromid=$1 and time>$2",
                uid,
                date.timestamp(),
            )
        ) and cnt >= 25:
            await send_message(message.peer_id, await messages.anon_limit())
            return
        mid = await conn.fetchval(
            "insert into anonmessages (fromid, chat_id, time) values ($1, $2, $3) "
            "returning id",
            uid,
            chatid,
            time.time(),
        )
    await send_message(
        chatid + 2000000000, await messages.anon_message(mid, " ".join(data[2:]))
    )
    await send_message(
        message.peer_id, await messages.anon_sent(mid, await get_chat_name(chatid))
    )


@bl.raw_event(
    GroupEventType.MESSAGE_NEW,
    GroupTypes.MessageNew,
    SearchPMCMD("deanon"),
    blocking=False,
)
async def deanon(event: GroupTypes.MessageNew):
    message = event.object.message
    if not message:
        return
    uid = message.from_id
    if not await get_user_premium(uid):
        return
    data = message.text.split()
    if len(data) < 2:
        await send_message(message.peer_id, await messages.deanon_help())
        return
    id = data[1].replace("#", "").replace("A", "").replace("А", "")
    if not id.isdigit():
        await send_message(message.peer_id, await messages.deanon_help())
        return
    async with (await pool()).acquire() as conn:
        deanon_target = await conn.fetchrow(
            "select chat_id, fromid, time from anonmessages where id=$1", int(id)
        )
    if deanon_target is None:
        await send_message(message.peer_id, await messages.deanon_target_not_found())
        return
    chatid, fromid = deanon_target[0], deanon_target[1]
    if not await is_chat_member(uid, chatid):
        await send_message(message.peer_id, await messages.anon_not_member())
        return
    await send_message(
        message.peer_id,
        await messages.deanon(
            id,
            fromid,
            await get_user_name(fromid),
            await get_user_nickname(fromid, chatid),
            deanon_target[2],
        ),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_NEW,
    GroupTypes.MessageNew,
    SearchPMCMD("code"),
    blocking=False,
)
async def code(event: GroupTypes.MessageNew):
    message = event.object.message
    if not message:
        return
    uid = message.from_id
    async with (await pool()).acquire() as conn:
        code = await conn.fetchval("select code from tglink where vkid=$1", uid)
        if not code:
            while not code or await conn.fetchval(
                "select exists(select 1 from tglink where code=$1)", code
            ):
                code = "".join(
                    [
                        random.choice(string.ascii_letters + string.digits)
                        for _ in range(6)
                    ]
                )
            await conn.execute(
                "insert into tglink (tgid, vkid, code) values (null, $1, $2)", uid, code
            )
    await send_message(message.peer_id, await messages.code(code))


@bl.raw_event(
    GroupEventType.MESSAGE_NEW,
    GroupTypes.MessageNew,
    SearchPMCMD("report"),
    blocking=False,
)
async def report(event: GroupTypes.MessageNew):
    message = event.object.message
    if not message:
        return
    uid = message.from_id
    if await get_user_rep_banned(uid) and uid not in settings.service.devs:
        await send_message(message.peer_id, await messages.repbanned())
        return
    data = message.text.split()

    photo_chunks = []
    current_chunk = []
    for attachment in message.attachments or []:
        if attachment.photo and attachment.photo.orig_photo:
            current_chunk.append(attachment.photo.orig_photo.url)
            if len(current_chunk) == 10:
                photo_chunks.append(current_chunk)
                current_chunk = []

    if current_chunk:
        photo_chunks.append(current_chunk)

    if len(data) <= 1 and not photo_chunks:
        await send_message(message.peer_id, await messages.report_empty())
        return

    async with (await pool()).acquire() as conn:
        repu = await conn.fetchval(
            "select time from reports where uid=$1 order by time desc limit 1", uid
        )
    if (
        repu is not None
        and time.time() - repu < settings.commands.cooldown["report"]
        and uid not in settings.service.devs
    ):
        await send_message(message.peer_id, await messages.report_cd())
        return

    async with (await pool()).acquire() as conn:
        repid = await conn.fetchval("select id from reports order by id desc limit 1")
        repid = (repid + 1) if repid else 1

    try:
        message_ids = []
        for chunk in photo_chunks:
            if len(chunk) == 1:
                msg = await tgbot.bot.send_photo(
                    chat_id=settings.telegram.reports_chat_id,
                    photo=chunk[0],
                    message_thread_id=settings.telegram.reports_new_thread_id,
                )
                message_ids.append(msg.message_id)
            else:
                msgs = await tgbot.bot.send_media_group(
                    chat_id=settings.telegram.reports_chat_id,
                    media=[InputMediaPhoto(media=photo) for photo in chunk],
                    message_thread_id=settings.telegram.reports_new_thread_id,
                )
                message_ids.extend([m.message_id for m in msgs])
        msg = await tgbot.bot.send_message(
            chat_id=settings.telegram.reports_chat_id,
            message_thread_id=settings.telegram.reports_new_thread_id,
            text=(
                report_text := await messages.report(
                    uid,
                    await get_user_name(uid),
                    " ".join(data[1:]),
                    repid,
                )
            ),
            reply_markup=tgkeyboard.report(repid),
            disable_web_page_preview=True,
            parse_mode="HTML",
        )
        message_ids.append(msg.message_id)
        try:
            async with (await pool()).acquire() as conn:
                await conn.execute(
                    "insert into reports (uid, id, time, report_message_ids, report_text) VALUES ($1, $2, $3, $4, $5)",
                    uid,
                    repid,
                    time.time(),
                    json.dumps(message_ids),
                    report_text,
                )
        except Exception as e:
            try:
                await msg.delete()
            except Exception:
                pass
            raise e
    except Exception:
        logger.exception("Unable to send report:")
        await send_message(message.peer_id, await messages.report_error(repid))
    else:
        await send_message(message.peer_id, await messages.report_sent(repid))


@bl.raw_event(
    GroupEventType.MESSAGE_NEW,
    GroupTypes.MessageNew,
    SearchPMCMD("premium"),
    blocking=False,
)
async def premium(event: GroupTypes.MessageNew):
    message = event.object.message
    if not message:
        return
    await send_message(
        peer_ids=message.peer_id,
        msg=await messages.pm_market(),
        kbd=keyboard.pm_market(message.from_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_NEW,
    GroupTypes.MessageNew,
    SearchPMCMD("shop"),
    blocking=False,
)
async def shop(event: GroupTypes.MessageNew):
    message = event.object.message
    if not message:
        return
    await send_message(
        peer_ids=message.peer_id,
        msg=await messages.shop(),
        kbd=keyboard.shop(message.from_id),
    )
