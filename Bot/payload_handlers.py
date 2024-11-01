import json
import os
import time
import traceback
from ast import literal_eval
from datetime import datetime

from vkbottle.bot import MessageEvent
from vkbottle.framework.labeler import BotLabeler
from vkbottle_types.events import GroupEventType

import keyboard
import messages
from Bot.checkers import haveAccess
from Bot.rules import SearchPayloadCMD
from Bot.tgbot import tgbot
from Bot.utils import sendMessageEventAnswer, editMessage, getUserAccessLevel, getUserXP, getUserPremium, addUserXP, \
    getUserName, getUserNickname, kickUser, getXPTop, getChatName, addWeeklyTask, \
    addDailyTask, getUserBan, getUserWarns, getUserMute, getULvlBanned, getChatSettings, turnChatSetting, \
    deleteMessages, setChatMute, getChatAltSettings, getChatMembers, getChatOwner
from config.config import API, COMMANDS, DEVS, TASKS_LOTS, TASKS_DAILY, PREMIUM_TASKS_DAILY, SETTINGS_COUNTABLE, \
    TG_CHAT_ID, TG_NEWCHAT_THREAD_ID, SETTINGS_PREMIUM
from db import pool

bl = BotLabeler()


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['join', 'rejoin'], checksender=False))
async def join(message: MessageEvent):
    payload = message.payload
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'join' or (cmd == 'rejoin' and payload['activate'] == 0):
        bp_chat_id = payload['chat_id']
        if int(chat_id) != int(bp_chat_id):
            return

        try:
            members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
            members = members.items
        except:
            msg = messages.notadmin()
            await API.messages.send(random_id=0, message=msg, chat_id=chat_id)
            return

        omembers = [i.member_id for i in members if i.is_admin or i.is_owner]
        bp = message.user_id
        if bp not in omembers:
            return
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if s := await (await c.execute(
                        'select uid from accesslvl where chat_id=%s and access_level=7', (chat_id,))).fetchone():
                    if s[0] != bp:
                        return
                for i in await (await c.execute(
                        'select uid from mute where chat_id=%s and mute>%s', (chat_id, time.time()))).fetchall():
                    await setChatMute(i[0], chat_id, 0)
                await c.execute('delete from accesslvl where chat_id=%s', (chat_id,))
                await c.execute('delete from nickname where chat_id=%s', (chat_id,))
                await c.execute('delete from settings where chat_id=%s', (chat_id,))
                await c.execute('delete from welcome where chat_id=%s', (chat_id,))
                await c.execute('delete from welcomehistory where chat_id=%s', (chat_id,))
                await c.execute('delete from accessnames where chat_id=%s', (chat_id,))
                await c.execute('delete from ignore where chat_id=%s', (chat_id,))
                await c.execute('delete from commandlevels where chat_id=%s', (chat_id,))
                await c.execute('delete from mute where chat_id=%s', (chat_id,))
                await c.execute('delete from warn where chat_id=%s', (chat_id,))
                await c.execute('delete from ban where chat_id=%s', (chat_id,))
                await c.execute('delete from gpool where chat_id=%s', (chat_id,))
                await c.execute('delete from chatgroups where chat_id=%s', (chat_id,))
                await c.execute('delete from silencemode where chat_id=%s', (chat_id,))
                await c.execute('delete from filters where chat_id=%s', (chat_id,))
                await c.execute('delete from chatlimit where chat_id=%s', (chat_id,))
                await c.execute('delete from notifications where chat_id=%s', (chat_id,))
                await c.execute('delete from typequeue where chat_id=%s', (chat_id,))
                await c.execute('delete from antispamurlexceptions where chat_id=%s', (chat_id,))
                await c.execute('delete from botjoineddate where chat_id=%s', (chat_id,))
                await c.execute('delete from captcha where chat_id=%s', (chat_id,))
                await c.execute('insert into accesslvl (uid, chat_id, access_level) values (%s, %s, 7)', (bp, chat_id))
                await c.execute('insert into botjoineddate (chat_id, time) values (%s, %s)',
                                (chat_id, int(time.time())))
                await conn.commit()

        try:
            await tgbot.send_message(chat_id=TG_CHAT_ID, message_thread_id=TG_NEWCHAT_THREAD_ID,
                                     text=f'{chat_id} | {await getChatName(chat_id)} | '
                                          f'{await getChatOwner(chat_id)} | {await getChatMembers(chat_id)} | '
                                          f'{datetime.now().strftime("%H:%M:%S")}',
                                     disable_web_page_preview=True, parse_mode='HTML')
        except:
            traceback.print_exc()

        msg = messages.start()
        await editMessage(msg, peer_id, message.conversation_message_id)
        return
    elif cmd == 'rejoin' and payload['activate'] == 1:
        members = await API.messages.get_conversation_members(peer_id=peer_id)
        if (await getUserAccessLevel(uid, chat_id) >= 7 or
                uid in [i.member_id for i in members.items if i.is_admin or i.is_owner]):
            msg = messages.rejoin_activate()
            await editMessage(msg, peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['duel'], answer=False, checksender=False))
async def duel(message: MessageEvent):
    payload = message.payload
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    duelxp = int(payload['xp'])
    id = int(message.user_id)
    uid = int(payload['uid'])

    if id == uid or await getULvlBanned(id):
        return

    xp = await getUserXP(id)
    uxp = await getUserXP(uid)
    if xp < duelxp:
        await message.show_snackbar("У вас недостаточно XP")
        return
    elif uxp < duelxp:
        await message.show_snackbar("У вашего соперника недостаточно XP")
        return
    await sendMessageEventAnswer(message.event_id, id, peer_id)

    rid = (id, uid)[int.from_bytes(os.urandom(1)) % 2]
    if rid == id:
        loseid = uid
        winid = id
    else:
        loseid = id
        winid = uid

    xtw = duelxp
    u_premium = await getUserPremium(winid)
    if not u_premium:
        xtw = int(xtw / 100 * 90)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update duelwins set wins=wins+1 where uid=%s', (winid,))).rowcount:
                await c.execute('insert into duelwins (uid, wins) values (%s, 1)', (winid,))
            await conn.commit()
    await addWeeklyTask(winid, 'duelwin')
    await addDailyTask(winid, 'duelwin')

    await addUserXP(winid, xtw)
    await addUserXP(loseid, -duelxp)

    uname = await getUserName(winid)
    name = await getUserName(loseid)

    unick = await getUserNickname(winid, chat_id)
    nick = await getUserNickname(loseid, chat_id)

    msg = messages.duel_res(winid, uname, unick, loseid, name, nick, xtw, u_premium)
    await editMessage(msg, peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['answer_report'], checksender=False))
