import json
import random
import secrets
import time
from ast import literal_eval
from datetime import datetime

from vkbottle.bot import MessageEvent
from vkbottle.framework.labeler import BotLabeler
from vkbottle_types.events import GroupEventType

import keyboard
import messages
from Bot.checkers import haveAccess
from Bot.rules import SearchPayloadCMD
from Bot.utils import sendMessageEventAnswer, editMessage, getUserAccessLevel, getUserXP, getUserPremium, addUserXP, \
    getUserName, getUserNickname, kickUser, getXPTop, getChatName, addWeeklyTask, \
    addDailyTask, getUserBan, getUserWarns, getUserMute, getULvlBanned, getChatSettings, turnChatSetting, \
    deleteMessages, setChatMute, getChatAltSettings
from config.config import API, COMMANDS, DEVS, TASKS_LOTS, TASKS_DAILY, PREMIUM_TASKS_DAILY, SETTINGS_COUNTABLE, \
    SETTINGS_COUNTABLE_NO_PUNISHMENT
from db import AccessLevel, JoinedDate, DuelWins, ReportAnswers, Nickname, Mute, Warn, Ban, Premium, \
    GPool, ChatGroups, Messages, Notifs, TypeQueue, CMDLevels, ReportWarns, CMDNames, Coins, XP, TasksWeekly, \
    TasksDaily, TasksStreak, Settings, AntispamURLExceptions, Welcome

bl = BotLabeler()


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['join', 'rejoin']))
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

        ac = AccessLevel.get_or_create(uid=bp, chat_id=chat_id)[0]
        ac.access_level = 7
        ac.save()

        chtime = JoinedDate.get_or_create(chat_id=chat_id)[0]
        chtime.time = time.time()
        chtime.save()

        msg = messages.start()
        await editMessage(msg, peer_id, message.conversation_message_id)
        return
    elif cmd == 'rejoin' and payload['activate'] == 1:
        members = await API.messages.get_conversation_members(peer_id=peer_id)
        if (await getUserAccessLevel(uid, chat_id) >= 7 or
                uid in [i.member_id for i in members.items if i.is_admin or i.is_owner]):
            msg = messages.rejoin_activate()
            await editMessage(msg, peer_id, message.conversation_message_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['duel']))
async def duel(message: MessageEvent):
    payload = message.payload

    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'duel':
        duelxp = int(payload['xp'])
        id = int(message.user_id)
        uid = int(payload['uid'])
        if id == uid or not await getULvlBanned(id):
            return

        xp = await getUserXP(id)
        uxp = await getUserXP(uid)
        if xp < duelxp:
            await message.show_snackbar("У вас недостаточно XP")
            return
        elif uxp < duelxp:
            await message.show_snackbar("У вашего соперника недостаточно XP")
            return

        rid = [id, uid][secrets.randbelow(2)]
        if rid == id:
            loseid = uid
            winid = id
        else:
            loseid = id
            winid = uid

        u_premium = await getUserPremium(winid)
        if u_premium:
            xtw = duelxp
        else:
            xtw = duelxp / 100 * 90

        dw = DuelWins.get_or_create(uid=winid, defaults={'wins': 0})[0]
        dw.wins += 1
        dw.save()
        await addWeeklyTask(winid, 'duelwin')
        await addDailyTask(winid, 'duelwin')

        await addUserXP(winid, xtw)
        await addUserXP(loseid, -duelxp)

        uname = await getUserName(winid)
        name = await getUserName(loseid)

        unick = await getUserNickname(winid, chat_id)
        nick = await getUserNickname(loseid, chat_id)

        msg = messages.duel_res(winid, uname, unick, loseid, name, nick, duelxp, u_premium)
        await editMessage(msg, peer_id, message.conversation_message_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['answer_report']))
async def answer_report(message: MessageEvent):
    payload = message.payload

    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id

    if cmd == 'answer_report':
        uid = int(payload['uid'])
        chat_id = int(payload['chat_id'])
        repid = int(payload['repid'])
        answering_id = int(message.user_id)
        report = payload['text']
        ReportAnswers.create(uid=uid, chat_id=chat_id, repid=repid, answering_id=answering_id, report_text=report,
                             cmid=message.conversation_message_id)

        msg = messages.report_answering(repid)
        await editMessage(msg, peer_id, message.conversation_message_id)
        await API.messages.mark_as_important(message_ids=message.conversation_message_id, important=1)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['settings_menu']))
async def settings_menu(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.peer_id

    if cmd in 'settings_menu' and sender == uid:
        msg = messages.settings()
        kb = keyboard.settings(uid)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['settings', 'change_setting']))
