import json
import os
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
from Bot.tgbot import tgbot
from Bot.utils import (sendMessageEventAnswer, editMessage, getUserAccessLevel, getUserXP, getUserPremium, addUserXP,
                       getUserName, getUserNickname, kickUser, getXPTop, getChatName, getUserBan, getUserWarns,
                       getUserMute, getULvlBanned, getChatSettings, turnChatSetting, deleteMessages, setChatMute,
                       getChatAltSettings, getChatMembers, getChatOwner, getUserPremmenuSettings, getSilenceAllowed,
                       sendMessage, getSilence, setUserAccessLevel, getGroupName, isMessagesFromGroupAllowed,
                       getImportSettings, turnImportSetting)
from config.config import api, COMMANDS, SETTINGS_COUNTABLE, \
    TG_CHAT_ID, TG_NEWCHAT_THREAD_ID, SETTINGS_PREMIUM, LEAGUE, PREMMENU_DEFAULT
from db import pool

bl = BotLabeler()


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['join', 'rejoin'], checksender=False))
async def join(message: MessageEvent):
    payload = message.payload
    cmd = payload['cmd']
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if cmd == 'join' or (cmd == 'rejoin' and not payload['activate']):
        try:
            members = (await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)).items
        except:
            return await api.messages.send(random_id=0, message=messages.notadmin(), chat_id=chat_id)

        bp = message.user_id
        if (bp not in [i.member_id for i in members if i.is_admin or i.is_owner] and
                await getUserAccessLevel(bp, chat_id) < 7):
            return
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                for i in await (await c.execute(
                        'select uid from mute where chat_id=%s and mute>%s', (chat_id, time.time()))).fetchall():
                    try:
                        await setChatMute(i[0], chat_id, 0)
                    except:
                        pass
                x = await (await c.execute('delete from accesslvl where chat_id=%s returning uid',
                                           (chat_id,))).fetchall()
                await c.execute('insert into accesslvl (uid, chat_id, access_level) values (%s, %s, %s)',
                                (bp, chat_id, 7))
                for id in x:
                    try:
                        await setChatMute(id[0], chat_id, 0)
                    except:
                        pass
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
                await c.execute('insert into botjoineddate (chat_id, time) values (%s, %s)',
                                (chat_id, int(time.time())))
                await conn.commit()

        if cmd == 'join':
            try:
                await tgbot.send_message(chat_id=TG_CHAT_ID, message_thread_id=TG_NEWCHAT_THREAD_ID,
                                         text=f'{chat_id} | {await getChatName(chat_id)} | '
                                              f'{await getChatOwner(chat_id)} | {await getChatMembers(chat_id)} | '
                                              f'{datetime.now().strftime("%H:%M:%S")}',
                                         disable_web_page_preview=True, parse_mode='HTML')
            except:
                pass

        return await editMessage(messages.start(), peer_id, message.conversation_message_id)
    elif cmd == 'rejoin' and payload['activate']:
        if (await getUserAccessLevel(uid, chat_id) >= 7 or
                uid in [i.member_id for i in (await api.messages.get_conversation_members(
                    peer_id=peer_id)).items if i.is_admin or i.is_owner]):
            return await editMessage(messages.rejoin_activate(), peer_id, message.conversation_message_id)


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
        return await message.show_snackbar("У вас недостаточно XP")
    if uxp < duelxp:
        return await message.show_snackbar("У вашего соперника недостаточно XP")

    rid = (id, uid)[int.from_bytes(os.urandom(1)) % 2]
    if rid == id:
        loseid, winid = uid, id
    else:
        loseid, winid = id, uid

    xtw = duelxp
    u_premium = await getUserPremium(winid)
    if not u_premium:
        xtw = int(xtw / 100 * 90)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update duelwins set wins=wins+1 where uid=%s', (winid,))).rowcount:
                await c.execute('insert into duelwins (uid, wins) values (%s, 1)', (winid,))
            await addUserXP(winid, xtw)
            await addUserXP(loseid, -duelxp)
            if await editMessage(messages.duel_res(
                    winid, await getUserName(winid), await getUserNickname(winid, chat_id), loseid,
                    await getUserName(loseid), await getUserNickname(loseid, chat_id), xtw, u_premium), peer_id,
                                 message.conversation_message_id):
                await conn.commit()
                await sendMessageEventAnswer(message.event_id, id, peer_id)
            else:
                await conn.rollback()


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['report_answer'], checksender=False))
async def report_answer(message: MessageEvent):
    payload = message.payload
    repid = int(payload['repid'])

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute(
                'insert into reportanswers (uid, chat_id, repid, answering_id, report_text, cmid, photos) values '
                '(%s, %s, %s, %s, %s, %s, %s)', (
                    int(payload['uid']), int(payload['chat_id']), repid, int(message.user_id), payload['text'],
                    message.conversation_message_id, payload['photos']))
            await conn.commit()
    await editMessage(messages.report_answering(repid), message.object.peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['report_ban'], checksender=False))
async def report_ban(message: MessageEvent):
    payload = message.payload
    repid = int(payload['repid'])
    uid = int(payload['uid'])

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not await (await c.execute('select id from reportban where uid=%s and time=0', (uid,))).fetchone():
                if not (await c.execute('update reportban set time = %s where uid=%s',
                                        (int(time.time() + 86400), uid))).rowcount:
                    await c.execute('insert into reportban (uid, time) values (%s, %s)',
                                    (uid, int(time.time() + 86400)))
                await conn.commit()
    await sendMessage(payload['uid'], messages.report_banned(message.user_id, await getUserName(message.user_id)))
    await editMessage(messages.report_ban(
        message.user_id, await getUserName(message.user_id), repid, payload['uid'], await getUserName(payload['uid']),
        payload['text']),
        message.object.peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['report_delete'], checksender=False))
async def report_delete(message: MessageEvent):
    await sendMessage(message.payload['uid'], messages.report_deleted(message.payload['repid']))
    await deleteMessages(message.conversation_message_id, message.peer_id - 2000000000)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['premmenu']))
async def premmenu(message: MessageEvent):
    uid = message.user_id
    settings = await getUserPremmenuSettings(uid)
    prem = await getUserPremium(uid)
    await editMessage(messages.premmenu(settings, prem), message.peer_id, message.conversation_message_id,
                      keyboard.premmenu(uid, settings, prem))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['premmenu_turn']))
async def premmenu_turn(message: MessageEvent):
    uid = message.user_id
    payload = message.payload
    if payload['setting'] == 'tagnotif' and not (await isMessagesFromGroupAllowed(uid)):
        return await editMessage(messages.tagnotiferror(), message.peer_id, message.conversation_message_id,)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update premmenu set pos = %s where uid=%s and setting=%s',
                                    (int(not bool(payload['pos'])), uid, payload['setting']))).rowcount:
                await c.execute('insert into premmenu (uid, setting, pos) values (%s, %s, %s)',
                                (uid, payload['setting'], int(not PREMMENU_DEFAULT[payload['setting']])))
    prem = await getUserPremium(uid)
    settings = await getUserPremmenuSettings(uid)
    await editMessage(messages.premmenu(settings, prem), message.peer_id, message.conversation_message_id,
                      keyboard.premmenu(uid, settings, prem))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['premmenu_action']))