async def answer_report(message: MessageEvent):
    payload = message.payload
    peer_id = message.object.peer_id
    uid = int(payload['uid'])
    chat_id = int(payload['chat_id'])
    repid = int(payload['repid'])
    answering_id = int(message.user_id)
    report = payload['text']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute(
                'insert into reportanswers (uid, chat_id, repid, answering_id, report_text, cmid) values (%s, %s, %s,'
                ' %s, %s, %s)', (uid, chat_id, repid, answering_id, report, message.conversation_message_id))
            await conn.commit()
    msg = messages.report_answering(repid)
    await editMessage(msg, peer_id, message.conversation_message_id)
    await API.messages.mark_as_important(message_ids=message.conversation_message_id, important=1)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['settings_menu']))
async def settings_menu(message: MessageEvent):
    uid = message.user_id
    peer_id = message.peer_id

    msg = messages.settings()
    kb = keyboard.settings(uid)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['settings', 'change_setting']))
async def settings(message: MessageEvent):
    payload = message.payload
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.peer_id
    chat_id = peer_id - 2000000000
    category = payload['category']

    if cmd == 'change_setting':
        setting = payload['setting']
        if setting in SETTINGS_PREMIUM and not await getUserPremium(uid):
            await editMessage(messages.no_prem(), peer_id, message.conversation_message_id,
                              keyboard.settings_goto(uid, True))
            return
        if setting not in SETTINGS_COUNTABLE:
            await turnChatSetting(chat_id, category, setting)
        else:
            async with (await pool()).connection() as conn:
                async with conn.cursor() as c:
                    chatsetting = await (await c.execute(
                        'select "value", value2, punishment from settings where chat_id=%s and '
                        'setting=%s', (chat_id, setting))).fetchone()
            value = None if chatsetting is None else chatsetting[0]
            value2 = None if chatsetting is None else chatsetting[1]
            punishment = None if chatsetting is None else chatsetting[2]
            settings = await getChatSettings(chat_id)
            pos = settings[category][setting]
            altsettings = await getChatAltSettings(chat_id)
            pos2 = altsettings[category][setting] if (category in altsettings and
                                                      setting in altsettings[category]) else None
            msg = messages.settings_change_countable(chat_id, setting, pos, value, value2, pos2, punishment)
            kb = keyboard.settings_change_countable(uid, category, setting, settings, altsettings)
            await editMessage(msg, peer_id, message.conversation_message_id, kb)
            return
    settings = (await getChatSettings(chat_id))[category]
    msg = messages.settings_category(category, settings)
    kb = keyboard.settings_category(uid, category, settings)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['settings_change_countable']))
async def settings_change_countable(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.peer_id
    chat_id = peer_id - 2000000000
    action = payload['action']
    category = payload['category']
    setting = payload['setting']

    if setting in SETTINGS_PREMIUM and not await getUserPremium(uid):
        await editMessage(messages.no_prem(), peer_id, message.conversation_message_id,
                          keyboard.settings_goto(uid, True))
        return
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('delete from typequeue where chat_id=%s and uid=%s', (chat_id, uid))
            await conn.commit()

    if action in ('turn', 'turnalt'):
        await turnChatSetting(chat_id, category, setting, alt=action == 'turnalt')
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                chatsetting = await (await c.execute(
                    'select "value", value2, punishment from settings where chat_id=%s and setting=%s',
                    (chat_id, setting))).fetchone()
        value = None if chatsetting is None else chatsetting[0]
        value2 = None if chatsetting is None else chatsetting[1]
        punishment = None if chatsetting is None else chatsetting[2]
        settings = await getChatSettings(chat_id)
        pos = settings[category][setting]
        altsettings = await getChatAltSettings(chat_id)
        pos2 = altsettings[category][setting] if (category in altsettings and
                                                  setting in altsettings[category]) else None
        msg = messages.settings_change_countable(chat_id, setting, pos, value, value2, pos2, punishment)
        kb = keyboard.settings_change_countable(uid, category, setting, settings, altsettings)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)
        return
    msg = None
    kb = None
    if action == 'set':
        if setting == 'welcome':
            async with (await pool()).connection() as conn:
                async with conn.cursor() as c:
                    w = await (await c.execute(
                        'select msg, photo, url from welcome where chat_id=%s', (chat_id,))).fetchone()
            if w:
                msg = messages.settings_countable_action(action, setting, w[0], w[1], w[2])
                kb = keyboard.settings_set_welcome(uid, w[0], w[1], w[2])
            else:
                msg = messages.settings_countable_action(action, setting)
                kb = keyboard.settings_set_welcome(uid, None, None, None)
        else:
            async with (await pool()).connection() as conn:
                async with conn.cursor() as c:
                    await c.execute(
                        'insert into typequeue (chat_id, uid, type, additional) values (%s, %s, %s, %s)',
                        (chat_id, uid, 'settings_change_countable',
                         '{' + f'"setting": "{setting}", "category": "{category}", '
                               f'"cmid": "{message.conversation_message_id}"' + '}'))
                    await conn.commit()
            msg = messages.settings_countable_action(action, setting)
    if action == 'setPunishment':
        msg = messages.settings_choose_punishment()
        kb = keyboard.settings_set_punishment(uid, category, setting)
    if action == 'setWhitelist' or action == 'setBlacklist':
        msg = messages.settings_setlist(setting, action[3:-4])
        kb = keyboard.settings_setlist(uid, category, setting, action[3:-4])
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['settings_set_punishment']))
async def settings_set_punishment(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.peer_id
    chat_id = peer_id - 2000000000
    action = payload['action']  # 'deletemessage' or 'kick' or 'mute' or 'ban'
    category = payload['category']
    setting = payload['setting']

    if setting in SETTINGS_PREMIUM and not await getUserPremium(uid):
        await editMessage(messages.no_prem(), peer_id, message.conversation_message_id,
                          keyboard.settings_goto(uid, True))
        return
    if action in ['deletemessage', 'kick']:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute(
                    'update settings set punishment = %s where chat_id=%s and setting=%s', (action, chat_id, setting))
                await conn.commit()
        msg = messages.settings_set_punishment(action)
        kb = keyboard.settings_change_countable(uid, category, setting, await getChatSettings(chat_id),
                                                await getChatAltSettings(chat_id), True)
    else:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute('insert into typequeue (chat_id, uid, type, additional) values (%s, %s, %s, %s)',
                                (chat_id, uid, 'settings_set_punishment', '{' +
                                 f'"setting": "{setting}", "action": "{action}", "category": "{category}", '
                                 f'"cmid": "{message.conversation_message_id}"' + '}'))
                await conn.commit()
        msg = messages.settings_set_punishment_input(action)
        kb = keyboard.settings_change_countable(uid, category, setting, await getChatSettings(chat_id),
                                                await getChatAltSettings(chat_id), True)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['settings_exceptionlist']))