async def settings(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.peer_id
    chat_id = peer_id - 2000000000

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)
    if cmd in ['settings', 'change_setting'] and sender == uid:
        category = payload['category']
        if cmd == 'change_setting':
            setting = payload['setting']
            if setting not in SETTINGS_COUNTABLE:
                await turnChatSetting(chat_id, category, setting)
            else:
                chatsetting = Settings.get_or_none(Settings.chat_id == chat_id, Settings.setting == setting)
                value = None if chatsetting is None else chatsetting.value
                value2 = None if chatsetting is None else chatsetting.value2
                punishment = None if chatsetting is None else chatsetting.punishment
                settings = await getChatSettings(chat_id)
                pos = settings[category][setting]
                altsettings = await getChatAltSettings(chat_id)
                pos2 = altsettings[category][setting]
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

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'settings_change_countable' and sender == uid:
        await sendMessageEventAnswer(message.event_id, uid, message.peer_id)
        action = payload['action']
        category = payload['category']
        setting = payload['setting']
        TypeQueue.delete().where(TypeQueue.uid == uid, TypeQueue.chat_id == chat_id).execute()

        if action in ('turn', 'turnalt'):
            await turnChatSetting(chat_id, category, setting, alt=action == 'turnalt')
            chatsetting = Settings.get_or_none(Settings.chat_id == chat_id, Settings.setting == setting)
            value = None if chatsetting is None else chatsetting.value
            punishment = None if chatsetting is None else chatsetting.punishment
            value2 = None if chatsetting is None else chatsetting.value2
            settings = await getChatSettings(chat_id)
            pos = settings[category][setting]
            altsettings = await getChatAltSettings(chat_id)
            pos2 = altsettings[category][setting]
            msg = messages.settings_change_countable(chat_id, setting, pos, value, value2, pos2, punishment)
            kb = keyboard.settings_change_countable(uid, category, setting, settings, altsettings)
            await editMessage(msg, peer_id, message.conversation_message_id, kb)
            return
        msg = None
        kb = None
        if action == 'set':
            if setting == 'welcome':
                w = Welcome.get_or_none(Welcome.chat_id == chat_id)
                if w is None:
                    msg = messages.settings_countable_action(action, setting)
                else:
                    msg = messages.settings_countable_action(action, setting, w.msg, w.photo, w.url)
                kb = keyboard.settings_set_welcome(uid)
            else:
                TypeQueue.create(
                    uid=uid, chat_id=chat_id, type='settings_change_countable',
                    additional='{' + f'"setting": "{setting}", "category": "{category}", '
                                     f'"cmid": "{message.conversation_message_id}"' + '}'
                )
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

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'settings_set_punishment' and sender == uid:
        action = payload['action']  # 'deletemessage' or 'kick' or 'mute' or 'ban'
        category = payload['category']
        setting = payload['setting']
        if action in ['deletemessage', 'kick']:
            chatsetting = Settings.get(Settings.chat_id == chat_id, Settings.setting == setting)
            chatsetting.punishment = action
            chatsetting.save()
            msg = messages.settings_set_punishment(action)
            kb = keyboard.settings_change_countable(uid, category, setting, await getChatSettings(chat_id),
                                                    await getChatAltSettings(chat_id), True)
        else:
            TypeQueue.create(
                uid=uid, chat_id=chat_id, type='settings_set_punishment',
                additional='{' + f'"setting": "{setting}", "action": "{action}", "category": "{category}", '
                                 f'"cmid": "{message.conversation_message_id}"' + '}'
            )
            msg = messages.settings_set_punishment_input(action)
            kb = keyboard.settings_change_countable(uid, category, setting, await getChatSettings(chat_id),
                                                    await getChatAltSettings(chat_id), True)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['settings_exceptionlist']))
async def settings_exceptionlist(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'settings_exceptionlist' and sender == uid:
        setting = payload['setting']
        if setting == 'disallowLinks':
            msg = messages.settings_exceptionlist(AntispamURLExceptions.select().where(
                AntispamURLExceptions.chat_id == chat_id))
            kb = keyboard.settings_change_countable(uid, category='antispam', onlybackbutton=True)
            await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['settings_listaction']))
async def settings_listaction(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'settings_listaction' and sender == uid:
        setting = payload['setting']
        action = payload['action']
        type = payload['type']
        TypeQueue.create(
            uid=uid, chat_id=chat_id, type='settings_listaction',
            additional='{' + f'"setting": "{setting}", "action": "{action}", "type": "{type}"' + '}'
        )
        msg = messages.settings_listaction_action(setting, action)
        await editMessage(msg, peer_id, message.conversation_message_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD([
    'settings_set_welcome_text', 'settings_set_welcome_photo', 'settings_set_welcome_url']))
async def settings_listaction(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.peer_id
    chat_id = peer_id - 2000000000

    if cmd in ['settings_set_welcome_text', 'settings_set_welcome_photo', 'settings_set_welcome_url'] and sender == uid:
        TypeQueue.create(uid=uid, chat_id=chat_id, type=cmd, additional='{}')
        msg = messages.get(cmd)
        await editMessage(msg, peer_id, message.conversation_message_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['nicklist']))
async def nicklist(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'nicklist' and sender == uid:
        members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        members = members.items
        members_uid = [i.member_id for i in members]
        res = Nickname.select().where(Nickname.uid > 0, Nickname.uid << members_uid, Nickname.chat_id == chat_id,
                                      Nickname.nickname.is_null(False)).order_by(Nickname.nickname)
        names = await API.users.get(user_ids=[f'{i.uid}' for i in res])
        msg = messages.nlist(res, names)
        kb = keyboard.nlist(uid, 0)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['prev_page_nlist', 'next_page_nlist']))