async def premmenu_action(message: MessageEvent):
    uid = message.user_id
    peer_id = message.peer_id
    setting = message.payload['setting']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if (await c.execute("delete from premmenu where uid=%s and setting=%s and value is not null and value!=''",
                                (uid, setting))).rowcount:
                await conn.commit()
                prem = await getUserPremium(uid)
                settings = await getUserPremmenuSettings(uid)
                return await editMessage(messages.premmenu(settings, prem), peer_id, message.conversation_message_id,
                                         keyboard.premmenu(uid, settings, prem))
            await c.execute(
                'insert into typequeue (chat_id, uid, type, additional) values (%s, %s, %s, %s)',
                (peer_id - 2000000000, uid, f'premmenu_action_{setting}', '{}'))
            await conn.commit()
            await editMessage(messages.premmenu_action(setting), peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['settings_menu']))
async def settings_menu(message: MessageEvent):
    await editMessage(messages.settings(), message.peer_id, message.conversation_message_id,
                      keyboard.settings(message.user_id))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['settings', 'change_setting']))
async def settings(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.peer_id
    chat_id = peer_id - 2000000000
    category = payload['category']

    if payload['cmd'] == 'settings':
        settings = (await getChatSettings(chat_id))[category]
        return await editMessage(messages.settings_category(category, settings), peer_id,
                                 message.conversation_message_id, keyboard.settings_category(uid, category, settings))
    setting = payload['setting']
    if setting in SETTINGS_PREMIUM and not await getUserPremium(uid):
        return await editMessage(messages.no_prem(), peer_id, message.conversation_message_id,
                                 keyboard.settings_goto(uid))
    settings = await getChatSettings(chat_id)
    altsettings = await getChatAltSettings(chat_id)
    if setting not in SETTINGS_COUNTABLE:
        if setting in settings[category]:
            settings[category][setting] = not settings[category][setting]
        else:
            altsettings[category][setting] = not altsettings[category][setting]
        await turnChatSetting(chat_id, category, setting)
        return await editMessage(
            messages.settings_category(category, settings[category]), peer_id,
            message.conversation_message_id, keyboard.settings_category(uid, category, settings[category]))
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            chatsetting = await (await c.execute(
                'select "value", value2, punishment from settings where chat_id=%s and '
                'setting=%s', (chat_id, setting))).fetchone()
    return await editMessage(messages.settings_change_countable(
        chat_id, setting, settings[category][setting], None if chatsetting is None else chatsetting[0],
        None if chatsetting is None else chatsetting[1], altsettings[category][setting] if (
                category in altsettings and setting in altsettings[category]) else None,
        None if chatsetting is None else chatsetting[2]), peer_id, message.conversation_message_id,
        keyboard.settings_change_countable(uid, category, setting, settings, altsettings))


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
                          keyboard.settings_goto(uid))
        return
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('delete from typequeue where chat_id=%s and uid=%s', (chat_id, uid))
            await conn.commit()

    if action in ('turn', 'turnalt'):
        settings = await getChatSettings(chat_id)
        altsettings = await getChatAltSettings(chat_id)
        if action == 'turn':
            settings[category][setting] = not settings[category][setting]
        else:
            altsettings[category][setting] = not altsettings[category][setting]
        await turnChatSetting(chat_id, category, setting, alt=action == 'turnalt')
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                chatsetting = await (await c.execute(
                    'select "value", value2, punishment, pos, pos2 from settings where chat_id=%s and setting=%s',
                    (chat_id, setting))).fetchone()
        return await editMessage(messages.settings_change_countable(
            chat_id, setting, settings[category][setting], None if chatsetting is None else chatsetting[0],
            None if chatsetting is None else chatsetting[1], altsettings[category][setting] if (
                    category in altsettings and setting in altsettings[category]) else None,
            None if chatsetting is None else chatsetting[2]), peer_id, message.conversation_message_id,
            keyboard.settings_change_countable(uid, category, setting, settings, altsettings))
    if action == 'set':
        if setting == 'welcome':
            async with (await pool()).connection() as conn:
                async with conn.cursor() as c:
                    w = await (await c.execute(
                        'select msg, photo, url from welcome where chat_id=%s', (chat_id,))).fetchone()
            if w:
                return await editMessage(messages.settings_countable_action(action, setting, w[0], w[1], w[2]), peer_id,
                                         message.conversation_message_id,
                                         keyboard.settings_set_welcome(uid, w[0], w[1], w[2]))
            return await editMessage(messages.settings_countable_action(action, setting), peer_id,
                                     message.conversation_message_id,
                                     keyboard.settings_set_welcome(uid, None, None, None))
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute(
                    'insert into typequeue (chat_id, uid, type, additional) values (%s, %s, %s, %s)',
                    (chat_id, uid, 'settings_change_countable',
                     '{' + f'"setting": "{setting}", "category": "{category}", '
                           f'"cmid": "{message.conversation_message_id}"' + '}'))
                await conn.commit()
        return await editMessage(messages.settings_countable_action(action, setting), peer_id,
                                 message.conversation_message_id)
    elif action == 'setPunishment':
        return await editMessage(messages.settings_choose_punishment(), peer_id, message.conversation_message_id,
                                 keyboard.settings_set_punishment(uid, category, setting))
    elif action == 'setWhitelist' or action == 'setBlacklist':
        return await editMessage(messages.settings_setlist(setting, action[3:-4]), peer_id,
                                 message.conversation_message_id,
                                 keyboard.settings_setlist(uid, category, setting, action[3:-4]))


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
        return await editMessage(messages.no_prem(), peer_id, message.conversation_message_id,
                                 keyboard.settings_goto(uid))
    if action in ['deletemessage', 'kick']:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute(
                    'update settings set punishment = %s where chat_id=%s and setting=%s', (action, chat_id, setting))
                await conn.commit()
        return await editMessage(messages.settings_set_punishment(action), peer_id, message.conversation_message_id,
                                 keyboard.settings_change_countable(
                                     uid, category, setting, await getChatSettings(chat_id),
                                     await getChatAltSettings(chat_id), True))
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into typequeue (chat_id, uid, type, additional) values (%s, %s, %s, %s)',
                            (chat_id, uid, 'settings_set_punishment', '{' +
                             f'"setting": "{setting}", "action": "{action}", "category": "{category}", '
                             f'"cmid": "{message.conversation_message_id}"' + '}'))
            await conn.commit()
    return await editMessage(messages.settings_set_punishment_input(action), peer_id, message.conversation_message_id,
                             keyboard.settings_change_countable(
                                 uid, category, setting, await getChatSettings(chat_id),
                                 await getChatAltSettings(chat_id), True))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['settings_exceptionlist']))
