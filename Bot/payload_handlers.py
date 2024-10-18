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
from Bot.tgbot import getTGBot
from Bot.utils import sendMessageEventAnswer, editMessage, getUserAccessLevel, getUserXP, getUserPremium, addUserXP, \
    getUserName, getUserNickname, kickUser, getXPTop, getChatName, addWeeklyTask, \
    addDailyTask, getUserBan, getUserWarns, getUserMute, getULvlBanned, getChatSettings, turnChatSetting, \
    deleteMessages, setChatMute, getChatAltSettings, getChatMembers, getChatOwner
from config.config import API, COMMANDS, DEVS, TASKS_LOTS, TASKS_DAILY, PREMIUM_TASKS_DAILY, SETTINGS_COUNTABLE, \
    TG_CHAT_ID, TG_NEWCHAT_THREAD_ID, SETTINGS_PREMIUM
from db import AccessLevel, JoinedDate, DuelWins, ReportAnswers, Nickname, Mute, Warn, Ban, Premium, \
    GPool, ChatGroups, Messages, Notifs, TypeQueue, CMDLevels, ReportWarns, CMDNames, Coins, XP, TasksWeekly, \
    TasksDaily, TasksStreak, Settings, AntispamURLExceptions, Welcome, Prefixes

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
        if s := AccessLevel.get_or_none(AccessLevel.access_level == 7, AccessLevel.chat_id == chat_id):
            if s.uid != bp:
                return

        AccessLevel.delete().where(AccessLevel.chat_id == chat_id).execute()

        ac = AccessLevel.get_or_create(uid=bp, chat_id=chat_id)[0]
        ac.access_level = 7
        ac.save()

        chtime = JoinedDate.get_or_create(chat_id=chat_id)[0]
        chtime.time = time.time()
        chtime.save()

        try:
            bot = getTGBot()
            await bot.send_message(chat_id=TG_CHAT_ID, message_thread_id=TG_NEWCHAT_THREAD_ID,
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


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['duel'], checksender=False))
async def duel(message: MessageEvent):
    payload = message.payload
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
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

    msg = messages.duel_res(winid, uname, unick, loseid, name, nick, xtw, u_premium)
    await editMessage(msg, peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['answer_report']))
async def answer_report(message: MessageEvent):
    payload = message.payload
    peer_id = message.object.peer_id
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
            chatsetting = Settings.get_or_none(Settings.chat_id == chat_id, Settings.setting == setting)
            value = None if chatsetting is None else chatsetting.value
            value2 = None if chatsetting is None else chatsetting.value2
            punishment = None if chatsetting is None else chatsetting.punishment
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
            w = Welcome.get_or_none(Welcome.chat_id == chat_id)
            if w is None:
                msg = messages.settings_countable_action(action, setting)
                kb = keyboard.settings_set_welcome(uid, None, None, None)
            else:
                msg = messages.settings_countable_action(action, setting, w.msg, w.photo, w.url)
                kb = keyboard.settings_set_welcome(uid, w.msg, w.photo, w.url)
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
        msg = messages.settings_exceptionlist(AntispamURLExceptions.select().where(
            AntispamURLExceptions.chat_id == chat_id))
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
    TypeQueue.create(
        uid=uid, chat_id=chat_id, type='settings_listaction',
        additional='{' + f'"setting": "{setting}", "action": "{action}", "type": "{type}"' + '}'
    )
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

    TypeQueue.create(uid=uid, chat_id=chat_id, type=cmd, additional='{}')
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

    welcome = Welcome.get(Welcome.chat_id == chat_id)
    text = welcome.msg
    img = welcome.photo
    url = welcome.url
    if (cmd in ['settings_unset_welcome_text', 'settings_unset_welcome_photo'] and
            not ((text and ((img and url) or (not img and not url) or not url)) or
                 (img and ((text and url) or (not text and not url) or not url)))):
        return
    if cmd == 'settings_unset_welcome_text':
        welcome.msg = None
    if cmd == 'settings_unset_welcome_photo':
        welcome.photo = None
    if cmd == 'settings_unset_welcome_url':
        welcome.url = None
    welcome.save()

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
    res = Nickname.select().where(Nickname.uid > 0, Nickname.uid << members_uid, Nickname.chat_id == chat_id,
                                  Nickname.nickname.is_null(False)).order_by(Nickname.nickname)
    count = len(res)
    res = res[:30]
    names = await API.users.get(user_ids=[f'{i.uid}' for i in res])
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
    res = Nickname.select().where(Nickname.uid > 0, Nickname.uid << members_uid,
                                  Nickname.chat_id == chat_id, Nickname.nickname.is_null(False)
                                  ).order_by(Nickname.nickname).offset(30 * page)
    if not (count := len(res)):
        return
    res = res[:30]
    names = await API.users.get(user_ids=[i.uid for i in res])
    msg = messages.nlist(res, names, page)
    kb = keyboard.nlist(uid, page, count)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['nonicklist']))