async def page_nlist(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    page = 0
    if cmd == 'prev_page_nlist':
        page = payload['page'] - 1
    elif cmd == 'next_page_nlist':
        page = payload['page'] + 1

    if (cmd == 'prev_page_nlist' or cmd == 'next_page_nlist') and sender == uid:
        if page >= 0:
            members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
            members = members.items
            members_uid = [i.member_id for i in members]
            res = Nickname.select().where(Nickname.uid > 0, Nickname.uid << members_uid, Nickname.chat_id == chat_id,
                                          Nickname.nickname.is_null(False)).order_by(Nickname.nickname)
            offset = page * 30
            if len(res) > 0:
                names = await API.users.get(user_ids=[i.uid for i in res])
                msg = messages.nlist(res, names, offset)
                kb = keyboard.nlist(uid, page)
                await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['nonicklist']))
async def nonicklist(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'nonicklist' and sender == uid:
        res = Nickname.select().where(Nickname.uid > 0, Nickname.chat_id == chat_id, Nickname.nickname.is_null(False))
        nickmembers = [i.uid for i in res]
        members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        members = members.items
        members_uid = [i.member_id for i in members if i.member_id not in nickmembers][:30]
        names = await API.users.get(user_ids=[f'{i}' for i in members_uid])
        msg = messages.nnlist(names)
        kb = keyboard.nnlist(uid, 0)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['prev_page_nnlist', 'next_page_nnlist']))
async def page_nnlist(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    page = 0
    if cmd == 'prev_page_nnlist':
        page = payload['page'] - 1
    elif cmd == 'next_page_nnlist':
        page = payload['page'] + 1

    if (cmd == 'prev_page_nnlist' or cmd == 'next_page_nnlist') and sender == uid:
        if page >= 0:
            res = Nickname.select().where(Nickname.uid > 0, Nickname.chat_id == chat_id)
            nickmembers = [i.uid for i in res]
            members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
            members = members.items
            members = [i for i in members if i.member_id not in nickmembers][page * 30: page * 30 + 30]
            if len(members) > 0:
                members = await API.users.get(user_ids=[f'{i.member_id}' for i in members])
                msg = messages.nnlist(members, page)
                kb = keyboard.nnlist(uid, page)
                await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
              SearchPayloadCMD(['prev_page_mutelist', 'next_page_mutelist']))
async def page_mutelist(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    page = 0
    if cmd == 'prev_page_mutelist':
        page = payload['page'] - 1
    elif cmd == 'next_page_mutelist':
        page = payload['page'] + 1

    if (cmd == 'prev_page_mutelist' or cmd == 'next_page_mutelist') and sender == uid:
        if page >= 0:
            res = Mute.select().where(Mute.mute > int(time.time()), Mute.chat_id == chat_id)
            if len(res) > 0:
                muted_count = len(res)
                res = res.offset(page * 30).limit(30)
                names = await API.users.get(user_ids=[i.uid for i in res])
                msg = await messages.mutelist(res, names, muted_count)
                kb = keyboard.mutelist(uid, page)
                await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
              SearchPayloadCMD(['prev_page_warnlist', 'next_page_warnlist']))
async def page_warnlist(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    page = 0
    if cmd == 'prev_page_warnlist':
        page = payload['page'] - 1
    elif cmd == 'next_page_warnlist':
        page = payload['page'] + 1

    if (cmd == 'prev_page_warnlist' or cmd == 'next_page_warnlist') and sender == uid:
        if page >= 0:
            res = Warn.select().where(Warn.warns > 0, Warn.chat_id == chat_id)
            if len(res) > 0:
                muted_count = len(res)
                res = res.offset(page * 30).limit(30)
                names = await API.users.get(user_ids=[i.uid for i in res])
                msg = await messages.warnlist(res, names, muted_count)
                kb = keyboard.warnlist(uid, page)
                await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['prev_page_banlist', 'next_page_banlist']))
async def page_banlist(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    page = 0
    if cmd == 'prev_page_banlist':
        page = payload['page'] - 1
    elif cmd == 'next_page_banlist':
        page = payload['page'] + 1

    if (cmd == 'prev_page_banlist' or cmd == 'next_page_banlist') and sender == uid:
        if page >= 0:
            res = Ban.select().where(Ban.ban > int(time.time()), Ban.chat_id == chat_id)
            if len(res) > 0:
                banned_count = len(res)
                res = res.offset(page * 30).limit(30)
                names = await API.users.get(user_ids=[i.uid for i in res])
                msg = await messages.banlist(res, names, banned_count)
                kb = keyboard.banlist(uid, page)
                await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
              SearchPayloadCMD(['prev_page_statuslist', 'next_page_statuslist']))
async def page_statuslist(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id

    page = 0
    if cmd == 'prev_page_statuslist' and sender == uid:
        page = payload['page'] - 1

    if cmd == 'next_page_statuslist' and sender == uid:
        page = payload['page'] + 1

    if (cmd == 'prev_page_statuslist' or cmd == 'next_page_statuslist') and sender == uid:
        if page >= 0:
            premium_pool = Premium.select().where(Premium.time >= time.time())
            if len(premium_pool) > 0:
                names = await API.users.get(user_ids=[i.uid for i in premium_pool])
                msg = messages.statuslist(names, premium_pool)
                kb = keyboard.statuslist(uid, 0)
                await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['demote']))