async def settings_exceptionlist(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.peer_id
    setting = payload['setting']

    if setting in SETTINGS_PREMIUM and not await getUserPremium(uid):
        return await editMessage(messages.no_prem(), peer_id, message.conversation_message_id,
                                 keyboard.settings_goto(uid))
    if setting == 'disallowLinks':
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                aurle = await (await c.execute(
                    'select url from antispamurlexceptions where chat_id=%s', (peer_id - 2000000000,))).fetchall()
        await editMessage(messages.settings_exceptionlist(aurle), peer_id, message.conversation_message_id,
                          keyboard.settings_change_countable(uid, category='antispam', onlybackbutton=True))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['settings_listaction']))
async def settings_listaction(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.peer_id
    setting = payload['setting']
    action = payload['action']

    if setting in SETTINGS_PREMIUM and not await getUserPremium(uid):
        return await editMessage(messages.no_prem(), peer_id, message.conversation_message_id,
                                 keyboard.settings_goto(uid))

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into typequeue (chat_id, uid, type, additional) values (%s, %s, %s, %s)',
                            (peer_id - 2000000000, uid, 'settings_listaction',
                             '{' + f'"setting": "{setting}", "action": "{action}", "type": "{payload["type"]}"' + '}'))
            await conn.commit()
    await editMessage(messages.settings_listaction_action(setting, action), peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD([
    'settings_set_welcome_text', 'settings_set_welcome_photo', 'settings_set_welcome_url']))
async def settings_set_welcome(message: MessageEvent):
    cmd = message.payload['cmd']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into typequeue (chat_id, uid, type, additional) values (%s, %s, %s, \'{}\')',
                            (message.peer_id - 2000000000, message.user_id, cmd,))
            await conn.commit()
    await editMessage(messages.get(cmd), message.peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD([
    'settings_unset_welcome_text', 'settings_unset_welcome_photo', 'settings_unset_welcome_url']))
async def settings_unset_welcome(message: MessageEvent):
    cmd = message.payload['cmd']
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
    await editMessage(messages.settings_countable_action('set', 'welcome'), peer_id, message.conversation_message_id,
                      keyboard.settings_set_welcome(message.user_id, text, img, url))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['nicklist']))
async def nicklist(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, nickname from nickname where chat_id=%s and uid>0 and uid=ANY(%s) and nickname is not null'
                ' order by nickname', (chat_id, [i.member_id for i in (await api.messages.get_conversation_members(
                    peer_id=chat_id + 2000000000)).items]))).fetchall()
    count = len(res)
    res = res[:30]
    await editMessage(messages.nlist(res, await api.users.get(user_ids=[i[0] for i in res])), peer_id,
                      message.conversation_message_id, keyboard.nlist(message.user_id, 0, count))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['prev_page_nlist', 'next_page_nlist']))
async def page_nlist(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    page = message.payload['page']

    members_uid = [i.member_id for i in (await api.messages.get_conversation_members(
        peer_id=chat_id + 2000000000)).items]
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, nickname from nickname where chat_id=%s and uid>0 and uid=ANY(%s) and nickname is not null'
                ' order by nickname', (chat_id, members_uid))).fetchall()
    if not (count := len(res)):
        return
    res = res[page * 30:page * 30 + 30]
    await editMessage(messages.nlist(res, await api.users.get(user_ids=[i[0] for i in res]), page), peer_id,
                      message.conversation_message_id, keyboard.nlist(message.user_id, page, count))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['nonicklist']))
async def nonicklist(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = [i[0] for i in await (await c.execute(
                'select uid from nickname where chat_id=%s and uid>0 and nickname is not null', (chat_id,))).fetchall()]
    members_uid = [i.member_id for i in (await api.messages.get_conversation_members(
        peer_id=chat_id + 2000000000)).items if i.member_id not in res]
    count = len(members_uid)
    members_uid = members_uid[:30]
    await editMessage(messages.nnlist(await api.users.get(user_ids=members_uid)), peer_id,
                      message.conversation_message_id, keyboard.nnlist(message.user_id, 0, count))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['prev_page_nnlist', 'next_page_nnlist']))
async def page_nnlist(message: MessageEvent):
    peer_id = message.object.peer_id
    page = message.payload['page']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = [i[0] for i in await (await c.execute(
                'select uid from nickname where chat_id=%s and uid>0 and nickname is not null',
                (peer_id - 2000000000,))).fetchall()]
    members = await api.messages.get_conversation_members(peer_id=peer_id)
    members_count = len(members.items[page * 30:])
    members = [i for i in members.items if i.member_id not in res][page * 30: page * 30 + 30]
    if len(members) <= 0:
        return
    await editMessage(messages.nnlist(await api.users.get(user_ids=[f'{i.member_id}' for i in members]), page), peer_id,
                      message.conversation_message_id, keyboard.nnlist(message.user_id, page, members_count))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
              SearchPayloadCMD(['prev_page_mutelist', 'next_page_mutelist']))
async def page_mutelist(message: MessageEvent):
    peer_id = message.object.peer_id
    page = message.payload['page']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, chat_id, last_mutes_causes, mute, last_mutes_names from mute where chat_id=%s and '
                'mute>%s order by uid desc', (peer_id - 2000000000, int(time.time())))).fetchall()
    if not (count := len(res)):
        return
    await editMessage(await messages.mutelist(res[page * 30: page * 30 + 30], count), peer_id,
                      message.conversation_message_id, keyboard.mutelist(message.user_id, page, count))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
              SearchPayloadCMD(['prev_page_warnlist', 'next_page_warnlist']))
async def page_warnlist(message: MessageEvent):
    peer_id = message.object.peer_id
    page = message.payload['page']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, chat_id, last_warns_causes, warns, last_warns_names from warn where chat_id=%s and'
                ' warns>0 order by uid desc', (peer_id - 2000000000,))).fetchall()
    if not (count := len(res)):
        return
    res = res[page * 30: page * 30 + 30]
    await editMessage(await messages.warnlist(res, count), peer_id,
                      message.conversation_message_id, keyboard.warnlist(message.user_id, page, count))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['prev_page_banlist', 'next_page_banlist']))
async def page_banlist(message: MessageEvent):
    payload = message.payload
    peer_id = message.object.peer_id
    page = payload['page'] + (-1 if payload['cmd'].startswith('prev') else 1)

    if page < 0:
        return
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, chat_id, last_bans_causes, ban, last_bans_names from ban where chat_id=%s and '
                'ban>%s order by uid desc', (peer_id - 2000000000, int(time.time())))).fetchall()
    if len(res) <= 0:
        return
    banned_count = len(res)
    res = res[page * 30:page * 30 + 30]
    await editMessage(await messages.banlist(res, banned_count), peer_id, message.conversation_message_id,
                      keyboard.banlist(message.user_id, page, banned_count))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
              SearchPayloadCMD(['mutelist_delall', 'warnlist_delall', 'banlist_delall'], answer=False))