async def settings_exceptionlist(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.peer_id
    chat_id = peer_id - 2000000000
    setting = payload['setting']

    if setting in SETTINGS_PREMIUM and not await getUserPremium(uid):
        await editMessage(messages.no_prem(), peer_id, message.conversation_message_id,
                          keyboard.settings_goto(uid, True))
        return
    if setting == 'disallowLinks':
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                aurle = await (await c.execute(
                    'select url from antispamurlexceptions where chat_id=%s', (chat_id,))).fetchall()
        msg = messages.settings_exceptionlist(aurle)
        kb = keyboard.settings_change_countable(uid, category='antispam', onlybackbutton=True)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['settings_listaction']))
async def settings_listaction(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.peer_id
    chat_id = peer_id - 2000000000
    setting = payload['setting']
    action = payload['action']
    type = payload['type']

    if setting in SETTINGS_PREMIUM and not await getUserPremium(uid):
        await editMessage(messages.no_prem(), peer_id, message.conversation_message_id,
                          keyboard.settings_goto(uid, True))
        return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into typequeue (chat_id, uid, type, additional) values (%s, %s, %s, %s)',
                            (chat_id, uid, 'settings_listaction',
                             '{' + f'"setting": "{setting}", "action": "{action}", "type": "{type}"' + '}'))
            await conn.commit()
    msg = messages.settings_listaction_action(setting, action)
    await editMessage(msg, peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD([
    'settings_set_welcome_text', 'settings_set_welcome_photo', 'settings_set_welcome_url']))
async def settings_set_welcome(message: MessageEvent):
    payload = message.payload
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.peer_id
    chat_id = peer_id - 2000000000

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into typequeue (chat_id, uid, type, additional) values (%s, %s, %s, \'{}\')',
                            (chat_id, uid, cmd,))
            await conn.commit()
    msg = messages.get(cmd)
    await editMessage(msg, peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD([
    'settings_unset_welcome_text', 'settings_unset_welcome_photo', 'settings_unset_welcome_url']))
async def settings_unset_welcome(message: MessageEvent):
    payload = message.payload
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.peer_id
    chat_id = peer_id - 2000000000

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            welcome = await (await c.execute(
                'select msg, photo, url from welcome where chat_id=%s', (chat_id,))).fetchone()
            text = welcome[0]
            img = welcome[1]
            url = welcome[2]
            if (cmd in ['settings_unset_welcome_text', 'settings_unset_welcome_photo'] and
                    not ((text and ((img and url) or (not img and not url) or not url)) or
                         (img and ((text and url) or (not text and not url) or not url)))):
                return
            await c.execute('update welcome set msg = %s, photo = %s, url = %s where chat_id=%s',
                            (None if cmd == 'settings_unset_welcome_text' else text,
                             None if cmd == 'settings_unset_welcome_photo' else img,
                             None if cmd == 'settings_unset_welcome_url' else url, chat_id))
            await conn.commit()

    kb = keyboard.settings_set_welcome(uid, welcome.msg, welcome.photo, welcome.url)
    msg = messages.settings_countable_action('set', 'welcome')
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['nicklist']))
async def nicklist(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = members.items
    members_uid = [i.member_id for i in members]
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, nickname from nickname where chat_id=%s and uid>0 and uid=ANY(%s) and nickname is not null'
                ' order by nickname', (chat_id, members_uid))).fetchall()
    count = len(res)
    res = res[:30]
    names = await API.users.get(user_ids=[i[0] for i in res])
    msg = messages.nlist(res, names)
    kb = keyboard.nlist(uid, 0, count)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['prev_page_nlist', 'next_page_nlist']))
async def page_nlist(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    page = payload['page']

    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = members.items
    members_uid = [i.member_id for i in members]
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, nickname from nickname where chat_id=%s and uid>0 and uid=ANY(%s) and nickname is not null'
                ' order by nickname', (chat_id, members_uid))).fetchall()
    if not (count := len(res)):
        return
    res = res[page * 30:page * 30 + 30]
    names = await API.users.get(user_ids=[i[0] for i in res])
    msg = messages.nlist(res, names, page)
    kb = keyboard.nlist(uid, page, count)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['nonicklist']))
async def nonicklist(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = [i[0] for i in await (await c.execute(
                'select uid from nickname where chat_id=%s and uid>0 and nickname is not null', (chat_id,))).fetchall()]
    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = members.items
    members_uid = [i.member_id for i in members if i.member_id not in res]
    count = len(members_uid)
    members_uid = members_uid[:30]
    names = await API.users.get(user_ids=members_uid)

    msg = messages.nnlist(names)
    kb = keyboard.nnlist(uid, 0, count)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['prev_page_nnlist', 'next_page_nnlist']))
async def page_nnlist(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    page = payload['page']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = [i[0] for i in await (await c.execute(
                'select uid from nickname where chat_id=%s and uid>0 and nickname is not null')).fetchall()]
    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members_count = len(members.items[page * 30:])
    members = [i for i in members.items if i.member_id not in res][page * 30: page * 30 + 30]
    if len(members) <= 0:
        return
    members = await API.users.get(user_ids=[f'{i.member_id}' for i in members])
    msg = messages.nnlist(members, page)
    kb = keyboard.nnlist(uid, page, members_count)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
              SearchPayloadCMD(['prev_page_mutelist', 'next_page_mutelist']))
async def page_mutelist(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    page = payload['page']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, chat_id, last_mutes_causes, mute, last_mutes_names from mute where chat_id=%s and '
                'mute>%s order by uid desc', (chat_id, int(time.time())))).fetchall()
    if not (count := len(res)):
        return
    res = res.offset(page * 30).limit(30)
    res = res[page * 30: page * 30 + 30]
    names = await API.users.get(user_ids=[i[0] for i in res])
    msg = await messages.mutelist(res, names, count)
    kb = keyboard.mutelist(uid, page, count)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
              SearchPayloadCMD(['prev_page_warnlist', 'next_page_warnlist']))
