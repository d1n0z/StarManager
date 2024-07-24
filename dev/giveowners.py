from config.config import *
from unused.olddb import dbhandle, getChat

vk_session_group = vk_api.VkApi(token=VK_TOKEN_GROUP)
updated = inserted = 0

tables = dbhandle.get_tables()
for i in tables:
    try:
        chat = getChat(i)
        if len(chat.select().where(chat.access_level == 7)) <= 0:
            continue
        try:
            members = vk_session_group.method("messages.getConversationMembers", {
                'peer_id': int(i) + 2000000000
            })['items']
        except:
            pass
        else:
            for member in members:
                if 'is_owner' in member:
                    if member['is_owner']:
                        owner_id = member['member_id']
                        try:
                            _ = chat.select().where(chat.uid == owner_id)[0]
                            chat.update(access_level=7).where(chat.uid == owner_id).execute()
                            updated += 1
                        except:
                            try:
                                _ = chat.select().where(chat.access_level == 7)[0]
                            except:
                                try:
                                    chat.insert(uid=owner_id, access_level=7).execute()
                                    inserted += 1
                                except:
                                    pass
    except:
        pass
