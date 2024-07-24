import time

from vkbottle_types.codegen.objects import MessagesMessageAction

import keyboard
import messages
from Bot.utils import kickUser, getUserName, getUserAccessLevel, getUserBan, getUserBanInfo, getUserNickname
from config.config import GROUP_ID, API
from db import AllUsers, UserJoinedDate, Referral, Blacklist, AllChats, LeavedChats, Welcome


async def action_handle(event: MessagesMessageAction, setKick, chat_id, id) -> None:
    uid = event.member_id
    if event.type.value == 'chat_kick_user':
        try:
            await kickUser(uid, chat_id=chat_id)
        except:
            pass
    if event.type.value == 'chat_invite_user':
        AllUsers.get_or_create(uid=id)
        ujd = UserJoinedDate.get_or_create(chat_id=chat_id, uid=id)[0]
        ujd.time = time.time()
        ujd.save()

        acc = await getUserAccessLevel(id, chat_id)
        if uid != -GROUP_ID and acc <= 0 and setKick != 0:
            await kickUser(uid, chat_id=chat_id)
            return
        if uid > 0:
            u_nickname = await getUserNickname(uid, chat_id)
            u_name = await getUserName(uid)
            ban = await getUserBan(uid, chat_id)
            if ban <= time.time():
                if id is not None and id:
                    r = Referral.get_or_create(chat_id=chat_id, uid=uid)[0]
                    r.from_id = id
                    r.save()

                welcome = Welcome.get_or_none(Welcome.chat_id == chat_id)
                if welcome is not None:
                    name = u_name if u_nickname is None else u_nickname
                    msg = welcome.msg.replace('%name%', f"[id{uid}|{name}]")
                    await API.messages.send(random_id=0, chat_id=chat_id, message=msg)
                return
            try:
                ban_info = await getUserBanInfo(uid, chat_id, {'causes': [None]})
                cause = ban_info['causes'][-1]
                msg = messages.kick_banned(uid, u_name, u_nickname, ban, cause)
                await API.messages.send(random_id=0, chat_id=chat_id, message=msg)
            except:
                pass
            await kickUser(uid, chat_id=chat_id)
        elif uid == -GROUP_ID:
            b = Blacklist.get_or_none(Blacklist.uid == id)
            if b is not None:
                msg = messages.blocked()
                await API.messages.send(random_id=0, chat_id=chat_id, message=msg)
                await kickUser(-GROUP_ID, chat_id=chat_id)
                return
            c = AllChats.get_or_none(AllChats.chat_id == chat_id)
            if c is None:
                AllChats.create(chat_id=chat_id)
                msg = messages.join()
                kb = keyboard.join(chat_id)
                await API.messages.send(random_id=0, chat_id=chat_id, message=msg, keyboard=kb)
                return
            lc = LeavedChats.get_or_none(LeavedChats.chat_id == chat_id)
            if lc is not None:
                lc.delete_instance()
            msg = messages.rejoin()
            kb = keyboard.rejoin(chat_id)
            await API.messages.send(random_id=0, chat_id=chat_id, message=msg, keyboard=kb)
