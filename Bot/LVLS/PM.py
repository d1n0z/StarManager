import random
import string
import time
from datetime import datetime

from vkbottle.framework.labeler import BotLabeler
from vkbottle_types import GroupTypes
from vkbottle_types.events import GroupEventType

import keyboard
import messages
from Bot.rules import SearchPMCMD
from Bot.utils import getUserName, getUserNickname, getUserPremium, getChatName, sendMessage, isChatMember, \
    getChatSettings, whoiscached, getURepBanned, uploadImage
from config.config import api, GROUP_ID, REPORT_CD, REPORT_TO, DEVS, PATH
from db import pool

bl = BotLabeler()


@bl.raw_event(GroupEventType.MESSAGE_NEW, GroupTypes.MessageNew, SearchPMCMD('anon'), blocking=False)
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
    if not (await getChatSettings(chatid))['entertaining']['allowAnon']:
        await sendMessage(message.peer_id, messages.anon_not_allowed())
        return
    try:
        await api.messages.get_conversations_by_id(peer_ids=chatid + 2000000000, group_id=GROUP_ID)
    except:
        await sendMessage(message.peer_id, messages.anon_chat_does_not_exist())
        return
    for i in data:
        for y in i.split('/'):
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
        if (cnt := await conn.fetchval('select count(*) as c from anonmessages where fromid=$1 and time>$2',
                                       uid, date.timestamp())) and cnt >= 25:
            await sendMessage(message.peer_id, messages.anon_limit())
            return
        mid = await conn.fetchval('insert into anonmessages (fromid, chat_id, time) values ($1, $2, $3) '
                                  'returning id', uid, chatid, time.time())
    await sendMessage(chatid + 2000000000, messages.anon_message(mid, ' '.join(data[2:])))
    await sendMessage(message.peer_id, messages.anon_sent(mid, await getChatName(chatid)))


@bl.raw_event(GroupEventType.MESSAGE_NEW, GroupTypes.MessageNew, SearchPMCMD('deanon'), blocking=False)
async def deanon(message: GroupTypes.MessageNew):
    message = message.object.message
    uid = message.from_id
    if not await getUserPremium(uid):
        return
    data = message.text.split()
    if len(data) < 2:
        await sendMessage(message.peer_id, messages.deanon_help())
        return
    id = data[1].replace('#', '').replace('A', '').replace('А', '')
    if not id.isdigit():
        await sendMessage(message.peer_id, messages.deanon_help())
        return
    async with (await pool()).acquire() as conn:
        deanon_target = await conn.fetchrow('select chat_id, fromid, time from anonmessages where id=$1', int(id))
    if deanon_target is None:
        await sendMessage(message.peer_id, messages.deanon_target_not_found())
        return
    chatid, fromid = deanon_target[0], deanon_target[1]
    if not await isChatMember(uid, chatid):
        await sendMessage(message.peer_id, messages.anon_not_member())
        return
    await sendMessage(message.peer_id, messages.deanon(id, fromid, await getUserName(fromid),
                                                       await getUserNickname(fromid, chatid), deanon_target[2]))


@bl.raw_event(GroupEventType.MESSAGE_NEW, GroupTypes.MessageNew, SearchPMCMD('code'), blocking=False)
async def code(message: GroupTypes.MessageNew):
    message = message.object.message
    uid = message.from_id
    async with (await pool()).acquire() as conn:
        code = await conn.fetchval('select code from tglink where vkid=$1', uid)
        if not code:
            while not code or await conn.fetchval('select exists(select 1 from tglink where code=$1)', code):
                code = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(6)])
            await conn.execute('insert into tglink (tgid, vkid, code) values (null, $1, $2)', uid, code)
    await sendMessage(message.peer_id, messages.code(code))


@bl.raw_event(GroupEventType.MESSAGE_NEW, GroupTypes.MessageNew, SearchPMCMD('report'), blocking=False)
async def report(message: GroupTypes.MessageNew):
    message = message.object.message
    uid = message.from_id
    if await getURepBanned(uid) and uid not in DEVS:
        await sendMessage(message.peer_id, messages.repbanned())
        return
    chat_id, data, photos = message.peer_id - 2000000000, message.text.split(), []
    for i in message.attachments:
        r = await api.http_client.request_content(i.photo.orig_photo.url)
        with open(PATH + f'media/temp/{i.photo.owner_id}{i.photo.id}.jpg', "wb") as f:
            f.write(r)
        photos.append(await uploadImage(PATH + f'media/temp/{i.photo.owner_id}{i.photo.id}.jpg'))
    if len(data) <= 1 and not photos:
        await sendMessage(message.peer_id, messages.report_empty())
        return

    async with (await pool()).acquire() as conn:
        repu = await conn.fetchval('select time from reports where uid=$1 order by time desc limit 1', uid)
    if repu is not None and time.time() - repu < REPORT_CD and uid not in DEVS:
        await sendMessage(message.peer_id, messages.report_cd())
        return

    async with (await pool()).acquire() as conn:
        repid = await conn.fetchval('select id from reports order by id desc limit 1')
        repid = (repid + 1) if repid else 1
        await conn.execute('insert into reports (uid, id, time) VALUES ($1, $2, $3)', uid, repid, time.time())

    photos = ','.join(photos) or None
    await api.messages.send(disable_mentions=1, chat_id=REPORT_TO, random_id=0, message=messages.report(
        uid, await getUserName(uid), ' '.join(data[1:]), repid, chat_id, await getChatName(chat_id)),
                            keyboard=keyboard.report(uid, repid, chat_id, ' '.join(data[1:]), photos),
                            attachment=photos)
    await sendMessage(message.peer_id, messages.report_sent(repid))