async def demote(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id

    if cmd == 'demote' and sender == uid:
        msg = messages.demote_yon()
        kb = keyboard.demote_accept(uid, payload['chat_id'], payload['option'])
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['demote_accept']))
async def demote_accept(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'demote_accept' and sender == uid:
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

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['demote_disaccept']))
async def demote_disaccept(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id

    if cmd == 'demote_disaccept' and sender == uid:
        await editMessage(messages.demote_disaccept(), peer_id, message.conversation_message_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['giveowner_no']))
async def giveowner_no(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id

    if cmd == 'giveowner_no' and sender == uid:
        await editMessage(messages.giveowner_no(), peer_id, message.conversation_message_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['giveowner']))
async def giveowner(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id

    if cmd == 'giveowner' and sender == uid:
        chat_id = payload['chat_id']
        uid = payload['uid']
        id = payload['chid']

        uname = await getUserName(uid)
        unick = await getUserNickname(uid, chat_id)

        name = await getUserName(id)
        nick = await getUserNickname(id, chat_id)

        u = AccessLevel.get(uid=uid, chat_id=chat_id)
        u.access_level = 0
        u.save()
        u = AccessLevel.get_or_create(uid=id, chat_id=chat_id)[0]
        u.access_level = 7
        u.save()

        GPool.delete().where(GPool.chat_id == chat_id).execute()
        ChatGroups.delete().where(ChatGroups.chat_id == chat_id).execute()

        await editMessage(messages.giveowner(uid, unick, uname, id, nick, name), peer_id,
                          message.conversation_message_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['mtop']))
async def mtop(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'mtop' and sender == uid:
        members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        members = [int(i.member_id) for i in members.items]

        res = Messages.select().where(Messages.uid > 0, Messages.messages > 0, Messages.uid << members,
                                      Messages.chat_id == chat_id).order_by(Messages.messages.desc()).limit(10)
        ids = [i.uid for i in res]

        names = await API.users.get(user_ids=ids)

        kb = keyboard.mtop(chat_id, uid)
        msg = messages.mtop(res, names)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['top_lvls']))
async def top_lvls(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'top_lvls' and sender == uid:
        top = await getXPTop('lvl', 10)
        names = await API.users.get(user_ids=[int(x) for x in list(top.keys())])

        msg = messages.top_lvls(names, top)
        kb = keyboard.top_lvls(chat_id, uid)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['top_lvls_in_group']))
async def top_lvls_in_group(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'top_lvls_in_group' and sender == uid:
        members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        members = members.items
        all_members = [i.member_id for i in members]
        top = await getXPTop('lvl', 10, all_members)

        names = await API.users.get(user_ids=[int(x) for x in list(top.keys())])

        msg = messages.top_lvls(names, top, 'в беседе')
        kb = keyboard.top_lvls_in_group(chat_id, uid)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['top_duels']))
async def top_duels(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'top_duels' and sender == uid:
        lvln = {i.uid: i.wins for i in DuelWins.select().order_by(DuelWins.wins.desc()) if int(i.uid) > 0}
        lvln = dict(list(lvln.items())[:10])

        names = await API.users.get(user_ids=[int(x) for x in list(lvln.keys())])

        msg = messages.top_duels(names, lvln)
        kb = keyboard.top_duels(chat_id, uid)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['top_duels_in_group']))
async def top_duels_in_group(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'top_duels_in_group' and sender == uid:
        members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        members = members.items
        all_members = [i.member_id for i in members]
        lvln = {i.uid: i.wins for i in DuelWins.select().order_by(DuelWins.wins.desc()) if
                int(i.uid) > 0 and int(i.uid) in all_members}
        lvln = dict(list(lvln.items())[:10])

        names = await API.users.get(user_ids=[int(x) for x in list(lvln.keys())])

        msg = messages.top_duels(names, lvln, 'в беседе')
        kb = keyboard.top_duels_in_group(chat_id, uid)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['resetnick_accept']))
async def resetnick_accept(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'resetnick_accept' and sender == uid:
        Nickname.delete().where(Nickname.chat_id == chat_id).execute()
        name = await getUserName(uid)
        msg = messages.resetnick_accept(uid, name)
        await editMessage(msg, peer_id, message.conversation_message_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['resetnick_disaccept']))
async def resetnick_disaccept(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id

    if cmd == 'resetnick_disaccept' and sender == uid:
        msg = messages.resetnick_disaccept()
        await editMessage(msg, peer_id, message.conversation_message_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['resetaccess_accept']))
async def resetaccess_accept(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'resetaccess_accept' and sender == uid:
        lvl = payload['lvl']
        AccessLevel.delete().where(AccessLevel.access_level == lvl, AccessLevel.chat_id == chat_id).execute()

        name = await getUserName(uid)

        msg = messages.resetaccess_accept(uid, name, lvl)
        await editMessage(msg, peer_id, message.conversation_message_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['resetaccess_disaccept']))
async def resetaccess_disaccept(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id

    if cmd == 'resetaccess_disaccept' and sender == uid:
        lvl = payload['lvl']
        msg = messages.resetaccess_disaccept(lvl)
        await editMessage(msg, peer_id, message.conversation_message_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['kick_nonick']))
