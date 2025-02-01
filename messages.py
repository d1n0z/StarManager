import calendar
import time
import traceback
from ast import literal_eval
from datetime import datetime

from memoization import cached

from Bot.utils import getUserNickname, pointMinutes, pointDays, pointHours, pointWords, getUserName, getLVLFromXP, \
    getChatAccessName
from config.config import COMMANDS, LVL_NAMES, COMMANDS_DESC, SETTINGS_POSITIONS, \
    SETTINGS_COUNTABLE_CHANGEPUNISHMENTMESSAGE, SETTINGS_COUNTABLE_NO_PUNISHMENT
from db import syncpool


@cached
def get(key: str, **kwargs):
    with syncpool().connection() as conn:
        with conn.cursor() as c:
            return c.execute('select text from botmessages where key=%s', (key,)).fetchone()[0].format(**kwargs)


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


async def top(top):
    return get('top') + ''.join(
        [f"[{k + 1}]. [id{i[0]}|{await getUserName(i[0])}] - {i[1]} сообщений\n" for k, i in enumerate(top)])


def help(page=0, cmds=COMMANDS):
    if page == 8:
        return get('help_page8')

    descs = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []}
    for k, i in cmds.items():
        try:
            descs[int(i)].append(COMMANDS_DESC[k])
        except:
            pass
    return get(f'help_page{page}') + ''.join([f'{i}\n' for i in descs[page]]) + get('help_last')


def helpdev():
    return get('helpdev')


def help_closed():
    return get('help_closed')


def help_sent(id, name, nick):
    return get('help_sent', id=id, n=nick if nick else name)


def query_error():
    return get('query_error')


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
    return get('kick', uid=uid, u_name=u_nick if u_nick else u_name, i='club' if id < 0 else 'id',
               id=abs(id), ch_name=ch_nick if ch_nick else ch_name, cause=cause)


def kicked(uid, name, nickname):
    return get('kicked', uid=uid, un=nickname if nickname else name)


def kick_error():
    return get('kick_error')


def kick_access(id, name, nick):
    return get('kick_access', i='club' if id < 0 else 'id', id=abs(id),
               n=nick if nick else name)


def kick_myself():
    return get('kick_myself')


def kick_higher():
    return get('kick_higher')


def mute_hint():
    return get('mute_hint')


def mute(name, nick, id, mutingname, mutingnick, mutingid, cause, time):
    return get('mute', id=id, n=nick if nick else name, mutingid=mutingid,
               mn=mutingnick if mutingnick else mutingname, time=time,
               cause=' по причине: ' + cause if cause else '')


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
    return get('already_muted', id=id, n=nick if nick else name, time_left=int((mute - time.time()) / 60))


def usermute_hint():
    return get('usermute_hint')


def userwarn_hint():
    return get('userwarn_hint')


def warn_hint():
    return get('warn_hint')


def warn(name, nick, uid, ch_name, ch_nick, id, cause):
    return get('warn', uid=uid, n=nick if nick else name, cause=' по причине: ' + cause if cause else '',
               cn=ch_nick if ch_nick else ch_name, id=id)


def warn_kick(name, nick, uid, ch_name, ch_nick, id, cause):
    return get('warn_kick', uid=uid, n=nick if nick else name, id=id, cn=ch_nick if ch_nick else ch_name,
               cause=' по причине: ' + cause if cause else '')


def warn_higher():
    return get('warn_higher')


def warn_myself():
    return get('warn_myself')


def unwarn_myself():
    return get('unwarn_myself')


def clear(names, u_name, uid):
    return get('clear', uid=uid, u_name=u_name, users=", ".join(
        set([f"[{'id' if int(id) > 0 else 'club'}{id}|{name}]" for id, name in names.items()])))


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
    return get('snick', uid=uid, un=u_nickname if u_nickname else u_name, id=id,
               newnickname=newnickname, n=nickname if nickname else ch_name)


def rnick_hint():
    return get('rnick_hint')


def rnick_user_has_no_nick():
    return get('rnick_user_has_no_nick')


def rnick_higher():
    return get('rnick_higher')


def rnick(uid, u_name, u_nick, id, name, nick):
    return get('rnick', uid=uid, un=u_nick if u_nick else u_name, id=id, nick=nick, name=name)


def nlist(res, members, page=0):
    msg, cnt, res = get('nlist'), 0, {item[0]: item for item in res}
    for it in members:
        if it.id < 0 or 'DELETED' in (it.first_name, it.last_name) or not (item := res.get(it.id)):
            continue
        cnt += 1
        msg += f"{cnt + 30 * page}. {item[1]} - [id{item[0]}|{it.first_name} {it.last_name}]\n"
    return msg


def nnlist(members, page=0):
    msg, k = get('nnlist'), page * 30
    for i in members:
        try:
            if i.first_name == 'DELETED' or i.last_name == 'DELETED' or i.id <= 0:
                continue
            msg += f"{k + 1}. [id{i.id}|{i.first_name} {i.last_name}]\n"
            k += 1
        except:
            pass
    return msg


