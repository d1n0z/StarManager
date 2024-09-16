import calendar
import time
import traceback
from ast import literal_eval
from datetime import datetime

from memoization import cached

from Bot.utils import getUserNickname, pointMinutes, pointDays, pointHours, pointWords, getUserName, getUserLVL
from config.config import COMMANDS, LVL_NAMES, COMMANDS_DESC, TASKS_LOTS, TASKS_DAILY, PREMIUM_TASKS_DAILY, \
    PREMIUM_TASKS_DAILY_TIERS, TASKS_WEEKLY, PREMIUM_TASKS_WEEKLY, SETTINGS_POSITIONS, \
    SETTINGS_COUNTABLE_CHANGEPUNISHMENTMESSAGE, SETTINGS_COUNTABLE_NO_PUNISHMENT
from db import AccessNames, BotMessages


@cached
def get(key: str, **kwargs):
    return BotMessages.get(BotMessages.key == key).text.format(**kwargs)


def join():
    return get('join')


def rejoin():
    return get('rejoin')


def rejoin_activate():
    return get('rejoin_activate')


def start():
    return get('start')


def id(uid, data, name, url):
    return get('id', uid=uid, data=data, name=name, url=url)


def mtop(res, names):
    msg = get('mtop')
    for index, item in enumerate(res):
        try:
            name = f"{names[index].first_name} {names[index].last_name}"
            addmsg = f"[{index + 1}]. [id{names[index].id}|{name}] - {item.messages} сообщений\n"
            if addmsg not in msg:
                msg += addmsg
        except:
            pass
    return msg


def help(page=0, cmds=COMMANDS):
    if page == 8:
        return get('help_page8')

    descs = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []}
    # print(cmds)
    for k, i in cmds.items():
        try:
            descs[int(i)].append(COMMANDS_DESC[k])
        except:
            pass  # traceback.print_exc()
    # print(descs)
    msg = None
    if page == 0:
        msg = get('help_page0')
    if page == 1:
        msg = get('help_page1')
    if page == 2:
        msg = get('help_page2')
    if page == 3:
        msg = get('help_page3')
    if page == 4:
        msg = get('help_page4')
    if page == 5:
        msg = get('help_page5')
    if page == 6:
        msg = get('help_page6')
    if page == 7:
        msg = get('help_page7')
    # print(page)
    for i in descs[page]:
        msg += f'{i}\n'
    # print(descs[page])
    msg += get('help_last')
    return msg


def helpdev():
    return get('helpdev')


def help_closed():
    return get('help_closed')


def help_sent(id, name, nick):
    if nick is not None:
        n = nick
    else:
        n = name
    return get('help_sent', id=id, n=n)


def query_error():
    return get(query_error())


def report(uid, name, report, repid, chatid, chatname):
    return get('report', repid=repid, uid=uid, name=name, chatid=chatid, chatname=chatname, report=report)


def report_cd():
    return get('report_cd')


def report_answering(repid):
    return get('report_answering', repid=repid)


def report_sent(rep_id):
    return get('report_sent', rep_id=rep_id)


def report_empty():
    return get('report_empty')


def report_answer(ansing_id, ansing_name, repid, ans, qusing_id, quesing_name):
    return get('report_answer', repid=repid, qusing_id=qusing_id, quesing_name=quesing_name, ansing_id=ansing_id,
               ansing_name=ansing_name, ans=ans)


def report_answered(ansing_id, ansing_name, repid, ans, report, uid, name, chatid, chatname):
    return get('report_answered', repid=repid, ansing_id=ansing_id, ansing_name=ansing_name, uid=uid, name=name,
               chatid=chatid, chatname=chatname, report=report, ans=ans)


def kick_hint():
    return get('kick_hint')


def kick(u_name, u_nick, uid, ch_name, ch_nick, id, cause):
    if id < 0:
        i = 'club'
        id = abs(id)
    else:
        i = 'id'
    u_name = u_nick if u_nick is not None else u_name
    ch_name = ch_nick if ch_nick is not None else ch_name
    return get('kick', uid=uid, u_name=u_name, i=i, id=id, ch_name=ch_name, cause=cause)


def kicked(uid, name, nickname):
    return get('kicked', uid=uid, un=nickname if nickname is not None else name)


def kick_error():
    return get('kick_error')


def kick_access(id, name, nick):
    if id < 0:
        i = 'club'
        id = abs(id)
    else:
        i = 'id'
    n = nick if nick is not None and len(nick) > 0 else name
    return get('kick_access', i=i, id=id, n=n)


def kick_myself():
    return get('kick_myself')


def kick_higher():
    return get('kick_higher')


def mute_hint():
    return get('mute_hint')


def mute(name, nick, id, mutingname, mutingnick, mutingid, cause, time):
    if cause != '':
        cause = ' по причине: ' + cause
    n = nick if nick is not None else name
    mn = mutingnick if mutingnick is not None else mutingname
    return get('mute', id=id, n=n, mutingid=mutingid, mn=mn, time=time, cause=cause)


def mute_error():
    return get('mute_error')


def mute_myself():
    return get('mute_myself')


def unmute_myself():
    return get('unmute_myself')


def mute_higher():
    return get('mute_higher')


def access_dont_match():
    return get('access_dont_match')


def already_muted(name, nick, id, mute):
    time_left = int((mute - time.time()) / 60)
    n = nick if nick is not None else name
    return get('already_muted', id=id, n=n, time_left=time_left)


def usermute_hint():
    return get('usermute_hint')


def userwarn_hint():
    return get('userwarn_hint')


def warn_hint():
    return get('warn_hint')


def warn(name, nick, uid, ch_name, ch_nick, id, cause):
    if cause != '':
        cause = ' по причине: ' + cause
    n = nick if nick is not None else name
    cn = ch_nick if ch_nick is not None else ch_name
    return get('warn', uid=uid, n=n,cause=cause, cn=cn, id=id)


def warn_kick(name, nick, uid, ch_name, ch_nick, id, cause):
    if cause != '':
        cause = ' по причине: ' + cause
    n = nick if nick is not None else name
    cn = ch_nick if ch_nick is not None else ch_name
    return get('warn_kick', uid=uid, n=n, id=id, cn=cn, cause=cause)


def warn_higher():
    return get('warn_higher')


def warn_myself():
    return get('warn_myself')


def unwarn_myself():
    return get('unwarn_myself')


def clear(names, u_ids, u_name, uid):
    users = []
    for ind, item in enumerate(names):
        user = f"[id{u_ids[ind]}|{item}]"
        if user not in users:
            users.append(user)
    users = ", ".join(users)
    return get('clear', uid=uid, u_name=u_name, users=users)


def clear_hint():
    return get('clear_hint')


def clear_higher():
    return get('clear_higher')


def clear_admin():
    return get('clear_admin')


def snick_hint():
    return get('snick_hint')


def snick_user_has_nick():
    return get('snick_user_has_nick')


def snick_too_long_nickname():
    return get('snick_too_long_nickname')


def snick_higher():
    return get('snick_higher')


def snick(uid, u_name, u_nickname, id, ch_name, nickname, newnickname):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else ch_name
    return get('snick', uid=uid, un=un, id=id, newnickname=newnickname, n=n)


def rnick_hint():
    return get('rnick_hint')


def rnick_user_has_no_nick():
    return get('rnick_user_has_no_nick')


def rnick_higher():
    return get('rnick_higher')


def rnick(uid, u_name, u_nick, id, name, nick):
    un = u_nick if u_nick is not None else u_name
    return get('rnick', uid=uid, un=un, id=id, nick=nick, name=name)


def nlist(res, members, offset=0):
    msg = get('nlist')
    cnt = 0
    offcnt = 0
    for it in members:
        offcnt += 1
        if offcnt >= offset:
            if it.id >= 0 and it.first_name != 'DELETED' and it.last_name != 'DELETED':
                for item in res:
                    if it.id == item.uid:
                        cnt += 1
                        addmsg = f"{cnt + offset}. {item.nickname} - [id{item.uid}|{it.first_name} " \
                                 f"{it.last_name}]\n"
                        if addmsg not in msg:
                            msg += addmsg
        if cnt > 29:
            break
    return msg


def nnlist(members, page=0):
    msg = get('nnlist')
    print(members)
    k = page * 30
    for i in members:
        try:
            if i.first_name != 'DELETED' and i.last_name != 'DELETED' and i.id > 0:
                addmsg = f"{k + 1}. [id{i.id}|{i.first_name} {i.last_name}]\n"
                if addmsg not in msg:
                    msg += addmsg
                    k += 1
        except:
            traceback.print_exc()
    return msg