async def nonicklist(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    res = Nickname.select().where(Nickname.uid > 0, Nickname.chat_id == chat_id, Nickname.nickname.is_null(False))
    nickmembers = [i.uid for i in res]
    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = members.items
    members_uid = [i.member_id for i in members if i.member_id not in nickmembers]
    count = len(members_uid)
    members_uid = members_uid[:30]
    names = await API.users.get(user_ids=[f'{i}' for i in members_uid])

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

    res = Nickname.select().where(Nickname.uid > 0, Nickname.chat_id == chat_id)
    nickmembers = [i.uid for i in res]
    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members_count = len(members.items[page * 30:])
    members = [i for i in members.items if i.member_id not in nickmembers][page * 30: page * 30 + 30]
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

    res = Mute.select().where(Mute.mute > int(time.time()), Mute.chat_id == chat_id)
    if len(res) <= 0:
        return
    muted_count = len(res)
    res = res.offset(page * 30).limit(30)
    names = await API.users.get(user_ids=[i.uid for i in res])
    msg = await messages.mutelist(res, names, muted_count)
    kb = keyboard.mutelist(uid, page, muted_count)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
              SearchPayloadCMD(['prev_page_warnlist', 'next_page_warnlist']))
async def page_warnlist(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    page = payload['page']

    res = Warn.select().where(Warn.warns > 0, Warn.chat_id == chat_id)
    if not (count := len(res)):
        return
    res = res.offset(page * 30).limit(30)
    names = await API.users.get(user_ids=[i.uid for i in res])
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
    res = Ban.select().where(Ban.ban > int(time.time()), Ban.chat_id == chat_id)
    if len(res) <= 0:
        return
    banned_count = len(res)
    res = res.offset(page * 30).limit(30)
    names = await API.users.get(user_ids=[i.uid for i in res])
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
    premium_pool = Premium.select().where(Premium.time >= time.time())
    if len(premium_pool) <= 0:
        return
    names = await API.users.get(user_ids=[i.uid for i in premium_pool])
    msg = messages.statuslist(names, premium_pool)
    kb = keyboard.statuslist(uid, 0, len(names))
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

    u = AccessLevel.get(uid=uid, chat_id=chat_id)
    u.access_level = 0
    u.save()
    AccessLevel.update(access_level=0).where(AccessLevel.chat_id == chat_id,
                                             AccessLevel.access_level == 7).execute()
    u = AccessLevel.get_or_create(uid=id, chat_id=chat_id)[0]
    u.access_level = 7
    u.save()

    GPool.delete().where(GPool.chat_id == chat_id).execute()
    ChatGroups.delete().where(ChatGroups.chat_id == chat_id).execute()

    await editMessage(messages.giveowner(uid, unick, uname, id, nick, name), peer_id,
                      message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['mtop']))
async def mtop(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    members = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
    members = [int(i.member_id) for i in members.items]

    res = Messages.select().where(Messages.uid > 0, Messages.messages > 0, Messages.uid << members,
                                  Messages.chat_id == chat_id).order_by(Messages.messages.desc()).limit(10)
    ids = [i.uid for i in res]

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

    lvln = {i.uid: i.wins for i in DuelWins.select().order_by(DuelWins.wins.desc()) if int(i.uid) > 0}
    lvln = dict(list(lvln.items())[:10])

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
    lvln = {i.uid: i.wins for i in DuelWins.select().order_by(DuelWins.wins.desc()) if
            int(i.uid) > 0 and int(i.uid) in all_members}
    lvln = dict(list(lvln.items())[:10])

    names = await API.users.get(user_ids=[int(x) for x in list(lvln.keys())])

    msg = messages.top_duels(names, lvln, 'в беседе')
    kb = keyboard.top_duels_in_group(chat_id, uid)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['resetnick_accept']))
