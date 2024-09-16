import time
from vkbottle_types.events import MessageNew

import keyboard
import messages
from Bot.utils import kickUser, getUserName, getUserBan, getUserBanInfo, getUserNickname, getChatSettings, sendMessage, \
    getUserAccessLevel
from config.config import GROUP_ID
from db import AllUsers, UserJoinedDate, Referral, Blacklist, AllChats, LeavedChats, Welcome


async def action_handle(event: MessageNew) -> None:
    event = event.object.message
    action = event.action
    chat_id = event.peer_id - 2000000000
    uid = action.member_id
    if action.type.value == 'chat_kick_user':
        if (await getChatSettings(chat_id))['main']['kickLeaving']:
            await kickUser(uid, chat_id=chat_id)
        return
    if action.type.value == 'chat_invite_user':
        id = event.from_id
        AllUsers.get_or_create(uid=id)
        ujd = UserJoinedDate.get_or_create(chat_id=chat_id, uid=id)[0]
        ujd.time = time.time()
        ujd.save()

        if uid == -GROUP_ID:
            b = Blacklist.get_or_none(Blacklist.uid == id)
            if b is not None:
                await sendMessage(event.peer_id, messages.blocked())
                await kickUser(-GROUP_ID, chat_id=chat_id)
                return

            c = AllChats.get_or_none(AllChats.chat_id == chat_id)
            if c is None:
                AllChats.create(chat_id=chat_id)
                await sendMessage(event.peer_id, messages.join(), keyboard.join(chat_id))
                return

            lc = LeavedChats.get_or_none(LeavedChats.chat_id == chat_id)
            if lc is not None:
                lc.delete_instance()
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

        if id is not None and id:
            r = Referral.get_or_create(chat_id=chat_id, uid=uid)[0]
            r.from_id = id
            r.save()

        welcome = Welcome.get_or_none(Welcome.chat_id == chat_id)
        if welcome is not None:
            name = u_name if u_nickname is None else u_nickname
            await sendMessage(event.peer_id, welcome.msg.replace('%name%', f"[id{uid}|{name}]"))