async def staff(res, names, chat_id):
    msg = get('staff')
    admins = {}
    included = []
    users = {'1': [], '2': [], '3': [], '4': [], '5': [], '6': [], '7': [], '8': []}
    for ind, item in enumerate(res[::-1]):
        x = {"uid": item.uid, "name": [f"{i.first_name} {i.last_name}" for i in names if i.id == item.uid][0],
             "nickname": await getUserNickname(item.uid, chat_id), "access_level": item.access_level}
        users[f'{item.access_level}'].append(x)
        admins[f'{item.access_level}'] = x
    for k, i in admins.items():
        try:
            if k == '1':
                try:
                    lvl_name = AccessNames.select().where(AccessNames.chat_id == chat_id, AccessNames.lvl == 1)[
                        0].name
                except:
                    lvl_name = LVL_NAMES[1]
                msg += f'[☀] {lvl_name}\n'
                for item in users['1']:
                    if item['access_level'] == 1:
                        if item['uid'] > 0:
                            if item['uid'] not in included:
                                if item['nickname'] is not None and item['nickname'] != '':
                                    msg += f"➖ [id{item['uid']}|{item['nickname']}]\n"
                                else:
                                    msg += f"➖ [id{item['uid']}|{item['name']}]\n"
                                included.append(item['uid'])
            if k == '2':
                try:
                    lvl_name = AccessNames.select().where(AccessNames.chat_id == chat_id, AccessNames.lvl == 2)[
                        0].name
                except:
                    lvl_name = LVL_NAMES[2]
                msg += f'[🔥] {lvl_name}\n'
                for item in users['2']:
                    if item['access_level'] == 2:
                        if item['uid'] > 0:
                            if item['uid'] not in included:
                                if item['nickname'] is not None and item['nickname'] != '':
                                    msg += f"➖ [id{item['uid']}|{item['nickname']}]\n"
                                else:
                                    msg += f"➖ [id{item['uid']}|{item['name']}]\n"
                                included.append(item['uid'])
            if k == '3':
                try:
                    lvl_name = AccessNames.select().where(AccessNames.chat_id == chat_id, AccessNames.lvl == 3)[
                        0].name
                except:
                    lvl_name = LVL_NAMES[3]
                msg += f'[🔥] {lvl_name}\n'
                for item in users['3']:
                    if item['access_level'] == 3:
                        if item['uid'] > 0:
                            if item['uid'] not in included:
                                if item['nickname'] is not None and item['nickname'] != '':
                                    msg += f"➖ [id{item['uid']}|{item['nickname']}]\n"
                                else:
                                    msg += f"➖ [id{item['uid']}|{item['name']}]\n"
                                included.append(item['uid'])
            if k == '4':
                try:
                    lvl_name = AccessNames.select().where(AccessNames.chat_id == chat_id, AccessNames.lvl == 4)[
                        0].name
                except:
                    lvl_name = LVL_NAMES[4]
                msg += f'[🔥] {lvl_name}\n'
                for item in users['4']:
                    if item['access_level'] == 4:
                        if item['uid'] > 0:
                            if item['uid'] not in included:
                                if item['nickname'] is not None and item['nickname'] != '':
                                    msg += f"➖ [id{item['uid']}|{item['nickname']}]\n"
                                else:
                                    msg += f"➖ [id{item['uid']}|{item['name']}]\n"
                                included.append(item['uid'])
            if k == '5':
                try:
                    lvl_name = AccessNames.select().where(AccessNames.chat_id == chat_id, AccessNames.lvl == 5)[
                        0].name
                except:
                    lvl_name = LVL_NAMES[5]
                msg += f'[✨] {lvl_name}\n'
                for item in users['5']:
                    if item['access_level'] == 5:
                        if item['uid'] > 0:
                            if item['uid'] not in included:
                                if item['nickname'] is not None and item['nickname'] != '':
                                    msg += f"➖ [id{item['uid']}|{item['nickname']}]\n"
                                else:
                                    msg += f"➖ [id{item['uid']}|{item['name']}]\n"
                                included.append(item['uid'])
            if k == '6':
                try:
                    lvl_name = AccessNames.select().where(AccessNames.chat_id == chat_id, AccessNames.lvl == 6)[
                        0].name
                except:
                    lvl_name = LVL_NAMES[6]
                msg += f'[⚡] {lvl_name}\n'
                for item in users['6']:
                    if item['access_level'] == 6:
                        if item['uid'] > 0:
                            if item['uid'] not in included:
                                if item['nickname'] is not None and item['nickname'] != '':
                                    msg += f"➖ [id{item['uid']}|{item['nickname']}]\n"
                                else:
                                    msg += f"➖ [id{item['uid']}|{item['name']}]\n"
                                included.append(item['uid'])
            if k == '7':
                try:
                    lvl_name = AccessNames.select().where(AccessNames.chat_id == chat_id, AccessNames.lvl == 7)[
                        0].name
                except:
                    lvl_name = LVL_NAMES[7]
                msg += f'[⭐] {lvl_name}\n'
                for item in users['7']:
                    if item['access_level'] == 7:
                        if item['uid'] > 0:
                            if item['uid'] not in included:
                                if item['nickname'] is not None and item['nickname'] != '':
                                    msg += f"➖ [id{item['uid']}|{item['nickname']}]\n"
                                else:
                                    msg += f"➖ [id{item['uid']}|{item['name']}]\n"
                                included.append(item['uid'])
        except:
            pass
    return msg


def unmute(uname, unickname, uid, name, nickname, id):
    un = unickname if unickname is not None else uname
    n = nickname if nickname is not None else name
    return get('unmute', uid=uid, un=un, id=id, n=n)


def unmute_no_mute(id, name, nickname):
    n = nickname if nickname is not None else name
    return get('unmute_no_mute', id=id, n=n)


def unmute_higher():
    return get('unmute_higher')


def unmute_hint():
    return get('unmute_hint')


def unwarn(uname, unick, uid, name, nick, id):
    un = unick if unick is not None else uname
    n = nick if nick is not None else name
    return get('unwarn', uid=uid, un=un, id=id, n=n)


def unwarn_no_warns(id, name, nick):
    n = nick if nick is not None else name
    return get('unwarn_no_warns', id=id, n=n)


def unwarn_higher():
    return get('unwarn_higher')


def unwarn_hint():
    return get('unwarn_hint')


async def mutelist(res, names, mutedcount):
    msg = get('mutelist', mutedcount=mutedcount)

    for ind, item in enumerate(res):
        if names[ind].first_name != 'DELETED' and names[ind].last_name != 'DELETED':
            nickname = await getUserNickname(item.uid, item.chat_id)
            if nickname is not None:
                name = nickname
            else:
                name = f"{names[ind].first_name} {names[ind].last_name}"
            if literal_eval(item.last_mutes_causes)[-1] is None or literal_eval(item.last_mutes_causes)[-1] == '':
                cause = "Без указания причины"
            else:
                cause = literal_eval(item.last_mutes_causes)[-1]
            addmsg = f"[{ind + 1}]. [id{item.uid}|{name}] | " \
                     f"{int((item.mute - time.time()) / 60)} минут | {cause} | Выдал: " \
                     f"{literal_eval(item.last_mutes_names)[-1]}\n"
            if addmsg not in msg:
                msg += addmsg
    return msg


async def warnlist(res, names, warnedcount):
    msg = get('warnlist', warnedcount=warnedcount)

    for ind, item in enumerate(res):
        if names[ind].first_name != 'DELETED' and names[ind].last_name != 'DELETED':
            nickname = await getUserNickname(item.uid, item.chat_id)
            if nickname is not None:
                name = nickname
            else:
                name = f"{names[ind].first_name} {names[ind].last_name}"
            if literal_eval(item.last_warns_causes)[-1] is None or literal_eval(item.last_warns_causes)[-1] == '':
                cause = "Без указания причины"
            else:
                cause = literal_eval(item.last_warns_causes)[-1]
            addmsg = f"[{ind + 1}]. [id{item.uid}|{name}] | " \
                     f"кол-во: {item.warns}/3 | {cause} | Выдал: " \
                     f"{literal_eval(item.last_warns_names)[-1]}\n"
            if addmsg not in msg:
                msg += addmsg
    return msg


def setacc_hint():
    return get('setacc_hint')


def setacc_myself():
    return get('setacc_myself')


def setacc_higher():
    return get('setacc_higher')


