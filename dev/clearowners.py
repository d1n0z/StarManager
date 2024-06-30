# import traceback
#
# from db import dbhandle, getChat
# from config import *
# import vk_api
# from vk_api.exceptions import VkApiError
#
# vk_session_group = vk_api.VkApi(token=VK_TOKEN_GROUP)
# vk = vk_session_group.get_api()
#
# tables = dbhandle.get_tables()
# print(tables)
# for i in tables:
#     try:
#         chat = getChat(i)
#         res = chat.select()
#         try:
#             members = vk_session_group.method("messages.getConversationMembers", {
#                 'peer_id': int(i) + 2000000000
#             })['items']
#         except VkApiError:
#             print(i)
#             try:
#                 chat.drop_table().execute()
#             except:
#                 chat.drop_table()
#         else:
#             res_uids = [int(i.uid) for i in res if int(i.uid) > 0]
#             uids = [int(i['member_id']) for i in members if int(i['member_id']) > 0]
#             for uid in uids:
#                 if uid not in res_uids:
#                     print(chat.insert(uid=uid, last_message=0, access_level=0).execute())
#             for uid in res_uids:
#                 if uid not in uids:
#                     res = chat.delete().where(chat.uid == uid, chat.access_level == 7).execute()
#                     if res != 0:
#                         print(res)
#     except:
#         traceback.print_exc()