async def punishlist_delall(message: MessageEvent):
    cmd: str = message.payload['cmd']
    uid = message.object.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if await getUserAccessLevel(uid, chat_id) < 6:
        return await message.show_snackbar('❌ Для данной функции требуется 6 уровень доступа')
    await sendMessageEventAnswer(message.event_id, uid, peer_id)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if cmd.startswith('mute'):
                uids = await (await c.execute('update mute set mute=0 where chat_id=%s returning uid',
                                              (chat_id,))).fetchall()
                for i in uids:
                    await setChatMute(i[0], chat_id, 0)
            elif cmd.startswith('warn'):
                await c.execute('update warn set warns=0 where chat_id=%s', (chat_id,))
            elif cmd.startswith('ban'):
                await c.execute('update ban set ban=0 where chat_id=%s', (chat_id,))
            else:
                raise Exception('cmd.startswith(mute or warn or ban)')
            await conn.commit()
    await editMessage(messages.punishlist_delall_done(cmd.replace('list_delall', '')), peer_id,
                      message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
              SearchPayloadCMD(['prev_page_statuslist', 'next_page_statuslist']))
async def page_statuslist(message: MessageEvent):
    payload = message.payload
    page = payload['page'] + (-1 if payload['cmd'].startswith('prev') else 1)

    if page < 0:
        return
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            premium_pool = await (await c.execute('select uid, time from premium where time>%s',
                                                  (int(time.time()),))).fetchall()
    if len(premium_pool) <= 0:
        return
    premium_pool = premium_pool[page * 30:page * 30 + 30]
    await editMessage(await messages.statuslist(premium_pool), message.object.peer_id, message.conversation_message_id,
                      keyboard.statuslist(message.user_id, page, len(premium_pool)))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['demote']))
async def demote(message: MessageEvent):
    payload = message.payload
    await editMessage(messages.demote_yon(), message.object.peer_id, message.conversation_message_id,
                      keyboard.demote_accept(message.user_id, payload['chat_id'], payload['option']))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['demote_accept']))
async def demote_accept(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    option = payload['option']

    if option == 'all':
        members = await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        for i in members.items:
            if not i.is_admin and i.member_id > 0:
                await kickUser(i.member_id, chat_id)
    elif option == 'lvl':
        members = await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        kicking = []
        for i in members.items:
            if not i.is_admin and i.member_id > 0:
                acc = await getUserAccessLevel(i.member_id, chat_id)
                if acc == 0:
                    kicking.append(i.member_id)
        for i in kicking:
            await kickUser(i, chat_id)
    await editMessage(messages.demote_accept(
        payload['uid'] if 'uid' in payload else message.user_id, await getUserName(uid),
        await getUserNickname(uid, chat_id)), peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['demote_disaccept']))
async def demote_disaccept(message: MessageEvent):
    await editMessage(messages.demote_disaccept(), message.object.peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['giveowner_no']))
async def giveowner_no(message: MessageEvent):
    await editMessage(messages.giveowner_no(), message.object.peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['giveowner']))
async def giveowner(message: MessageEvent):
    payload = message.payload
    chat_id = payload['chat_id']
    uid = payload['uid']
    id = payload['chid']

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('delete from accesslvl where chat_id=%s and uid=%s', (chat_id, uid))).rowcount:
                return
            if await getSilence(chat_id):
                if 0 in await getSilenceAllowed(chat_id):
                    await setChatMute(uid, chat_id, 0)
                else:
                    await setChatMute(uid, chat_id)
            await setUserAccessLevel(id, chat_id, 7)
            await setChatMute(id, chat_id, 0)
            await c.execute('delete from gpool where chat_id=%s', (chat_id,))
            await c.execute('delete from chatgroups where chat_id=%s', (chat_id,))
            await conn.commit()

    await editMessage(messages.giveowner(
        uid, await getUserNickname(uid, chat_id), await getUserName(uid), id, await getUserNickname(id, chat_id),
        await getUserName(id)), message.object.peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['top']))
async def top(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select uid, messages from messages where uid>0 and messages>0 and chat_id=%s and '
                'uid=ANY(%s) order by messages desc limit 10',
                (chat_id, [i.member_id for i in (
                    await api.messages.get_conversation_members(peer_id=peer_id)).items]))).fetchall()
    await editMessage(await messages.top(res), peer_id, message.conversation_message_id,
                      keyboard.top(chat_id, message.user_id))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['top_leagues']))
async def top_leagues(message: MessageEvent):
    peer_id = message.object.peer_id
    lg = message.payload['league']
    top = await getXPTop('lvl', league=lg)
    chattop = await getXPTop('lvl', league=lg, users=[i.member_id for i in (
        await api.messages.get_conversation_members(peer_id=peer_id)).items])
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            availableleagues = [k for k, _ in enumerate(LEAGUE) if await (
                await c.execute('select id from xp where league=%s limit 1', (k + 1,))).fetchone()]
    await editMessage(
        await messages.top_lvls(top, chattop),
        peer_id, message.conversation_message_id, keyboard.top_leagues(
            peer_id - 2000000000, message.user_id, lg, availableleagues))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['top_duels']))
async def top_duels(message: MessageEvent):
    peer_id = message.object.peer_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            lvln = await (await c.execute(
                'select uid, wins from duelwins where uid>0 order by wins desc limit 10')).fetchall()
    lvln = {i[0]: i[1] for i in lvln}
    await editMessage(
        await messages.top_duels(lvln), peer_id, message.conversation_message_id,
        keyboard.top_duels(peer_id - 2000000000, message.user_id))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['top_duels_in_group']))
async def top_duels_in_group(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            lvln = await (await c.execute(
                'select uid, wins from duelwins where uid>0 and uid=ANY(%s) order by wins desc limit 10',
                ([i.member_id for i in (await api.messages.get_conversation_members(
                    peer_id=chat_id + 2000000000)).items],))).fetchall()
    lvln = {i[0]: i[1] for i in lvln}
    await editMessage(await messages.top_duels(lvln, 'в беседе'), peer_id, message.conversation_message_id,
                      keyboard.top_duels_in_group(chat_id, message.user_id))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['resetnick_accept']))
async def resetnick_accept(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('delete from nickname where chat_id=%s', (peer_id - 2000000000,))
            await conn.commit()
    await editMessage(messages.resetnick_accept(uid, await getUserName(uid)), peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['resetnick_disaccept']))
async def resetnick_disaccept(message: MessageEvent):
    await editMessage(messages.resetnick_disaccept(), message.object.peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['resetaccess_accept']))
async def resetaccess_accept(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    lvl = message.payload['lvl']
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            x = await (await c.execute(
                'delete from accesslvl where chat_id=%s and access_level=%s and uid!=%s returning uid',
                (chat_id, lvl, uid))).fetchall()
            await conn.commit()
    if await getSilence(chat_id):
        if 0 in await getSilenceAllowed(chat_id):
            for id in x:
                await setChatMute(id[0], chat_id, 0)
        else:
            for id in x:
                await setChatMute(id[0], chat_id)
    await editMessage(messages.resetaccess_accept(uid, await getUserName(uid), lvl), peer_id,
                      message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['resetaccess_disaccept']))