def setacc(uid, u_name, u_nick, acc, id, name, nick):
    if u_nick is not None:
        u_n = f'[id{uid}|{u_nick}]'
    else:
        u_n = f'[id{uid}|{u_name}]'
    if nick is not None:
        n = f'[id{id}|{nick}]'
    else:
        n = f'[id{id}|{name}]'
    acc = LVL_NAMES[acc]
    return get('setacc', u_n=u_n, acc=acc, n=n)


def setacc_already_have_acc(id, name, nick):
    if nick is not None:
        n = nick
    else:
        n = name
    return get('setacc_already_have_acc', id=id, n=n)


def setacc_low_acc(acc):
    acc = LVL_NAMES[acc]
    return get('setacc_low_acc', acc=acc)


def delaccess_hint():
    return get('delaccess_hint')


def delaccess_myself():
    return get('delaccess_myself')


def delaccess_noacc(id, name, nick):
    if nick is not None:
        n = nick
    else:
        n = name
    return get('delaccess_noacc', id=id, n=n)


def delaccess_higher():
    return get('delaccess_higher')


def delaccess(uid, uname, unick, id, name, nick):
    if unick is not None:
        un = unick
    else:
        un = uname
    if nick is not None:
        n = nick
    else:
        n = name
    return get('delaccess', uid=uid, un=un, id=id, n=n)


def timeout_hint():
    return get('timeout_hint')


def timeouton(id, name, nickname):
    if nickname is not None:
        n = nickname
    else:
        n = name
    return get('timeouton', id=id, n=n)


def timeoutoff(id, name, nickname):
    if nickname is not None:
        n = nickname
    else:
        n = name
    return get('timeoutoff', id=id, n=n)


def inactive_hint():
    return get('inactive_hint')


def inactive_no_results():
    return get('inactive_no_results')


def inactive(uid, name, nick, count):
    if int(count) > 0:
        if nick is not None:
            n = nick
        else:
            n = name
        return get('inactive', uid=uid, n=n, count=count)
    else:
        return get('inactive_no_active')


def ban_hint():
    return get('ban_hint')


def ban(uid, u_name, u_nickname, id, name, nickname, cause, time):
    cause = f' по причине: "{cause}"' if cause is not None else ''
    n = u_nickname if u_nickname is not None else u_name
    bn = nickname if nickname is not None else name
    if time < 3650:
        time = f' {time} дней'
    else:
        time = f'всегда'
    return get('ban', uid=uid, n=n, id=id, bn=bn, time=time, cause=cause)


def ban_error():
    return get('ban_error')


def ban_maxtime():
    return get('ban_maxtime')


def ban_myself():
    return get('ban_myself')


def ban_higher():
    return get('ban_higher')


def already_banned(name, nick, id, ban):
    time_left = (ban - time.time()) // 86400 + 1
    n = nick if nick is not None else name
    return get('already_banned', id=id, n=n, time_left=time_left)


def unban(uname, unick, uid, name, nick, id):
    un = unick if unick is not None else uname
    n = nick if nick is not None else name
    return get('unban', uid=uid, un=un, id=id, n=n)


def unban_no_ban(id, name, nick):
    n = nick if nick is not None else name
    return get('unban_no_ban', id=id, n=n)


def unban_higher():
    return get('unban_higher')


def unban_hint():
    return get('unban_hint')


def async_already_bound():
    return get('async_already_bound')


def async_done(uid, u_name, u_nickname):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('async_done', uid=uid, n=n)


def async_limit():
    return get('async_limit')


def delasync_already_unbound():
    return get('delasync_already_unbound')


def delasync_not_owner():
    return get('delasync_not_owner')


def delasync_done(uid, u_name, u_nickname, chname=''):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    if chname != '':
        chname = f' "{chname}"'
    return get('delasync_done', uid=uid, n=n, chname=chname)


