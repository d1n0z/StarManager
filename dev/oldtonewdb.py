import traceback

import db
from unused import olddb
from peewee import IntegrityError


for i in olddb.dbhandle.get_tables():
    try:
        if not i.isdigit() or int(i) < 0:
            continue
        print(i)
        oldt = olddb.getChat(i)
        for y in oldt.select():
            if y.access_level != 0:
                t = newdb.getAccessLevel()
                try:
                    print(t.insert(uid=y.uid, chat_id=i, access_level=y.access_level).execute())
                except IntegrityError as e:
                    print(e)
                except:
                    traceback.print_exc()

            if y.last_warns_names != '[]' and y.last_warns_names is not None:
                t = newdb.getWarn()
                try:
                    print(t.insert(uid=y.uid, chat_id=i, warns=y.warns, last_warns_times=y.last_warns_times,
                             last_warns_names=y.last_warns_names, last_warns_dates=y.last_warns_dates,
                             last_warns_causes=y.last_warns_causes).execute())
                except IntegrityError as e:
                    print(e)
                except:
                    traceback.print_exc()

            if y.last_mutes_causes != '[]' and y.last_bans_causes is not None:
                t = newdb.getMute()
                try:
                    print(t.insert(uid=y.uid, chat_id=i, mute=y.mute, last_mutes_times=y.last_mutes_times,
                             last_mutes_causes=y.last_mutes_causes, last_mutes_names=y.last_mutes_names,
                             last_mutes_dates=y.last_mutes_dates).execute())
                except IntegrityError as e:
                    print(e)
                except:
                    traceback.print_exc()

            if y.last_bans_causes != '[]' and y.last_bans_causes is not None:
                t = newdb.getBan()
                try:
                    print(t.insert(uid=y.uid, chat_id=i, ban=y.ban, last_bans_times=y.last_bans_times,
                             last_bans_causes=y.last_bans_causes, last_bans_names=y.last_bans_names,
                             last_bans_dates=y.last_bans_dates).execute())
                except IntegrityError as e:
                    print(e)
                except:
                    traceback.print_exc()

            if isinstance(y.messages, int) and y.messages > 0:
                t = newdb.getMessages()
                try:
                    print(t.insert(uid=y.uid, chat_id=i, messages=y.messages).execute())
                except IntegrityError as e:
                    print(e)
                except:
                    traceback.print_exc()

            if y.nickname is not None and y.nickname != '[]':
                t = newdb.getNickname()
                try:
                    print(t.insert(uid=y.uid, chat_id=i, nickname=y.nickname).execute())
                except IntegrityError as e:
                    print(e)
                except:
                    traceback.print_exc()

            if y.last_message is not None and y.last_message != 0:
                t = newdb.getLastMessageDate()
                try:
                    print(t.insert(uid=y.uid, chat_id=i, last_message=y.last_message).execute())
                except IntegrityError as e:
                    print(e)
                except:
                    traceback.print_exc()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getSilenceMode()
for i in oldt.select():
    try:
        t = newdb.getSilenceMode()
        t.insert(chat_id=i.chat_id, time=i.unix_time).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getGPool()
for i in oldt.select():
    try:
        t = newdb.getGPool()
        t.insert(uid=i.uid, chat_id=i.chat_id).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getChatGroups()
for i in oldt.select():
    try:
        t = newdb.getChatGroups()
        t.insert(uid=i.uid, group=i.group, chat_id=i.chat_id).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = db.getFilters()
for i in oldt.select():
    try:
        t = newdb.getFilters()
        t.insert(chat_id=i.chat_id, filter=i.filter).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getCommandLevels()
for i in oldt.select():
    try:
        t = newdb.getCommandLevels()
        t.insert(chat_id=i.chat_id, cmd=i.cmd, lvl=i.lvl).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = db.getBlacklist()
for i in oldt.select():
    try:
        t = newdb.getBlacklist()
        t.insert(uid=i.uid).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getPremium()
for i in oldt.select():
    try:
        t = newdb.getPremium()
        t.insert(uid=i.uid, time=i.unix_time).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getBonus()
for i in oldt.select():
    try:
        t = newdb.getBonus()
        t.insert(uid=i.uid, time=i.unix_time).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getSettings()
for i in oldt.select():
    try:
        t = newdb.getSettings()
        t.insert(chat_id=i.chat_id, setting=i.setting, pos=i.pos).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getJoinedDate()