async def page_warnlist(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    page = payload['page']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, chat_id, last_warns_causes, warns, last_warns_names from warn where chat_id=%s and'
                ' warns>0 order by uid desc', (chat_id,))).fetchall()
    if not (count := len(res)):
        return
    res = res[page * 30: page * 30 + 30]
    names = await API.users.get(user_ids=[i[0] for i in res])
    msg = await messages.warnlist(res, names, count)
    kb = keyboard.warnlist(uid, page, count)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['prev_page_banlist', 'next_page_banlist']))
async def page_banlist(message: MessageEvent):
    payload = message.payload
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    page = 0
    if cmd == 'prev_page_banlist':
        page = payload['page'] - 1
    elif cmd == 'next_page_banlist':
        page = payload['page'] + 1

    if page < 0:
        return
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, chat_id, last_bans_causes, ban, last_bans_names from ban where chat_id=%s and '
                'ban>%s order by uid desc', (chat_id, int(time.time())))).fetchall()
    if len(res) <= 0:
        return
    banned_count = len(res)
    res = res[page * 30:page * 30 + 30]
    names = await API.users.get(user_ids=[i[0] for i in res])
    msg = await messages.banlist(res, names, banned_count)
    kb = keyboard.banlist(uid, page, banned_count)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
              SearchPayloadCMD(['prev_page_statuslist', 'next_page_statuslist']))
async def page_statuslist(message: MessageEvent):
    payload = message.payload
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.object.peer_id
    page = 0
    if cmd == 'prev_page_statuslist':
        page = payload['page'] - 1
    if cmd == 'next_page_statuslist':
        page = payload['page'] + 1

    if page < 0:
        return
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            premium_pool = await (await c.execute('select uid, time from premium where time>%s',
                                                  (int(time.time()),))).fetchall()
    if len(premium_pool) <= 0:
        return
    premium_pool = premium_pool[page * 30:page * 30 + 30]
    names = await API.users.get(user_ids=[i[0] for i in premium_pool])
    msg = messages.statuslist(names, premium_pool)
    kb = keyboard.statuslist(uid, page, len(names))
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['demote']))
async def demote(message: MessageEvent):
    payload = message.payload
    kb = keyboard.demote_accept(message.user_id, payload['chat_id'], payload['option'])
    await editMessage(messages.demote_yon(), message.object.peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['demote_accept']))
async def demote_accept(message: MessageEvent):
    payload = message.payload
    sender = payload['uid'] if 'uid' in payload else message.user_id
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    option = payload['option']

    if option == 'all':
        members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        members = members.items
        for i in members:
            if not i.is_admin and i.member_id > 0:
                await kickUser(i.member_id, chat_id)
    elif option == 'lvl':
        members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        members = members.items
        kicking = []
        for i in members:
            if not i.is_admin and i.member_id > 0:
                acc = await getUserAccessLevel(i.member_id, chat_id)
                if acc == 0:
                    kicking.append(i.member_id)
        for i in kicking:
            await kickUser(i, chat_id)

    name = await getUserName(uid)

    nickname = await getUserNickname(uid, chat_id)
    await editMessage(messages.demote_accept(sender, name, nickname), peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['demote_disaccept']))
async def demote_disaccept(message: MessageEvent):
    await editMessage(messages.demote_disaccept(), message.object.peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['giveowner_no']))
async def giveowner_no(message: MessageEvent):
    await editMessage(messages.giveowner_no(), message.object.peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['giveowner']))
async def giveowner(message: MessageEvent):
    payload = message.payload
    peer_id = message.object.peer_id
    chat_id = payload['chat_id']
    uid = payload['uid']
    id = payload['chid']

    uname = await getUserName(uid)
    unick = await getUserNickname(uid, chat_id)

    name = await getUserName(id)
    nick = await getUserNickname(id, chat_id)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from accesslvl where chat_id=%s and uid=%s', (chat_id, uid))).rowcount:
                return
            if not (await c.execute('update accesslvl set access_level=7 where chat_id=%s and uid=%s',
                                    (chat_id, id))).rowcount:
                await c.execute('insert into accesslvl (uid, chat_id, access_level) values (%s, %s, 7)',
                                (id, chat_id))
            await c.execute('delete from gpool where chat_id=%s', (chat_id,))
            await c.execute('delete from chatgroups where chat_id=%s', (chat_id,))
            await conn.commit()

    await editMessage(messages.giveowner(uid, unick, uname, id, nick, name), peer_id,
                      message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['mtop']))
async def mtop(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = [int(i.member_id) for i in members.items]

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, messages from messages where uid>0 and messages>0 and chat_id=%s and '
                'uid=ANY(%s) order by messages desc limit 10', (chat_id, members))).fetchall()
    ids = [i[0] for i in res]

    names = await API.users.get(user_ids=ids)

    kb = keyboard.mtop(chat_id, uid)
    msg = messages.mtop(res, names)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['top_lvls']))
async def top_lvls(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    top = await getXPTop('lvl', 10)
    names = await API.users.get(user_ids=[int(x) for x in list(top.keys())])

    msg = messages.top_lvls(names, top)
    kb = keyboard.top_lvls(chat_id, uid)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['top_lvls_in_group']))
async def top_lvls_in_group(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = members.items
    all_members = [i.member_id for i in members]
    top = await getXPTop('lvl', 10, all_members)

    names = await API.users.get(user_ids=[int(x) for x in list(top.keys())])

    msg = messages.top_lvls(names, top, 'в беседе')
    kb = keyboard.top_lvls_in_group(chat_id, uid)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['top_duels']))
async def top_duels(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            lvln = await (await c.execute(
                'select uid, wins from duelwins where uid>0 order by wins desc limit 10')).fetchall()
    lvln = {i[0]: i[1] for i in lvln}
    names = await API.users.get(user_ids=[int(x) for x in list(lvln.keys())])

    msg = messages.top_duels(names, lvln)
    kb = keyboard.top_duels(chat_id, uid)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['top_duels_in_group']))