async def resetaccess_disaccept(message: MessageEvent):
    await editMessage(messages.resetaccess_disaccept(message.payload['lvl']), message.object.peer_id,
                      message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['kick_nonick']))
async def kick_nonick(message: MessageEvent):
    uid = message.user_id
    chat_id = message.object.peer_id - 2000000000
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute('select uid from nickname where chat_id=%s and uid>0 and nickname is not null',
                                         (chat_id,))).fetchall()
    res = [i[0] for i in res]
    kicked = 0
    for i in (await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)).items:
        if i.member_id not in res and i.member_id > 0:
            kicked += await kickUser(i.member_id, chat_id)
    await api.messages.send(random_id=0, message=messages.kickmenu_kick_nonick(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), kicked), chat_id=chat_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['kick_nick']))
async def kick_nick(message: MessageEvent):
    uid = message.user_id
    chat_id = message.object.peer_id - 2000000000
    kicked = 0
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            nicknamed = await (await c.execute(
                'select uid from nickname where chat_id=%s and uid>0 and nickname is not null', (chat_id,))).fetchall()
    for i in nicknamed:
        kicked += await kickUser(i[0], chat_id)
    await api.messages.send(random_id=0, message=messages.kickmenu_kick_nick(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), kicked), chat_id=chat_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['kick_banned']))
async def kick_banned(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    kicked = 0
    lst = await api.messages.get_conversation_members(peer_id=peer_id)
    lst = await api.users.get(user_ids=[i.member_id for i in lst.items])
    for i in lst:
        if i.deactivated:
            kicked += await kickUser(i.id, chat_id)
    await api.messages.send(random_id=0, message=messages.kickmenu_kick_banned(
        uid, await getUserName(uid), await getUserNickname(uid, chat_id), kicked), chat_id=chat_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notif']))
async def notif(message: MessageEvent):
    payload = message.payload
    peer_id = message.object.peer_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            notifs = await (await c.execute(
                'select status, name from notifications where chat_id=%s order by name desc',
                (peer_id - 2000000000,))).fetchall()
    await editMessage(
        messages.notifs(notifs), peer_id, message.conversation_message_id,
        keyboard.notif_list(
            message.user_id, notifs, int(payload['page']) if payload['cmd'] == 'page' in payload else 1
        ) if len(notifs) > 0 else None)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notif_select']))
async def notif_select(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            notif = await (await c.execute(
                'select name, text, time, every, tag, status from notifications where chat_id=%s and name=%s',
                (chat_id, message.payload['name']))).fetchone()
            await c.execute('delete from typequeue where uid=%s and chat_id=%s', (uid, chat_id))
            await conn.commit()
    await editMessage(messages.notification(notif[0], notif[1], notif[2], notif[3], notif[4], notif[5]), peer_id,
                      message.conversation_message_id, keyboard.notification(uid, notif[5], notif[0]))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_status']))
async def notification_status(message: MessageEvent):
    payload = message.payload
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
    await editMessage(messages.notification(name, snotif[0], ntime, snotif[1], snotif[2], turn_to), peer_id,
                      message.conversation_message_id, keyboard.notification(message.user_id, turn_to, name))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_text']))
async def notification_text(message: MessageEvent):
    payload = message.payload
    peer_id = message.object.peer_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into typequeue (chat_id, uid, type, additional) values (%s, %s, %s, %s)',
                            (peer_id - 2000000000, message.user_id, 'notification_text',
                             '{' + f'"name": "{payload["name"]}", "cmid": "{message.conversation_message_id}"' + '}'))
            await conn.commit()
    await editMessage(messages.notification_changing_text(), peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_time']))
async def notification_time(message: MessageEvent):
    await editMessage(
        messages.notification_changing_time_choose(), message.object.peer_id,
        message.conversation_message_id, keyboard.notification_time(message.user_id, message.payload['name']))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_time_change']))
async def notification_time_change(message: MessageEvent):
    payload = message.payload
    peer_id = message.object.peer_id
    ctype = payload['type']
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute(
                'insert into typequeue (chat_id, uid, type, additional) values (%s, %s, %s, %s)',
                (peer_id - 2000000000, message.user_id, 'notification_time_change', '{' +
                 f'"name": "{payload["name"]}", "cmid": "{message.conversation_message_id}", "type": "{ctype}"' + '}'))
            await conn.commit()
    if ctype == 'single':
        await editMessage(messages.notification_changing_time_single(), peer_id, message.conversation_message_id)
    elif ctype == 'everyday':
        await editMessage(messages.notification_changing_time_everyday(), peer_id, message.conversation_message_id)
    else:
        await editMessage(messages.notification_changing_time_everyxmin(), peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_tag']))
async def notification_tag(message: MessageEvent):
    await editMessage(
        messages.notification_changing_tag_choose(), message.object.peer_id,
        message.conversation_message_id, keyboard.notification_tag(message.user_id, message.payload['name']))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_tag_change']))
async def notification_tag_change(message: MessageEvent):
    peer_id = message.object.peer_id
    name = message.payload['name']
    ctype = message.payload['type']
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            notif = await (await c.execute(
                'update notifications set tag = %s where chat_id=%s and name=%s returning text, time, every, status',
                (ctype, peer_id - 2000000000, name))).fetchone()
            await conn.commit()
    await editMessage(messages.notification(name, notif[0], notif[1], notif[2], ctype, notif[3]), peer_id,
                      message.conversation_message_id, keyboard.notification(message.user_id, notif[3], name))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['notification_delete']))
async def notification_delete(message: MessageEvent):
    peer_id = message.object.peer_id
    name = message.payload['name']
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('delete from notifications where chat_id=%s and name=%s', (peer_id - 2000000000, name))
            await conn.commit()
    await editMessage(messages.notification_delete(name), peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['listasync']))
async def listasync(message: MessageEvent):
    uid = message.user_id
    page = message.payload['page']
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            chat_ids = await (await c.execute('select chat_id from gpool where uid=%s order by id desc',
                                              (uid,))).fetchall()
    chat_ids = [i[0] for i in chat_ids]
    total = len(chat_ids)
    chat_ids = chat_ids[(page - 1) * 10:page * 10]
    names = [await getChatName(chat_id) for chat_id in chat_ids] if len(chat_ids) > 0 else []
    await editMessage(messages.listasync([{"id": i, "name": names[k]} for k, i in enumerate(chat_ids)], total),
                      message.object.peer_id, message.conversation_message_id, keyboard.listasync(uid, total, page))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['help']))
async def help(message: MessageEvent):
    payload = message.payload
    peer_id = message.object.peer_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            cmds = await (await c.execute('select cmd, lvl from commandlevels where chat_id=%s',
                                          (peer_id - 2000000000,))).fetchall()
    base = COMMANDS.copy()
    for i in cmds:
        try:
            base[i[0]] = int(i[1])
        except:
            pass
    await editMessage(messages.help(payload['page'], base), peer_id, message.conversation_message_id,
                      keyboard.help(message.user_id, payload['page'], payload['prem']))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['cmdlist']))
