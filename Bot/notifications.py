from datetime import datetime

import messages
from Bot.utils import sendMessage
from config.config import API
from db import AccessLevel, Notifs


async def run_notifications():
    for i in Notifs.select().where(Notifs.status == 1, Notifs.every != -1):
        try:
            if (datetime.fromtimestamp(i.time) - datetime.now()).total_seconds() > 0:
                continue
            call = False
            if i.tag == 1:
                call = True
            elif i.tag == 2:
                try:
                    members = await API.messages.get_conversation_members(i.chat_id + 2000000000)
                    call = ''.join(
                        [f"[id{y.member_id}|\u200b\u206c]" for y in members.items if y.member_id > 0])
                except:
                    pass
            elif i.tag == 3:
                ac = AccessLevel.select().where(AccessLevel.access_level > 0, AccessLevel.uid > 0)
                call = ''.join([f"[id{y.uid}|\u200b\u206c]" for y in ac.iterator()])
            else:
                ac = AccessLevel.select().where(AccessLevel.access_level > 0, AccessLevel.uid > 0)
                chat = [y.uid for y in ac.iterator()]
                try:
                    members = await API.messages.get_conversation_members(i.chat_id + 2000000000)
                    call = ''.join([f"[id{i.member_id}|\u200b\u206c]" for i in members.items
                                    if i.member_id > 0 and i.member_id not in chat])
                except:
                    pass
            if call:
                if not await sendMessage(i.chat_id, messages.send_notification(i.text, call)):
                    await sendMessage(i.chat_id, messages.notification_too_long_text(i.name))
            notif = Notifs.get(Notifs.chat_id == i.chat_id, Notifs.name == i.name)
            notif.status = 0
            if i.every != 0:
                notif.time = i.time + (i.every * 60)
            notif.save()
        except:
            pass
