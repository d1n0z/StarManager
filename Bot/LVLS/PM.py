import time
from datetime import datetime

from vkbottle.framework.labeler import BotLabeler
from vkbottle_types import GroupTypes
from vkbottle_types.events import GroupEventType

import messages
from Bot.rules import SearchPMCMD
from Bot.utils import getUserName, getUserNickname, getUserPremium, getChatName, sendMessage, isChatMember, \
    getChatSettings, whoiscached
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
        return await sendMessage(message.peer_id, messages.anon_help())
    chatid = int(data[1])
    if not (await getChatSettings(chatid))['entertaining']['allowAnon']:
        return await sendMessage(message.peer_id, messages.anon_not_allowed())
    try:
        await API.messages.get_conversations_by_id(peer_ids=chatid + 2000000000, group_id=GROUP_ID)
    except:
        return await sendMessage(message.peer_id, messages.anon_chat_does_not_exist())
    for i in data:
        for y in i.split('/'):
            try:
                if whoiscached(y)['domain_name'] is None:
                    continue
            except:
                continue
            return await sendMessage(message.peer_id, messages.anon_link())
    if len(message.attachments) > 0:
        return await sendMessage(message.peer_id, messages.anon_attachments())
    if not await isChatMember(uid, chatid):
        return await sendMessage(message.peer_id, messages.anon_not_member())
    date = datetime.now().replace(hour=0, minute=0, second=0)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if (cnt := await (await c.execute('select count(*) as c from anonmessages where fromid=%s and time>%s',
                                              (uid, date.timestamp()))).fetchone()) and cnt[0] >= 25:
                return await sendMessage(message.peer_id, messages.anon_limit())
            mid = (await (await c.execute('insert into anonmessages (fromid, chat_id, time) values (%s, %s, %s) '
                                          'returning id', (uid, chatid, time.time()))).fetchone())[0]
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
        return await sendMessage(message.peer_id, messages.deanon_help())
    id = data[1].replace('#', '').replace('A', '').replace('А', '')
    if not id.isdigit():
        return await sendMessage(message.peer_id, messages.deanon_help())
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            deanon_target = await (await c.execute(
                'select chat_id, fromid, time from anonmessages where id=%s', (id,))).fetchone()
    if deanon_target is None:
        return await sendMessage(message.peer_id, messages.deanon_target_not_found())
    chatid, fromid = deanon_target[0], deanon_target[1]
    if not await isChatMember(uid, chatid):
        return await sendMessage(message.peer_id, messages.anon_not_member())
    await sendMessage(message.peer_id, messages.deanon(id, fromid, await getUserName(fromid),
                                                       await getUserNickname(fromid, chatid), deanon_target[2]))