async def top_duels_in_group(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = members.items
    all_members = [i.member_id for i in members]
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            lvln = await (await c.execute(
                'select uid, wins from duelwins where uid>0 and uid=ANY(%s) order by wins desc limit 10',
                (all_members,))).fetchall()
    lvln = {i[0]: i[1] for i in lvln}

    names = await API.users.get(user_ids=[int(x) for x in list(lvln.keys())])

    msg = messages.top_duels(names, lvln, 'в беседе')
    kb = keyboard.top_duels_in_group(chat_id, uid)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['resetnick_accept']))
async def resetnick_accept(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('delete from nickname where chat_id=%s', (chat_id,))
            await conn.commit()
    name = await getUserName(uid)
    msg = messages.resetnick_accept(uid, name)
    await editMessage(msg, peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['resetnick_disaccept']))
async def resetnick_disaccept(message: MessageEvent):
    peer_id = message.object.peer_id
    msg = messages.resetnick_disaccept()
    await editMessage(msg, peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['resetaccess_accept']))
async def resetaccess_accept(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    lvl = payload['lvl']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('delete from accesslvl where chat_id=%s and access_level=%s', (chat_id, lvl))
            await conn.commit()
    name = await getUserName(uid)

    msg = messages.resetaccess_accept(uid, name, lvl)
    await editMessage(msg, peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['resetaccess_disaccept']))
async def resetaccess_disaccept(message: MessageEvent):
    payload = message.payload
    peer_id = message.object.peer_id
    lvl = payload['lvl']

    msg = messages.resetaccess_disaccept(lvl)
    await editMessage(msg, peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['kick_nonick']))
async def kick_nonick(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    nick = await getUserNickname(uid, chat_id)
    uname = await getUserName(uid)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute('select uid from nickname where chat_id=%s and uid>0 and nickname is not null',
                                         (chat_id,))).fetchall()
    res = [i[0] for i in res]
    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = members.items
    members_uid = [i.member_id for i in members if i.member_id not in res and i.member_id > 0]

    kicked = 0
    for i in members_uid:
        kicked += await kickUser(i, chat_id)

    msg = messages.kickmenu_kick_nonick(uid, uname, nick, kicked)
    await API.messages.send(random_id=0, message=msg, chat_id=chat_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['kick_nick']))
async def kick_nick(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    nick = await getUserNickname(uid, chat_id)
    uname = await getUserName(uid)

    kicked = 0
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            nicknamed = await (await c.execute(
                'select uid from nickname where chat_id=%s and uid>0 and nickname is not null', (chat_id,))).fetchall()
    for i in nicknamed:
        kicked += await kickUser(i[0], chat_id)

    msg = messages.kickmenu_kick_nick(uid, uname, nick, kicked)
    await API.messages.send(random_id=0, message=msg, chat_id=chat_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['kick_banned']))