async def resetnick_accept(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    Nickname.delete().where(Nickname.chat_id == chat_id).execute()
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

    AccessLevel.delete().where(AccessLevel.access_level == lvl, AccessLevel.chat_id == chat_id).execute()

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


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['kick_nick']))
async def kick_nick(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    nick = await getUserNickname(uid, chat_id)
    uname = await getUserName(uid)

    kicked = 0
    for i in Nickname.select().where(Nickname.nickname.is_null(False), Nickname.chat_id == chat_id,
                                     Nickname.uid > 0):
        kicked += await kickUser(i.uid, chat_id)

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


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notif_select']))
async def notif_select(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    name = payload['name']

    notif = Notifs.get(Notifs.chat_id == chat_id, Notifs.name == name)
    TypeQueue.delete().where(TypeQueue.uid == uid, TypeQueue.chat_id == chat_id).execute()
    msg = messages.notification(notif.name, notif.text, notif.time, notif.every, notif.tag, notif.status)
    kb = keyboard.notification(uid, notif.status, notif.name)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_status']))
async def notification_status(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
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


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_text']))
async def notification_text(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    name = payload['name']

    TypeQueue.create(uid=uid, chat_id=chat_id, type='notification_text',
                     additional='{' + f'"name": "{name}", "cmid": "{message.conversation_message_id}"' + '}')
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

    TypeQueue.create(
        uid=uid, chat_id=chat_id, type='notification_time_change',
        additional='{' + f'"name": "{name}", "cmid": "{message.conversation_message_id}", "type": "{ctype}"' + '}'
    )

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

    notif = Notifs.get(Notifs.name == name, Notifs.chat_id == chat_id)
    notif.tag = ctype
    notif.save()

    msg = messages.notification(name, notif.text, notif.time, notif.every, notif.tag, notif.status)
    kb = keyboard.notification(uid, notif.status, name)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_delete']))
async def notification_delete(message: MessageEvent):
    payload = message.payload
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    name = payload['name']

    Notifs.get(Notifs.chat_id == chat_id, Notifs.name == name).delete_instance()
    msg = messages.notification_delete(name)
    await editMessage(msg, peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['listasync']))
async def listasync(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
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


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['help']))
async def help(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
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


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['warn_report'], checksender=False))
async def warn_report(message: MessageEvent):
    payload = message.payload
    id = message.user_id
    peer_id = message.peer_id

    if id not in DEVS:
        return
    uid = payload['uid']
    uws = ReportWarns.get_or_create(uid=uid, defaults={'warns': 0})[0]
    uws.warns += 1
    uws.save()

    kb = keyboard.warn_report(uid, uws.warns)
    if uws.warns < 3:
        msg = messages.warn_report(id, await getUserName(id), uws.warns, uid, await getUserName(uid))
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

    cmdnames = {}
    for i in CMDNames.select().where(CMDNames.uid == uid).iterator():
        cmdnames[i.cmd] = i.name

    msg = messages.cmdlist(dict(list(cmdnames.items())[page * 10: (page * 10) + 10]), page, len(list(cmdnames)))
    kb = keyboard.cmdlist(uid, page, len(cmdnames))
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['task']))
async def task(message: MessageEvent):
    uid = message.user_id
    peer_id = message.peer_id

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


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['task_trade']))
async def task_trade(message: MessageEvent):
    uid = message.user_id
    peer_id = message.peer_id

    c = Coins.get_or_none(Coins.uid == uid)
    c = c.coins if c is not None else 0
    msg = messages.task_trade(c)
    kb = keyboard.task_trade(uid, c)
    await editMessage(msg, peer_id, message.conversation_message_id, kb)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['task_trade_lot']))
async def task_trade_lot(message: MessageEvent):
    payload = message.payload
    lot = payload['lot']
    uid = message.user_id
    peer_id = message.peer_id

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


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['task_weekly']))
async def task_weekly(message: MessageEvent):
    uid = message.user_id
    peer_id = message.peer_id
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


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['task_daily']))
async def task_daily(message: MessageEvent):
    uid = message.user_id
    peer_id = message.peer_id
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


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['check']))
async def check(message: MessageEvent):
    payload = message.payload
    sender = payload['uid'] if 'uid' in payload else message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
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


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, 
              SearchPayloadCMD(['unmute', 'unwarn', 'unban'], checksender=False))
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
    if cmd == 'prefix_add' and len(Prefixes.select().where(Prefixes.uid == uid)) >= 3:
        await editMessage(messages.addprefix_max(), peer_id, message.conversation_message_id, keyboard.prefix_back(uid))
        return
    if cmd in ('prefix_add', 'prefix_del'):
        TypeQueue.create(uid=uid, chat_id=chat_id, type=cmd,
                         additional='{"cmid": ' + str(message.conversation_message_id) + '}')
        await editMessage(messages.get(cmd), peer_id, message.conversation_message_id)
    elif cmd == 'prefix_list':
        await editMessage(messages.listprefix(uid, await getUserName(uid), await getUserNickname(uid, chat_id),
                                              Prefixes.select().where(Prefixes.uid == uid)),
                          peer_id, message.conversation_message_id, keyboard.prefix_back(uid))
    else:
        await editMessage(messages.prefix(), peer_id, message.conversation_message_id, keyboard.prefix(uid))