async def staff(res, names, chat_id):
    msg, admins, users = get('staff'), set(), {}
    for ind, item in enumerate(res):
        if f'{item[1]}' not in users:
            users[f'{item[1]}'] = []
        users[f'{item[1]}'].append({
            "uid": item[0], "name": [f"{i.first_name} {i.last_name}" for i in names if i.id == item[0]][0],
            "nickname": await getUserNickname(item[0], chat_id), "access_level": item[1]})
    emoji = {'1': '☀', '2': '🔥', '3': '🔥', '4': '🔥', '5': '✨', '6': '⚡', '7': '⭐'}
    for k in sorted(users.keys(), reverse=True):
        msg += f'[{emoji[k]}] {await getChatAccessName(chat_id, int(k), LVL_NAMES[int(k)])}\n' + ''.join(
            [f"➖ [id{item['uid']}|{item['nickname'] if item['nickname'] else item['name']}]\n" for item in users[k]])
    return msg


def unmute(uname, unickname, uid, name, nickname, id):
    return get('unmute', uid=uid, un=unickname if unickname else uname, id=id, n=nickname if nickname else name)


def unmute_no_mute(id, name, nickname):
    return get('unmute_no_mute', id=id, n=nickname if nickname else name)


def unmute_higher():
    return get('unmute_higher')


def unmute_hint():
    return get('unmute_hint')


def unwarn(uname, unick, uid, name, nick, id):
    return get('unwarn', uid=uid, un=unick if unick else uname, id=id, n=nick if nick else name)


def unwarn_no_warns(id, name, nick):
    return get('unwarn_no_warns', id=id, n=nick if nick else name)


def unwarn_higher():
    return get('unwarn_higher')


def unwarn_hint():
    return get('unwarn_hint')


async def mutelist(res, mutedcount):
    msg = get('mutelist', mutedcount=mutedcount)
    for ind, item in enumerate(res):
        nickname = await getUserNickname(item[0], item[1])
        msg += (
            f"[{ind + 1}]. [id{item[0]}|{nickname if nickname else await getUserName(item[0])}] | "
            f"{int((item[3] - time.time()) / 60)} минут | "
            f"{literal_eval(item[2])[-1] if item[2] and literal_eval(item[2])[-1] else 'Без указания причины'} "
            f"| Выдал: {literal_eval(item[4])[-1]}\n")
    return msg


async def warnlist(res, warnedcount):
    msg = get('warnlist', warnedcount=warnedcount)
    for ind, item in enumerate(res):
        nickname = await getUserNickname(item[0], item[1])
        msg += (
            f"[{ind + 1}]. [id{item[0]}|{nickname if nickname else await getUserName(item[0])}] | "
            f"кол-во: {item[3]}/3 | "
            f"{'Без указания причины' if not item[2] or not literal_eval(item[2])[-1] else literal_eval(item[2])[-1]} |"
            f" Выдал: {literal_eval(item[4])[-1]}\n")
    return msg


def setacc_hint():
    return get('setacc_hint')


def setacc_myself():
    return get('setacc_myself')


def setacc_higher():
    return get('setacc_higher')


def setacc(uid, u_name, u_nick, acc, id, name, nick, lvlname=None):
    return get('setacc', u_n=f'[id{uid}|{u_nick}]' if u_nick else f'[id{uid}|{u_name}]',
               acc=LVL_NAMES[acc] if lvlname is None else lvlname,
               n=f'[id{id}|{nick}]' if nick is not None else f'[id{id}|{name}]')


def setacc_already_have_acc(id, name, nick):
    return get('setacc_already_have_acc', id=id, n=nick if nick else name)


def setacc_low_acc(acc):
    return get('setacc_low_acc', acc=LVL_NAMES[acc])


def delaccess_hint():
    return get('delaccess_hint')


def delaccess_myself():
    return get('delaccess_myself')


def delaccess_noacc(id, name, nick):
    return get('delaccess_noacc', id=id, n=nick if nick else name)


def delaccess_higher():
    return get('delaccess_higher')


def delaccess(uid, uname, unick, id, name, nick):
    return get('delaccess', uid=uid, un=unick if unick else uname, id=id, n=nick if nick else name)


def timeout_hint():
    return get('timeout_hint')


def timeouton(id, name, nickname):
    return get('timeouton', id=id, n=nickname if nickname else name)


def timeoutoff(id, name, nickname):
    return get('timeoutoff', id=id, n=nickname if nickname else name)


def inactive_hint():
    return get('inactive_hint')


def inactive_no_results():
    return get('inactive_no_results')


def inactive(uid, name, nick, count):
    return get('inactive_no_active') if int(count) <= 0 else get(
        'inactive', uid=uid, n=nick if nick else name, count=count)


def ban_hint():
    return get('ban_hint')


def ban(uid, u_name, u_nickname, id, name, nickname, cause, time):
    return get('ban', uid=uid, n=u_nickname if u_nickname else u_name, id=id,
               bn=nickname if nickname else name, time=f' {time} дней' if time < 3650 else 'всегда',
               cause=f' по причине: "{cause}"' if cause is not None else '')