async def kick_nonick(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'kick_nonick' and sender == uid:
        nick = await getUserNickname(uid, chat_id)
        uname = await getUserName(uid)

        res = Nickname.select().where(Nickname.uid > 0, Nickname.chat_id == chat_id, Nickname.nickname.is_null(False))
        nickmembers = [i.uid for i in res]
        members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        members = members.items
        members_uid = [i.member_id for i in members if i.member_id not in nickmembers and i.member_id > 0]

        kicked = 0
        for i in members_uid:
            kicked += await kickUser(i, chat_id)

        msg = messages.kickmenu_kick_nonick(uid, uname, nick, kicked)
        await API.messages.send(random_id=0, message=msg, chat_id=chat_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['kick_nick']))
async def kick_nick(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'kick_nick' and sender == uid:
        nick = await getUserNickname(uid, chat_id)
        uname = await getUserName(uid)

        kicked = 0
        for i in Nickname.select().where(Nickname.nickname.is_null(False), Nickname.chat_id == chat_id,
                                         Nickname.uid > 0):
            kicked += await kickUser(i.uid, chat_id)

        msg = messages.kickmenu_kick_nick(uid, uname, nick, kicked)
        await API.messages.send(random_id=0, message=msg, chat_id=chat_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['kick_banned']))
async def kick_banned(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'kick_banned' and sender == uid:
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

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notif']))
async def notif(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'notif' and sender == uid:
        notifs = Notifs.select().where(Notifs.chat_id == chat_id).order_by(Notifs.name.desc())
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

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notif_select']))
async def notif_select(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'notif_select' and sender == uid:
        name = payload['name']
        notif = Notifs.get(Notifs.chat_id == chat_id, Notifs.name == name)
        TypeQueue.delete().where(TypeQueue.uid == uid, TypeQueue.chat_id == chat_id).execute()
        msg = messages.notification(notif.name, notif.text, notif.time, notif.every, notif.tag, notif.status)
        kb = keyboard.notification(uid, notif.status, notif.name)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_status']))
async def notification_status(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'notification_status' and sender == uid:
        turn_to = payload['turn']
        name = payload['name']
        snotif = Notifs.get(Notifs.name == name, Notifs.chat_id == chat_id)
        st = time.time() + snotif.every
        snotif.status = turn_to
        snotif.time = st
        snotif.save()
        msg = messages.notification(name, snotif.text, st, snotif.every, snotif.tag, turn_to)
        kb = keyboard.notification(uid, turn_to, name)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_text']))
async def notification_text(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'notification_text' and sender == uid:
        name = payload['name']
        TypeQueue.create(uid=uid, chat_id=chat_id, type='notification_text',
                         additional='{' + f'"name": "{name}", "cmid": "{message.conversation_message_id}"' + '}')
        msg = messages.notification_changing_text()
        await editMessage(msg, peer_id, message.conversation_message_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_time']))
async def notification_time(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.object.peer_id

    if cmd == 'notification_time' and sender == uid:
        name = payload['name']
        msg = messages.notification_changing_time_choose()
        kb = keyboard.notification_time(uid, name)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_time_change']))
async def notification_time_change(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'notification_time_change' and sender == uid:
        name = payload['name']
        ctype = payload['type']
        if ctype == 'single':
            msg = messages.notification_changing_time_single()
        elif ctype == 'everyday':
            msg = messages.notification_changing_time_everyday()
        else:
            msg = messages.notification_changing_time_everyxmin()

        TypeQueue.create(
            uid=uid, chat_id=chat_id, type='notification_time_change',
            additional='{' + f'"name": "{name}", "cmid": "{message.conversation_message_id}", "type": "{ctype}"' + '}'
        )

        await editMessage(msg, peer_id, message.conversation_message_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_tag']))
async def notification_tag(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.object.peer_id

    if cmd == 'notification_tag' and sender == uid:
        name = payload['name']
        msg = messages.notification_changing_tag_choose()
        kb = keyboard.notification_tag(uid, name)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_tag_change']))
async def notification_tag_change(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'notification_tag_change' and sender == uid:
        name = payload['name']
        ctype = payload['type']
        notif = Notifs.get(Notifs.name == name, Notifs.chat_id == chat_id)
        notif.tag = ctype
        notif.save()

        msg = messages.notification(name, notif.text, notif.time, notif.every, notif.tag, notif.status)
        kb = keyboard.notification(uid, notif.status, name)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_delete']))
async def notification_delete(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'notification_delete' and sender == uid:
        name = payload['name']
        Notifs.get(Notifs.chat_id == chat_id, Notifs.name == name).delete_instance()
        msg = messages.notification_delete(name)
        await editMessage(msg, peer_id, message.conversation_message_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['listasync']))
async def listasync(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.object.peer_id

    if cmd == 'listasync' and sender == uid:
        page = payload['page']

        chat_ids = [i.chat_id for i in GPool.select().where(GPool.uid == uid).iterator()]
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

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['help']))
async def help(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'help' and sender == uid:
        page = payload['page']
        prem = payload['prem']
        cmds = CMDLevels.select().where(CMDLevels.chat_id == chat_id)
        base = COMMANDS.copy()
        for i in cmds:
            try:
                base[i.cmd] = int(i.lvl)
            except:
                pass
        msg = messages.help(page, base)
        kb = keyboard.help(uid, page, prem)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['warn_report']))
async def warn_report(message: MessageEvent):
    payload = message.payload

    cmd = payload['cmd']
    id = message.user_id
    peer_id = message.peer_id

    if cmd == 'warn_report' and id in DEVS:
        uid = payload['uid']
        uws = ReportWarns.get_or_create(uid=uid, defaults={'warns': 0})[0]
        uws.warns += 1
        uws.save()

        kb = keyboard.warn_report(uid, uws.warns)
        if uws.warns < 3:
            msg = messages.warn_report(id, await getUserName(id), uws.warns, uid, await getUserName(uid))
            await API.messages.send(message=msg, peer_id=peer_id, keyboard=kb,
                                    random_id=0)
        else:
            msg = messages.warn_report_ban(id, await getUserName(id), uid, await getUserName(uid))
            await API.messages.send(message=msg, peer_id=peer_id, keyboard=kb,
                                    random_id=0)

    await sendMessageEventAnswer(message.event_id, id, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['unwarn_report']))
async def unwarn_report(message: MessageEvent):
    payload = message.payload

    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.peer_id

    if cmd == 'unwarn_report' and uid in DEVS:
        uwarns = payload['warns']
        id = payload['uid']
        uws = ReportWarns.get_or_none(uid=id)
        if uws is not None:
            uwarns = uws.warns - uwarns
            if uwarns < 0:
                uwarns = 0
            uws.warns = uwarns
            uws.save()
        else:
            uwarns = 0

        kb = keyboard.warn_report(id, uwarns)
        if uwarns < 3:
            msg = messages.unwarn_report(id, await getUserName(id), uwarns, uid, await getUserName(uid))
            await API.messages.send(message=msg, peer_id=peer_id, keyboard=kb,
                                    random_id=0)
        else:
            msg = messages.warn_report_ban(id, await getUserName(id), uid, await getUserName(uid))
            await API.messages.send(message=msg, peer_id=peer_id, keyboard=kb,
                                    random_id=0)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['cmdlist']))
async def cmdlist(message: MessageEvent):
    payload = message.payload

    cmd = payload['cmd']
    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    page = payload['page']
    uid = message.user_id
    peer_id = message.peer_id

    if cmd == 'cmdlist' and sender == uid:
        cmdnames = {}

        for i in CMDNames.select().where(CMDNames.uid == uid).iterator():
            cmdnames[i.cmd] = i.name

        msg = messages.cmdlist(dict(list(cmdnames.items())[page * 10: (page * 10) + 10]), page, len(list(cmdnames)))
        kb = keyboard.cmdlist(uid, page, len(cmdnames))
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['task']))
async def task(message: MessageEvent):
    payload = message.payload

    cmd = payload['cmd']
    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    uid = message.user_id
    peer_id = message.peer_id

    if cmd == 'task' and sender == uid:
        completed = 0
        prem = await getUserPremium(uid)
        t = TasksDaily.select().where(TasksDaily.uid == uid)
        for i in t:
            if i.count >= (TASKS_DAILY | PREMIUM_TASKS_DAILY)[i.task]:
                if i.task in PREMIUM_TASKS_DAILY and not prem:
                    continue
                completed += 1
        c = Coins.get_or_none(Coins.uid == uid)
        c = c.coins if c is not None else 0
        s = TasksStreak.get_or_none(TasksStreak.uid == uid)
        s = s.streak if s is not None else 0
        kb = keyboard.tasks(uid)
        msg = messages.task(completed, c, s)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['task_trade']))
async def task_trade(message: MessageEvent):
    payload = message.payload

    cmd = payload['cmd']
    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    uid = message.user_id
    peer_id = message.peer_id

    if cmd == 'task_trade' and sender == uid:
        c = Coins.get_or_none(Coins.uid == uid)
        c = c.coins if c is not None else 0
        msg = messages.task_trade(c)
        kb = keyboard.task_trade(uid, c)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['task_trade_lot']))
