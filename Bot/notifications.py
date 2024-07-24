from datetime import datetime
from time import sleep

import messages
from config.config import VK_API_SESSION
from db import AccessLevel, Notifs


def run_notifications():
    while True:
        try:
            sleep(10)
            for i in Notifs.select().where(Notifs.status == 1, Notifs.every != -1):
                try:
                    if (datetime.fromtimestamp(i.time) - datetime.now()).total_seconds() > 0:
                        continue
                    call = ''
                    if i.tag == 1:
                        members = True
                    elif i.tag == 2:
                        try:
                            members = VK_API_SESSION.method("messages.getConversationMembers", {
                                'peer_id': i.chat_id + 2000000000
                            })['items']
                            call = ''.join(
                                [f"[id{i['member_id']}|\u200b\u206c]" for i in members if i['member_id'] > 0])
                        except:
                            members = None
                    elif i.tag == 3:
                        ac = AccessLevel.select().where(AccessLevel.access_level > 0, AccessLevel.uid > 0)
                        call = ''.join([f"[id{i.uid}|\u200b\u206c]" for i in ac.iterator()])
                        members = True
                    else:
                        ac = AccessLevel.select().where(AccessLevel.access_level > 0, AccessLevel.uid > 0)
                        chat = [i.uid for i in ac.iterator()]
                        try:
                            members = VK_API_SESSION.method("messages.getConversationMembers", {
                                'peer_id': i.chat_id + 2000000000
                            })['items']
                            call = ''.join(
                                [f"[id{i['member_id']}|\u200b\u206c]" for i in members
                                 if i['member_id'] > 0 and i['member_id'] not in chat]
                            )
                        except:
                            members = None
                    if members is None:
                        notif = Notifs.get(Notifs.chat_id == i.chat_id, Notifs.name == i.name)
                        notif.status = 0
                        notif.save()
                    else:
                        msg = messages.send_notification(i.text, call)
                        try:
                            VK_API_SESSION.method('messages.send', {
                                'chat_id': i.chat_id,
                                'message': msg,
                                'random_id': 0
                            })
                        except:
                            try:
                                VK_API_SESSION.method('messages.send', {
                                    'chat_id': i.chat_id,
                                    'message': messages.notification_too_long_text(i.name),
                                    'random_id': 0
                                })
                            except:
                                pass
                            notif = Notifs.get(Notifs.chat_id == i.chat_id, Notifs.name == i.name)
                            notif.status = 0
                            notif.save()
                    if i.every == 0:
                        notif = Notifs.get(Notifs.chat_id == i.chat_id, Notifs.name == i.name)
                        notif.status = 0
                        notif.save()
                    else:
                        notif = Notifs.get(Notifs.chat_id == i.chat_id, Notifs.name == i.name)
                        notif.time = i.time + (i.every * 60)
                        notif.save()
                except:
                    pass
        except:
            pass
