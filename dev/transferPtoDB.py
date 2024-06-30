import pickle

# with open('silence_mode.p', 'rb') as data:
#     silence_mode = pickle.load(data)
#     data.close()
# with open('pool.p', 'rb') as data:
#     pool = pickle.load(data)
#     data.close()
# with open('welcome.p', 'rb') as data:
#     welcome = pickle.load(data)
#     data.close()
# with open('chatgroups.p', 'rb') as data:
#     chatgroups = pickle.load(data)
#     data.close()
# with open('filters.p', 'rb') as data:
#     filters = pickle.load(data)
#     data.close()
# with open('commands_access.p', 'rb') as data:
#     commands_access = pickle.load(data)
#     data.close()
# with open('blacklist.p', 'rb') as data:
#     blacklist = pickle.load(data)
#     data.close()
# with open('premium.p', 'rb') as data:
#     premium = pickle.load(data)
#     data.close()
# with open('bonus.p', 'rb') as data:
#     bonus = pickle.load(data)
#     data.close()
# with open('settings.p', 'rb') as data:
#     settings = pickle.load(data)
#     data.close()
# with open('joineddate.p', 'rb') as data:
#     joineddate = pickle.load(data)
#     data.close()
# with open('userjoineddate.p', 'rb') as data:
#     userjoineddate = pickle.load(data)
#     data.close()
# with open('lvlt.p', 'rb') as data:
#     lvlt = pickle.load(data)
#     data.close()
# with open('premmenu.p', 'rb') as data:
#     premmenu = pickle.load(data)
#     data.close()
# with open('prefixes.p', 'rb') as data:
#     prefixes = pickle.load(data)
#     data.close()
# with open('access_names.p', 'rb') as data:
#     access_names = pickle.load(data)
#     data.close()
with open('cmdcounter.p', 'rb') as data:
    cmdcounter = pickle.load(data)
    data.close()

# try:
#     getSilenceMode().drop_table()
# except:
#     pass
# try:
#     getGPool().drop_table()
# except:
#     pass
# try:
#     getChatGroups().drop_table()
# except:
#     pass
# try:
#     getFilters().drop_table()
# except:
#     pass
# try:
#     getCommandLevels().drop_table()
# except:
#     pass
# try:
#     getBlacklist().drop_table()
# except:
#     pass
# try:
#     getPremium().drop_table()
# except:
#     pass
# try:
#     getBonus().drop_table()
# except:
#     pass
# try:
#     getSettings().drop_table()
# except:
#     pass
# try:
#     getJoinedDate().drop_table()
# except:
#     pass
# try:
#     getUserJoinedDate().drop_table()
# except:
#     pass
# try:
#     getLVL().drop_table()
# except:
#     pass
# try:
#     getPremMenu().drop_table()
# except:
#     pass
# try:
#     getPrefix().drop_table()
# except:
#     pass
# try:
#     getAccessNames().drop_table()
# except:
#     pass
# try:
#     getCMDCounter().drop_table()
# except:
#     pass

# for k, i in silence_mode.items():
#     try:
#         getSilenceMode().insert(chat_id=k, unix_time=i).execute()
#     except:
#         traceback.print_exc()
#
# for k, i in pool.items():
#     try:
#         for y in i:
#             try:
#                 getGPool().insert(uid=k, chat_id=y).execute()
#             except:
#                 traceback.print_exc()
#     except:
#         traceback.print_exc()
#
# for k, i in chatgroups.items():
#     try:
#         for ky, iy in i.items():
#             try:
#                 for yy in iy:
#                     try:
#                         getChatGroups().insert(uid=k, group=ky, chat_id=yy).execute()
#                     except:
#                         traceback.print_exc()
#             except:
#                 traceback.print_exc()
#     except:
#         traceback.print_exc()
#
# for k, i in filters.items():
#     try:
#         for ii in i:
#             try:
#                 getFilters().insert(chat_id=k, filter=ii).execute()
#             except:
#                 traceback.print_exc()
#     except:
#         traceback.print_exc()
#
# for k, i in commands_access.items():
#     try:
#         for ky, iy in i.items():
#             try:
#                 getCommandLevels().insert(chat_id=k, cmd=ky, lvl=iy).execute()
#             except:
#                 traceback.print_exc()
#     except:
#         traceback.print_exc()
#
# for i in blacklist:
#     try:
#         getBlacklist().insert(uid=i).execute()
#     except:
#         traceback.print_exc()
#
# for k, i in premium.items():
#     try:
#         getPremium().insert(uid=k, unix_time=i[0]).execute()
#     except:
#         traceback.print_exc()
#
# for k, i in bonus.items():
#     try:
#         getBonus().insert(uid=k, unix_time=i).execute()
#     except:
#         traceback.print_exc()
#
# for k, i in settings.items():
#     try:
#         getSettings().insert(chat_id=k, setting='setKick', pos=i).execute()
#     except:
#         traceback.print_exc()
#
# for k, i in joineddate.items():
#     try:
#         getJoinedDate().insert(chat_id=k, unix_time=i).execute()
#     except:
#         traceback.print_exc()
#
# for k, i in userjoineddate.items():
#     try:
#         for ki, ii in i.items():
#             try:
#                 getUserJoinedDate().insert(chat_id=k, uid=ki, unix_time=ii).execute()
#             except:
#                 traceback.print_exc()
#     except:
#         traceback.print_exc()

# for k, i in lvlt.items():
#     try:
#         getLVL().insert(uid=k, xp=i['xp'], lm=i['lm']).execute()
#     except:
#         traceback.print_exc()

# for k, i in premmenu.items():
#     try:
#         for ki, ii in premmenu.items():
#             try:
#                 getPremium().insert(uid=k, setting=ki, pos=int(ii)).execute()
#             except:
#                 traceback.print_exc()
#     except:
#         traceback.print_exc()
#
# for k, i in prefixes.items():
#     try:
#         for ii in i:
#             try:
#                 getPrefix().insert(uid=k, prefix=ii).execute()
#             except:
#                 traceback.print_exc()
#     except:
#         traceback.print_exc()
#
# for k, i in access_names.items():
#     try:
#         for ki, ii in enumerate(i):
#             try:
#                 getAccessNames().insert(chat_id=k, lvl=ki, name=ii).execute()
#             except:
#                 traceback.print_exc()
#     except:
#         traceback.print_exc()
#
# for k, i in cmdcounter.items():
#     try:
#         getCMDCounter().insert(cmd=k, count=i).execute()
#     except:
#         pass