async def task_trade_lot(message: MessageEvent):
    payload = message.payload

    cmd = payload['cmd']
    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    lot = payload['lot']
    uid = message.user_id
    peer_id = message.peer_id

    if cmd == 'task_trade_lot' and sender == uid:
        c = Coins.get_or_none(Coins.uid == uid)
        cc = c.coins if c is not None else 0
        cost = list(TASKS_LOTS.keys())[lot - 1]
        if cc < cost:
            msg = messages.task_trade_not_enough(cost - cc)
            kb = keyboard.task_back(uid)
            await editMessage(msg, peer_id, message.conversation_message_id, kb)
            return
        c.coins -= cost
        c.save()
        if lot < 4:
            x = XP.get(XP.uid == uid)
            x.xp += TASKS_LOTS[cost] * 200
            x.save()
        else:
            p = Premium.get_or_create(uid=uid, defaults={'time': 0})[0]
            if p.time < datetime.now().timestamp():
                p.time = datetime.now().timestamp() + (TASKS_LOTS[cost] * 86400)
            else:
                p.time += TASKS_LOTS[cost] * 86400
            p.save()

        msg = messages.task_trade_lot_log(lot, uid, await getUserName(uid))
        await API.messages.send(peer_id=2000020672, random_id=0, message='#task' + msg)

        msg = messages.task_trade_lot(lot)
        kb = keyboard.task_back(uid)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['task_weekly']))