async def kick_banned(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    nick = await getUserNickname(uid, chat_id)
    uname = await getUserName(uid)

    kicked = 0
    lst = await API.messages.get_conversation_members(peer_id=peer_id)
    lst = await API.users.get(user_ids=[i.member_id for i in lst.items])
    for i in lst:
        if i.deactivated:
            kicked += await kickUser(i.id, chat_id)

    msg = messages.kickmenu_kick_banned(uid, uname, nick, kicked)
    await API.messages.send(random_id=0, message=msg, chat_id=chat_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notif']))
async def notif(message: MessageEvent):
    payload = message.payload
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            notifs = await (await c.execute(
                'select status, name from notifications where chat_id=%s order by name desc',
                (chat_id,))).fetchall()
    if cmd == 'page' in payload:
        page = int(payload['page'])
    else:
        page = 1
    msg = messages.notifs(notifs)
    if len(notifs) > 0:
        kb = keyboard.notif_list(uid, notifs, page)
    else:
        kb = None
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notif_select']))
async def notif_select(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    name = payload['name']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            notif = await (await c.execute(
                'select name, text, time, every, tag, status from notifications where chat_id=%s and name=%s',
                (chat_id, name))).fetchone()
            await c.execute('delete from typequeue where uid=%s and chat_id=%s', (uid, chat_id))
            await conn.commit()
    msg = messages.notification(notif[0], notif[1], notif[2], notif[3], notif[4], notif[5])
    kb = keyboard.notification(uid, notif[5], notif[0])
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_status']))
async def notification_status(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    turn_to = payload['turn']
    name = payload['name']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            snotif = await (await c.execute('select time, every from notifications where chat_id=%s and name=%s',
                                            (chat_id, name))).fetchone()
            ntime = snotif[0]
            while ntime < time.time() and snotif[1] > 0:
                ntime += snotif[1] * 60
            snotif = await (await c.execute(
                'update notifications set status = %s, time = %s where chat_id=%s and name=%s '
                'returning text, every, tag', (turn_to, ntime, chat_id, name))).fetchone()
            await conn.commit()
    msg = messages.notification(name, snotif[0], ntime, snotif[1], snotif[2], turn_to)
    kb = keyboard.notification(uid, turn_to, name)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_text']))
async def notification_text(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    name = payload['name']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into typequeue (chat_id, uid, type, additional) values (%s, %s, %s, %s)',
                            (chat_id, uid, 'notification_text',
                             '{' + f'"name": "{name}", "cmid": "{message.conversation_message_id}"' + '}'))
            await conn.commit()
    msg = messages.notification_changing_text()
    await editMessage(msg, peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_time']))
async def notification_time(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    name = payload['name']

    msg = messages.notification_changing_time_choose()
    kb = keyboard.notification_time(uid, name)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_time_change']))
async def notification_time_change(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    name = payload['name']
    ctype = payload['type']

    if ctype == 'single':
        msg = messages.notification_changing_time_single()
    elif ctype == 'everyday':
        msg = messages.notification_changing_time_everyday()
    else:
        msg = messages.notification_changing_time_everyxmin()

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into typequeue (chat_id, uid, type, additional) values (%s, %s, %s, %s)',
                            (chat_id, uid, 'notification_time_change', '{' +
                             f'"name": "{name}", "cmid": "{message.conversation_message_id}", "type": "{ctype}"' + '}'))
            await conn.commit()

    await editMessage(msg, peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_tag']))
async def notification_tag(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    name = payload['name']

    msg = messages.notification_changing_tag_choose()
    kb = keyboard.notification_tag(uid, name)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_tag_change']))
async def notification_tag_change(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    name = payload['name']
    ctype = payload['type']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            notif = await (await c.execute(
                'update notifications set tag = %s where chat_id=%s and name=%s returning text, time, every, status',
                (ctype, chat_id, name))).fetchone()
            await conn.commit()

    msg = messages.notification(name, notif[0], notif[1], notif[2], ctype, notif[3])
    kb = keyboard.notification(uid, notif[3], name)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_delete']))
async def notification_delete(message: MessageEvent):
    payload = message.payload
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    name = payload['name']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('delete from notifications where chat_id=%s and name=%s', (chat_id, name))
            await conn.commit()
    msg = messages.notification_delete(name)
    await editMessage(msg, peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['listasync']))
async def listasync(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    page = payload['page']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            chat_ids = await (await c.execute('select chat_id from gpool where uid=%s', (uid,))).fetchall()
    chat_ids = [i[0] for i in chat_ids]
    total = len(chat_ids)
    chat_ids = chat_ids[(page - 1) * 10:page * 10]
    if len(chat_ids) > 0:
        names = [await getChatName(chat_id) for chat_id in chat_ids]
    else:
        names = []
    chats_info = [{"id": i, "name": names[k]} for k, i in enumerate(chat_ids)]

    msg = messages.listasync(chats_info, total)
    kb = keyboard.listasync(uid, total, page)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['help']))
async def help(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    page = payload['page']
    prem = payload['prem']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            cmds = await (await c.execute('select cmd, lvl from commandlevels where chat_id=%s', (chat_id,))).fetchall()
    base = COMMANDS.copy()
    for i in cmds:
        try:
            base[i[0]] = int(i[1])
        except:
            pass
    msg = messages.help(page, base)
    kb = keyboard.help(uid, page, prem)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['warn_report'], checksender=False))
async def warn_report(message: MessageEvent):
    payload = message.payload
    id = message.user_id
    peer_id = message.peer_id

    if id not in DEVS:
        return
    uid = payload['uid']
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (w := await (await c.execute(
                    'update reportwarns set warns=warns+1 where uid=%s returning warns', (uid,))).fetchone()):
                await c.execute('insert into reportwarns (uid, warns) values (%s, 1)', (uid,))
                w = 1
            else:
                w = w[0]
            await conn.commit()

    kb = keyboard.warn_report(uid, w)
    if w < 3:
        msg = messages.warn_report(id, await getUserName(id), w, uid, await getUserName(uid))
        await API.messages.send(message=msg, peer_id=peer_id, keyboard=kb, random_id=0)
        return
    msg = messages.warn_report_ban(id, await getUserName(id), uid, await getUserName(uid))
    await API.messages.send(message=msg, peer_id=peer_id, keyboard=kb, random_id=0)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['unwarn_report'], checksender=False))
async def unwarn_report(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.peer_id

    if uid not in DEVS:
        return
    uwarns = payload['warns']
    id = payload['uid']
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            uws = await (await c.execute('select warns from reportwarns where uid=%s', (id,))).fetchone()
            if uws:
                uwarns = uws[0] - uwarns
                if uwarns < 0:
                    uwarns = 0
                await c.execute('update reportwarns set warns = %s where uid=%s', (uwarns, id))
                await conn.commit()
            else:
                uwarns = 0

    kb = keyboard.warn_report(id, uwarns)
    if uwarns < 3:
        msg = messages.unwarn_report(id, await getUserName(id), uwarns, uid, await getUserName(uid))
        await API.messages.send(message=msg, peer_id=peer_id, keyboard=kb,
                                random_id=0)
        return
    msg = messages.warn_report_ban(id, await getUserName(id), uid, await getUserName(uid))
    await API.messages.send(message=msg, peer_id=peer_id, keyboard=kb,
                            random_id=0)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['cmdlist']))
async def cmdlist(message: MessageEvent):
    payload = message.payload
    page = payload['page']
    uid = message.user_id
    peer_id = message.peer_id

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            cmdnames = {i[0]: i[1] for i in await (await c.execute('select cmd, name from cmdnames where uid=%s',
                                                                   (uid,))).fetchall()}

    msg = messages.cmdlist(dict(list(cmdnames.items())[page * 10: (page * 10) + 10]), page, len(list(cmdnames)))
    kb = keyboard.cmdlist(uid, page, len(cmdnames))
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['task']))
async def task(message: MessageEvent):
    uid = message.user_id
    peer_id = message.peer_id

    completed = 0
    prem = await getUserPremium(uid)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            cs = await (await c.execute('select coins from coins where uid=%s', (uid,))).fetchone()
            cs = cs[0] if cs else 0
            s = await (await c.execute('select streak from tasksstreak where uid=%s', (uid,))).fetchone()
            s = s[0] if s else 0
            t = await (await c.execute('select count, task from tasksdaily where uid=%s', (uid,))).fetchall()
    for i in t:
        if i[0] >= (TASKS_DAILY | PREMIUM_TASKS_DAILY)[i[1]]:
            if i[1] in PREMIUM_TASKS_DAILY and not prem:
                continue
            completed += 1
    kb = keyboard.tasks(uid)
    msg = messages.task(completed, cs, s)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['task_trade']))
async def task_trade(message: MessageEvent):
    uid = message.user_id
    peer_id = message.peer_id

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            c = await (await c.execute('select coins from coins where uid=%s', (uid,))).fetchone()
            c = c[0] if c else 0
    msg = messages.task_trade(c)
    kb = keyboard.task_trade(uid, c)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['task_trade_lot']))
async def task_trade_lot(message: MessageEvent):
    payload = message.payload
    lot = payload['lot']
    uid = message.user_id
    peer_id = message.peer_id

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            cs = await (await c.execute('select id, coins from coins where uid=%s', (uid,))).fetchone()
            cc = cs[1] if cs else 0
            cost = list(TASKS_LOTS.keys())[lot - 1]
            if cc < cost or not (await c.execute(
                    'update coins set coins=coins-%s where uid=%s', (cost, uid,))).rowcount:
                msg = messages.task_trade_not_enough(cost - cc)
                kb = keyboard.task_back(uid)
                await editMessage(msg, peer_id, message.conversation_message_id, kb)
                return
            if lot < 4:
                await c.execute('update xp set xp=xp+%s where uid=%s', (TASKS_LOTS[cost] * 200, uid))
            else:
                if not (await c.execute(
                        'update premium set time=time+%s where uid=%s', (TASKS_LOTS[cost] * 86400, uid))).rowcount:
                    await c.execute('insert into premium (uid, time) values (%s, %s)',
                                    (uid, int(time.time() + TASKS_LOTS[cost] * 86400)))
            await conn.commit()

    msg = messages.task_trade_lot_log(lot, uid, await getUserName(uid))
    await API.messages.send(peer_id=2000020672, random_id=0, message='#task' + msg)

    msg = messages.task_trade_lot(lot)
    kb = keyboard.task_back(uid)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['task_weekly']))
