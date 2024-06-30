# import traceback
#
# from db import *
#
# for i in getLeavedChats().select():
#     try:
#         getChat(i.id).delete().execute()
#     except:
#         traceback.print_exc()