async def task_weekly(message: MessageEvent):
    payload = message.payload

    cmd = payload['cmd']
    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    uid = message.user_id
    peer_id = message.peer_id

    if cmd == 'task_weekly' and sender == uid:
        prem = await getUserPremium(uid)
        bonus = TasksWeekly.get_or_none(TasksWeekly.uid == uid, TasksWeekly.task == 'bonus')
        bonus = bonus.count if bonus is not None else 0
        dailytask = TasksWeekly.get_or_none(TasksWeekly.uid == uid, TasksWeekly.task == 'dailytask')
        dailytask = dailytask.count if dailytask is not None else 0
        sendmsgs = TasksWeekly.get_or_none(TasksWeekly.uid == uid, TasksWeekly.task == 'sendmsgs')
        sendmsgs = sendmsgs.count if sendmsgs is not None else 0
        lvlup = TasksWeekly.get_or_none(TasksWeekly.uid == uid, TasksWeekly.task == 'lvlup')
        lvlup = lvlup.count if lvlup is not None else 0
        duelwin = TasksWeekly.get_or_none(TasksWeekly.uid == uid, TasksWeekly.task == 'duelwin')
        duelwin = duelwin.count if duelwin is not None else 0
        msg = messages.task_weekly(prem, [bonus, dailytask, sendmsgs, lvlup, duelwin])
        kb = keyboard.task_back(uid)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['task_daily']))
async def task_daily(message: MessageEvent):
    payload = message.payload

    cmd = payload['cmd']
    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    uid = message.user_id
    peer_id = message.peer_id

    if cmd == 'task_daily' and sender == uid:
        prem = await getUserPremium(uid)
        sendmsgs = TasksDaily.get_or_none(TasksDaily.uid == uid, TasksDaily.task == 'sendmsgs')
        sendmsgs = sendmsgs.count if sendmsgs is not None else 0
        sendvoice = TasksDaily.get_or_none(TasksDaily.uid == uid, TasksDaily.task == 'sendvoice')
        sendvoice = sendvoice.count if sendvoice is not None else 0
        duelwin = TasksDaily.get_or_none(TasksDaily.uid == uid, TasksDaily.task == 'duelwin')
        duelwin = duelwin.count if duelwin is not None else 0
        cmds = TasksDaily.get_or_none(TasksDaily.uid == uid, TasksDaily.task == 'cmds')
        cmds = cmds.count if cmds is not None else 0
        stickers = TasksDaily.get_or_none(TasksDaily.uid == uid, TasksDaily.task == 'stickers')
        stickers = stickers.count if stickers is not None else 0
        msg = messages.task_daily(prem, [sendmsgs, sendvoice, duelwin, cmds, stickers])
        kb = keyboard.task_back(uid)
        await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['test']))
async def test(message: MessageEvent):
    uid = message.user_id
    await sendMessageEventAnswer(message.event_id, uid, message.peer_id,
                                 json.dumps({'type': 'show_snackbar', 'text': 'test'}))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['check']))
async def check(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'check' and sender == uid:
        id = payload['id']
        check = payload['check']
        if check == 'ban':
            res = Ban.get_or_none(Ban.chat_id == chat_id, Ban.uid == id)
            if res is not None:
                u_bans_causes = literal_eval(res.last_bans_causes)[::-1]
                u_bans_names = literal_eval(res.last_bans_names)[::-1]
                u_bans_dates = literal_eval(res.last_bans_dates)[::-1]
                u_bans_times = literal_eval(res.last_bans_times)[::-1]
                ban_date = u_bans_dates[0]
                ban_from = u_bans_names[0]
                ban_reason = u_bans_causes[0]
                ban_time = u_bans_times[0]
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
            res = Mute.get_or_none(Mute.chat_id == chat_id, Mute.uid == id)
            if res is not None:
                u_mutes_causes = literal_eval(res.last_mutes_causes)[::-1]
                u_mutes_names = literal_eval(res.last_mutes_names)[::-1]
                u_mutes_dates = literal_eval(res.last_mutes_dates)[::-1]
                u_mutes_times = literal_eval(res.last_mutes_times)[::-1]
                mute_date = u_mutes_dates[0]
                mute_from = u_mutes_names[0]
                mute_reason = u_mutes_causes[0]
                mute_time = u_mutes_times[0]
            else:
                u_mutes_names = []
                mute_date = mute_from = mute_reason = mute_time = None
            mute = await getUserMute(id, chat_id)
            if mute:
                mute -= time.time()
            name = await getUserName(id)
            nickname = await getUserNickname(id, chat_id)
            msg = messages.check_mute(id, name, nickname, mute, u_mutes_names, mute_date,
                                      mute_from, mute_reason, mute_time)
            kb = keyboard.check_history(sender, id, 'mute', len(u_mutes_names))
            await editMessage(msg, peer_id, message.conversation_message_id, kb)
        if check == 'warn':
            res = Warn.get_or_none(Warn.chat_id == chat_id, Warn.uid == id)
            if res is not None:
                u_warns_causes = literal_eval(res.last_warns_causes)[::-1]
                u_warns_names = literal_eval(res.last_warns_names)[::-1]
                u_warns_dates = literal_eval(res.last_warns_dates)[::-1]
            else:
                u_warns_names = u_warns_causes = u_warns_dates = []
            warn = await getUserWarns(id, chat_id)
            name = await getUserName(id)
            nickname = await getUserNickname(id, chat_id)
            msg = messages.check_warn(id, name, nickname, warn, u_warns_names,
                                      u_warns_dates, u_warns_names, u_warns_causes)
            kb = keyboard.check_history(sender, id, 'warn', len(u_warns_causes))
            await editMessage(msg, peer_id, message.conversation_message_id, kb)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['check_menu']))
