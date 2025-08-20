import json
import random
import string
import time
from datetime import datetime
from io import BytesIO

from aiogram.types import InputMediaPhoto
from loguru import logger
from vkbottle.framework.labeler import BotLabeler
from vkbottle_types import GroupTypes
from vkbottle_types.events import GroupEventType

import BotTG
import BotTG.bot
import BotTG.keyboard
import keyboard
import messages
from Bot.rules import SearchPMCMD
from Bot.utils import (
    getChatName,
    getChatSettings,
    getURepBanned,
    getUserName,
    getUserNickname,
    getUserPremium,
    isChatMember,
    sendMessage,
    uploadImage,
    whoiscached,
)
from config.config import (
    DEVS,
    GROUP_ID,
    PATH,
    REPORT_CD,
    TG_REPORTS_CHAT_ID,
    TG_REPORTS_NEW_THREAD_ID,
    api,
)
from db import pool

bl = BotLabeler()


@bl.raw_event(
    GroupEventType.MESSAGE_NEW,
    GroupTypes.MessageNew,
    SearchPMCMD("anon"),
    blocking=False,
)
async def anon(message: GroupTypes.MessageNew):
    message = message.object.message
    uid = message.from_id
    if not await getUserPremium(uid):
        return
    data = message.text.split()
    if len(data) < 3 or not data[1].isdigit():
        await sendMessage(message.peer_id, messages.anon_help())
        return
    chatid = int(data[1])
    if not (await getChatSettings(chatid))["entertaining"]["allowAnon"]:
        await sendMessage(message.peer_id, messages.anon_not_allowed())
        return
    try:
        await api.messages.get_conversations_by_id(
            peer_ids=chatid + 2000000000, group_id=GROUP_ID
        )
    except Exception:
        await sendMessage(message.peer_id, messages.anon_chat_does_not_exist())
        return
    for i in data:
        for y in i.split("/"):
            if not whoiscached(y):
                continue
            await sendMessage(message.peer_id, messages.anon_link())
            return
    if len(message.attachments) > 0:
        await sendMessage(message.peer_id, messages.anon_attachments())
        return
    if not await isChatMember(uid, chatid):
        await sendMessage(message.peer_id, messages.anon_not_member())
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
            await sendMessage(message.peer_id, messages.anon_limit())
            return
        mid = await conn.fetchval(
            "insert into anonmessages (fromid, chat_id, time) values ($1, $2, $3) "
            "returning id",
            uid,
            chatid,
            time.time(),
        )
    await sendMessage(
        chatid + 2000000000, messages.anon_message(mid, " ".join(data[2:]))
    )
    await sendMessage(
        message.peer_id, messages.anon_sent(mid, await getChatName(chatid))
    )


@bl.raw_event(
    GroupEventType.MESSAGE_NEW,
    GroupTypes.MessageNew,
    SearchPMCMD("deanon"),
    blocking=False,
)
async def deanon(message: GroupTypes.MessageNew):
    message = message.object.message
    uid = message.from_id
    if not await getUserPremium(uid):
        return
    data = message.text.split()
    if len(data) < 2:
        await sendMessage(message.peer_id, messages.deanon_help())
        return
    id = data[1].replace("#", "").replace("A", "").replace("А", "")
    if not id.isdigit():
        await sendMessage(message.peer_id, messages.deanon_help())
        return
    async with (await pool()).acquire() as conn:
        deanon_target = await conn.fetchrow(
            "select chat_id, fromid, time from anonmessages where id=$1", int(id)
        )
    if deanon_target is None:
        await sendMessage(message.peer_id, messages.deanon_target_not_found())
        return
    chatid, fromid = deanon_target[0], deanon_target[1]
    if not await isChatMember(uid, chatid):
        await sendMessage(message.peer_id, messages.anon_not_member())
        return
    await sendMessage(
        message.peer_id,
        messages.deanon(
            id,
            fromid,
            await getUserName(fromid),
            await getUserNickname(fromid, chatid),
            deanon_target[2],
        ),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_NEW,
    GroupTypes.MessageNew,
    SearchPMCMD("code"),
    blocking=False,
)
async def code(message: GroupTypes.MessageNew):
    message = message.object.message
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
    await sendMessage(message.peer_id, messages.code(code))


@bl.raw_event(
    GroupEventType.MESSAGE_NEW,
    GroupTypes.MessageNew,
    SearchPMCMD("report"),
    blocking=False,
)
async def report(message: GroupTypes.MessageNew):
    message = message.object.message
    uid = message.from_id
    if await getURepBanned(uid) and uid not in DEVS:
        await sendMessage(message.peer_id, messages.repbanned())
        return
    data = message.text.split()

    photo_chunks = []
    current_chunk = []
    for attachment in message.attachments:
        current_chunk.append(attachment.photo.orig_photo.url)
        if len(current_chunk) == 10:
            photo_chunks.append(current_chunk)
            current_chunk = []

    if current_chunk:
        photo_chunks.append(current_chunk)

    if len(data) <= 1 and not photo_chunks:
        await sendMessage(message.peer_id, messages.report_empty())
        return

    async with (await pool()).acquire() as conn:
        repu = await conn.fetchval(
            "select time from reports where uid=$1 order by time desc limit 1", uid
        )
    if repu is not None and time.time() - repu < REPORT_CD and uid not in DEVS:
        await sendMessage(message.peer_id, messages.report_cd())
        return

    async with (await pool()).acquire() as conn:
        repid = await conn.fetchval("select id from reports order by id desc limit 1")
        repid = (repid + 1) if repid else 1

    try:
        message_ids = []
        for chunk in photo_chunks:
            if len(chunk) == 1:
                msg = await BotTG.bot.bot.send_photo(
                    chat_id=TG_REPORTS_CHAT_ID,
                    photo=chunk[0],
                    message_thread_id=TG_REPORTS_NEW_THREAD_ID,
                )
                message_ids.append(msg.message_id)
            else:
                msgs = await BotTG.bot.bot.send_media_group(
                    chat_id=TG_REPORTS_CHAT_ID,
                    media=[InputMediaPhoto(media=photo) for photo in chunk],
                    message_thread_id=TG_REPORTS_NEW_THREAD_ID,
                )
                message_ids.extend([m.message_id for m in msgs])
        msg = await BotTG.bot.bot.send_message(
            chat_id=TG_REPORTS_CHAT_ID,
            message_thread_id=TG_REPORTS_NEW_THREAD_ID,
            text=(
                report_text := messages.report(
                    uid,
                    await getUserName(uid),
                    " ".join(data[1:]),
                    repid,
                )
            ),
            reply_markup=BotTG.keyboard.report(repid),
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
        await sendMessage(message.peer_id, messages.report_error(repid))
    else:
        await sendMessage(message.peer_id, messages.report_sent(repid))


@bl.raw_event(
    GroupEventType.MESSAGE_NEW,
    GroupTypes.MessageNew,
    SearchPMCMD("premium"),
    blocking=False,
)
async def premium(message: GroupTypes.MessageNew):
    await sendMessage(
        peer_ids=message.object.message.peer_id,
        msg=messages.pm_market(),
        kbd=keyboard.pm_market(message.object.message.from_id),
    )


@bl.raw_event(
    GroupEventType.MESSAGE_NEW,
    GroupTypes.MessageNew,
    SearchPMCMD("shop"),
    blocking=False,
)
async def shop(message: GroupTypes.MessageNew):
    await sendMessage(
        peer_ids=message.object.message.peer_id,
        msg=messages.shop(),
        kbd=keyboard.shop(message.from_id),
    )