for i in oldt.select():
    try:
        t = newdb.getBotJoinedDate()
        t.insert(chat_id=i.chat_id, time=i.unix_time).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getUserJoinedDate()
for i in oldt.select():
    try:
        t = newdb.getUserJoinedDate()
        t.insert(chat_id=i.chat_id, time=i.unix_time, uid=i.uid).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getLVL()
for i in oldt.select():
    try:
        t = newdb.getXP()
        t.insert(xp=i.xp, uid=i.uid).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getPremMenu()
for i in oldt.select():
    try:
        t = newdb.getPremMenu()
        t.insert(uid=i.uid, setting=i.setting, pos=i.pos).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getPrefixes()
for i in oldt.select():
    try:
        t = newdb.getPrefix()
        t.insert(uid=i.uid, prefix=i.prefix).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = db.getPrefixes()
for i in oldt.select():
    try:
        t = newdb.getPrefix()
        t.insert(uid=i.uid, prefix=i.prefix).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = db.getAccessNames()
for i in oldt.select():
    try:
        t = newdb.getPrefix()
        t.insert(chat_id=i.chat_id, lvl=i.lvl, name=i.name).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getIgnore()
for i in oldt.select():
    try:
        t = newdb.getIgnore()
        t.insert(chat_id=i.chat_id, uid=i.uid).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getChatLimit()
for i in oldt.select():
    try:
        t = newdb.getChatLimit()
        t.insert(chat_id=i.chat_id, time=i.unix_time).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getPayments()
for i in oldt.select():
    try:
        t = newdb.getPayments()
        t.insert(uid=i.uid, payment_id=i.id, success=i.success).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getCMDNames()
for i in oldt.select():
    try:
        t = newdb.getCMDNames()
        t.insert(uid=i.uid, cmd=i.cmd, name=i.name).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getDuels()
for i in oldt.select():
    try:
        t = newdb.getDuelWins()
        t.insert(uid=i.uid, wins=i.wins).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = db.getLastFiveCommands()
for i in oldt.select():
    try:
        t = newdb.getLastFiveCommands()
        t.insert(uid=i.uid, cmds=i.cmds, cmd_time=i.cmd_time).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getGlobalWarns()
for i in oldt.select():
    try:
        t = newdb.getGlobalWarns()
        t.insert(uid=i.uid, warns=i.warns, time=i.time).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getReports()
for i in oldt.select():
    try:
        t = newdb.getReports()
        t.insert(uid=i.uid, id=i.id, time=i.time).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getReportAnswers()
for i in oldt.select():
    try:
        t = newdb.getReportAnswers()
        t.insert(answering_id=i.answering_id, uid=i.uid, chat_id=i.chat_id, repid=i.repid,
                 report_text=i.report_text).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getComments()
for i in oldt.select():
    try:
        t = newdb.getComments()
        t.insert(uid=i.uid, time=i.time).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getLikes()
for i in oldt.select():
    try:
        t = newdb.getLikes()
        t.insert(uid=i.uid, post_id=i.post_id).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getInfBanned()
for i in oldt.select():
    try:
        t = newdb.getInfBanned()
        t.insert(uid=i.uid, type=i.type).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getLeavedChats()
for i in oldt.select():
    try:
        t = newdb.getLeavedChats()
        t.insert(chat_id=i.id, time=i.time).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getRewards()
for i in oldt.select():
    try:
        t = newdb.getRewards()
        t.insert(uid=i.uid, type=i.type, count=i.count).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getCompletedRewards()
for i in oldt.select():
    try:
        t = newdb.getCompletedRewards()
        t.insert(uid=i.uid, type=i.type).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getNotifs()
for i in oldt.select():
    try:
        t = newdb.getNotifs()
        t.insert(chat_id=i.chat_id, tag=i.tag, every=i.every, status=i.status, time=i.time, name=i.name,
                 description=i.description, text=i.text).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getTypeQueue()
for i in oldt.select():
    try:
        t = newdb.getTypeQueue()
        t.insert(chat_id=i.chat_id, uid=i.uid, type=i.type, additional=i.additional).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getReportWarns()
for i in oldt.select():
    try:
        t = newdb.getReportWarns()
        t.insert(uid=i.uid, warns=i.warns).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()


oldt = olddb.getReboots()
for i in oldt.select():
    try:
        t = newdb.getReboots()
        t.insert(chat_id=i.chat_id, time=i.time, sended=i.sended).execute()
    except IntegrityError as e:
        print(e)
    except:
        traceback.print_exc()