async def cmdlist(message: MessageEvent):
    page = message.payload['page']
    uid = message.user_id
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            cmdnames = {i[0]: i[1] for i in await (await c.execute('select cmd, name from cmdnames where uid=%s',
                                                                   (uid,))).fetchall()}
    await editMessage(messages.cmdlist(
        dict(list(cmdnames.items())[page * 10: (page * 10) + 10]), page, len(list(cmdnames))), message.peer_id,
        message.conversation_message_id, keyboard.cmdlist(uid, page, len(cmdnames)))


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
        await editMessage(messages.check_ban(
            id, await getUserName(id), await getUserNickname(id, chat_id),
            max(await getUserBan(id, chat_id) - time.time(), 0), u_bans_names, ban_date, ban_from, ban_reason, ban_time
        ), peer_id, message.conversation_message_id, keyboard.check_history(sender, id, 'ban', len(u_bans_names)))
    elif check == 'mute':
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
        await editMessage(messages.check_mute(
            id, await getUserName(id), await getUserNickname(id, chat_id),
            max(await getUserMute(id, chat_id) - time.time(), 0), u_mutes_names, mute_date,
            mute_from, mute_reason, mute_time), peer_id, message.conversation_message_id,
            keyboard.check_history(sender, id, 'mute', len(u_mutes_names)))
    elif check == 'warn':
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
        await editMessage(messages.check_warn(
            id, await getUserName(id), await getUserNickname(id, chat_id), await getUserWarns(id, chat_id),
            u_warns_names, u_warns_dates, u_warns_names, u_warns_causes),
            peer_id, message.conversation_message_id, keyboard.check_history(sender, id, 'warn', len(u_warns_causes)))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['check_menu']))
async def check_menu(message: MessageEvent):
    payload = message.payload
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    id = payload['id']
    await editMessage(messages.check(
        id, await getUserName(id), await getUserNickname(id, chat_id),
        max(await getUserBan(id, chat_id) - time.time(), 0), await getUserWarns(id, chat_id),
        max(await getUserMute(id, chat_id) - time.time(), 0)), peer_id, message.conversation_message_id,
        keyboard.check(uid, id))


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
        await editMessage(messages.check_history_ban(
            id, await getUserName(id), await getUserNickname(id, chat_id), bans_dates, bans_names, bans_times,
            bans_causes), peer_id, message.conversation_message_id)
    elif check == 'mute':
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
        await editMessage(messages.check_history_mute(id, await getUserName(id), await getUserNickname(id, chat_id),
                                                      mutes_dates, mutes_names, mutes_times, mutes_causes),
                          peer_id, message.conversation_message_id)
    elif check == 'warn':
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
        await editMessage(messages.check_history_warn(
            id, await getUserName(id), await getUserNickname(id, chat_id), warns_dates, warns_names, warns_times,
            warns_causes), peer_id, message.conversation_message_id)


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
        await editMessage(messages.unmute(uname, unickname, uid, name, nickname, id), peer_id,
                          message.conversation_message_id)
    elif cmd == 'unwarn':
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if not (await c.execute(
                        'update warn set warns=warns-1 where chat_id=%s and uid=%s and warns>0 and warns<3',
                        (chat_id, id))).rowcount:
                    return
                await conn.commit()
        await editMessage(messages.unwarn(uname, unickname, uid, name, nickname, id), peer_id,
                          message.conversation_message_id)
    elif cmd == 'unban':
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if not (await c.execute('update ban set ban=0 where chat_id=%s and uid=%s and ban>%s',
                                        (chat_id, id, int(time.time())))).rowcount:
                    return
                await conn.commit()
        await editMessage(messages.unban(uname, unickname, uid, name, nickname, id), peer_id,
                          message.conversation_message_id)
    else:
        return
    await deleteMessages(cmid, chat_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
              SearchPayloadCMD(['prefix_add', 'prefix_del', 'prefix_list', 'prefix']))
async def addprefix(message: MessageEvent):
    cmd = message.payload['cmd']
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000

    if not await getUserPremium(uid):
        return await editMessage(messages.no_prem(), peer_id, message.conversation_message_id)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if cmd == 'prefix_add' and (await (await c.execute(
                    'select count(*) as c from prefix where uid=%s', (uid,))).fetchone())[0] > 2:
                return await editMessage(messages.addprefix_max(), peer_id, message.conversation_message_id,
                                         keyboard.prefix_back(uid))
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


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['timeout_turn']))
async def timeout_turn(message: MessageEvent):
    uid = message.user_id
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute(
                    'update silencemode set activated=not activated where chat_id=%s returning activated',
                    (chat_id,))).rowcount:
                await c.execute('insert into silencemode (chat_id, activated) values (%s, True)', (chat_id,))
                activated = True
            else:
                activated = (await c.fetchone())[0]
            allowed = await getSilenceAllowed(chat_id)
            lvls = await (await c.execute('select uid, access_level from accesslvl where chat_id=%s',
                                          (chat_id,))).fetchall()
            lvls = {i[0]: i[1] for i in lvls}
            for i in (await api.messages.get_conversation_members(peer_id)).items:
                if i.member_id < 0:
                    continue
                if i.member_id in lvls:
                    if lvls[i.member_id] in allowed or lvls[i.member_id] not in range(0, 7):
                        continue
                elif 0 in allowed:
                    continue
                if activated:
                    await setChatMute(i.member_id, chat_id)
                else:
                    await setChatMute(i.member_id, chat_id, 0)
            if activated:
                await sendMessage(peer_id, messages.timeouton(
                    uid, await getUserName(uid), await getUserNickname(uid, chat_id)))
            else:
                await sendMessage(peer_id, messages.timeoutoff(
                    uid, await getUserName(uid), await getUserNickname(uid, chat_id)))
            await conn.commit()
    await editMessage(messages.timeout(activated), peer_id, message.conversation_message_id,
                      keyboard.timeout(uid, activated))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['timeout']))
async def timeout(message: MessageEvent):
    peer_id = message.object.peer_id
    activated = await getSilence(peer_id - 2000000000)
    await editMessage(messages.timeout(activated), peer_id, message.conversation_message_id,
                      keyboard.timeout(message.user_id, activated))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['timeout_settings']))
async def timeout_settings(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if await (await c.execute('select id from silencemode where chat_id=%s and activated=true',
                                      (chat_id,))).fetchone():
                return
    await editMessage(messages.timeout_settings(), peer_id, message.conversation_message_id,
                      keyboard.timeout_settings(message.user_id, await getSilenceAllowed(chat_id)))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['timeout_settings_turn']))