def gkick(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('gkick', uid=uid, n=n, success=success, chats=chats)


def gkick_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('gkick_start', uid=uid, un=un, chats=chats, id=id, n=n)


def gkick_hint():
    return get('gkick_hint')


async def banlist(res, names, bancount):
    msg = get('banlist', bancount=bancount)

    for ind, item in enumerate(res):
        if names[ind].first_name != 'DELETED' and names[ind].last_name != 'DELETED':
            nickname = await getUserNickname(item.uid, item.chat_id)
            if nickname is not None:
                name = nickname
            else:
                name = f"{names[ind].first_name} {names[ind].last_name}"
            if literal_eval(item.last_bans_causes)[-1] is None or literal_eval(item.last_bans_causes)[-1] == '':
                cause = "Без указания причины"
            else:
                cause = literal_eval(item.last_bans_causes)[-1]
            addmsg = f"[{ind + 1}]. [id{item.uid}|{name}] | " \
                     f"{int((item.ban - time.time()) / 86400) + 1} дней | {cause} | Выдал: " \
                     f"{literal_eval(item.last_bans_names)[-1]}\n"
            if addmsg not in msg:
                msg += addmsg
    return msg


def userban_hint():
    return get('userban_hint')


def gban(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('gban', uid=uid, n=n, success=success, chats=chats)


def gban_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('gban_start', uid=uid, un=un, chats=chats, id=id, n=n)


def gban_hint():
    return get('gban_hint')


def kick_banned(id, name, nick, btime, cause):
    if nick is not None:
        n = nick
    else:
        n = name
    if cause is None:
        cause = ''
    else:
        cause = f' по причине {cause}'
    t = int((btime - time.time()) / 86400)
    return get('kick_banned', id=id, n=n, t=t, cause=cause)


def gunban(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('gunban', uid=uid, n=n, success=success, chats=chats)


def gunban_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('gunban_start', uid=uid, un=un, chats=chats, id=id, n=n)


def gunban_hint():
    return get('gunban_hint')


def gmute(uid, u_name, u_nickname, chats, success):
    n = u_name if u_nickname is None else u_nickname
    return get('gmute', uid=uid, n=n, success=success, chats=chats)


def gmute_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('gmute_start', uid=uid, un=un, chats=chats, id=id, n=n)


def gmute_hint():
    return get('gmute_hint')


def gunmute(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('gunmute', uid=uid, n=n, success=success, chats=chats)


def gunmute_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('gunmute_start', uid=uid, un=un, chats=chats, id=id, n=n)


def gunmute_hint():
    return get('gunmute_hint')


def gwarn(uid, u_name, u_nick, chats, success):
    un = u_nick if u_nick is not None else u_name
    return get('gwarn', uid=uid, un=un, success=success, chats=chats)


def gwarn_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('gwarn_start', uid=uid, un=un, chats=chats, id=id, n=n)


def gwarn_hint():
    return get('gwarn_hint')


def gunwarn(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('gunwarn', uid=uid, n=n, success=success, chats=chats)


def gunwarn_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('gunwarn_start', uid=uid, un=un, chats=chats, id=id, n=n)


def gunwarn_hint():
    return get('gunwarn_hint')


def gsnick(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('gsnick', uid=uid, n=n, success=success, chats=chats)


def gsnick_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('gkick_start', uid=uid, un=un, chats=chats, id=id, n=n)


def gsnick_hint():
    return get('gsnick_hint')


def grnick(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('grnick', uid=uid, n=n, success=success, chats=chats)


def grnick_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('grnick_start', uid=uid, un=un, chats=chats, id=id, n=n)


def grnick_hint():
    return get('grnick_hint')


def gdelaccess(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('gdelaccess', uid=uid, n=n, success=success, chats=chats)


def gdelaccess_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('gdelaccess_start', uid=uid, un=un, chats=chats, id=id, n=n)


def gdelaccess_hint():
    return get('gdelaccess_hint')


def gdelaccess_admin_unknown():
    return get('gdelaccess_admin_unknown')


def gdelaccess_admin(uid, u_name, u_nickname):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('gdelaccess_admin', uid=uid, n=n)


def setaccess_myself():
    return get('setaccess_myself')


def gsetaccess(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('gsetaccess', uid=uid, n=n, success=success, chats=chats)


def gsetaccess_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('gsetaccess_start', uid=uid, un=un, chats=chats, id=id, n=n)


def gsetaccess_hint():
    return get('gsetaccess_hint')


def zov(uid, name, nickname, cause, members):
    if nickname is not None:
        n = nickname
    else:
        n = name
    call = [f"[id{i.member_id}|\u200b\u206c]" for i in members if i.member_id > 0]
    lc = len(call)
    lm = len(members)
    jc = ''.join(call)
    return get('zov', uid=uid, n=n, lc=lc, lm=lm, cause=cause, jc=jc)


def zov_hint():
    return get('zov_hint')


def welcome(id, name, nickname):
    if nickname is not None:
        n = nickname
    else:
        n = name
    return get('welcome', id=id, n=n)


def welcome_hint():
    return get('welcome_hint')


def delwelcome(id, name, nickname):
    if nickname is not None:
        n = nickname
    else:
        n = name
    return get('delwelcome', id=id, n=n)


def delwelcome_hint():
    return get('delwelcome_hint')


def chat_unbound():
    return get('chat_unbound')


def gzov_start(uid, u_name, u_nickname, chats):
    if u_nickname is not None:
        un = u_nickname
    else:
        un = u_name
    return get('gzov_start', uid=uid, un=un, chats=chats)


def gzov(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('gzov', uid=uid, n=n, success=success, chats=chats)


def gzov_hint():
    return get('gzov_hint')


def creategroup_already_created(group):
    return get('creategroup_already_created', group=group)


def creategroup_done(uid, u_name, u_nickname, group):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('creategroup_done', uid=uid, n=n, group=group)


def creategroup_incorrect_name():
    return get('creategroup_incorrect_name')


def creategroup_hint():
    return get('creategroup_hint')


def creategroup_premium():
    return get('creategroup_premium')


def bind_group_not_found(group):
    return get('bind_group_not_found', group=group)


def bind_chat_already_bound(group):
    return get('bind_chat_already_bound', group=group)


def bind_hint():
    return get('bind_hint')


def bind(uid, u_name, u_nickname, group):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('bind', uid=uid, n=n, group=group)


def unbind_group_not_found(group):
    return get('unbind_group_not_found', group=group)


def unbind_chat_already_unbound(group):
    return get('unbind_chat_already_unbound', group=group)


def unbind_hint():
    return get('unbind_hint')


def unbind(uid, u_name, u_nickname, group):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('unbind', uid=uid, n=n, group=group)


def delgroup_not_found(group):
    return get('delgroup_not_found', group=group)


def delgroup(uid, u_name, u_nickname, group):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('delgroup', group=group, uid=uid, n=n)


def delgroup_hint():
    return get('delgroup_hint')


def s_invalid_group(group):
    return get('s_invalid_group', group=group)


def skick_hint():
    return get('skick_hint')


def skick(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('skick', uid=uid, n=n, success=success, chats=chats)


def skick_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('skick_start', uid=uid, un=un, group=group, chats=chats, id=id, n=n)


def sban_hint():
    return get('sban_hint')


def sban(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('sban', uid=uid, n=n, success=success, chats=chats)


def sban_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('sban_start', uid=uid, un=un, group=group, chats=chats, id=id, n=n)


def sunban_hint():
    return get('sunban_hint')


def sunban(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('sunban', uid=uid, n=n, success=success, chats=chats)


def sunban_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('sunban_start', uid=uid, un=un, group=group, chats=chats, id=id, n=n)


def ssnick_hint():
    return get('ssnick_hint')


def ssnick(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('ssnick', uid=uid, n=n, success=success, chats=chats)


def ssnick_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('ssnick_start', uid=uid, un=un, group=group, chats=chats, id=id, n=n)


def srnick_hint():
    return get('srnick_hint')


def srnick(uid, u_name, chats, success):
    return get('srnick', uid=uid, u_name=u_name, success=success, chats=chats)


def srnick_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('srnick_start', uid=uid, un=un, group=group, chats=chats, id=id, n=n)


def szov_hint():
    return get('szov_hint')


def szov_start(uid, u_name, u_nickname, chats, group):
    if u_nickname is not None:
        un = u_nickname
    else:
        un = u_name
    return get('szov_start', uid=uid, un=un, group=group, chats=chats)


def szov(uid, u_name, u_nickname, group, pool, success):
    if u_nickname is not None:
        un = u_nickname
    else:
        un = u_name
    return get('szov', uid=uid, un=un, success=success, pool=pool, group=group)


def ssetaccess_hint():
    return get('ssetaccess_hint')


def ssetaccess(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('ssetaccess', uid=uid, n=n, success=success, chats=chats)


def ssetaccess_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('ssetaccess_start', uid=uid, un=un, group=group, pool=chats, id=id, n=n)


def sdelaccess_hint():
    return get('sdelaccess_hint')


def sdelaccess(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return get('sdelaccess', uid=uid, n=n, success=success, chats=chats)


def sdelaccess_start(uid, u_name, u_nickname, id, name, nickname, group, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return get('ssetaccess_start', uid=uid, un=un, group=group, chats=chats, id=id, n=n)


def demote_choose():
    return get('demote_choose')


def demote_yon():
    return get('demote_yon')


def demote_disaccept():
    return get('demote_disaccept')


def demote_accept(id, name, nick):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return get('demote_accept', id=id, n=n)


def mygroups_no_groups():
    return get('mygroups_no_groups')


def addfilter(id, name, nickname):
    if nickname is not None:
        n = nickname
    else:
        n = name
    return get('addfilter', id=id, n=n)


def addfilter_hint():
    return get('addfilter_hint')


def delfilter(id, name, nickname):
    if nickname is not None:
        n = nickname
    else:
        n = name
    return get('delfilter', id=id, n=n)


def delfilter_hint():
    return get('delfilter_hint')


def delfilter_no_filter():
    return get('delfilter_no_filter')


def gaddfilter_start(uid, u_name, u_nickname, chats):
    if u_nickname is not None:
        un = u_nickname
    else:
        un = u_name
    return get('gaddfilter_start', uid=uid, un=un, chats=chats)


def gaddfilter(uid, name, chats, success):
    return get('gaddfilter', uid=uid, name=name, success=success, chats=chats)


def gaddfilter_hint():
    return get('gaddfilter_hint')


def gdelfilter_start(uid, u_name, u_nickname, chats):
    if u_nickname is not None:
        un = u_nickname
    else:
        un = u_name
    return get('gdelfilter_start', uid=uid, un=un, chats=chats)


def gdelfilter(uid, name, chats, success):
    return get('gdelfilter', uid=uid, name=name, success=success, chats=chats)


def gdelfilter_hint():
    return get('gdelfilter_hint')


def editlvl_hint():
    return get('editlvl_hint')


def editlvl(id, name, nickname, cmd, beforelvl, lvl):
    if nickname is not None:
        n = nickname
    else:
        n = name
    return get('editlvl', id=id, n=n, cmd=cmd, beforelvl=beforelvl, lvl=lvl)


def editlvl_command_not_found():
    return get('editlvl_command_not_found')


def editlvl_no_premium():
    return get('editlvl_no_premium')


def msg_hint():
    return get('msg_hint')


def blocked():
    return get('blocked')


def addblack_hint():
    return get('addblack_hint')


def addblack_myself():
    return get('addblack_myself')


def unban_myself():
    return get('unban_myself')


def addblack(uid, uname, unick, id, name, nick):
    if unick is not None:
        un = unick
    else:
        un = uname
    if nick is not None:
        n = nick
    else:
        n = name
    return get('addblack', uid=uid, un=un, id=id, n=n)


def blacked(id, name, nick):
    if nick is not None:
        n = nick
    else:
        n = name
    return get('blacked', id=id, n=n)


def delblack_hint():
    return get('delblack_hint')


def delblack_myself():
    return get('delblack_myself')


def delblack(uid, uname, unick, id, name, nick):
    if unick is not None:
        un = unick
    else:
        un = uname
    if nick is not None:
        n = nick
    else:
        n = name
    return get('delblack', uid=uid, un=un, id=id, n=n)


def delblacked(id, name, nick):
    if nick is not None:
        n = nick
    else:
        n = name
    return get('delblacked', id=id, n=n)


def delblack_no_user(id, u_name, nick):
    if nick is not None:
        n = nick
    else:
        n = u_name
    return get('delblack_no_user', id=id, n=n)


def setstatus_hint():
    return get('setstatus_hint')


def setstatus(uid, uname, unick, id, name, nick):
    if unick is not None:
        un = unick
    else:
        un = uname
    if nick is not None:
        n = nick
    else:
        n = name
    return get('setstatus', uid=uid, un=un, id=id, n=n)


def delstatus_hint():
    return get('delstatus_hint')


def delstatus(uid, uname, unick, id, name, nick):
    if unick is not None:
        un = unick
    else:
        un = uname
    if nick is not None:
        n = nick
    else:
        n = name
    return get('delstatus', uid=uid, un=un, id=id, n=n)


def sgroup_unbound(group):
    return get('sgroup_unbound', group=group)


def statuslist(names, pp):
    msg = ''

    ind = 0
    for _ in names:
        if names[ind].first_name != 'DELETED' and names[ind].last_name != 'DELETED':
            name = f"{names[ind].first_name} {names[ind].last_name}"
            np = pp[0]
            for i in pp:
                if i.uid == int(names[ind].id):
                    np = i
                    break
            addmsg = f"[{ind + 1}]. [id{names[ind].id}|{name}] | " \
                     f"Осталось: {int((np.time - time.time()) / 86400) + 1} дней\n"
            if addmsg not in msg:
                msg += addmsg
        ind += 1
    return get('statuslist', premium_status=ind) + msg


def settings():
    msg = get('settings')
    return msg


def settings_category(category, settings):
    settings = [SETTINGS_POSITIONS[category][k][i] for k, i in settings.items()]

    return get(f'settings_{category}', settings=settings)


def settings_change_countable(setting, pos, value, value2, punishment=None):
    status = "Включено" if pos else "Выключено"
    value = 0 if value is None else value
    if setting not in SETTINGS_COUNTABLE_NO_PUNISHMENT:
        if punishment == 'deletemessage':
            punishment = 'удаление сообщения'
        elif punishment == 'kick':
            punishment = f'исключение'
        elif punishment is not None and punishment.startswith('mute'):
            punishment = f'мут на {punishment.split("|")[-1]} минут'
        elif punishment is not None and punishment.startswith('ban'):
            punishment = f'блокировку на {punishment.split("|")[-1]} дней'
        else:
            punishment = 'без наказания'
        return get(f'settings_change_countable_{setting}', status=status, count=value, punishment=punishment)
    elif setting == 'nightmode':
        if not pos or value2 is None:
            value2 = '❌'
        return get(f'settings_change_countable_{setting}', status=status, time=value2)


def settings_change_countable_digit_error():
    return get(f'settings_change_countable_digit_error')


def settings_change_countable_format_error():
    return get(f'settings_change_countable_format_error')


def settings_choose_punishment():
    return get(f'settings_choose_punishment')


def settings_countable_action(action, setting):
    return get(f'settings_{action}_{setting}')


def settings_set_punishment(punishment, time=None):
    if punishment == 'deletemessage':
        punishment = 'удаление сообщения'
    elif punishment == 'mute':
        punishment = f'мут на {time} минут'
    elif punishment == 'kick':
        punishment = f'исключение'
    elif punishment == 'ban':
        punishment = f'блокировку на {time} дней'
    return get('settings_set_punishment', punishment=punishment)


def settings_set_punishment_input(punishment):
    return get(f'settings_set_punishment_{punishment}', punishment=punishment)


def settings_change_countable_done(setting, data):
    return get(f'settings_change_countable_done_{setting}', data=data)


def settings_set_punishment_countable(action, count):
    return get(f'settings_set_punishment',
               punishment=(SETTINGS_COUNTABLE_CHANGEPUNISHMENTMESSAGE[action].format(count=count)))


def settings_setlist(setting, type):
    return get(f'settings_{setting}_set{type.lower()}list')


def settings_exceptionlist(exceptions):
    msg = ''
    for k, i in enumerate(exceptions):
        msg += f'[{k + 1}]. {i.url}'
    return get('settings_exceptionlist', msg=msg)


def settings_listaction_action(setting, action):
    return get(f'settings_listaction_{setting}_{action}')


def settings_listaction_done(setting, action, data):
    return get(f'settings_listaction_{setting}_{action}_done', data=data)


def giveStatus(date):
    return get('giveStatus', date=date)


def ugiveStatus(date, gave, name):
    return get('ugiveStatus', date=date, gave=gave, name=name)


def udelStatus(uid, dev_name):
    return get('udelStatus', uid=uid, dev_name=dev_name)


def uexpStatus():
    return get('uexpStatus')


def q(uid, name, nick):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return get('q', uid=uid, n=n)


def q_fail(uid, name, nick):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return get('q_fail', uid=uid, n=n)


def premium():
    return get('premium')


def premium_sent(uid, name, nickname):
    if nickname is not None and len(nickname) >= 0:
        n = nickname
    else:
        n = name
    return get('premium_sent', uid=uid, n=n)


def chat(uid, uname, chat_id, bind, gbind, muted, banned, users, time, prefix, chat_name):
    return get('chat', prefix=prefix, uid=uid, uname=uname, chat_id=chat_id, chat_name=chat_name, bind=bind,
               gbind=gbind, banned=banned, muted=muted, users=users, time=time)


def getnick(res, names, members, query):
    msg = ''
    cnt = 0
    for it in members:
        if it.member_id < 0:
            members.remove(it)
    for ind, item in enumerate(res):
        for i in members:
            if i.member_id == item.uid and i.member_id > 0:
                try:
                    if names[ind].first_name != 'DELETED' and names[ind].last_name != 'DELETED':
                        cnt += 1
                        addmsg = f"{cnt}. {item.nickname} - [id{item.uid}|{names[ind].first_name} " \
                                 f"{names[ind].last_name}]\n"
                        if addmsg not in msg:
                            msg += addmsg
                except:
                    pass
    msg = get('getnick', query=query, cnt=cnt) + msg
    return msg


def getnick_no_result(query):
    return get('getnick_no_result', query=query)


def getnick_hint():
    return get('getnick_hint')


def id_group():
    return get('id_group')


def id_deleted():
    return get('id_deleted')


def clear_old():
    return get('clear_old')


def mkick_error():
    return get('mkick_error')


def no_prem():
    return get('no_prem')


def mkick_no_kick():
    return get('mkick_no_kick')


def giveowner_hint():
    return get('giveowner_hint')


def giveowner_ask():
    return get('giveowner_ask')


def giveowner_no():
    return get('giveowner_no')


def giveowner(uid, unick, uname, id, nick, name):
    if unick is not None and len(unick) > 0:
        un = unick
    else:
        un = uname
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return get('giveowner', uid=uid, un=un, id=id, n=n)


def bonus(id, nick, name, xp):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return get('bonus', id=id, n=n, xp=xp)


def bonus_time(id, nick, name, timeleft):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    hours = pointHours((timeleft // 3600) * 3600)
    minutes = pointMinutes(timeleft - (timeleft // 3600) * 3600)
    return get('bonus_time', id=id, n=n, hours=hours, minutes=minutes)


def top_lvls(names, lvls, category='общее'):
    dl = calendar.monthrange(datetime.now().year, datetime.now().month)[1] - datetime.now().day + 1
    msg = get('top_lvls', category=category, dl=dl)
    for index, item in enumerate(list(lvls.values())):
        try:
            name = f"{names[index].first_name} {names[index].last_name}"
            addmsg = f"[{index + 1}]. [id{names[index].id}|{name}] - {item} уровень\n"
            if addmsg not in msg:
                msg += addmsg
        except:
            pass
    return msg


def top_duels(names, duels, category='общее'):
    msg = get('top_duels', category=category)
    for index, item in enumerate(list(duels.values())):
        try:
            name = f"{names[index].first_name} {names[index].last_name}"
            addmsg = f"[{index + 1}]. [id{names[index].id}|{name}] - {item} побед\n"
            if addmsg not in msg:
                msg += addmsg
        except:
            pass
    return msg


def premmenu(settings):
    msg = get('premmenu')
    k = 0
    for e, i in settings.items():
        k += 1
        if e == 'clear_by_fire':
            msg += f'\n[{k}]. Удаление сообщения с помощью реакции(🔥) '
            if i == 1:
                msg += '| ✔'
            else:
                msg += '| ❌'
        elif e == 'border_color':
            msg += f'\n[{k}]. Смена цвета рамки в /stats | 🛠 В разработке'
    return msg


def addprefix_hint():
    return get('addprefix_hint')


def addprefix_max():
    return get('addprefix_max')


def addprefix_too_long():
    return get('addprefix_too_long')


def addprefix(uid, name, nick, prefix):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return get('addprefix', uid=uid, n=n, prefix=prefix)


def delprefix_hint():
    return get('delprefix_hint')


def delprefix(uid, name, nick, prefix):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return get('delprefix', uid=uid, n=n, prefix=prefix)


def delprefix_not_found(prefix):
    return get('delprefix_not_found', prefix=prefix)


def listprefix(uid, name, nick, prefixes):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    msg = get('listprefix', uid=uid, n=n)
    if len(prefixes) == 0:
        msg += 'Префиксов не обнаружено. Используйте команду /addprefix'
    for i in prefixes:
        msg += f'➖ "{i.prefix}"\n'
    return msg


def levelname_hint():
    return get('levelname_hint')


def levelname(uid, name, nick, lvl, lvlname):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return get('levelname', uid=uid, n=n, lvlname=lvlname, lvl=lvl)


def resetlevel_hint():
    return get('resetlevel_hint')


def cmdcount(cmdcounter):
    summ = 0
    for i in cmdcounter:
        summ += i.count
    msg = get('cmdcount')
    for i in cmdcounter:
        if i.cmd not in msg:
            msg += f'➖{i.cmd} | использовано: {i.count} раз | {str(i.count / summ * 100)[:5]}%\n'
    return msg


def lvl_up(lvl):
    return get('lvl_up', lvl=lvl, lvlp=lvl + 1)


def ignore_hint():
    return get('ignore_hint')


def ignore_not_found():
    return get('ignore_not_found')


def ignore(id, name, nick):
    if nick is not None:
        n = nick
    else:
        n = name
    return get('ignore', id=id, n=n)


def unignore_hint():
    return get('unignore_hint')


def unignore_not_found():
    return get('unignore_not_found')


def unignore_not_ignored():
    return get('unignore_not_ignored')


def unignore(id, name, nick):
    if nick is not None:
        n = nick
    else:
        n = name
    return get('unignore', id=id, n=n)


def ignorelist(res, names):
    msg = get('ignorelist', lres=len(res))
    k = 0
    for i in res:
        addmsg = f'➖ [id{i.uid}|{names[k]}]'
        if addmsg not in msg:
            msg += addmsg
        k += 1
    return msg


def chatlimit_hint():
    return get('chatlimit_hint')


def chatlimit(id, name, nick, t, postfix, lpos):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    if bool(t):
        if t == 1 or (t > 20 and int(str(t)[-1]) == 1):
            if postfix == 's':
                postfix = 'секунду'
            elif postfix == 'm':
                postfix = 'минуту'
            else:
                postfix = 'час'
        elif t in [2, 3, 4] or (t > 20 and int(str(t)[-1]) in [2, 3, 4]):
            if postfix == 's':
                postfix = 'секунды'
            elif postfix == 'm':
                postfix = 'минуты'
            else:
                postfix = 'час'
        else:
            if postfix == 's':
                postfix = 'секунд'
            elif postfix == 'm':
                postfix = 'минут'
            else:
                postfix = 'часов'
        return get('chatlimit', id=id, n=n, t=t, postfix=postfix)
    else:
        if lpos == 0:
            return get('chatlimit_already_on')
        else:
            return get('chatlimit_off', id=id, n=n)


def pm():
    return get('pm')


def pm_market():
    return get('pm_market')


def pm_market_buy(days, cost, last_payment, link):
    return get('pm_market_buy', days=days, cost=cost, last_payment=last_payment, link=link)


def payment_success(order_id, days):
    return get('payment_success', order_id=order_id, days=days)


def cmd_changed_in_cmds():
    return get('cmd_changed_in_cmds')


def cmd_changed_in_users_cmds(cmd):
    return get('cmd_changed_in_users_cmds', cmd=cmd)


def cmd_hint():
    return get('cmd_hint')


def cmd_prem():
    return get('cmd_prem')


def cmd_set(uid, name, nick, cmd, changed):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return get('cmd_set', uid=uid, n=n, changed=changed, cmd=cmd)


def resetcmd_hint():
    return get('resetcmd_hint')


def resetcmd_not_found(cmd):
    return get('resetcmd_not_found', cmd=cmd)


def resetcmd_not_changed(cmd):
    return get('resetcmd_not_changed', cmd=cmd)


def resetcmd(uid, name, nick, cmd, cmdname):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return get('resetcmd', uid=uid, n=n, cmdname=cmdname, cmd=cmd)


def cmd_char_limit():
    return get('cmd_char_limit')


def cmdlist(cmdnames, page, cmdlen):
    msg = get('cmdlist', cmdlen=cmdlen)
    c = page * 10
    for k, i in cmdnames.items():
        c += 1
        msg += f'[{c}] {k} - {i}\n'
    return msg


def listasync(chats, total):
    msg = ''
    for k, i in enumerate(chats[:10]):
        if i["name"] is not None:
            msg += f'\n➖ ID: {i["id"]} | Название: {i["name"]}'
        else:
            total -= 1
    if total <= 0:
        msg = get('listasync_not_found')
    else:
        msg = get('listasync', total=total) + msg
    return msg


def duel_not_allowed():
    return get('duel_not_allowed')


def duel_hint():
    return get('duel_hint')


def duel_uxp_not_enough(uid, name, nick):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return get('duel_uxp_not_enough', uid=uid, n=n)


def duel_xp_minimum():
    return get('duel_xp_minimum')


def duel(uid, name, nick, xp):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return get('duel', uid=uid, n=n, xp=xp)


def duel_res(uid, uname, unick, id, name, nick, xp, prem):
    if unick is not None and len(unick) > 0:
        un = unick
    else:
        un = uname
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    if prem is not None and int(prem) > 0:
        return get('duel_res', uid=uid, un=un, id=id, n=n, xp=xp)
    else:
        return get('duel_res', uid=uid, un=un, id=id, n=n, xp=int(xp / 100 * 90))


def dueling():
    return get('dueling')


def resetnick_yon():
    return get('resetnick_yon')


def resetnick_accept(id, name):
    return get('resetnick_accept', id=id, name=name)


def resetnick_disaccept():
    return get('resetnick_disaccept')


def resetaccess_hint():
    return get('resetaccess_hint')


def resetaccess_yon(lvl):
    return get('resetaccess_yon', lvl=lvl)


def resetaccess_accept(id, name, lvl):
    return get('resetaccess_accept', id=id, name=name, lvl=lvl)


def resetaccess_disaccept(lvl):
    return get('resetaccess_disaccept', lvl=lvl)


def olist(members):
    msg = get('olist', members=len(list(members.keys())))
    ind = 0
    for k, i in members.items():
        ind += 1
        msg += f"[{ind}]. {k} - "
        if i:
            msg += "Телефон\n"
        else:
            msg += "ПК\n"
    return msg


def farm(name, uid):
    return get('farm', name=name, uid=uid)


def farm_cd(name, uid, timeleft):
    return get('farm_cd', name=name, uid=uid, tl=int(timeleft / 60) + 1)


def kickmenu():
    return get('kickmenu')


def kickmenu_kick_nonick(uid, name, nick, kicked):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return get('kickmenu_kick_nonick', uid=uid, n=n, kicked=kicked)


def kickmenu_kick_nick(uid, name, nick, kicked):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return get('kickmenu_kick_nick', uid=uid, n=n, kicked=kicked)


def kickmenu_kick_banned(uid, name, nick, kicked):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return get('kickmenu_kick_banned', uid=uid, n=n, kicked=kicked)


def rewards(sub, wd):
    subs = wds = ''
    if sub >= 1:
        sub = 1
        subs = '✅'
    if wd >= 10:
        wd = 10
        wds = '✅'
    return get('rewards', sub=sub, subs=subs, wd=wd, wds=wds)


def lock(time):
    return get('lock', time=time)


def send_notification(text, tagging):
    return get('send_notification', text=text, tagging=tagging)


def notif(notifs, activenotifs):
    return get('notif', lnotifs=len(notifs), lactive=len(activenotifs))


def notif_already_exist(name):
    return get('notif_already_exist', name=name)


def notification(name, text, time, every, tag, status):
    msg = get('name', name=name, text=text)

    if every == 1440:
        msg += f'Каждый день в {datetime.fromtimestamp(time).strftime("%H:%M")}'
    elif every > 0:
        msg += f'Каждые {every} минут'
    elif every != -1:
        msg += f'Один раз в {datetime.fromtimestamp(time).strftime("%H:%M")}'

    msg += '\n🔔 Тег: '

    if tag == 1:
        msg += 'Отключено'
    elif tag == 2:
        msg += 'Всех'
    elif tag == 3:
        msg += 'С правами'
    elif tag == 4:
        msg += 'Без прав'

    msg += '\n\n🟣 Статус: '

    if status == 0:
        msg += 'Выключено'
    elif status == 1:
        msg += 'Включено'

    return msg


def notification_changing_text():
    return get('notification_changing_text')


def notification_changed_text(name):
    return get('notification_changed_text', name=name)


def notification_changing_time_choose():
    return get('notification_changing_time_choose')


def notification_changing_time_single():
    return get('notification_changing_time_single')


def notification_changing_time_everyday():
    return get('notification_changing_time_everyday')


def notification_changing_time_everyxmin():
    return get('notification_changing_time_everyxmin')


def notification_changed_time(name):
    return get('notification_changed_time', name=name)


def notification_changing_time_error():
    return get('notification_changing_time_error')


def notification_delete(name):
    return get('notification_delete', name=name)


def notification_changing_tag_choose():
    return get('notification_changing_tag_choose')


def notification_changing_tag_changed(name):
    return get('notification_changing_tag_changed', name=name)


def notification_too_long_text(name):
    return get('notification_too_long_text', name=name)


def notifs(notifs):
    msg = get('notifs')

    for k, i in enumerate(notifs):
        if i.status == 1:
            status = 'Включено'
        else:
            status = 'Выключено'
        msg += f'[{k + 1}]. {i.name} | {status}\n'

    return msg


def transfer_hint():
    return get('transfer_hint')


def transfer_wrong_number():
    return get('transfer_wrong_number')


def transfer_not_enough(uid, name, nickname):
    n = name if nickname is None else nickname
    return get('transfer_not_enough', uid=uid, n=n)


def transfer_myself():
    return get('transfer_myself')


def transfer_community():
    return get('transfer_community')


def transfer(uid, uname, id, name, xp, u_prem):
    if int(u_prem) == 0:
        return get('transfer', uid=uid, uname=uname, xp=xp, id=id, name=name)
    else:
        return get('transfer_nocom', uid=uid, uname=uname, xp=xp, id=id, name=name)


def transfer_not_allowed():
    return get('transfer_not_allowed')


def notadmin():
    return get('notadmin')


def bot_info(chats, total_users, users, premium_users, all_groups, biggest_gpool, biggest_gpool_owner_name, max_pool,
             max_group_name, max_group_count, biggest_chat_id, biggest_chat_users, biggest_chat_owner_id,
             biggest_chat_owner_name):
    return get('bot_info', lchats=len(chats), total_users=total_users, lusers=len(users), premium_users=premium_users,
               lag=len(all_groups), biggest_gpool=biggest_gpool, biggest_gpool_owner_name=biggest_gpool_owner_name,
               max_pool=max_pool, max_group_name=max_group_name, max_group_count=max_group_count,
               biggest_chat_id=biggest_chat_id, biggest_chat_users=biggest_chat_users,
               biggest_chat_owner_id=biggest_chat_owner_id, biggest_chat_owner_name=biggest_chat_owner_name)


def warn_report(uid, name, uwarns, from_id, from_name):
    if uwarns <= 0:
        h = '💙'
    elif uwarns == 1:
        h = '💚'
    else:
        h = '💛'
    return get('warn_report', h=h, uid=uid, name=name, from_id=from_id, from_name=from_name, uwarns=uwarns)


def unwarn_report(uid, name, uwarns, from_id, from_name):
    if uwarns <= 0:
        h = '💙'
    elif uwarns == 1:
        h = '💚'
    else:
        h = '💛'
    return get('unwarn_report', h=h, uid=uid, name=name, from_id=from_id, from_name=from_name, uwarns=uwarns)


def reportwarn(uid, name, uwarns):
    if uwarns <= 0:
        h = '💙'
    elif uwarns == 1:
        h = '💚'
    else:
        h = '💛'
    return get('reportwarn', h=h, uid=uid, name=name, uwarns=uwarns)


def warn_report_ban(uid, name, from_id, from_name):
    return get('warn_report_ban', uid=uid, name=name, from_id=from_id, from_name=from_name)


def reboot():
    return get('reboot')


def like_premium_bonus(days):
    return get('like_premium_bonus', days=days)


def givexp(uid, dev_name, id, u_name, xp):
    return get('givexp', uid=uid, dev_name=dev_name, xp=xp, id=id, u_name=u_name)


def inprogress():
    return get('inprogress')


def msg(devmsg):
    return get('msg', devmsg=devmsg)


def stats_loading():
    return get('stats_loading')


def infunban_noban():
    return get('infunban_noban')


def infunban_hint():
    return get('infunban_hint')


def infunban():
    return get('infunban')


def infban_hint():
    return get('infban_hint')


def infban():
    return get('infban')


def newseason_top(top, reward):
    return get('newseason_top', top=top, reward=reward)


async def newseason_post(top, season_start, season_end):
    msg = get('newseason_post_f')
    for i in top:
        msg += f'[id{i.uid}|{await getUserName(i.uid)}] - {await getUserLVL(i.xp)} уровень\n'
    msg += get('newseason_post_s', season_start=season_start, season_end=season_end)
    return msg


def task(tasks, coins, streak):
    return get('task', tasks=tasks, coins=coins, streak=streak)


def task_not_allowed():
    return get('task_not_allowed')


def task_trade(c):
    return get('task_trade', c=c)


def task_trade_not_enough(c):
    return get('task_trade_not_enough', c=c)


def task_trade_lot(lot):
    buy = f'{TASKS_LOTS[list(TASKS_LOTS.keys())[lot - 1]]} '
    if lot < 4:
        buy += 'уровня'
    else:
        buy += 'дня Premium подписки'
    return get('task_trade_lot', buy=buy)


def task_trade_lot_log(lot, id, name):
    buy = f'{TASKS_LOTS[list(TASKS_LOTS.keys())[lot - 1]]} '
    if lot < 4:
        buy += 'уровня'
    else:
        buy += 'дня Premium подписки'
    return get('task_trade_lot_log', id=id, name=name, buy=buy)


def task_weekly(prem, tasks):
    def point(num, maxv):
        return num if num < maxv else maxv
    count = [point(tasks[0], TASKS_WEEKLY["bonus"]) == TASKS_WEEKLY["bonus"],
             point(tasks[1], TASKS_WEEKLY["dailytask"]) == TASKS_WEEKLY["dailytask"],
             point(tasks[2], TASKS_WEEKLY["sendmsgs"]) == TASKS_WEEKLY["sendmsgs"]].count(True)
    if prem:
        count += [point(tasks[3], PREMIUM_TASKS_WEEKLY["lvlup"]) == PREMIUM_TASKS_WEEKLY["lvlup"],
                  point(tasks[4], PREMIUM_TASKS_WEEKLY["duelwin"]) == PREMIUM_TASKS_WEEKLY["duelwin"]].count(True)
    tl = datetime.now()
    tl = 24 * (7 - tl.weekday()) - tl.hour - 1
    hours = pointHours((tl % 24) * 3600)
    days = pointDays((tl // 24) * 86400)
    msg = f'''🟣 Выполнено заданий — {count} / {5 if prem else 3}
🟣 До сброса заданий — {days} {hours}\n
[1]. Забрать приз /bonus 6 раз | {point(tasks[0], TASKS_WEEKLY["bonus"])} / 6
[2]. Выполнить ежедневные задания 7 раз | {point(tasks[1], TASKS_WEEKLY["dailytask"])} / 7
[3]. Отправить 10.000 сообщений | {point(tasks[2], TASKS_WEEKLY["sendmsgs"])} / 10.000'''
    if prem:
        msg += f'''\n[4]. Повысить 10 уровней профиля | {point(tasks[3], PREMIUM_TASKS_WEEKLY["lvlup"])} / 10
[5]. Победить 60 раз в дуэлях | {point(tasks[4], PREMIUM_TASKS_WEEKLY["duelwin"])} / 60'''
    return msg + '''\n\n🪙 За каждое задание вы получаете +10 монет Star.'''


def task_daily(prem, tasks):
    def point(num, maxv):
        return num if num < maxv else maxv
    count = [point(tasks[0], TASKS_DAILY["sendmsgs"]) == TASKS_DAILY["sendmsgs"],
             point(tasks[1], TASKS_DAILY["sendvoice"]) == TASKS_DAILY["sendvoice"],
             point(tasks[2], TASKS_DAILY["duelwin"]) == TASKS_DAILY["duelwin"]].count(True)
    if prem:
        count += [point(tasks[3], PREMIUM_TASKS_DAILY["cmds"]) == PREMIUM_TASKS_DAILY["cmds"],
                  point(tasks[4], PREMIUM_TASKS_DAILY["stickers"]) == PREMIUM_TASKS_DAILY["stickers"]].count(True)
    tl = datetime.now()
    tl = 1440 - tl.hour * 60 - tl.minute
    hours = pointHours((tl // 60) * 3600)
    minutes = pointMinutes((tl % 60) * 60)

    msg = (f'🟣 Выполнено заданий — {count} / {5 if prem else 3}\n'
           f'🟣 До сброса заданий — {hours} {minutes}\n\n')
    if prem:
        if point(tasks[0], TASKS_DAILY["sendmsgs"]) == TASKS_DAILY["sendmsgs"]:
            msg += (f'[1.1]. Отправить 600 сообщений | '
                    f'{point(tasks[0], PREMIUM_TASKS_DAILY_TIERS["sendmsgs"])} / 600\n')
        else:
            msg += f'[1]. Отправить 300 сообщений | {point(tasks[0], TASKS_DAILY["sendmsgs"])} / 300\n'
        if point(tasks[1], TASKS_DAILY["sendvoice"]) == TASKS_DAILY["sendvoice"]:
            msg += (f'[2.1]. Отправить 60 голосовых сообщений | '
                    f'{point(tasks[1], PREMIUM_TASKS_DAILY_TIERS["sendvoice"])} / 60\n')
        else:
            msg += f'[2]. Отправить 30 голосовых сообщений | {point(tasks[1], TASKS_DAILY["sendvoice"])} / 30\n'
        if point(tasks[2], TASKS_DAILY["duelwin"]) == TASKS_DAILY["duelwin"]:
            msg += (f'[3.1]. Победить 25 раз в дуэлях | '
                    f'{point(tasks[2], PREMIUM_TASKS_DAILY_TIERS["duelwin"])} / 25\n')
        else:
            msg += f'[3]. Победить 15 раз в дуэлях | {point(tasks[2], TASKS_DAILY["duelwin"])} / 15\n'
        if point(tasks[3], PREMIUM_TASKS_DAILY["cmds"]) == PREMIUM_TASKS_DAILY["cmds"]:
            msg += (f'[4.1]. Использовать команды бота 100 раз | '
                    f'{point(tasks[3], PREMIUM_TASKS_DAILY_TIERS["cmds"])} / 100\n')
        else:
            msg += f'[4]. Использовать команды бота 50 раз | {point(tasks[3], PREMIUM_TASKS_DAILY["cmds"])} / 50\n'
        if point(tasks[4], PREMIUM_TASKS_DAILY["stickers"]) == PREMIUM_TASKS_DAILY["stickers"]:
            msg += (f'[5.1]. Отправить 200 стикеров | '
                    f'{point(tasks[4], PREMIUM_TASKS_DAILY_TIERS["stickers"])} / 200\n')
        else:
            msg += f'[5]. Отправить 100 стикеров | {point(tasks[4], PREMIUM_TASKS_DAILY["stickers"])} / 100\n'
    else:
        msg += f'''[1]. Отправить 300 сообщений | {point(tasks[0], TASKS_DAILY["sendmsgs"])} / 300
[2]. Отправить 30 голосовых сообщений | {point(tasks[1], TASKS_DAILY["sendvoice"])} / 30
[3]. Победить 15 раз в дуэлях | {point(tasks[2], TASKS_DAILY["duelwin"])} / 15\n'''

    return msg + '''\n🪙 За каждое задание вы получаете +5 монет Star.'''


def resetlvl(id, u_name):
    return get('resetlvl', id=id, u_name=u_name)


def resetlvlcomplete(id, u_name):
    return get('resetlvlcomplete', id=id, u_name=u_name)


def check_help():
    return get('check_help')


def check(id, name, nickname, ban, warn, mute):
    n = nickname if nickname is not None else name
    ban = pointDays(ban) if ban else "Отсутствуют"
    warn = f"{warn} из 3" if warn else "Отсутствуют"
    mute = pointMinutes(mute) if mute else "Отсутствует"
    return get('check', id=id, n=n, ban=ban, warn=warn, mute=mute)


def check_ban(id, name, nickname, ban, ban_history, ban_date, ban_from, ban_reason, ban_time):
    n = nickname if nickname is not None else name
    lbh = len(ban_history)
    banm = pointDays(ban) if ban else "Отсутствует"
    msg = get('check_ban', id=id, n=n, lbh=lbh, banm=banm)
    if ban:
        msg += f'★ {ban_date} | {ban_from} | {pointDays(ban_time)} | {ban_reason}'
    return msg


def check_mute(id, name, nickname, mute, mute_history, mute_date, mute_from, mute_reason, mute_time):
    n = nickname if nickname is not None else name
    lmh = len(mute_history)
    mutem = pointMinutes(mute) if mute else "Отсутствует"
    msg = get('check_mute', id=id, n=n, lmh=lmh, mutem=mutem)
    if mute:
        msg += f'★ {mute_date} | {mute_from} | {pointMinutes(mute_time)} | {mute_reason}'
    return msg


def check_warn(id, name, nickname, warn, warn_history, warns_date, warns_from, warns_reason):
    n = nickname if nickname is not None else name
    lwh = len(warn_history)
    warnm = f"{warn} из 3" if warn else "Отсутствуют"
    msg = get('check_warn', id=id, n=n, lwh=lwh, warnm=warnm)
    if warn:
        for k, _ in enumerate(warn_history[:warn]):
            msg += f'★ {warns_date[k]} | {warns_from[k]} | {warn - k} из 3 | {warns_reason[k]}\n'

    return msg


def check_history_ban(id, name, nickname, dates, names, times, causes):
    n = nickname if nickname is not None else name
    msg = get('check_history_ban', id=id, n=n)
    for k in range(len(times)):
        msg += f'★ {dates[k]} | {names[k]} | {pointDays(times[k])} | {causes[k]}\n'
    return msg


def check_history_mute(id, name, nickname, dates, names, times, causes):
    n = nickname if nickname is not None else name
    msg = get('check_history_mute', id=id, n=n)
    for k in range(len(times)):
        msg += f'★ {dates[k]} | {names[k]} | {pointMinutes(times[k])} | {causes[k]}\n'
    return msg


def check_history_warn(id, name, nickname, dates, names, times, causes):
    n = nickname if nickname is not None else name
    msg = get('check_history_warn', id=id, n=n)
    for k in range(len(times)):
        msg += f'★ {dates[k]} | {names[k]} | {causes[k]}\n'
    return msg


def purge_start():
    return get('purge_start')


def purge_empty():
    return get('purge_empty')


def purge(nicknames, levels):
    nicknames = pointWords(nicknames, ("никнейм", "никнейма", "никнеймов"))
    levels = pointWords(levels, ("уровень", "уровня", "уровней"))
    return get('purge', nicknames=nicknames, levels=levels)


def lvlbanned():
    return get('lvlbanned')


def lvlunban_noban():
    return get('lvlunban_noban')


def lvlunban_hint():
    return get('lvlunban_hint')


def lvlunban():
    return get('lvlunban')


def lvlban_hint():
    return get('lvlban_hint')


def lvlban():
    return get('lvlban')


def user_lvlbanned():
    return get('user_lvlbanned')


def anon_not_pm():
    return get('anon_not_pm')


def anon_help():
    return get('anon_help')


def anon_chat_does_not_exist():
    return get('anon_chat_does_not_exist')


def anon_not_member():
    return get('anon_not_member')


def anon_limit():
    return get('anon_limit')


def anon_link():
    return get('anon_link')


def anon_attachments():
    return get('anon_link')


def anon_message(id, text):
    return get('anon_message', id=id, text=text)


def anon_sent(id, chatname):
    return get('anon_sent', id=id, chatname=chatname)


def anon_not_allowed():
    return get('anon_not_allowed')


def deanon_help():
    return get('deanon_help')


def deanon_target_not_found():
    return get('deanon_target_not_found')


def deanon(id, from_id, name, nickname, time):
    n = nickname if nickname is not None else name
    time = datetime.fromtimestamp(time).strftime('%d.%m.%Y - %H:%M')
    return get('deanon', id=id, from_id=from_id, from_name=n, time=time)


def antispam_punishment(uid, name, nick, setting, punishment, violation_count, time=None):
    n = nick if nick is not None else name
    return get(f'antispam_punishment_{setting}_{punishment}', uid=uid, n=n, time=time,
               violation_count=violation_count)


def nightmode_start(start, end):
    return get('nightmode_start', start=start, end=end)


def nightmode_end():
    return get('nightmode_end')


def speccommandscooldown(time):
    return get('speccommandscooldown', time=pointWords(time, ['секунду', 'секунды', 'секунд']))