async def task_weekly(message: MessageEvent):
    uid = message.user_id
    peer_id = message.peer_id
    prem = await getUserPremium(uid)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            bonus = await (await c.execute(
                'select count from tasksweekly where uid=%s and task=\'bonus\'', (uid,))).fetchone()
            bonus = bonus[0] if bonus else 0
            dailytask = await (await c.execute(
                'select count from tasksweekly where uid=%s and task=\'dailytask\'', (uid,))).fetchone()
            dailytask = dailytask[0] if dailytask else 0
            sendmsgs = await (await c.execute(
                'select count from tasksweekly where uid=%s and task=\'sendmsgs\'', (uid,))).fetchone()
            sendmsgs = sendmsgs[0] if sendmsgs else 0
            lvlup = await (await c.execute(
                'select count from tasksweekly where uid=%s and task=\'lvlup\'', (uid,))).fetchone()
            lvlup = lvlup[0] if lvlup else 0
            duelwin = await (await c.execute(
                'select count from tasksweekly where uid=%s and task=\'duelwin\'', (uid,))).fetchone()
            duelwin = duelwin[0] if duelwin else 0

    msg = messages.task_weekly(prem, [bonus, dailytask, sendmsgs, lvlup, duelwin])
    kb = keyboard.task_back(uid)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['task_daily']))
async def task_daily(message: MessageEvent):
    uid = message.user_id
    peer_id = message.peer_id
    prem = await getUserPremium(uid)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            sendmsgs = await (await c.execute(
                'select count from tasksdaily where uid=%s and task=\'sendmsgs\'', (uid,))).fetchone()
            sendmsgs = sendmsgs[0] if sendmsgs else 0
            sendvoice = await (await c.execute(
                'select count from tasksdaily where uid=%s and task=\'sendvoice\'', (uid,))).fetchone()
            sendvoice = sendvoice[0] if sendvoice else 0
            duelwin = await (await c.execute(
                'select count from tasksdaily where uid=%s and task=\'duelwin\'', (uid,))).fetchone()
            duelwin = duelwin[0] if duelwin else 0
            cmds = await (await c.execute(
                'select count from tasksdaily where uid=%s and task=\'cmds\'', (uid,))).fetchone()
            cmds = cmds[0] if cmds else 0
            stickers = await (await c.execute(
                'select count from tasksdaily where uid=%s and task=\'stickers\'', (uid,))).fetchone()
            stickers = stickers[0] if stickers else 0

    msg = messages.task_daily(prem, [sendmsgs, sendvoice, duelwin, cmds, stickers])
    kb = keyboard.task_back(uid)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['check']))
async def check(message: MessageEvent):
    payload = message.payload
    sender = payload['uid'] if 'uid' in payload else message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    id = payload['id']
    check = payload['check']

    if check == 'ban':
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                res = await (await c.execute(
                    'select last_bans_causes, last_bans_names, last_bans_dates, last_bans_times from ban where '
                    'chat_id=%s and uid=%s', (chat_id, id))).fetchone()
        if res is not None:
            ban_date = literal_eval(res[0])[::-1][0]
            u_bans_names = literal_eval(res[1])[::-1]
            ban_from = u_bans_names[0]
            ban_reason = literal_eval(res[2])[::-1][0]
            ban_time = literal_eval(res[3])[::-1][0]
        else:
            u_bans_names = []
            ban_date = ban_from = ban_reason = ban_time = None
        ban = await getUserBan(id, chat_id)
        if ban:
            ban -= time.time()
        name = await getUserName(id)
        nickname = await getUserNickname(id, chat_id)
        msg = messages.check_ban(id, name, nickname, ban, u_bans_names, ban_date, ban_from, ban_reason, ban_time)
        kb = keyboard.check_history(sender, id, 'ban', len(u_bans_names))
        await editMessage(msg, peer_id, message.conversation_message_id, kb)
    if check == 'mute':
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                res = await (await c.execute(
                    'select last_mutes_causes, last_mutes_names, last_mutes_dates, last_mutes_times from mute '
                    'where chat_id=%s and uid=%s', (chat_id, id))).fetchone()
        if res is not None:
            mute_date = literal_eval(res[0])[::-1][0]
            u_mutes_names = literal_eval(res[1])[::-1]
            mute_from = u_mutes_names[0]
            mute_reason = literal_eval(res[2])[::-1][0]
            mute_time = literal_eval(res[3])[::-1][0]
        else:
            u_mutes_names = []
            mute_date = mute_from = mute_reason = mute_time = None
        mute = await getUserMute(id, chat_id) - time.time()
        if mute < 0:
            mute = 0
        name = await getUserName(id)
        nickname = await getUserNickname(id, chat_id)
        msg = messages.check_mute(id, name, nickname, mute, u_mutes_names, mute_date,
                                  mute_from, mute_reason, mute_time)
        kb = keyboard.check_history(sender, id, 'mute', len(u_mutes_names))
        await editMessage(msg, peer_id, message.conversation_message_id, kb)
    if check == 'warn':
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                res = await (await c.execute(
                    'select last_warns_causes, last_warns_names, last_warns_dates from warn where uid=%s and '
                    'chat_id=%s', (id, chat_id))).fetchone()
        if res is not None:
            u_warns_causes = literal_eval(res[0])[::-1]
            u_warns_names = literal_eval(res[1])[::-1]
            u_warns_dates = literal_eval(res[2])[::-1]
        else:
            u_warns_names = u_warns_causes = u_warns_dates = []
        warn = await getUserWarns(id, chat_id)
        name = await getUserName(id)
        nickname = await getUserNickname(id, chat_id)
        msg = messages.check_warn(id, name, nickname, warn, u_warns_names,
                                  u_warns_dates, u_warns_names, u_warns_causes)
        kb = keyboard.check_history(sender, id, 'warn', len(u_warns_causes))
        await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['check_menu']))
async def check_menu(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    id = payload['id']
    
    ban = await getUserBan(id, chat_id) - time.time()
    if ban < 0:
        ban = 0
    mute = await getUserMute(id, chat_id) - time.time()
    if mute < 0:
        mute = 0
    warn = await getUserWarns(id, chat_id)

    name = await getUserName(id)
    nickname = await getUserNickname(id, chat_id)
    msg = messages.check(id, name, nickname, ban, warn, mute)
    kb = keyboard.check(uid, id)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['check_history'], answer=False))
