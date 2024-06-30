from unused.olddb import dbhandle, getChat
from config.config import *
import vk_api

vk_session_group = vk_api.VkApi(token=VK_TOKEN_GROUP)
vk = vk_session_group.get_api()

tables = dbhandle.get_tables()
for i in tables:
    try:
        chat = getChat(i)
        chat.delete().where(chat.uid < 0).execute()
    except:
        pass