def ban_error():
    return get('ban_error')


def ban_maxtime():
    return get('ban_maxtime')


def ban_myself():
    return get('ban_myself')


def ban_higher():
    return get('ban_higher')


def already_banned(name, nick, id, ban):
    return get('already_banned', id=id, n=nick if nick else name, time_left=int((ban - time.time()) / 86400 + 1))


def unban(uname, unick, uid, name, nick, id):
    return get('unban', uid=uid, un=unick if unick else uname, id=id, n=nick if nick else name)


def unban_no_ban(id, name, nick):
    return get('unban_no_ban', id=id, n=nick if nick else name)


def unban_higher():
    return get('unban_higher')


def unban_hint():
    return get('unban_hint')


def async_already_bound():
    return get('async_already_bound')


def async_done(uid, u_name, u_nickname):
    return get('async_done', uid=uid, n=u_nickname if u_nickname else u_name)


def async_limit():
    return get('async_limit')


def delasync_already_unbound():
    return get('delasync_already_unbound')


def delasync_not_owner():
    return get('delasync_not_owner')


def delasync_done(uid, u_name, u_nickname, chname=''):
    return get('delasync_done', uid=uid, n=u_nickname if u_nickname else u_name,
               chname=f' "{chname}"' if chname else '')


def gkick(uid, u_name, u_nickname, chats, success):
    return get('gkick', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def gkick_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return get('gkick_start', uid=uid, un=u_nickname if u_nickname else u_name, chats=chats, id=id,
               n=nickname if nickname else name)


def gkick_hint():
    return get('gkick_hint')


async def banlist(res, bancount):
    msg = get('banlist', bancount=bancount)
    for k, i in enumerate(res):
        nickname = await getUserNickname(i[0], i[1])
        cause = literal_eval(i[2])[-1]
        msg += (f"[{k + 1}]. [id{i[0]}|{nickname if nickname else await getUserName(i[0])}] | "
                f"{int((i[3] - time.time()) / 86400) + 1} дней | "
                f"{cause if cause else 'Без указания причины'} | Выдал: {literal_eval(i[4])[-1]}\n")
    return msg


def userban_hint():
    return get('userban_hint')


def gban(uid, u_name, u_nickname, chats, success):
    return get('gban', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def gban_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return get('gban_start', uid=uid, un=u_nickname if u_nickname else u_name, chats=chats, id=id,
               n=nickname if nickname else name)


def gban_hint():
    return get('gban_hint')


def kick_banned(id, name, nick, btime, cause):
    return get('kick_banned', id=id, n=nick if nick else name, t=int((btime - time.time()) / 86400),
               cause=f' по причине {cause}' if cause else '')


def gunban(uid, u_name, u_nickname, chats, success):
    return get('gunban', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def gunban_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return get('gunban_start', uid=uid, un=u_nickname if u_nickname else u_name, chats=chats, id=id,
               n=nickname if nickname else name)


def gunban_hint():
    return get('gunban_hint')


def gmute(uid, u_name, u_nickname, chats, success):
    return get('gmute', uid=uid, n=u_name if u_nickname is None else u_nickname, success=success, chats=chats)


def gmute_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return get('gmute_start', uid=uid, un=u_nickname if u_nickname else u_name, chats=chats, id=id,
               n=nickname if nickname else name)


def gmute_hint():
    return get('gmute_hint')


def gunmute(uid, u_name, u_nickname, chats, success):
    return get('gunmute', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def gunmute_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return get('gunmute_start', uid=uid, un=u_nickname if u_nickname else u_name, chats=chats, id=id,
               n=nickname if nickname else name)


def gunmute_hint():
    return get('gunmute_hint')


def gwarn(uid, u_name, u_nick, chats, success):
    return get('gwarn', uid=uid, un=u_nick if u_nick is not None else u_name, success=success, chats=chats)


def gwarn_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return get('gwarn_start', uid=uid, un=u_nickname if u_nickname else u_name, chats=chats, id=id,
               n=nickname if nickname else name)


def gwarn_hint():
    return get('gwarn_hint')


def gunwarn(uid, u_name, u_nickname, chats, success):
    return get('gunwarn', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def gunwarn_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return get('gunwarn_start', uid=uid, un=u_nickname if u_nickname else u_name, chats=chats, id=id,
               n=nickname if nickname else name)


def gunwarn_hint():
    return get('gunwarn_hint')


def gsnick(uid, u_name, u_nickname, chats, success):
    return get('gsnick', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def gsnick_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return get('gkick_start', uid=uid, un=u_nickname if u_nickname else u_name, chats=chats, id=id,
               n=nickname if nickname else name)


def gsnick_hint():
    return get('gsnick_hint')


def grnick(uid, u_name, u_nickname, chats, success):
    return get('grnick', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def grnick_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return get('grnick_start', uid=uid, un=u_nickname if u_nickname else u_name, chats=chats, id=id,
               n=nickname if nickname else name)


def grnick_hint():
    return get('grnick_hint')


def gdelaccess(uid, u_name, u_nickname, chats, success):
    return get('gdelaccess', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def gdelaccess_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return get('gdelaccess_start', uid=uid, un=u_nickname if u_nickname else u_name, chats=chats, id=id,
               n=nickname if nickname else name)


def gdelaccess_hint():
    return get('gdelaccess_hint')


def gdelaccess_admin_unknown():
    return get('gdelaccess_admin_unknown')


def gdelaccess_admin(uid, u_name, u_nickname):
    return get('gdelaccess_admin', uid=uid, n=u_nickname if u_nickname else u_name)


def setaccess_myself():
    return get('setaccess_myself')


def gsetaccess(uid, u_name, u_nickname, chats, success):
    return get('gsetaccess', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def gsetaccess_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return get('gsetaccess_start', uid=uid, un=u_nickname if u_nickname else u_name, chats=chats, id=id,
               n=nickname if nickname else name)


def gsetaccess_hint():
    return get('gsetaccess_hint')


def zov(uid, name, nickname, cause, members):
    call = [f"[id{i.member_id}|\u200b\u206c]" for i in members if i.member_id > 0]
    return get('zov', uid=uid, n=nickname if nickname else name, lc=len(call), lm=len(members), cause=cause,
               jc=''.join(call))


def zov_hint():
    return get('zov_hint')


def welcome(id, name, nickname):
    return get('welcome', id=id, n=nickname if nickname else name)


def welcome_hint():
    return get('welcome_hint')


def delwelcome(id, name, nickname):
    return get('delwelcome', id=id, n=nickname if nickname else name)


def delwelcome_hint():
    return get('delwelcome_hint')


def chat_unbound():
    return get('chat_unbound')


def gzov_start(uid, u_name, u_nickname, chats):
    return get('gzov_start', uid=uid, un=u_nickname if u_nickname else u_name, chats=chats)


def gzov(uid, u_name, u_nickname, chats, success):
    return get('gzov', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def gzov_hint():
    return get('gzov_hint')


def creategroup_already_created(group):
    return get('creategroup_already_created', group=group)


def creategroup_done(uid, u_name, u_nickname, group):
    return get('creategroup_done', uid=uid, n=u_nickname if u_nickname else u_name, group=group)


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
    return get('bind', uid=uid, n=u_nickname if u_nickname else u_name, group=group)


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
    return get('unbind', uid=uid, n=u_nickname if u_nickname else u_name, group=group)


def delgroup_not_found(group):
    return get('delgroup_not_found', group=group)


def delgroup(uid, u_name, u_nickname, group):
    return get('delgroup', group=group, uid=uid, n=u_nickname if u_nickname else u_name)


def delgroup_hint():
    return get('delgroup_hint')


def s_invalid_group(group):
    return get('s_invalid_group', group=group)


def skick_hint():
    return get('skick_hint')


def skick(uid, u_name, u_nickname, chats, success):
    return get('skick', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def skick_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    return get('skick_start', uid=uid, un=u_nickname if u_nickname else u_name, group=group, chats=chats, id=id,
               n=nickname if nickname else name)


def sban_hint():
    return get('sban_hint')


def sban(uid, u_name, u_nickname, chats, success):
    return get('sban', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def sban_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    return get('sban_start', uid=uid, un=u_nickname if u_nickname else u_name, group=group, chats=chats, id=id,
               n=nickname if nickname else name)


def sunban_hint():
    return get('sunban_hint')


def sunban(uid, u_name, u_nickname, chats, success):
    return get('sunban', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def sunban_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    return get('sunban_start', uid=uid, un=u_nickname if u_nickname else u_name, group=group, chats=chats, id=id,
               n=nickname if nickname else name)


def ssnick_hint():
    return get('ssnick_hint')


def ssnick(uid, u_name, u_nickname, chats, success):
    return get('ssnick', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def ssnick_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    return get('ssnick_start', uid=uid, un=u_nickname if u_nickname else u_name, group=group, chats=chats, id=id,
               n=nickname if nickname else name)


def srnick_hint():
    return get('srnick_hint')


def srnick(uid, u_name, chats, success):
    return get('srnick', uid=uid, u_name=u_name, success=success, chats=chats)


def srnick_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    return get('srnick_start', uid=uid, un=u_nickname if u_nickname else u_name, group=group, chats=chats, id=id,
               n=nickname if nickname else name)


def szov_hint():
    return get('szov_hint')


def szov_start(uid, u_name, u_nickname, chats, group):
    return get('szov_start', uid=uid, un=u_nickname if u_nickname else u_name, group=group, chats=chats)


def szov(uid, u_name, u_nickname, group, pool, success):
    return get('szov', uid=uid, un=u_nickname if u_nickname else u_name, success=success, pool=pool, group=group)


def ssetaccess_hint():
    return get('ssetaccess_hint')


def ssetaccess(uid, u_name, u_nickname, chats, success):
    return get('ssetaccess', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def ssetaccess_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    return get('ssetaccess_start', uid=uid, un=u_nickname if u_nickname else u_name, group=group, chats=chats, id=id,
               n=nickname if nickname else name)


def sdelaccess_hint():
    return get('sdelaccess_hint')


def sdelaccess(uid, u_name, u_nickname, chats, success):
    return get('sdelaccess', uid=uid, n=u_nickname if u_nickname else u_name, success=success, chats=chats)


def sdelaccess_start(uid, u_name, u_nickname, id, name, nickname, group, chats):
    return get('ssetaccess_start', uid=uid, un=u_nickname if u_nickname else u_name, group=group, chats=chats, id=id,
               n=nickname if nickname else name)


def demote_choose():
    return get('demote_choose')


def demote_yon():
    return get('demote_yon')


def demote_disaccept():
    return get('demote_disaccept')


def demote_accept(id, name, nick):
    return get('demote_accept', id=id, n=nick if nick else name)


def mygroups_no_groups():
    return get('mygroups_no_groups')


def addfilter(id, name, nickname):
    return get('addfilter', id=id, n=nickname if nickname else name)


def addfilter_hint():
    return get('addfilter_hint')


def delfilter(id, name, nickname):
    return get('delfilter', id=id, n=nickname if nickname else name)


def delfilter_hint():
    return get('delfilter_hint')


def delfilter_no_filter():
    return get('delfilter_no_filter')


def gaddfilter_start(uid, u_name, u_nickname, chats):
    return get('gaddfilter_start', uid=uid, un=u_nickname if u_nickname else u_name, chats=chats)


def gaddfilter(uid, name, chats, success):
    return get('gaddfilter', uid=uid, name=name, success=success, chats=chats)


def gaddfilter_hint():
    return get('gaddfilter_hint')


def gdelfilter_start(uid, u_name, u_nickname, chats):
    return get('gdelfilter_start', uid=uid, un=u_nickname if u_nickname else u_name, chats=chats)


def gdelfilter(uid, name, chats, success):
    return get('gdelfilter', uid=uid, name=name, success=success, chats=chats)


def gdelfilter_hint():
    return get('gdelfilter_hint')


def editlvl_hint():
    return get('editlvl_hint')


def editlvl(id, name, nickname, cmd, beforelvl, lvl):
    return get('editlvl', id=id, n=nickname if nickname else name, cmd=cmd, beforelvl=beforelvl, lvl=lvl)


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
    return get('addblack', uid=uid, un=unick if unick else uname, id=id, n=nick if nick else name)


def blacked(id, name, nick):
    return get('blacked', id=id, n=nick if nick else name)


def delblack_hint():
    return get('delblack_hint')


def delblack_myself():
    return get('delblack_myself')


def delblack(uid, uname, unick, id, name, nick):
    return get('delblack', uid=uid, un=unick if unick else uname, id=id, n=nick if nick else name)


def delblacked(id, name, nick):
    return get('delblacked', id=id, n=nick if nick else name)


def delblack_no_user(id, name, nick):
    return get('delblack_no_user', id=id, n=nick if nick else name)


def setstatus_hint():
    return get('setstatus_hint')


def setstatus(uid, uname, unick, id, name, nick):
    return get('setstatus', uid=uid, un=unick if unick else uname, id=id, n=nick if nick else name)


def delstatus_hint():
    return get('delstatus_hint')


def delstatus(uid, uname, unick, id, name, nick):
    return get('delstatus', uid=uid, un=unick if unick else uname, id=id, n=nick if nick else name)


def sgroup_unbound(group):
    return get('sgroup_unbound', group=group)


async def statuslist(pp):
    msg = ''
    k = 0
    for k, i in enumerate(pp):
        msg += (f"[{k + 1}]. [id{i[0]}|{await getUserName(i[0])}] | "
                f"Осталось: {int((i[1] - time.time()) / 86400) + 1} дней\n")
    return get('statuslist', premium_status=k) + msg


def settings():
    return get('settings')


def settings_category(category, settings):
    return get(f'settings_{category}', settings=[SETTINGS_POSITIONS[category][k][i] for k, i in settings.items()])


def settings_change_countable(chat_id, setting, pos, value, value2, pos2, punishment=None):
    if setting not in SETTINGS_COUNTABLE_NO_PUNISHMENT:
        if punishment == 'deletemessage':
            punishment = 'удаление сообщения'
        elif punishment == 'kick':
            punishment = f'исключение'
        elif punishment and punishment.startswith('mute'):
            punishment = f'мут на {punishment.split("|")[-1]} минут'
        elif punishment and punishment.startswith('ban'):
            punishment = f'блокировку на {punishment.split("|")[-1]} дней'
        else:
            punishment = 'без наказания'
        return get(f'settings_change_countable_{setting}', status="Включено" if pos else "Выключено",
                   count=0 if not value else value, punishment=punishment)
    elif setting == 'nightmode':
        return get(f'settings_change_countable_{setting}', status="Включено" if pos else "Выключено",
                   time='❌' if not pos or value2 is None else value2)
    elif setting == 'welcome':
        with syncpool().connection() as conn:
            with conn.cursor() as c:
                w = c.execute('select msg, photo from welcome where chat_id=%s', (chat_id,)).fetchone()
        return get(f'settings_change_countable_{setting}', status="Включено" if pos else "Выключено",
                   status2="Да" if pos2 else "Нет",
                   value='Установлено' if pos and w is not None and (w[0] or w[1]) else '❌')


def settings_change_countable_digit_error():
    return get(f'settings_change_countable_digit_error')


def settings_change_countable_format_error():
    return get(f'settings_change_countable_format_error')


def settings_choose_punishment():
    return get(f'settings_choose_punishment')


def settings_countable_action(action, setting, text=None, image=None, url=None):
    if setting == 'welcome':
        return get(f'settings_{action}_{setting}', text='Не установлено' if not text else text,
                   url='Не установлено' if not url else url, image='Не установлено' if not image else 'Установлено')
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
        msg += f'[{k + 1}]. {i[0]}'
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
    return get('q', uid=uid, n=nick if nick else name)


def q_fail(uid, name, nick):
    return get('q_fail', uid=uid, n=nick if nick else name)


def premium():
    return get('premium')


def premium_sent(uid, name, nickname):
    return get('premium_sent', uid=uid, n=nickname if nickname else name)


def chat(uid, uname, chat_id, bind, gbind, public, muted, banned, users, time, prefix, chat_name):
    return get('chat', prefix=prefix, uid=uid, uname=uname, chat_id=chat_id, chat_name=chat_name, bind=bind,
               gbind=gbind, public=public, banned=banned, muted=muted, users=users, time=time)


async def getnick(res, query):
    msg = ''
    k = 0
    for k, item in enumerate(res):
        msg += f"{k + 1}. {item[1]} - [id{item[0]}|{await getUserName(item[0])}]\n"
    return get('getnick', query=query, cnt=k + 1) + msg


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
    return get('giveowner', uid=uid, un=unick if unick else uname, id=id, n=nick if nick else name)


def bonus(id, nick, name, xp):
    return get('bonus', id=id, n=nick if nick else name, xp=xp)


def bonus_time(id, nick, name, timeleft):
    return get('bonus_time', id=id, n=nick if nick else name, hours=pointHours((timeleft // 3600) * 3600),
               minutes=pointMinutes(timeleft - (timeleft // 3600) * 3600))


async def top_lvls(top, chattop):
    msg = get('top_lvls')
    for k, i in enumerate(top.items()):
        msg += f"[{k + 1}]. [id{i[0]}|{await getUserName(i[0])}] - {i[1]} уровень\n"
    msg += f'\n🥨 В беседе:\n'
    for k, i in enumerate(chattop.items()):
        msg += f"[{k + 1}]. [id{i[0]}|{await getUserName(i[0])}] - {i[1]} уровень\n"
    return msg


async def top_duels(duels, category='общее'):
    msg = get('top_duels', category=category)
    for k, item in enumerate(duels.items()):
        msg += f"[{k + 1}]. [id{item[0]}|{await getUserName(item[0])}] - {item[1]} побед\n"
    return msg


def premmenu(settings, prem):
    msg = get('premmenu')
    c = 0
    for e, i in settings.items():
        if e == 'clear_by_fire':
            c += 1
            msg += f'\n[{c}]. Удаление сообщения с помощью реакции(🔥) | {"✔" if i == 1 else "❌"}'
        elif e == 'border_color':
            if prem:
                c += 1
                msg += f'\n[{c}]. Смена цвета рамки в /stats | {i if i else "Выкл."}'
    return msg


def premmenu_action(setting):
    return get(f'premmenu_action_{setting}')


def premmenu_action_complete(setting, value):
    return get(f'premmenu_action_complete_{setting}', value=value)


def prefix():
    return get('prefix')


def addprefix_max():
    return get('addprefix_max')


def addprefix_too_long():
    return get('addprefix_too_long')


def addprefix(uid, name, nick, prefix):
    return get('addprefix', uid=uid, n=nick if nick else name, prefix=prefix)


def delprefix(uid, name, nick, prefix):
    return get('delprefix', uid=uid, n=nick if nick else name, prefix=prefix)


def delprefix_not_found(prefix):
    return get('delprefix_not_found', prefix=prefix)


def listprefix(uid, name, nick, prefixes):
    if not prefixes:
        return (get('listprefix', uid=uid, n=nick if nick else name) +
                'Префиксов не обнаружено. Используйте кнопку "Добавить префикс"')
    return (get('listprefix', uid=uid, n=nick if nick else name) +
            ''.join([f'➖ "{i[0]}"\n' for i in prefixes]))


def levelname_hint():
    return get('levelname_hint')


def levelname(uid, name, nick, lvl, lvlname):
    return get('levelname', uid=uid, n=nick if nick else name, lvlname=lvlname, lvl=lvl)


def resetlevel_hint():
    return get('resetlevel_hint')


def cmdcount(cmdcounter):
    summ = sum([i.count for i in cmdcounter])
    msg = get('cmdcount')
    for i in cmdcounter:
        if i.cmd not in msg:
            msg += f'➖{i.cmd} | использовано: {i.count} раз | {str(i.count / summ * 100)[:5]}%\n'
    return msg


def lvl_up(lvl):
    return get('lvl_up', lvl=lvl, lvlp=lvl + 1)


def ignore_hint():
    return get('ignore_hint')


def ignore_higher():
    return get('ignore_higher')


def ignore_not_found():
    return get('ignore_not_found')


def ignore(id, name, nick):
    return get('ignore', id=id, n=nick if nick else name)


def unignore_hint():
    return get('unignore_hint')


def unignore_not_found():
    return get('unignore_not_found')


def unignore_not_ignored():
    return get('unignore_not_ignored')


def unignore(id, name, nick):
    return get('unignore', id=id, n=nick if nick else name)


def ignorelist(res, names):
    return get('ignorelist', lres=len(res)) + ''.join([f'➖ [id{i}|{names[k]}]\n' for k, i in enumerate(res)])


def chatlimit_hint():
    return get('chatlimit_hint')


def chatlimit(id, name, nick, t, postfix, lpos):
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
        return get('chatlimit', id=id, n=nick if nick else name, t=t, postfix=postfix)
    elif lpos == 0:
        return get('chatlimit_already_on')
    return get('chatlimit_off', id=id, n=nick if nick else name)


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


def cmd_prem(l):
    return get('cmd_prem', l=l)


def cmd_set(uid, name, nick, cmd, changed):
    return get('cmd_set', uid=uid, n=nick if nick else name, changed=changed, cmd=cmd)


def resetcmd_hint():
    return get('resetcmd_hint')


def resetcmd_not_found(cmd):
    return get('resetcmd_not_found', cmd=cmd)


def resetcmd_not_changed(cmd):
    return get('resetcmd_not_changed', cmd=cmd)


def resetcmd(uid, name, nick, cmd, cmdname):
    return get('resetcmd', uid=uid, n=nick if nick else name, cmdname=cmdname, cmd=cmd)


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
        return get('listasync_not_found')
    return get('listasync', total=total) + msg


def duel_not_allowed():
    return get('duel_not_allowed')


def duel_hint():
    return get('duel_hint')


def duel_uxp_not_enough(uid, name, nick):
    return get('duel_uxp_not_enough', uid=uid, n=nick if nick else name)


def duel_xp_minimum():
    return get('duel_xp_minimum')


def duel(uid, name, nick, xp):
    return get('duel', uid=uid, n=nick if nick else name, xp=xp)


def duel_res(uid, uname, unick, id, name, nick, xp, prem, com=10):
    return get('duel_res', uid=uid, un=unick if unick else uname, id=id, n=nick if nick else name, xp=xp,
               com='' if prem else f' с учётом комиссии {com}%')


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
    return get('kickmenu_kick_nonick', uid=uid, n=nick if nick else name, kicked=kicked)


def kickmenu_kick_nick(uid, name, nick, kicked):
    return get('kickmenu_kick_nick', uid=uid, n=nick if nick else name, kicked=kicked)


def kickmenu_kick_banned(uid, name, nick, kicked):
    return get('kickmenu_kick_banned', uid=uid, n=nick if nick else name, kicked=kicked)


def send_notification(text, tagging):
    return get('send_notification', text=text, tagging='' if tagging is True else tagging)


def notif(notifs, activenotifs):
    return get('notif', lnotifs=notifs, lactive=activenotifs)


def notif_already_exist(name):
    return get('notif_already_exist', name=name)


def notification(name, text, time, every, tag, status):
    msg = get('notification', name=name, text=text)

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

    msg += f'\n\n🟣 Статус: {"Выключено" if not status else "Включено"}'

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
        msg += f'[{k + 1}]. {i[1]} | {"Включено" if i[0] == 1 else "Выключено"}\n'
    return msg


def transfer_hint():
    return get('transfer_hint')


def transfer_wrong_number():
    return get('transfer_wrong_number')


def transfer_not_enough(uid, name, nickname):
    return get('transfer_not_enough', uid=uid, n=name if nickname is None else nickname)


def transfer_myself():
    return get('transfer_myself')


def transfer_community():
    return get('transfer_community')


def transfer(uid, uname, id, name, xp, com):
    return get('transfer', uid=uid, uname=uname, xp=xp, id=id, name=name,
               com='' if com == 0 else f' с учётом комиссии {com}%')


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


def resetlvl(id, u_name):
    return get('resetlvl', id=id, u_name=u_name)


def resetlvlcomplete(id, u_name):
    return get('resetlvlcomplete', id=id, u_name=u_name)


def check_help():
    return get('check_help')


def check(id, name, nickname, ban, warn, mute):
    return get('check', id=id, n=nickname if nickname else name, ban=pointDays(ban) if ban else "Отсутствуют",
               warn=f"{warn} из 3" if warn else "Отсутствуют", mute=pointMinutes(mute) if mute else "Отсутствует")


def check_ban(id, name, nickname, ban, ban_history, ban_date, ban_from, ban_reason, ban_time):
    msg = get('check_ban', id=id, n=nickname if nickname else name,
              lbh=len(ban_history), banm=pointDays(ban) if ban else "Отсутствует")
    if ban:
        msg += f'★ {ban_date} | {ban_from} | {pointDays(ban_time)} | {ban_reason}'
    return msg


def check_mute(id, name, nickname, mute, mute_history, mute_date, mute_from, mute_reason, mute_time):
    msg = get('check_mute', id=id, n=nickname if nickname else name, lmh=len(mute_history),
              mutem=pointMinutes(mute) if mute else "Отсутствует")
    if mute:
        msg += f'★ {mute_date} | {mute_from} | {pointMinutes(mute_time)} | {mute_reason}'
    return msg


def check_warn(id, name, nickname, warn, warn_history, warns_date, warns_from, warns_reason):
    msg = get('check_warn', id=id, n=nickname if nickname else name, lwh=len(warn_history),
              warnm=f"{warn} из 3" if warn else "Отсутствуют")
    if warn:
        for k, _ in enumerate(warn_history[:warn]):
            msg += f'★ {warns_date[k]} | {warns_from[k]} | {warn - k} из 3 | {warns_reason[k]}\n'
    return msg


def check_history_ban(id, name, nickname, dates, names, times, causes):
    msg = get('check_history_ban', id=id, n=nickname if nickname else name)
    for k in range(len(times)):
        msg += f'★ {dates[k]} | {names[k]} | {pointDays(times[k])} | {causes[k]}\n'
    return msg


def check_history_mute(id, name, nickname, dates, names, times, causes):
    msg = get('check_history_mute', id=id, n=nickname if nickname else name)
    for k in range(len(times)):
        msg += f'★ {dates[k]} | {names[k]} | {pointMinutes(times[k])} | {causes[k]}\n'
    return msg


def check_history_warn(id, name, nickname, dates, names, times, causes):
    msg = get('check_history_warn', id=id, n=nickname if nickname else name)
    for k in range(len(times)):
        msg += f'★ {dates[k]} | {names[k]} | {causes[k]}\n'
    return msg


def purge_start():
    return get('purge_start')


def purge_empty():
    return get('purge_empty')


def purge(nicknames, levels):
    return get('purge', nicknames=pointWords(nicknames, ("никнейм", "никнейма", "никнеймов")),
               levels=pointWords(levels, ("уровень", "уровня", "уровней")))


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


def repbanned():
    return get('repbanned')


def repunban_noban():
    return get('repunban_noban')


def repunban_hint():
    return get('repunban_hint')


def repunban():
    return get('repunban')


def repban_hint():
    return get('repban_hint')


def repban():
    return get('repban')


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
    return get('deanon', id=id, from_id=from_id, from_name=nickname if nickname else name,
               time=datetime.fromtimestamp(time).strftime('%d.%m.%Y - %H:%M'))


def antispam_punishment(uid, name, nick, setting, punishment, violation_count, time=None):
    return get(f'antispam_punishment_{setting}_{punishment}', uid=uid, n=nick if nick else name, time=time,
               violation_count=violation_count)


def nightmode_start(start, end):
    return get('nightmode_start', start=start, end=end)


def nightmode_end():
    return get('nightmode_end')


def speccommandscooldown(time):
    return get('speccommandscooldown', time=pointWords(time, ['секунду', 'секунды', 'секунд']))


def captcha(uid, n, ctime, punishment: str):
    if punishment == 'kick':
        punishment = 'кикнуты'
    elif punishment.startswith('mute'):
        t = punishment.split("|")[-1]
        punishment = f'замучены на {t} {pointHours(t)}'
    elif punishment.startswith('ban'):
        t = punishment.split("|")[-1]
        punishment = f'забанены на {t} {pointDays(t)}'
    return get('captcha', uid=uid, n=n, time=ctime, punishment=punishment)


def captcha_punish(uid, n, punishment):
    ctime = None
    if punishment.startswith('mute'):
        ctime = punishment.split("|")[-1]
        punishment = punishment.split("|")[0]
    elif punishment.startswith('ban'):
        ctime = punishment.split("|")[-1]
        punishment = punishment.split("|")[0]
    return get(f'captcha_punishment_{punishment}', uid=uid, n=n, time=ctime)


def captcha_pass(uid, n, date):
    return get('captcha_pass', uid=uid, n=n, date=date)


def punishlist_delall_done(punish):
    return get('punishlist_delall_done', punish={"mute": "муты", "ban": "баны", "warn": "варны"}[punish])


def timeout(activated):
    return get('timeout',
               activated='Для активации нажмите "Включить"' if not activated else 'Для деактивации нажмите "Выключить"')


def timeout_settings():
    return get('timeout_settings')


def chats():
    return get('chats')


def setprem(id):
    return get('setprem', id=id)


def setprem_hint():
    return get('setprem_hint')


def delprem(id):
    return get('delprem', id=id)


def delprem_hint():
    return get('delprem_hint')


def premchat(uid, name):
    return get('premchat', uid=uid, name=name)


def premlist(prem):
    return get('premlist') + '\n' + '\n'.join([str(i[0]) for i in prem])


def transfer_limit(u_prem):
    return get('transfer_limit_prem' if u_prem else 'transfer_limit')


def code(code):
    return get('code', code=code)