async def check_history(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    id = payload['id']
    check = payload['check']
    
    if not int(payload['ie']):
        await sendMessageEventAnswer(message.event_id, uid, message.peer_id,
                                     json.dumps({'type': 'show_snackbar', 'text': 'Нету истории'}))
        return
    await sendMessageEventAnswer(message.event_id, uid, peer_id)

    if check == 'ban':
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                res = await (await c.execute(
                    'select last_bans_causes, last_bans_names, last_bans_dates, last_bans_times from ban where '
                    'chat_id=%s and uid=%s', (chat_id, id))).fetchone()
        if res is not None:
            bans_causes = literal_eval(res[0])[::-1][:50]
            bans_names = literal_eval(res[1])[::-1][:50]
            bans_dates = literal_eval(res[2])[::-1][:50]
            bans_times = literal_eval(res[3])[::-1][:50]
        else:
            bans_causes = bans_names = bans_dates = bans_times = []
        name = await getUserName(id)
        nickname = await getUserNickname(id, chat_id)
        msg = messages.check_history_ban(id, name, nickname, bans_dates, bans_names, bans_times, bans_causes)
        await editMessage(msg, peer_id, message.conversation_message_id)
    if check == 'mute':
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                res = await (await c.execute(
                    'select last_mutes_causes, last_mutes_names, last_mutes_dates, last_mutes_times from '
                    'mute where chat_id=%s and uid=%s',  (chat_id, id))).fetchone()
        if res is not None:
            mutes_causes = literal_eval(res[0])[::-1][:50]
            mutes_names = literal_eval(res[1])[::-1][:50]
            mutes_dates = literal_eval(res[2])[::-1][:50]
            mutes_times = literal_eval(res[3])[::-1][:50]
        else:
            mutes_causes = mutes_names = mutes_dates = mutes_times = []
        name = await getUserName(id)
        nickname = await getUserNickname(id, chat_id)
        msg = messages.check_history_mute(id, name, nickname, mutes_dates, mutes_names, mutes_times, mutes_causes)
        await editMessage(msg, peer_id, message.conversation_message_id)
    if check == 'warn':
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                res = await (await c.execute(
                    'select last_warns_causes, last_warns_names, last_warns_dates, last_warns_times from warn '
                    'where chat_id=%s and uid=%s', (chat_id, id))).fetchone()
        if res is not None:
            warns_causes = literal_eval(res[0])[::-1][:50]
            warns_names = literal_eval(res[1])[::-1][:50]
            warns_dates = literal_eval(res[2])[::-1][:50]
            warns_times = literal_eval(res[3])[::-1][:50]
        else:
            warns_causes = warns_names = warns_dates = warns_times = []
        name = await getUserName(id)
        nickname = await getUserNickname(id, chat_id)
        msg = messages.check_history_warn(id, name, nickname, warns_dates, warns_names, warns_times, warns_causes)
        await editMessage(msg, peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, 
              SearchPayloadCMD(['unmute', 'unwarn', 'unban'], answer=False, checksender=False))
async def unpunish(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    cmd = payload['cmd']
    id = payload['id']
    cmid = payload['cmid']
    
    u_acc = await getUserAccessLevel(uid, chat_id)
    if u_acc <= await getUserAccessLevel(id, chat_id) or not await haveAccess(cmd, chat_id, u_acc):
        await message.show_snackbar("⛔️ У вас недостаточно прав.")
        return
    await sendMessageEventAnswer(message.event_id, uid, peer_id)

    name = await getUserName(id)
    nickname = await getUserNickname(id, chat_id)
    uname = await getUserName(uid)
    unickname = await getUserNickname(uid, chat_id)
    
    if cmd == 'unmute':
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if not (await c.execute('update mute set mute=0 where chat_id=%s and uid=%s and mute>%s',
                                        (chat_id, id, int(time.time())))).rowcount:
                    return
                await conn.commit()
        await setChatMute(id, chat_id, 0)
        msg = messages.unmute(uname, unickname, uid, name, nickname, id)
    elif cmd == 'unwarn':
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if not (await c.execute(
                        'update warn set warns=warns-1 where chat_id=%s and uid=%s and warns>0 and warns<3',
                        (chat_id, id))).rowcount:
                    return
                await conn.commit()
        msg = messages.unwarn(uname, unickname, uid, name, nickname, id)
    elif cmd == 'unban':
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if not (await c.execute('update ban set ban=0 where chat_id=%s and uid=%s and ban>%s',
                                        (chat_id, id, int(time.time())))).rowcount:
                    return
                await conn.commit()
        msg = messages.unban(uname, unickname, uid, name, nickname, id)
    else:
        return

    await editMessage(msg, peer_id, message.conversation_message_id)
    await deleteMessages(cmid, chat_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
              SearchPayloadCMD(['prefix_add', 'prefix_del', 'prefix_list', 'prefix']))
async def addprefix(message: MessageEvent):
    payload = message.payload
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if not await getUserPremium(uid):
        await editMessage(messages.no_prem(), peer_id, message.conversation_message_id)
        return
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if cmd == 'prefix_add' and (await (await c.execute(
                    'select count(*) as c from prefix where uid=%s', (uid,))).fetchone())[0] > 2:
                await editMessage(messages.addprefix_max(), peer_id, message.conversation_message_id,
                                  keyboard.prefix_back(uid))
                return
            if cmd in ('prefix_add', 'prefix_del'):
                await c.execute('insert into typequeue (chat_id, uid, type, additional) values (%s, %s, %s, %s)',
                                (chat_id, uid, cmd, '{"cmid": ' + str(message.conversation_message_id) + '}'))
                await conn.commit()
                await editMessage(messages.get(cmd), peer_id, message.conversation_message_id)
            elif cmd == 'prefix_list':
                prefixes = await (await c.execute('select prefix from prefix where uid=%s', (uid,))).fetchall()
                await editMessage(
                    messages.listprefix(uid, await getUserName(uid), await getUserNickname(uid, chat_id), prefixes),
                    peer_id, message.conversation_message_id, keyboard.prefix_back(uid))
            else:
                await editMessage(messages.prefix(), peer_id, message.conversation_message_id, keyboard.prefix(uid))