async def timeout_settings(message: MessageEvent):
    lvl = message.payload['lvl']
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if await (await c.execute('select id from silencemode where chat_id=%s and activated=true',
                                      (chat_id,))).fetchone():
                return
    allowed = await getSilenceAllowed(chat_id)
    if lvl in allowed:
        allowed.remove(lvl)
    else:
        allowed.append(lvl)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update silencemode set allowed = %s where chat_id=%s',
                                    (f'{sorted(allowed)}', chat_id))).rowcount:
                await c.execute('insert into silencemode (chat_id, activated, allowed) values (%s, false, %s)',
                                (chat_id, f'{sorted(allowed)}'))
            await conn.commit()
    await editMessage(messages.timeout_settings(), peer_id, message.conversation_message_id,
                      keyboard.timeout_settings(message.user_id, allowed))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['turnpublic']))
async def turnpublic(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update publicchats set isopen=not isopen where chat_id=%s', (chat_id,))).rowcount:
                await c.execute('insert into publicchats (chat_id, premium, isopen) values (%s, false, true)',
                                (chat_id,))
            await conn.commit()
            chatgroup = 'Привязана' if (await (await c.execute(
                'select count(*) as c from chatgroups where chat_id=%s', (chat_id,))).fetchone())[0] else 'Не привязана'
            gpool = 'Привязана' if (await (await c.execute(
                'select count(*) as c from gpool where chat_id=%s', (chat_id,))).fetchone())[0] else 'Не привязана'
            muted = (await (await c.execute('select count(*) as c from mute where chat_id=%s and mute>%s',
                                            (chat_id, int(time.time())))).fetchone())[0]
            banned = (await (await c.execute('select count(*) as c from ban where chat_id=%s and ban>%s',
                                             (chat_id, int(time.time())))).fetchone())[0]
            if bjd := await (await c.execute('select time from botjoineddate where chat_id=%s', (chat_id,))).fetchone():
                bjd = datetime.utcfromtimestamp(bjd[0]).strftime('%d.%m.%Y %H:%M')
            else:
                bjd = 'Невозможно определить'
            if await (await c.execute('select id from publicchats where chat_id=%s and isopen=true',
                                      (chat_id,))).fetchone():
                public = 'Открытый'
            else:
                public = 'Приватный'
                await c.execute('delete from publicchatssettings where chat_id=%s', (chat_id,))
                await conn.commit()
    members = (await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)).items
    id = [i for i in members if i.is_admin and i.is_owner][0].member_id
    try:
        names = await api.users.get(user_ids=id)
        name = f"{names[0].first_name} {names[0].last_name}"
        prefix = 'id'
    except:
        name = await getGroupName(-int(id))
        prefix = 'club'
    await editMessage(messages.chat(
        id, name, chat_id, chatgroup, gpool, public, muted, banned, len(members), bjd, prefix,
        await getChatName(chat_id)
    ), peer_id, message.conversation_message_id, keyboard.chat(
        message.user_id, public == 'Открытый'))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['antitag_list']))
async def antitag_list(message: MessageEvent):
    peer_id = message.object.peer_id
    chat_id = peer_id - 2000000000
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            users = set([i[0] for i in await (await c.execute('select uid from antitag where chat_id=%s',
                                                              (chat_id,))).fetchall()])
    await editMessage(await messages.antitag_list(users, chat_id), peer_id, message.conversation_message_id)


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['import']))
async def import_(message: MessageEvent):
    importchatid = message.payload['importchatid']
    if await getUserAccessLevel(message.user_id, importchatid) < 7:
        return await editMessage(
            messages.import_notowner(), message.object.peer_id, message.conversation_message_id)
    await editMessage(messages.import_(importchatid, await getChatName(importchatid)),
                      message.object.peer_id, message.conversation_message_id,
                      keyboard.import_(message.user_id, importchatid))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['import_settings']))
async def import_settings(message: MessageEvent):
    importchid = message.payload['importchatid']
    await editMessage(messages.import_settings(
        importchid, await getChatName(importchid), s := await getImportSettings(message.user_id, importchid)),
                      message.object.peer_id, message.conversation_message_id, keyboard.import_settings(
            message.user_id, importchid, s))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['import_turn']))
async def import_turn(message: MessageEvent):
    importchid = message.payload['importchatid']
    setting = message.payload['setting']
    await turnImportSetting(importchid, message.user_id, setting)
    await editMessage(messages.import_settings(
        importchid, await getChatName(importchid), s := await getImportSettings(message.user_id, importchid)),
                      message.object.peer_id, message.conversation_message_id, keyboard.import_settings(
            message.user_id, importchid, s))


