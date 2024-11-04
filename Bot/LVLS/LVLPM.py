import time
from datetime import datetime

import validators
from vkbottle.framework.labeler import BotLabeler
from vkbottle_types import GroupTypes
from vkbottle_types.events import GroupEventType

import messages
from Bot.rules import SearchPMCMD
from Bot.utils import getUserName, getUserNickname, getUserPremium, getChatName, sendMessage, isChatMember, \
    getChatSettings
from config.config import API, GROUP_ID
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
        msg = messages.anon_help()
        await sendMessage(message.peer_id, msg)
        return
    chatid = int(data[1])
    if not (await getChatSettings(chatid))['entertaining']['allowAnon']:
        msg = messages.anon_not_allowed()
        await sendMessage(message.peer_id, msg)
        return
    try:
        await API.messages.get_conversations_by_id(peer_ids=chatid + 2000000000, group_id=GROUP_ID)
    except:
        msg = messages.anon_chat_does_not_exist()
        await sendMessage(message.peer_id, msg)
        return
    for i in data:
        for y in i.split('/'):
            if validators.url(y) or validators.domain(y):
                msg = messages.anon_link()
                await sendMessage(message.peer_id, msg)
                return
    if len(message.attachments) > 0:
        msg = messages.anon_attachments()
        await sendMessage(message.peer_id, msg)
        return
    if not await isChatMember(uid, chatid):
        msg = messages.anon_not_member()
        await sendMessage(message.peer_id, msg)
        return

    date = datetime.now().replace(hour=0, minute=0, second=0)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if (cnt := await (await c.execute('select count(*) as c from anonmessages where fromid=%s and time>%s',
                                              (uid, date.timestamp()))).fetchone()) and cnt[0] >= 25:
                msg = messages.anon_limit()
                await sendMessage(message.peer_id, msg)
                return
            mid = (await (await c.execute('insert into anonmessages (fromid, chat_id, time) values (%s, %s, %s) '
                                          'returning id', (uid, chatid, time.time()))).fetchone())[0]
    text = ' '.join(data[2:])
    msg = messages.anon_message(mid, text)
    await sendMessage(chatid + 2000000000, msg)
    msg = messages.anon_sent(mid, await getChatName(chatid))
    await sendMessage(message.peer_id, msg)
    return


@bl.raw_event(GroupEventType.MESSAGE_NEW, GroupTypes.MessageNew, SearchPMCMD('deanon'), blocking=False)
async def deanon(message: GroupTypes.MessageNew):
    message = message.object.message
    uid = message.from_id
    if not await getUserPremium(uid):
        return
    data = message.text.split()
    if len(data) < 2:
        msg = messages.deanon_help()
        await sendMessage(message.peer_id, msg)
        return
    id = data[1].replace('#', '').replace('A', '').replace('А', '')
    if not id.isdigit():
        msg = messages.deanon_help()
        await sendMessage(message.peer_id, msg)
        return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            deanon_target = await (await c.execute(
                'select chat_id, fromid, time from anonmessages where id=%s', (id,))).fetchone()
    if deanon_target is None:
        msg = messages.deanon_target_not_found()
        await sendMessage(message.peer_id, msg)
        return
    chatid = deanon_target[0]
    fromid = deanon_target[1]
    dttime = deanon_target[2]
    if not await isChatMember(uid, chatid):
        msg = messages.anon_not_member()
        await sendMessage(message.peer_id, msg)
        return
    msg = messages.deanon(id, fromid, await getUserName(fromid),
                          await getUserNickname(fromid, chatid), dttime)
    await sendMessage(message.peer_id, msg)
    return