async def check_menu(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'check_menu' and sender == uid:
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

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['check_history']))
async def check_history(message: MessageEvent):
    payload = message.payload

    try:
        sender = payload['uid']
    except:
        sender = message.user_id
    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'check_history' and sender == uid:
        id = payload['id']
        check = payload['check']
        if not int(payload['ie']):
            await sendMessageEventAnswer(message.event_id, uid, message.peer_id,
                                         json.dumps({'type': 'show_snackbar', 'text': 'Нету истории'}))
            return
        if check == 'ban':
            res = Ban.get_or_none(Ban.chat_id == chat_id, Ban.uid == id)
            if res is not None:
                bans_causes = literal_eval(res.last_bans_causes)[::-1][:50]
                bans_names = literal_eval(res.last_bans_names)[::-1][:50]
                bans_dates = literal_eval(res.last_bans_dates)[::-1][:50]
                bans_times = literal_eval(res.last_bans_times)[::-1][:50]
            else:
                bans_causes = bans_names = bans_dates = bans_times = []
            name = await getUserName(id)
            nickname = await getUserNickname(id, chat_id)
            msg = messages.check_history_ban(id, name, nickname, bans_dates, bans_names, bans_times, bans_causes)
            await editMessage(msg, peer_id, message.conversation_message_id)
        if check == 'mute':
            res = Mute.get_or_none(Mute.chat_id == chat_id, Mute.uid == id)
            if res is not None:
                mutes_causes = literal_eval(res.last_mutes_causes)[::-1][:50]
                mutes_names = literal_eval(res.last_mutes_names)[::-1][:50]
                mutes_dates = literal_eval(res.last_mutes_dates)[::-1][:50]
                mutes_times = literal_eval(res.last_mutes_times)[::-1][:50]
            else:
                mutes_causes = mutes_names = mutes_dates = mutes_times = []
            name = await getUserName(id)
            nickname = await getUserNickname(id, chat_id)
            msg = messages.check_history_mute(id, name, nickname, mutes_dates, mutes_names, mutes_times, mutes_causes)
            await editMessage(msg, peer_id, message.conversation_message_id)
        if check == 'warn':
            res = Warn.get_or_none(Warn.chat_id == chat_id, Warn.uid == id)
            if res is not None:
                warns_causes = literal_eval(res.last_warns_causes)[::-1][:50]
                warns_names = literal_eval(res.last_warns_names)[::-1][:50]
                warns_dates = literal_eval(res.last_warns_dates)[::-1][:50]
                warns_times = literal_eval(res.last_warns_times)[::-1][:50]
            else:
                warns_causes = warns_names = warns_dates = warns_times = []
            name = await getUserName(id)
            nickname = await getUserNickname(id, chat_id)
            msg = messages.check_history_warn(id, name, nickname, warns_dates, warns_names, warns_times, warns_causes)
            await editMessage(msg, peer_id, message.conversation_message_id)

    await sendMessageEventAnswer(message.event_id, uid, message.peer_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['unmute', 'unwarn', 'unban']))
async def check_history(message: MessageEvent):
    payload = message.payload

    cmd = payload['cmd']
    uid = message.user_id

    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd in ('unmute', 'unwarn', 'unban'):
        id = payload['id']
        cmid = payload['cmid']
        u_acc = await getUserAccessLevel(uid, chat_id)
        if u_acc <= await getUserAccessLevel(id, chat_id) or not await haveAccess(cmd[2:], chat_id, u_acc):
            await message.show_snackbar("⛔️ У вас недостаточно прав.")
            await sendMessageEventAnswer(message.event_id, uid, message.peer_id)
            return
        await sendMessageEventAnswer(message.event_id, uid, message.peer_id)
        name = await getUserName(id)
        nickname = await getUserNickname(id, chat_id)
        uname = await getUserName(uid)
        unickname = await getUserNickname(uid, chat_id)
        if cmd == 'unmute':
            res = Mute.get(Mute.chat_id == chat_id, Mute.uid == id)
            if res.mute < time.time():
                return
            res.mute = 0
            await setChatMute(id, chat_id, 0)
            msg = messages.unmute(uname, unickname, uid, name, nickname, id)
        elif cmd == 'unwarn':
            res = Warn.get(Warn.chat_id == chat_id, Warn.uid == id)
            if res.warns <= 0 or res.warns >= 3:
                return
            res.warns -= 1
            msg = messages.unwarn(uname, unickname, uid, name, nickname, id)
        elif cmd == 'unban':
            res = Ban.get(Ban.chat_id == chat_id, Ban.uid == id)
            if res.ban < time.time():
                return
            res.ban = 0
            msg = messages.unban(uname, unickname, uid, name, nickname, id)
        else:
            return
        res.save()
        await editMessage(msg, peer_id, message.conversation_message_id)
        await deleteMessages(cmid, chat_id)