@bl.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, SearchPayloadCMD(['import_start']))
async def import_start(message: MessageEvent):
    importchatid = message.payload['importchatid']
    await editMessage(messages.import_start(importchatid), message.object.peer_id, message.conversation_message_id)
    chatid = message.object.peer_id - 2000000000
    settings = await getImportSettings(message.user_id, importchatid)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if settings['sys']:
                if t := await (await c.execute('select activated, allowed from silencemode where chat_id=%s',
                                               (importchatid,))).fetchone():
                    if not (await c.execute('update silencemode set activated = %s, allowed = %s where chat_id=%s',
                                            (*t, chatid))).rowcount:
                        await c.execute('insert into silencemode (chat_id, activated, allowed) values (%s, %s, %s)',
                                        (chatid, *t))
                for i in await (await c.execute('select filter from filters where chat_id=%s',
                                                (importchatid,))).fetchall():
                    if not await (await c.execute('select id from filters where chat_id=%s and filter=%s',
                                                  (chatid, *i))).fetchone():
                        await c.execute('insert into filters (chat_id, filter) values (%s, %s)', (chatid, *i))
                for i in await (await c.execute('select cmd, lvl from commandlevels where chat_id=%s',
                                                (importchatid,))).fetchall():
                    if not (await c.execute('update commandlevels set lvl = %s where chat_id=%s and '
                                            'cmd=%s', (i[1], chatid, i[0]))).rowcount:
                        await c.execute('insert into commandlevels (chat_id, cmd, lvl) values (%s, %s, %s)',
                                        (chatid, *i))
                for i in await (await c.execute('select setting, pos, "value", punishment, value2, pos2 from settings '
                                                'where chat_id=%s', (importchatid,))).fetchall():
                    if not (await c.execute(
                            'update settings set pos = %s, value = %s, punishment = %s, value2 = %s, '
                            'pos2 = %s where chat_id=%s and setting=%s', (*i[1:], chatid, i[0]))).rowcount:
                        await c.execute('insert into settings (chat_id, setting, pos, value, punishment, value2, pos2) '
                                        'values (%s, %s, %s, %s, %s, %s, %s)', (chatid, *i))
                if t := await (await c.execute('select msg, url, photo, button_label from welcome where chat_id=%s',
                                               (importchatid,))).fetchone():
                    if not (await c.execute('update welcome set msg = %s, url = %s, photo = %s, button_label = %s where'
                                            ' chat_id=%s', (*t, chatid))).rowcount:
                        await c.execute('insert into welcome (chat_id, msg, url, photo, button_label) values '
                                        '(%s, %s, %s, %s, %s)', (chatid, *t))
                for i in await (await c.execute('select lvl, name from accessnames where chat_id=%s',
                                                (importchatid,))).fetchall():
                    if not (await c.execute('update accessnames set name = %s where chat_id=%s and lvl=%s',
                                            (i[1], chatid, i[0]))).rowcount:
                        await c.execute('insert into accessnames (chat_id, lvl, name) values (%s, %s, %s)',
                                        (chatid, *i))
                for i in await (await c.execute('select uid from ignore where chat_id=%s', (importchatid,))).fetchall():
                    if not await (await c.execute('select id from ignore where chat_id=%s and uid=%s',
                                                  (chatid, *i))).fetcone():
                        await c.execute('insert into ignore (chat_id, uid) values (%s, %s)', (chatid, *i))
                if t := await (await c.execute('select time from chatlimit where chat_id=%s',
                                               (importchatid,))).fetchone():
                    if not (await c.execute('update chatlimit set time = %s where chat_id=%s', (*i, chatid))).rowcount:
                        await c.execute('insert into chatlimit (chat_id, time) values (%s, %s)', (chatid, *t))
                for i in await (await c.execute('select tag, every, status, time, description, text, name from '
                                                'notifications where chat_id=%s', (importchatid,))).fetchall():
                    if not (await c.execute('update notifications set tag = %s, every = %s, status = %s, time = %s, '
                                            'description = %s, text = %s where chat_id=%s and name=%s',
                                            (*i[:-1], chatid, i[-1]))).rowcount:
                        await c.execute('insert into notifications (chat_id, tag, every, status, time, description, '
                                        'text, name) values (%s, %s, %s, %s, %s, %s, %s, %s)', (chatid, *i))
                for i in await (await c.execute('select url from antispamurlexceptions where chat_id=%s',
                                                (importchatid,))).fetchall():
                    if not await (await c.execute('select id from antispamurlexceptions where chat_id=%s and url=%s',
                                                  (chatid, *i))).fetchone():
                        await c.execute(
                            'insert into antispamurlexceptions (chat_id, url) values (%s, %s)', (chatid, *i))
                for i in await (await c.execute('select uid from antitag where chat_id=%s', 
                                                (importchatid,))).fetchall():
                    if not await (await c.execute('select id from antitag where chat_id=%s and uid=%s', 
                                                  (chatid, *i))).fetchone():
                        await c.execute('insert into antitag (chat_id, uid) values (%s, %s)', (chatid, *i))
                for i in await (await c.execute('select uid, sys, acc, nicks, punishes, binds from importsettings where'
                                                ' chat_id=%s', (importchatid,))).fetchall():
                    if not (await c.execute('update importsettings set sys = %s, acc = %s, nicks = %s, punishes = %s, '
                                            'binds = %s where chat_id=%s and uid=%s', (*i[1:], chatid, i[0]))).rowcount:
                        await c.execute('insert into importsettings (chat_id, uid, sys, acc, nicks, punishes, binds) '
                                        'values (%s, %s, %s, %s, %s, %s, %s)', (chatid, *i))
            if settings['acc']:
                for i in await (await c.execute('select uid, access_level from accesslvl where chat_id=%s',
                                                (importchatid,))).fetchall():
                    if not (await c.execute('update accesslvl set access_level = %s where chat_id=%s and uid=%s',
                                            (i[1], chatid, i[0]))).rowcount:
                        await c.execute('insert into accesslvl (chat_id, uid, access_level) values (%s, %s, %s)',
                                        (chatid, *i))
            if settings['nicks']:
                for i in await (await c.execute('select uid, nickname from nickname where chat_id=%s',
                                                (importchatid,))).fetchall():
                    if not (await c.execute('update nickname set nickname = %s where chat_id=%s and uid=%s',
                                            (i[1], chatid, i[0]))).rowcount:
                        await c.execute('insert into nickname (chat_id, uid, nickname) values (%s, %s, %s)', 
                                        (chatid, *i))
            if settings['punishes']:
                for i in await (await c.execute(
                        'select uid, warns, last_warns_times, last_warns_names, last_warns_dates, last_warns_causes '
                        'from warn where chat_id=%s', (importchatid,))).fetchall():
                    if not (await c.execute('update warn set warns = %s, last_warns_times = %s, last_warns_names = %s, '
                                            'last_warns_dates = %s, last_warns_causes = %s where chat_id=%s and uid=%s',
                                            (*i[1:], chatid, i[0]))).rowcount:
                        await c.execute('insert into warn (chat_id, uid, warns, last_warns_times, last_warns_names, '
                                        'last_warns_dates, last_warns_causes) values (%s, %s, %s, %s, %s, %s, %s)', 
                                        (chatid, *i))
                for i in await (await c.execute(
                        'select uid, ban, last_bans_times, last_bans_names, last_bans_dates, last_bans_causes '
                        'from ban where chat_id=%s', (importchatid,))).fetchall():
                    if not (await c.execute('update ban set ban = %s, last_bans_times = %s, last_bans_names = %s, '
                                            'last_bans_dates = %s, last_bans_causes = %s where chat_id=%s and uid=%s',
                                            (*i[1:], chatid, i[0]))).rowcount:
                        await c.execute('insert into ban (chat_id, uid, ban, last_bans_times, last_bans_names, '
                                        'last_bans_dates, last_bans_causes) values (%s, %s, %s, %s, %s, %s, %s)', 
                                        (chatid, *i))
                for i in await (await c.execute(
                        'select uid, mute, last_mutes_times, last_mutes_names, last_mutes_dates, last_mutes_causes '
                        'from mute where chat_id=%s', (importchatid,))).fetchall():
                    if not (await c.execute('update mute set mute = %s, last_mutes_times = %s, last_mutes_names = %s, '
                                            'last_mutes_dates = %s, last_mutes_causes = %s where chat_id=%s and uid=%s',
                                            (*i[1:], chatid, i[0]))).rowcount:
                        await c.execute('insert into mute (chat_id, uid, mute, last_mutes_times, last_mutes_names, '
                                        'last_mutes_dates, last_mutes_causes) values (%s, %s, %s, %s, %s, %s, %s)', 
                                        (chatid, *i))
            if settings['binds']:
                for i in await (await c.execute('select uid from gpool where chat_id=%s', (importchatid,))).fetchall():
                    if not await (await c.execute('select id from gpool where chat_id=%s and uid=%s',
                                                  (chatid, *i))).fetchone():
                        await c.execute('insert into gpool (chat_id, uid) values (%s, %s)', (chatid, *i))
                for i in await (await c.execute('select uid, "group" from chatgroups where chat_id=%s',
                                                (importchatid,))).fetchall():
                    if not await (await c.execute(
                            'select id from chatgroups where chat_id=%s and uid=%s and "group"=%s',
                            (chatid, *i))).fetchone():
                        await c.execute('insert into chatgroups (chat_id, uid, "group") values (%s, %s, %s)',
                                        (chatid, *i))
    await editMessage(messages.import_end(importchatid), message.object.peer_id, message.conversation_message_id)
