import time

from vkbottle_types.events.bot_events import MessageNew

import keyboard
import messages
from Bot.utils import (kickUser, getUserName, getUserBan, getUserBanInfo, getUserNickname, getChatSettings, sendMessage,
                       getUserAccessLevel, deleteMessages, uploadImage, generateCaptcha)
from config.config import GROUP_ID
from db import pool


async def action_handle(event: MessageNew) -> None:
    event = event.object.message
    action = event.action
    chat_id = event.peer_id - 2000000000
    uid = action.member_id
    if action.type.value == 'chat_kick_user':
        if (await getChatSettings(chat_id))['main']['kickLeaving']:
            await kickUser(uid, chat_id=chat_id)
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute('delete from captcha where chat_id=%s and uid=%s', (chat_id, uid))
                await c.execute('delete from typequeue where chat_id=%s and uid=%s and type=\'captcha\'',
                                (chat_id, uid))
                await conn.commit()
        return
    if action.type.value == 'chat_invite_user':
        id = event.from_id
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute('insert into allusers (uid) values (%s) on conflict (uid) do nothing', (id,))
                if not (await c.execute('update userjoineddate set time = %s where chat_id=%s and uid=%s',
                                        (int(time.time()), chat_id, id))).rowcount:
                    await c.execute('insert into userjoineddate (chat_id, uid, time) values (%s, %s, %s)',
                                    (chat_id, id, int(time.time())))
                await conn.commit()

        if uid == -GROUP_ID:
            async with (await pool()).connection() as conn:
                async with conn.cursor() as c:
                    if await (await c.execute('select id from blacklist where uid=%s', (id,))).fetchone():
                        await sendMessage(event.peer_id, messages.blocked())
                        await kickUser(-GROUP_ID, chat_id=chat_id)
                        return

                    if not await (await c.execute('select id from allchats where chat_id=%s', (chat_id,))).fetchone():
                        await c.execute('insert into allchats (chat_id) values (%s)', (chat_id,))
                        await conn.commit()
                        await sendMessage(event.peer_id, messages.join(), keyboard.join(chat_id))
                        return

                    await c.execute('delete from leavedchats where chat_id=%s', (chat_id,))
                    await conn.commit()
            await sendMessage(event.peer_id, messages.rejoin(), keyboard.rejoin(chat_id))
            return

        if (await getUserAccessLevel(id, chat_id) <= 0 and
                (await getChatSettings(chat_id))['main']['kickInvitedByNoAccess']):
            await kickUser(uid, chat_id=chat_id)
            return

        if uid < 0:
            return

        u_nickname = await getUserNickname(uid, chat_id)
        u_name = await getUserName(uid)
        ban = await getUserBan(uid, chat_id)
        if ban > time.time():
            await sendMessage(event.peer_id, messages.kick_banned(uid, u_name, u_nickname, ban,
                                                                  (await getUserBanInfo(uid, chat_id))['causes'][-1]))
            await kickUser(uid, chat_id=chat_id)
            return

        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if id is not None and id:
                    if not (await c.execute('update refferal set from_id = %s where chat_id=%s and uid=%s',
                                            (id, chat_id, uid))).rowcount:
                        await c.execute('insert into refferal (chat_id, uid, from_id) values (%s, %s, %s)',
                                        (chat_id, uid, id))
                    await conn.commit()

                if s := await (await c.execute(
                        'select pos, "value", punishment from settings where chat_id=%s and setting=\'captcha\'',
                        (chat_id,))).fetchone():
                    if s[0] and s[1] and s[2]:
                        captcha = await generateCaptcha(uid, chat_id, s[1])
                        m = await sendMessage(event.peer_id, messages.captcha(uid, u_name, s[1], s[2]),
                                              photo=await uploadImage(captcha[0]))
                        await c.execute('update captcha set cmid = %s where id=%s',
                                        (m[0].conversation_message_id, captcha[1]))
                        await c.execute('insert into typequeue (chat_id, uid, "type", additional) '
                                        'values (%s, %s, \'captcha\', \'{}\')', (chat_id, uid))
                        await conn.commit()
                        if m:
                            return

                if s := await (await c.execute(
                        'select pos, pos2 from settings where chat_id=%s and setting=\'welcome\'',
                        (chat_id,))).fetchone():
                    welcome = await (await c.execute(
                        'select msg, url, button_label, photo from welcome where chat_id=%s',
                        (chat_id,))).fetchone()
                    if welcome is not None and s[0]:
                        name = u_name if u_nickname is None else u_nickname
                        m = await sendMessage(event.peer_id, welcome[0].replace('%name%', f"[id{uid}|{name}]"),
                                              keyboard.welcome(welcome[1], welcome[2]), welcome[3])
                        if s[1]:
                            lw = (await (await c.execute(
                                'delete from welcomehistory where chat_id=%s returning cmid',
                                (chat_id,))).fetchone())[0]
                            await deleteMessages(lw, chat_id)
                        await c.execute('insert into welcomehistory (chat_id, time, cmid) values (%s, %s, %s) '
                                        'on conflict (chat_id) do nothing',
                                        (chat_id, time.time(), m[0].conversation_message_id))
                        await conn.commit()
