import time
from ast import literal_eval
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Iterable

from cache.async_lru import AsyncLRU

from StarManager.core import enums, tables, utils
from StarManager.core.config import settings
from StarManager.core.db import pool
from StarManager.core.managers.access_level import CachedAccessLevelRow
from StarManager.core.managers.custom_access_level import CachedCustomAccessLevelRow


@AsyncLRU(maxsize=0)
async def get(key: str, **kwargs):
    async with (await pool()).acquire() as conn:
        msg = await conn.fetchval("select text from botmessages where key=$1", key)
    if msg is None:
        raise Exception(f'unknown message key "{key}"')
    return msg.format(**kwargs)


async def join():
    return await get("join")


async def rejoin():
    return await get("rejoin")


async def rejoin_activate():
    return await get("rejoin_activate")


async def start():
    return await get("start")


async def id(uid, data, name, url, last_message):
    return await get(
        "id",
        uid=uid,
        data=data,
        name=name,
        url=url,
        last_message=f"\n🕒 Последняя активность в чате: {last_message}"
        if last_message
        else "",
    )


async def top(top):
    return await get("top") + "".join(
        [
            f"{utils.number_to_emoji(k + 1)} [id{i[0]}|{await utils.get_user_name(i[0])}] - {i[1]} сообщений\n"
            for k, i in enumerate(top)
        ]
    )


async def help(page: int = 0, cmds: Dict[str, int] = settings.commands.commands) -> str:
    header = await get(f"help_page{page}")
    footer = await get("help_last")

    if page == 8:
        premium_descs = (
            f"{settings.commands.descriptions[name]}\n"
            for name in settings.commands.premium
        )
        return header + "".join(premium_descs) + footer

    descs: dict[int, list[str]] = defaultdict(list)
    for name, group in cmds.items():
        if name in settings.commands.premium:
            continue
        try:
            descs[int(group)].append(settings.commands.descriptions[name])
        except (KeyError, ValueError):
            continue

    return header + "".join(f"{d}\n" for d in descs[page]) + footer


async def helpdev():
    devcmds = [
        f"{settings.commands.descriptions[k] if k in settings.commands.descriptions else f'/{k} - Без описания.'}"
        for k, i in settings.commands.commands.items()
        if i == 8
    ]
    return await get("helpdev", cmds="\n".join(devcmds))


async def report(uid, name, report, repid):
    return await get(
        "report",
        repid=repid,
        uid=uid,
        name=name,
        report=report,
    )


async def report_cd():
    return await get("report_cd")


async def report_sent(rep_id):
    return await get("report_sent", rep_id=rep_id)


async def report_error(rep_id):
    return await get("report_error", rep_id=rep_id)


async def report_empty():
    return await get("report_empty")


async def kick_hint():
    return await get("kick_hint")


async def kick(u_name, u_nick, uid, ch_name, ch_nick, id, cause):
    return await get(
        "kick",
        uid=uid,
        u_name=u_nick or u_name,
        i="club" if id < 0 else "id",
        id=abs(id),
        ch_name=ch_nick or ch_name,
        cause=cause,
    )


async def kick_error():
    return await get("kick_error")


async def kick_access(id, name, nick):
    return await get(
        "kick_access", i="club" if id < 0 else "id", id=abs(id), n=nick or name
    )


async def kick_myself():
    return await get("kick_myself")


async def kick_higher():
    return await get("kick_higher")


async def mute_hint():
    return await get("mute_hint")


async def mute(name, nick, id, mutingname, mutingnick, mutingid, cause, time):
    return await get(
        "mute",
        id=id,
        n=nick or name,
        mutingid=mutingid,
        mn=mutingnick or mutingname,
        time=time,
        cause=" по причине: " + cause if cause else "",
    )


async def mute_myself():
    return await get("mute_myself")


async def unmute_myself():
    return await get("unmute_myself")


async def mute_higher():
    return await get("mute_higher")


async def already_muted(name, nick, id, mute):
    return await get(
        "already_muted", id=id, n=nick or name, time_left=int((mute - time.time()) / 60)
    )


async def warn_hint():
    return await get("warn_hint")


async def warn(name, nick, uid, ch_name, ch_nick, id, cause):
    return await get(
        "warn",
        uid=uid,
        n=nick or name,
        cause=" по причине: " + cause if cause else "",
        cn=ch_nick or ch_name,
        id=id,
    )


async def warn_kick(name, nick, uid, ch_name, ch_nick, id, cause):
    return await get(
        "warn_kick",
        uid=uid,
        n=nick or name,
        id=id,
        cn=ch_nick or ch_name,
        cause=" по причине: " + cause if cause else "",
    )


async def warn_higher():
    return await get("warn_higher")


async def warn_myself():
    return await get("warn_myself")


async def unwarn_myself():
    return await get("unwarn_myself")


async def clear(deleting, uid, chat_id, delete_from):
    if delete_from:
        return await get(
            "clear_from",
            uid=uid,
            u_name=await utils.get_user_name(uid)
            or await utils.get_user_nickname(uid, chat_id),
            id=delete_from,
            name=await utils.get_user_name(delete_from)
            or await utils.get_user_nickname(delete_from, chat_id),
            deleted=len(deleting),
        )
    return await get(
        "clear",
        uid=uid,
        u_name=await utils.get_user_name(uid)
        or await utils.get_user_nickname(uid, chat_id),
        users=", ".join(
            set(
                [
                    f"[{'id' if int(id) > 0 else 'club'}{id}|"
                    f"{(await utils.get_user_name(id) or await utils.get_user_nickname(id, chat_id)) if id > 0 else await utils.get_group_name(id)}]"
                    for id in deleting
                ]
            )
        ),
    )


async def clear_hint():
    return await get("clear_hint")


async def clear_higher():
    return await get("clear_higher")


async def clear_admin():
    return await get("clear_admin")


async def snick_hint():
    return await get("snick_hint")


async def snick_too_long_nickname():
    return await get("snick_too_long_nickname")


async def snick_higher():
    return await get("snick_higher")


async def snick(uid, u_name, u_nickname, id, ch_name, nickname, newnickname):
    return await get(
        "snick",
        uid=uid,
        un=u_nickname or u_name,
        id=id,
        newnickname=newnickname,
        n=nickname or ch_name,
    )


async def rnick_hint():
    return await get("rnick_hint")


async def rnick_user_has_no_nick():
    return await get("rnick_user_has_no_nick")


async def rnick_higher():
    return await get("rnick_higher")


async def rnick(uid, u_name, u_nick, id, name, nick):
    return await get("rnick", uid=uid, un=u_nick or u_name, id=id, nick=nick, name=name)


async def nlist(res, members, page=0):
    msg, cnt, res = await get("nlist"), 0, {item[0]: item for item in res}
    for it in members:
        if (
            it.id < 0
            or "DELETED" in (it.first_name, it.last_name)
            or not (item := res.get(it.id))
        ):
            continue
        cnt += 1
        msg += f"{cnt + 30 * page}. {item[1]} - [id{item[0]}|{it.first_name} {it.last_name}]\n"
    return msg


async def nnlist(members, page=0):
    msg, k = await get("nnlist"), page * 30
    for i in members:
        try:
            if i.first_name == "DELETED" or i.last_name == "DELETED" or i.id <= 0:
                continue
            msg += f"{k + 1}. [id{i.id}|{i.first_name} {i.last_name}]\n"
            k += 1
        except Exception:
            pass
    return msg


async def staff(res, names, chat_id):
    emoji = {"1": "☀", "2": "🔥", "3": "🔥", "4": "🔥", "5": "✨", "6": "⚡", "7": "⭐"}
    msg, users = await get("staff"), {}
    for item in res:
        if f"{item.access_level}" not in users:
            users[f"{item.access_level}"] = []
        users[f"{item.access_level}"].append(
            {
                "uid": item.uid,
                "name": [
                    f"{i.first_name} {i.last_name}" for i in names if i.id == item.uid
                ][0],
                "nickname": await utils.get_user_nickname(item.uid, chat_id),
                "access_level": item.access_level,
            }
        )
    for k in sorted(users.keys(), reverse=True):
        msg += (
            f"[{emoji[k]}] {await utils.get_chat_access_name(chat_id, int(k), settings.lvl_names[int(k)])}\n"
            + "".join(
                set(
                    [
                        f"➖ [id{item['uid']}|{item['nickname'] if item['nickname'] else item['name']}]\n"
                        for item in users[k]
                    ]
                )
            )
        )
    return msg


async def staff_custom(
    levels: Iterable[CachedCustomAccessLevelRow], users: Iterable[CachedAccessLevelRow]
):
    msg = await get("staff_custom")
    for level in levels:
        emoji = f"[{level.emoji}] " if level.emoji else ""
        tmpmsg = [f"{emoji}{level.name}\n"]
        for user in users:
            if user.access_level == level.access_level:
                tmpmsg.append(
                    f"➖ [id{user.uid}|{await utils.get_user_nickname(user.uid, level.chat_id) or await utils.get_user_name(user.uid)}]\n"
                )
        if len(tmpmsg) > 1:
            msg += f"{''.join(tmpmsg)}\n"
    return msg


async def unmute(uname, unickname, uid, name, nickname, id):
    return await get(
        "unmute", uid=uid, un=unickname or uname, id=id, n=nickname or name
    )


async def unmute_no_mute(id, name, nickname):
    return await get("unmute_no_mute", id=id, n=nickname or name)


async def unmute_higher():
    return await get("unmute_higher")


async def unmute_hint():
    return await get("unmute_hint")


async def unwarn(uname, unick, uid, name, nick, id):
    return await get("unwarn", uid=uid, un=unick or uname, id=id, n=nick or name)


async def unwarn_no_warns(id, name, nick):
    return await get("unwarn_no_warns", id=id, n=nick or name)


async def unwarn_higher():
    return await get("unwarn_higher")


async def unwarn_hint():
    return await get("unwarn_hint")


async def mutelist(res, mutedcount):
    msg = await get("mutelist", mutedcount=mutedcount)
    for ind, item in enumerate(res):
        nickname = await utils.get_user_nickname(item[0], item[1])
        msg += (
            f"[{ind + 1}]. [id{item[0]}|{nickname or await utils.get_user_name(item[0])}] | "
            f"{int((item[3] - time.time()) / 60)} минут | "
            f"{literal_eval(item[2])[-1] if item[2] and literal_eval(item[2])[-1] else 'Без указания причины'} "
            f"| Выдал: {literal_eval(item[4])[-1]}\n"
        )
    return msg


async def warnlist(res, warnedcount):
    msg = await get("warnlist", warnedcount=warnedcount)
    for ind, item in enumerate(res):
        nickname = await utils.get_user_nickname(item[0], item[1])
        msg += (
            f"[{ind + 1}]. [id{item[0]}|{nickname or await utils.get_user_name(item[0])}] | "
            f"кол-во: {item[3]}/3 | "
            f"{'Без указания причины' if not item[2] or not literal_eval(item[2])[-1] else literal_eval(item[2])[-1]} |"
            f" Выдал: {literal_eval(item[4])[-1]}\n"
        )
    return msg


async def setacc_hint():
    return await get("setacc_hint")


async def setacc_higher():
    return await get("setacc_higher")


async def setacc(uid, u_name, u_nick, acc, id, name, nick, lvlname=None):
    return await get(
        "setacc",
        u_n=f"[id{uid}|{u_nick or u_name}]",
        acc=lvlname if lvlname else settings.lvl_names[acc],
        n=f"[id{id}|{nick or name}]",
    )


async def setacc_already_have_acc(id, name, nick):
    return await get("setacc_already_have_acc", id=id, n=nick or name)


async def setacc_low_acc(acc):
    return await get("setacc_low_acc", acc=settings.lvl_names[acc])


async def setaccess_has_custom_level():
    return await get("setaccess_has_custom_level")


async def delaccess_has_custom_level():
    return await get("delaccess_has_custom_level")


async def delaccess_hint():
    return await get("delaccess_hint")


async def delaccess_myself():
    return await get("delaccess_myself")


async def delaccess_noacc(id, name, nick):
    return await get("delaccess_noacc", id=id, n=nick or name)


async def delaccess_higher():
    return await get("delaccess_higher")


async def delaccess(uid, uname, unick, id, name, nick):
    return await get("delaccess", uid=uid, un=unick or uname, id=id, n=nick or name)


async def timeouton(id, name, nickname):
    return await get("timeouton", id=id, n=nickname or name)


async def timeoutoff(id, name, nickname):
    return await get("timeoutoff", id=id, n=nickname or name)


async def inactive_hint():
    return await get("inactive_hint")


async def inactive_no_results():
    return await get("inactive_no_results")


async def inactive(uid, name, nick, count):
    return (
        await get("inactive_no_active")
        if not count
        else await get(
            "inactive",
            uid=uid,
            n=nick or name,
            count=utils.pluralize_words(
                int(count),
                (
                    "неактивного участника",
                    "неактивных участника",
                    "неактивных участников",
                ),
            ),
        )
    )


async def ban_hint():
    return await get("ban_hint")


async def ban(uid, u_name, u_nickname, id, name, nickname, cause, time):
    return await get(
        "ban",
        uid=uid,
        n=u_nickname or u_name,
        id=id,
        bn=nickname or name,
        time=f" {time} дней" if time < 3650 else "всегда",
        cause=f' по причине: "{cause}"' if cause is not None else "",
    )


async def ban_maxtime():
    return await get("ban_maxtime")


async def ban_myself():
    return await get("ban_myself")


async def ban_higher():
    return await get("ban_higher")


async def already_banned(name, nick, id, ban):
    return await get(
        "already_banned",
        id=id,
        n=nick or name,
        time_left=int((ban - time.time()) / 86400 + 1),
    )


async def unban(uname, unick, uid, name, nick, id):
    return await get("unban", uid=uid, un=unick or uname, id=id, n=nick or name)


async def unban_no_ban(id, name, nick):
    return await get("unban_no_ban", id=id, n=nick or name)


async def unban_higher():
    return await get("unban_higher")


async def unban_hint():
    return await get("unban_hint")


async def async_already_bound():
    return await get("async_already_bound")


async def async_done(uid, u_name, u_nickname):
    return await get("async_done", uid=uid, n=u_nickname or u_name)


async def async_limit():
    return await get("async_limit")


async def delasync_already_unbound():
    return await get("delasync_already_unbound")


async def delasync_done(uid, u_name, u_nickname, chname=""):
    return await get(
        "delasync_done",
        uid=uid,
        n=u_nickname or u_name,
        chname=f' "{chname}"' if chname else "",
    )


async def gkick(uid, u_name, u_nickname, chats, success):
    return await get(
        "gkick", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def gkick_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return await get(
        "gkick_start",
        uid=uid,
        un=u_nickname or u_name,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def gkick_hint():
    return await get("gkick_hint")


async def banlist(res, bancount):
    msg = await get("banlist", bancount=bancount)
    for k, i in enumerate(res):
        nickname = await utils.get_user_nickname(i[0], i[1])
        cause = literal_eval(i[2])[-1]
        msg += (
            f"[{k + 1}]. [id{i[0]}|{nickname or await utils.get_user_name(i[0])}] | "
            f"{int((i[3] - time.time()) / 86400) + 1} дней | "
            f"{cause if cause else 'Без указания причины'} | Выдал: {literal_eval(i[4])[-1]}\n"
        )
    return msg


async def gban(uid, u_name, u_nickname, chats, success):
    return await get(
        "gban", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def gban_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return await get(
        "gban_start",
        uid=uid,
        un=u_nickname or u_name,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def gban_hint():
    return await get("gban_hint")


async def kick_banned(id, name, nick, btime, cause):
    return await get(
        "kick_banned",
        id=id,
        n=nick or name,
        t=int((btime - time.time()) / 86400),
        cause=f" по причине {cause}" if cause else "",
    )


async def gunban(uid, u_name, u_nickname, chats, success):
    return await get(
        "gunban", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def gunban_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return await get(
        "gunban_start",
        uid=uid,
        un=u_nickname or u_name,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def gunban_hint():
    return await get("gunban_hint")


async def gmute(uid, u_name, u_nickname, chats, success):
    return await get(
        "gmute", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def gmute_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return await get(
        "gmute_start",
        uid=uid,
        un=u_nickname or u_name,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def gmute_hint():
    return await get("gmute_hint")


async def gunmute(uid, u_name, u_nickname, chats, success):
    return await get(
        "gunmute", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def gunmute_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return await get(
        "gunmute_start",
        uid=uid,
        un=u_nickname or u_name,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def gunmute_hint():
    return await get("gunmute_hint")


async def gwarn(uid, u_name, u_nick, chats, success):
    return await get(
        "gwarn", uid=uid, un=u_nick or u_name, success=success, chats=chats
    )


async def gwarn_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return await get(
        "gwarn_start",
        uid=uid,
        un=u_nickname or u_name,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def gwarn_hint():
    return await get("gwarn_hint")


async def gunwarn(uid, u_name, u_nickname, chats, success):
    return await get(
        "gunwarn", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def gunwarn_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return await get(
        "gunwarn_start",
        uid=uid,
        un=u_nickname or u_name,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def gunwarn_hint():
    return await get("gunwarn_hint")


async def gsnick(uid, u_name, u_nickname, chats, success):
    return await get(
        "gsnick", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def gsnick_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return await get(
        "gkick_start",
        uid=uid,
        un=u_nickname or u_name,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def gsnick_hint():
    return await get("gsnick_hint")


async def grnick(uid, u_name, u_nickname, chats, success):
    return await get(
        "grnick", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def grnick_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return await get(
        "grnick_start",
        uid=uid,
        un=u_nickname or u_name,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def grnick_hint():
    return await get("grnick_hint")


async def gdelaccess(uid, u_name, u_nickname, chats, success):
    return await get(
        "gdelaccess", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def gdelaccess_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return await get(
        "gdelaccess_start",
        uid=uid,
        un=u_nickname or u_name,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def gdelaccess_hint():
    return await get("gdelaccess_hint")


async def setaccess_myself():
    return await get("setaccess_myself")


async def gsetaccess(uid, u_name, u_nickname, chats, success):
    return await get(
        "gsetaccess", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def gsetaccess_start(uid, u_name, u_nickname, id, name, nickname, chats):
    return await get(
        "gsetaccess_start",
        uid=uid,
        un=u_nickname or u_name,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def gsetaccess_hint():
    return await get("gsetaccess_hint")


async def zov(uid, name, nickname, cause, members):
    call = [
        f"[id{i.member_id}|\u200b\u206c]"
        for i in members
        if i.member_id > 0
        and not getattr(i, "deleted", False)
        and not getattr(i, "banned", False)
    ]
    return await get(
        "zov",
        uid=uid,
        n=nickname or name,
        lc=len(call),
        lm=len(members),
        cause=cause,
        jc="".join(call),
    )


async def zov_hint():
    return await get("zov_hint")


async def chat_unbound():
    return await get("chat_unbound")


async def gzov_start(uid, u_name, u_nickname, chats):
    return await get("gzov_start", uid=uid, un=u_nickname or u_name, chats=chats)


async def gzov(uid, u_name, u_nickname, chats, success):
    return await get(
        "gzov", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def gzov_hint():
    return await get("gzov_hint")


async def creategroup_already_created(group):
    return await get("creategroup_already_created", group=group)


async def creategroup_done(uid, u_name, u_nickname, group):
    return await get("creategroup_done", uid=uid, n=u_nickname or u_name, group=group)


async def creategroup_incorrect_name():
    return await get("creategroup_incorrect_name")


async def creategroup_hint():
    return await get("creategroup_hint")


async def creategroup_premium():
    return await get("creategroup_premium")


async def bind_group_not_found(group):
    return await get("bind_group_not_found", group=group)


async def bind_chat_already_bound(group):
    return await get("bind_chat_already_bound", group=group)


async def bind_hint():
    return await get("bind_hint")


async def bind(uid, u_name, u_nickname, group):
    return await get("bind", uid=uid, n=u_nickname or u_name, group=group)


async def unbind_group_not_found(group):
    return await get("unbind_group_not_found", group=group)


async def unbind_chat_already_unbound(group):
    return await get("unbind_chat_already_unbound", group=group)


async def unbind_hint():
    return await get("unbind_hint")


async def unbind(uid, u_name, u_nickname, group):
    return await get("unbind", uid=uid, n=u_nickname or u_name, group=group)


async def delgroup_not_found(group):
    return await get("delgroup_not_found", group=group)


async def delgroup(uid, u_name, u_nickname, group):
    return await get("delgroup", group=group, uid=uid, n=u_nickname or u_name)


async def delgroup_hint():
    return await get("delgroup_hint")


async def s_invalid_group(group):
    return await get("s_invalid_group", group=group)


async def skick_hint():
    return await get("skick_hint")


async def skick(uid, u_name, u_nickname, chats, success):
    return await get(
        "skick", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def skick_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    return await get(
        "skick_start",
        uid=uid,
        un=u_nickname or u_name,
        group=group,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def sban_hint():
    return await get("sban_hint")


async def sban(uid, u_name, u_nickname, chats, success):
    return await get(
        "sban", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def sban_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    return await get(
        "sban_start",
        uid=uid,
        un=u_nickname or u_name,
        group=group,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def sunban_hint():
    return await get("sunban_hint")


async def sunban(uid, u_name, u_nickname, chats, success):
    return await get(
        "sunban", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def sunban_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    return await get(
        "sunban_start",
        uid=uid,
        un=u_nickname or u_name,
        group=group,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def ssnick_hint():
    return await get("ssnick_hint")


async def ssnick(uid, u_name, u_nickname, chats, success):
    return await get(
        "ssnick", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def ssnick_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    return await get(
        "ssnick_start",
        uid=uid,
        un=u_nickname or u_name,
        group=group,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def srnick_hint():
    return await get("srnick_hint")


async def srnick(uid, u_name, chats, success):
    return await get("srnick", uid=uid, u_name=u_name, success=success, chats=chats)


async def srnick_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    return await get(
        "srnick_start",
        uid=uid,
        un=u_nickname or u_name,
        group=group,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def szov_hint():
    return await get("szov_hint")


async def szov_start(uid, u_name, u_nickname, chats, group):
    return await get(
        "szov_start", uid=uid, un=u_nickname or u_name, group=group, chats=chats
    )


async def szov(uid, u_name, u_nickname, group, pool, success):
    return await get(
        "szov",
        uid=uid,
        un=u_nickname or u_name,
        success=success,
        pool=pool,
        group=group,
    )


async def ssetaccess_hint():
    return await get("ssetaccess_hint")


async def ssetaccess(uid, u_name, u_nickname, chats, success):
    return await get(
        "ssetaccess", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def ssetaccess_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    return await get(
        "ssetaccess_start",
        uid=uid,
        un=u_nickname or u_name,
        group=group,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def sdelaccess_hint():
    return await get("sdelaccess_hint")


async def sdelaccess(uid, u_name, u_nickname, chats, success):
    return await get(
        "sdelaccess", uid=uid, n=u_nickname or u_name, success=success, chats=chats
    )


async def sdelaccess_start(uid, u_name, u_nickname, id, name, nickname, group, chats):
    return await get(
        "ssetaccess_start",
        uid=uid,
        un=u_nickname or u_name,
        group=group,
        chats=chats,
        id=id,
        n=nickname or name,
    )


async def demote_choose():
    return await get("demote_choose")


async def demote_yon():
    return await get("demote_yon")


async def demote_disaccept():
    return await get("demote_disaccept")


async def demote_accept(id, name, nick):
    return await get("demote_accept", id=id, n=nick or name)


async def mygroups_no_groups():
    return await get("mygroups_no_groups")


async def editlvl_hint():
    return await get("editlvl_hint")


async def editlvl(id, name, nickname, cmd, beforelvl, lvl):
    return await get(
        "editlvl", id=id, n=nickname or name, cmd=cmd, beforelvl=beforelvl, lvl=lvl
    )


async def editlvl_command_not_found():
    return await get("editlvl_command_not_found")


async def editlvl_no_premium():
    return await get("editlvl_no_premium")


async def msg_hint():
    return await get("msg_hint")


async def blocked():
    return await get("blocked")


async def addblack_hint():
    return await get("addblack_hint")


async def addblack_myself():
    return await get("addblack_myself")


async def unban_myself():
    return await get("unban_myself")


async def addblack(uid, uname, unick, id, name, nick):
    return await get("addblack", uid=uid, un=unick or uname, id=id, n=nick or name)


async def blacked(id, name, nick):
    return await get("blacked", id=id, n=nick or name)


async def delblack_hint():
    return await get("delblack_hint")


async def delblack_myself():
    return await get("delblack_myself")


async def delblack(uid, uname, unick, id, name, nick):
    return await get("delblack", uid=uid, un=unick or uname, id=id, n=nick or name)


async def delblacked(id, name, nick):
    return await get("delblacked", id=id, n=nick or name)


async def delblack_no_user(id, name, nick):
    return await get("delblack_no_user", id=id, n=nick or name)


async def setstatus_hint():
    return await get("setstatus_hint")


async def setstatus(uid, uname, unick, id, name, nick):
    return await get("setstatus", uid=uid, un=unick or uname, id=id, n=nick or name)


async def delstatus_hint():
    return await get("delstatus_hint")


async def delstatus(uid, uname, unick, id, name, nick):
    return await get("delstatus", uid=uid, un=unick or uname, id=id, n=nick or name)


async def statuslist(pp):
    msg = ""
    k = 0
    for k, i in enumerate(pp):
        msg += (
            f"[{k + 1}]. [id{i[0]}|{await utils.get_user_name(i[0])}] | "
            f"Осталось: {int((i[1] - time.time()) / 86400) + 1} дней\n"
        )
    return await get("statuslist", premium_status=k) + msg


async def settings_():
    return await get("settings")


async def settings_category(category, chat_settings, chat_id):
    chat_settings = [
        settings.settings_meta.positions[category][k][i]
        for k, i in chat_settings.items()
    ]
    if category == "antispam":
        if (
            chat_settings[0] == "Вкл."
            and (
                val := await utils.get_chat_setting_value(chat_id, "messagesPerMinute")
            )
            is not None
        ):
            chat_settings[0] = (
                utils.pluralize_words(val, ("сообщение", "сообщения", "сообщений"))
                + "/мин"
            )
        if (
            chat_settings[1] == "Вкл."
            and (
                val := await utils.get_chat_setting_value(
                    chat_id, "maximumCharsInMessage"
                )
            )
            is not None
        ):
            chat_settings[1] = utils.pluralize_words(
                val, ("символ", "символа", "символов")
            )
        return await get(f"settings_{category}", settings=chat_settings)
    return await get(f"settings_{category}", settings=chat_settings)


async def settings_change_countable(
    chat_id, setting, pos, value, value2, pos2, punishment=None
):
    if (
        setting in settings.settings_meta.alt_to_delete
        or setting not in settings.settings_meta.countable_no_punishment
    ):
        if punishment == "deletemessage":
            punishment = "удаление сообщения"
        elif punishment == "kick":
            punishment = "исключение"
        elif punishment and punishment.startswith("mute"):
            pnshtime = int(punishment.split("|")[-1])
            punishment = "мут на" + (
                f" {pnshtime} минут" if pnshtime < 44600 else "всегда"
            )
        elif punishment and punishment.startswith("ban"):
            pnshtime = int(punishment.split("|")[-1])
            punishment = "блокировка на" + (
                f" {pnshtime} дней" if pnshtime < 3650 else "всегда"
            )
        elif punishment == "warn":
            punishment = "предупреждение"
        else:
            punishment = "без наказания"

    if setting in settings.settings_meta.alt_to_delete:
        return await get(
            f"settings_change_countable_{setting}",
            status="Включено" if pos else "Выключено",
            count=(0 if not value else value)
            if setting != "forwardeds"
            else (["все", "пользователи", "сообщества"][value or 0]),
            punishment=punishment,
            deletemsg="Включено" if pos2 else "Выключено",
        )
    elif setting not in settings.settings_meta.countable_no_punishment:
        return await get(
            f"settings_change_countable_{setting}",
            status="Включено" if pos else "Выключено",
            count=0 if not value else value,
            punishment=punishment,
        )
    elif setting == "nightmode":
        return await get(
            f"settings_change_countable_{setting}",
            status="Включено" if pos else "Выключено",
            time="❌" if not pos or value2 is None else value2,
        )
    elif setting == "welcome":
        w = await tables.Welcome.filter(chat_id=chat_id).first()
        return await get(
            f"settings_change_countable_{setting}",
            status="Включено" if pos else "Выключено",
            status2="Да" if pos2 else "Нет",
            value="Установлено"
            if pos and w is not None and (w.msg or w.photo)
            else "❌",
        )
    elif setting == "autodelete":
        return await get(
            f"settings_change_countable_{setting}",
            status="Включено" if pos else "Выключено",
            time=f"{utils.pluralize_hours(value)} {utils.pluralize_minutes(value % 3600)}"
            if value
            else "❌",
        )


async def settings_set_preset(category, setting):
    return await get(f"settings_set_preset_{category}_{setting}")


async def settings_change_countable_digit_error():
    return await get("settings_change_countable_digit_error")


async def settings_autodelete_input_error():
    return await get("settings_autodelete_input_error")


async def settings_change_countable_format_error():
    return await get("settings_change_countable_format_error")


async def settings_choose_punishment():
    return await get("settings_choose_punishment")


async def settings_countable_action(action, setting, text=None, image=None, url=None):
    if setting == "welcome":
        return await get(
            f"settings_{action}_{setting}",
            text="Не установлено" if not text else text,
            url="Не установлено" if not url else url,
            image="Не установлено" if not image else "Установлено",
        )
    return await get(f"settings_{action}_{setting}")


async def settings_set_punishment(punishment, p_time=0):
    if punishment == "deletemessage":
        punishment = "применили удаление сообщения в качестве наказания"
    elif punishment == "mute":
        punishment = (
            "применили мут на"
            + (f" {p_time} минут" if p_time < 44600 else "всегда")
            + " в качестве наказания"
        )
    elif punishment == "kick":
        punishment = "применили исключение в качестве наказания"
    elif punishment == "ban":
        punishment = (
            "применили блокировку на"
            + (f" {p_time} дней" if p_time < 3650 else "всегда")
            + " в качестве наказания"
        )
    elif punishment == "warn":
        punishment = "применили предупреждение в качестве наказания"
    elif punishment == "":
        punishment = "убрали наказание"
    return await get("settings_set_punishment", punishment=punishment)


async def settings_set_punishment_input(punishment):
    return await get(f"settings_set_punishment_{punishment}", punishment=punishment)


async def settings_change_countable_done(setting, data):
    return await get(f"settings_change_countable_done_{setting}", data=data)


async def settings_change_autodelete_done(itime):
    return await get(
        "settings_change_countable_done_autodelete",
        hours=utils.pluralize_hours(itime),
        minutes=utils.pluralize_minutes(int(itime % 3600)),
    )


async def settings_setlist(setting, type):
    return await get(f"settings_{setting}_set{type.lower()}list")


async def settings_exceptionlist(exceptions):
    msg = ""
    for k, i in enumerate(exceptions):
        msg += f"[{k + 1}]. {i}\n"
    return await get("settings_exceptionlist", msg=msg)


async def settings_listaction_action(setting, action):
    return await get(f"settings_listaction_{setting}_{action}")


async def settings_listaction_done(setting, action, data):
    return await get(f"settings_listaction_{setting}_{action}_done", data=data)


async def ugiveStatus(id, nick, name, uid, unick, uname, days):
    return await get(
        "ugiveStatus",
        id=id,
        n=nick or name,
        uid=uid,
        un=unick or uname,
        days=days,
        gtime=datetime.now().strftime("%d.%m.%Y / %H:%M:%S"),
    )


async def udelStatus(uid, dev_name):
    return await get("udelStatus", uid=uid, dev_name=dev_name)


async def q(uid, name, nick):
    return await get("q", uid=uid, n=nick or name)


async def q_fail(uid, name, nick):
    return await get("q_fail", uid=uid, n=nick or name)


async def chat(
    uid,
    uname,
    chat_id,
    bind,
    gbind,
    public,
    muted,
    banned,
    users,
    time,
    prefix,
    chat_name,
    prem,
):
    return await get(
        "chat",
        prefix=prefix,
        uid=uid,
        uname=uname,
        chat_id=chat_id,
        chat_name=chat_name,
        bind=bind,
        gbind=gbind,
        public=public,
        banned=banned,
        muted=muted,
        users=users,
        time=time,
        prem=prem,
    )


async def getnick(res, query):
    msg = ""
    k = 0
    for k, item in enumerate(res):
        msg += (
            f"{k + 1}. {item[1]} - [id{item[0]}|{await utils.get_user_name(item[0])}]\n"
        )
    return await get("getnick", query=query, cnt=k + 1) + msg


async def getnick_no_result(query):
    return await get("getnick_no_result", query=query)


async def getnick_hint():
    return await get("getnick_hint")


async def id_group():
    return await get("id_group")


async def id_deleted():
    return await get("id_deleted")


async def clear_old():
    return await get("clear_old")


async def mkick_error():
    return await get("mkick_error")


async def no_prem():
    return await get("no_prem")


async def mkick_no_kick():
    return await get("mkick_no_kick")


async def giveowner_hint():
    return await get("giveowner_hint")


async def giveowner_ask():
    return await get("giveowner_ask")


async def giveowner_no():
    return await get("giveowner_no")


async def giveowner(uid, unick, uname, id, nick, name):
    return await get("giveowner", uid=uid, un=unick or uname, id=id, n=nick or name)


async def bonus(id, nick, name, xp, premium, streak):
    maxxp = 2500 if premium else 1000
    return await get(
        "bonus",
        id=id,
        n=nick or name,
        xp=xp,
        nextxp=min(maxxp, xp + (50 if premium else 25)),
        maxxp=maxxp,
        s=""
        if not streak
        else f"Серия: {utils.pluralize_words(streak + 1, ('день', 'дня', 'дней'))} подряд! ",
    ) + (
        ""
        if premium
        else "\n✨ Премиум-пользователи получают до 2500 XP и бонус +50 в день. (/premium)"
    )


async def bonus_time(id, nick, name, timeleft):
    return await get(
        "bonus_time",
        id=id,
        n=nick or name,
        hours=utils.pluralize_hours((timeleft // 3600) * 3600),
        minutes=utils.pluralize_minutes(timeleft - (timeleft // 3600) * 3600),
    )


async def top_lvls(top, chattop):
    msg = await get("top_lvls")
    for k, i in enumerate(top.items()):
        msg += f"{utils.number_to_emoji(k + 1)} [id{i[0]}|{await utils.get_user_name(i[0])}] - {i[1]} уровень\n"
    msg += "\n🥨 В беседе:\n"
    for k, i in enumerate(chattop.items()):
        msg += f"{utils.number_to_emoji(k + 1)} [id{i[0]}|{await utils.get_user_name(i[0])}] - {i[1]} уровень\n"
    return msg


async def top_duels(duels, category="общее"):
    msg = await get("top_duels", category=category)
    for k, item in enumerate(duels) if duels else []:
        msg += f"{utils.number_to_emoji(k + 1)} [id{item[0]}|{await utils.get_user_name(item[0])}] - {item[1]} побед\n"
    return msg


async def top_rep(top, category):
    msg = await get("top_rep", category=category)
    for k, item in enumerate(top[:10]) if top else []:
        msg += f"{utils.number_to_emoji(k + 1)} [id{item[0]}|{await utils.get_user_name(item[0])}] - {'+' if item[1] > 0 else ''}{item[1]}\n"
    return msg


async def top_math(top):
    msg = await get("top_math")
    for k, item in enumerate(top[:10]) if top else []:
        msg += f"{utils.number_to_emoji(k + 1)} [id{item[0]}|{await utils.get_user_name(item[0])}] - {item[1]} ответов\n"
    return msg


async def top_bonus(top):
    msg = await get("top_bonus")
    for k, item in enumerate(top[:10]) if top else []:
        msg += f"{utils.number_to_emoji(k + 1)} [id{item[0]}|{await utils.get_user_name(item[0])}] - {item[1]} дней\n"
    return msg


async def top_coins(top):
    msg = await get("top_coins")
    for k, item in enumerate(top[:10]) if top else []:
        msg += f"{utils.number_to_emoji(k + 1)} [id{item[0]}|{await utils.get_user_name(item[0])}] - {utils.pluralize_words(item[1].coins, ('монетка', 'монетки', 'монет'))}\n"
    return msg


async def premmenu(menu_settings, prem):
    msg = await get("premmenu")
    c = 0
    for e, i in menu_settings.items():
        if e == "clear_by_fire":
            c += 1
            msg += f"\n[{c}]. Удаление сообщения с помощью реакции(🔥) | {'✔' if i == 1 else '❌'}"
        if not prem:
            continue
        if e == "border_color":
            c += 1
            msg += f"\n[{c}]. Смена цвета рамки в /stats | {i if i else 'Выкл.'}"
        if e == "tagnotif":
            c += 1
            msg += f"\n[{c}]. Оповещение об упоминаниях в беседах | {'✔' if i == 1 else '❌'}"
    return msg


async def premmenu_action(setting):
    return await get(f"premmenu_action_{setting}")


async def premmenu_action_complete(setting, value):
    return await get(f"premmenu_action_complete_{setting}", value=value)


async def prefix():
    return await get("prefix")


async def addprefix_max():
    return await get("addprefix_max")


async def addprefix_too_long():
    return await get("addprefix_too_long")


async def addprefix(uid, name, nick, prefix):
    return await get("addprefix", uid=uid, n=nick or name, prefix=prefix)


async def delprefix(uid, name, nick, prefix):
    return await get("delprefix", uid=uid, n=nick or name, prefix=prefix)


async def delprefix_not_found(prefix):
    return await get("delprefix_not_found", prefix=prefix)


async def listprefix(uid, name, nick, prefixes):
    if not prefixes:
        return (
            await get("listprefix", uid=uid, n=nick or name)
            + 'Префиксов не обнаружено. Используйте кнопку "Добавить префикс"'
        )
    return await get("listprefix", uid=uid, n=nick or name) + "".join(
        [f'➖ "{i}"\n' for i in prefixes]
    )


async def levelname_hint():
    return await get("levelname_hint")


async def levelname(uid, name, nick, lvl, lvlname):
    return await get("levelname", uid=uid, n=nick or name, lvlname=lvlname, lvl=lvl)


async def resetlevel_hint():
    return await get("resetlevel_hint")


async def ignore_hint():
    return await get("ignore_hint")


async def ignore_higher():
    return await get("ignore_higher")


async def ignore(id, name, nick):
    return await get("ignore", id=id, n=nick or name)


async def unignore_not_ignored():
    return await get("unignore_not_ignored")


async def unignore(id, name, nick):
    return await get("unignore", id=id, n=nick or name)


async def ignorelist(res, names):
    return await get("ignorelist", lres=len(res)) + "".join(
        [f"➖ [id{i}|{names[k]}]\n" for k, i in enumerate(res)]
    )


async def chatlimit_hint():
    return await get("chatlimit_hint")


async def chatlimit(id, name, nick, t, postfix, lpos):
    if bool(t):
        if t == 1 or (t > 20 and int(str(t)[-1]) == 1):
            if postfix == "s":
                postfix = "секунду"
            elif postfix == "m":
                postfix = "минуту"
            else:
                postfix = "час"
        elif t in [2, 3, 4] or (t > 20 and int(str(t)[-1]) in [2, 3, 4]):
            if postfix == "s":
                postfix = "секунды"
            elif postfix == "m":
                postfix = "минуты"
            else:
                postfix = "час"
        else:
            if postfix == "s":
                postfix = "секунд"
            elif postfix == "m":
                postfix = "минут"
            else:
                postfix = "часов"
        return await get("chatlimit", id=id, n=nick or name, t=t, postfix=postfix)
    elif lpos == 0:
        return await get("chatlimit_already_on")
    return await get("chatlimit_off", id=id, n=nick or name)


async def pm():
    return await get("pm")


async def market():
    return await get("market")


async def buy():
    return await get("buy")


async def buy_order(order_id, uid, name, days, cost, url):
    return await get(
        "buy_order", oid=order_id, id=uid, n=name, days=days, cost=cost, url=url
    )


async def pm_market():
    return await get("pm_market")


async def cmd_changed_in_cmds():
    return await get("cmd_changed_in_cmds")


async def cmd_changed_in_users_cmds(cmd):
    return await get("cmd_changed_in_users_cmds", cmd=cmd)


async def cmd_hint():
    return await get("cmd_hint")


async def cmd_prem(lr):
    return await get("cmd_prem", lr=lr)


async def cmd_set(uid, name, nick, cmd, changed):
    return await get("cmd_set", uid=uid, n=nick or name, changed=changed, cmd=cmd)


async def resetcmd_hint():
    return await get("resetcmd_hint")


async def resetcmd_not_found(cmd):
    return await get("resetcmd_not_found", cmd=cmd)


async def resetcmd_not_changed(cmd):
    return await get("resetcmd_not_changed", cmd=cmd)


async def resetcmd(uid, name, nick, cmd, cmdname):
    return await get("resetcmd", uid=uid, n=nick or name, cmdname=cmdname, cmd=cmd)


async def cmd_char_limit():
    return await get("cmd_char_limit")


async def cmdlist(cmdnames, page, cmdlen):
    msg = await get("cmdlist", cmdlen=cmdlen)
    c = page * 10
    for k, i in cmdnames.items():
        c += 1
        msg += f"[{c}] {k} - {i}\n"
    return msg


async def listasync(chats, total):
    msg = ""
    for k, i in enumerate(chats[:10]):
        if i["name"] is not None:
            msg += f"\n➖ ID: {i['id']} | Название: {i['name']}"
        else:
            total -= 1
    if total <= 0:
        return await get("listasync_not_found")
    return await get("listasync", total=total) + msg


async def duel_not_allowed():
    return await get("duel_not_allowed")


async def duel_hint():
    return await get("duel_hint")


async def not_enough_coins(uid, name, nick):
    return await get("not_enough_coins", uid=uid, n=nick or name)


async def duel_coins_minimum():
    return await get("duel_coins_minimum")


async def duel(uid, name, nick, coins):
    return await get("duel", uid=uid, n=nick or name, coins=coins, coins_win=coins)


async def duel_res(uid, uname, unick, id, name, nick, coins, has_comission, com=10):
    return await get(
        "duel_res",
        uid=uid,
        un=unick or uname,
        id=id,
        n=nick or name,
        coins=coins,
        com="" if not has_comission else f" с учётом комиссии {com}%",
    )


async def resetnick_yon():
    return await get("resetnick_yon")


async def resetnick_accept(id, name):
    return await get("resetnick_accept", id=id, name=name)


async def resetnick_disaccept():
    return await get("resetnick_disaccept")


async def resetaccess_hint():
    return await get("resetaccess_hint")


async def resetaccess_yon(lvl):
    return await get("resetaccess_yon", lvl=lvl)


async def resetaccess_accept(id, name, lvl):
    return await get("resetaccess_accept", id=id, name=name, lvl=lvl)


async def resetaccess_disaccept(lvl):
    return await get("resetaccess_disaccept", lvl=lvl)


async def olist(members):
    msg = await get("olist", members=len(list(members.keys())))
    for k, i in members.items():
        if i:
            msg += f"📱 {k} — Телефон\n"
        else:
            msg += f"💻 {k} — ПК\n"
    return msg


async def farm(name, uid):
    return await get("farm", name=name, uid=uid)


async def farm_cd(name, uid, timeleft):
    return await get("farm_cd", name=name, uid=uid, tl=int(timeleft / 60) + 1)


async def kickmenu():
    return await get("kickmenu")


async def kickmenu_kick_nonick(uid, name, nick, kicked):
    return await get("kickmenu_kick_nonick", uid=uid, n=nick or name, kicked=kicked)


async def kickmenu_kick_nick(uid, name, nick, kicked):
    return await get("kickmenu_kick_nick", uid=uid, n=nick or name, kicked=kicked)


async def kickmenu_kick_banned(uid, name, nick, kicked):
    return await get("kickmenu_kick_banned", uid=uid, n=nick or name, kicked=kicked)


async def send_notification(text, tagging):
    return await get(
        "send_notification", text=text, tagging="" if tagging is True else tagging
    )


async def notif(notifs, activenotifs):
    return await get("notif", lnotifs=notifs, lactive=activenotifs)


async def notif_already_exist(name):
    return await get("notif_already_exist", name=name)


async def notification(name, text, time, every, tag, status):
    msg = await get("notification", name=name, text=text)

    if every == 1440:
        msg += f"Каждый день в {datetime.fromtimestamp(time).strftime('%H:%M')}"
    elif every > 0:
        msg += f"Каждые {every} минут"
    elif every != -1:
        msg += f"Один раз в {datetime.fromtimestamp(time).strftime('%H:%M')}"

    msg += "\n🔔 Тег: "

    if tag == 1:
        msg += "Отключено"
    elif tag == 2:
        msg += "Всех"
    elif tag == 3:
        msg += "С правами"
    elif tag == 4:
        msg += "Без прав"

    msg += f"\n\n🟣 Статус: {'Выключено' if not status else 'Включено'}"

    return msg


async def notification_changing_text():
    return await get("notification_changing_text")


async def notification_changed_text(name):
    return await get("notification_changed_text", name=name)


async def notification_changing_time_choose():
    return await get("notification_changing_time_choose")


async def notification_changing_time_single():
    return await get("notification_changing_time_single")


async def notification_changing_time_everyday():
    return await get("notification_changing_time_everyday")


async def notification_changing_time_everyxmin():
    return await get("notification_changing_time_everyxmin")


async def notification_changed_time(name):
    return await get("notification_changed_time", name=name)


async def notification_changing_time_error():
    return await get("notification_changing_time_error")


async def notification_delete(name):
    return await get("notification_delete", name=name)


async def notification_changing_tag_choose():
    return await get("notification_changing_tag_choose")


async def notification_too_long_text(name):
    return await get("notification_too_long_text", name=name)


async def notifs(notifs):
    msg = await get("notifs")
    for k, i in enumerate(notifs):
        msg += f"[{k + 1}]. {i[1]} | {'Включено' if i[0] == 1 else 'Выключено'}\n"
    return msg


async def transfer_hint():
    return await get("transfer_hint")


async def transfer_wrong_number():
    return await get("transfer_wrong_number")


async def transfer_not_enough(uid, name, nickname):
    return await get("transfer_not_enough", uid=uid, n=nickname or name)


async def transfer_myself():
    return await get("transfer_myself")


async def transfer_community():
    return await get("transfer_community")


async def transfer(uid, uname, id, name, coins, com):
    return await get(
        "transfer",
        uid=uid,
        uname=uname,
        coins=coins,
        id=id,
        name=name,
        com="" if com == 0 else f" с учётом комиссии {com}%",
    )


async def transfer_not_allowed():
    return await get("transfer_not_allowed")


async def notadmin():
    return await get("notadmin")


async def reboot():
    return await get("reboot")


async def givexp(uid, dev_name, id, u_name, xp):
    return await get("givexp", uid=uid, dev_name=dev_name, xp=xp, id=id, u_name=u_name)


async def givecoins(uid, dev_name, id, u_name, coins):
    return await get(
        "givecoins", uid=uid, dev_name=dev_name, coins=coins, id=id, u_name=u_name
    )


async def inprogress():
    return await get("inprogress")


async def msg(devmsg):
    return await get("msg", devmsg=devmsg)


async def stats_loading():
    return await get("stats_loading")


async def unblock_noban():
    return await get("unblock_noban")


async def unblock_hint():
    return await get("unblock_hint")


async def unblock():
    return await get("unblock")


async def block_hint():
    return await get("block_hint")


async def block():
    return await get("block")


async def resetlvl(id, u_name):
    return await get("resetlvl", id=id, u_name=u_name)


async def resetlvlcomplete(id, u_name):
    return await get("resetlvlcomplete", id=id, u_name=u_name)


async def check_help():
    return await get("check_help")


async def check(id, name, nickname, ban, warn, mute):
    return await get(
        "check",
        id=id,
        n=nickname or name,
        ban=utils.pluralize_days(ban) if ban else "Отсутствуют",
        warn=f"{warn} из 3" if warn else "Отсутствуют",
        mute=utils.pluralize_minutes(mute) if mute else "Отсутствует",
    )


async def check_ban(
    id, name, nickname, ban, ban_history, ban_date, ban_from, ban_reason, ban_time
):
    msg = await get(
        "check_ban",
        id=id,
        n=nickname or name,
        lbh=len(ban_history),
        banm=utils.pluralize_days(ban) if ban else "Отсутствует",
    )
    if ban:
        msg += f"★ {ban_date} | {ban_from} | {utils.pluralize_days(ban_time)} | {ban_reason}"
    return msg


async def check_mute(
    id, name, nickname, mute, mute_history, mute_date, mute_from, mute_reason, mute_time
):
    msg = await get(
        "check_mute",
        id=id,
        n=nickname or name,
        lmh=len(mute_history),
        mutem=utils.pluralize_minutes(mute) if mute else "Отсутствует",
    )
    if mute:
        msg += f"★ {mute_date} | {mute_from} | {utils.pluralize_minutes(mute_time)} | {mute_reason}"
    return msg


async def check_warn(
    id, name, nickname, warn, warn_history, warns_date, warns_from, warns_reason
):
    msg = await get(
        "check_warn",
        id=id,
        n=nickname or name,
        lwh=len(warn_history),
        warnm=f"{warn} из 3" if warn else "Отсутствуют",
    )
    if warn:
        for k, _ in enumerate(warn_history[:warn]):
            msg += f"★ {warns_date[k]} | {warns_from[k]} | {warn - k} из 3 | {warns_reason[k]}\n"
    return msg


async def check_history_ban(id, name, nickname, dates, names, times, causes):
    msg = await get("check_history_ban", id=id, n=nickname or name)
    for k in range(len(times)):
        msg += f"★ {dates[k]} | {names[k]} | {utils.pluralize_days(times[k]) if times[k] < 3650 else 'Навсегда'} | {causes[k]}\n"
    return msg


async def check_history_mute(id, name, nickname, dates, names, times, causes):
    msg = await get("check_history_mute", id=id, n=nickname or name)
    for k in range(len(times)):
        msg += f"★ {dates[k]} | {names[k]} | {utils.pluralize_minutes(times[k]) if times[k] < 44600 else 'Навсегда'} | {causes[k]}\n"
    return msg


async def check_history_warn(id, name, nickname, dates, names, times, causes):
    msg = await get("check_history_warn", id=id, n=nickname or name)
    for k in range(len(times)):
        msg += f"★ {dates[k]} | {names[k]} | {causes[k]}\n"
    return msg


async def purge_start():
    return await get("purge_start")


async def purge_empty():
    return await get("purge_empty")


async def purge(nicknames, levels):
    return await get(
        "purge",
        nicknames=utils.pluralize_words(
            nicknames, ("никнейм", "никнейма", "никнеймов")
        ),
        levels=utils.pluralize_words(levels, ("уровень", "уровня", "уровней")),
    )


async def lvlbanned():
    return await get("lvlbanned")


async def lvlunban_noban():
    return await get("lvlunban_noban")


async def lvlunban_hint():
    return await get("lvlunban_hint")


async def lvlunban():
    return await get("lvlunban")


async def lvlban_hint():
    return await get("lvlban_hint")


async def lvlban():
    return await get("lvlban")


async def user_lvlbanned():
    return await get("user_lvlbanned")


async def repbanned():
    return await get("repbanned")


async def repunban_noban():
    return await get("repunban_noban")


async def repunban_hint():
    return await get("repunban_hint")


async def repunban():
    return await get("repunban")


async def repban_hint():
    return await get("repban_hint")


async def repban():
    return await get("repban")


async def anon_not_pm():
    return await get("anon_not_pm")


async def anon_help():
    return await get("anon_help")


async def anon_chat_does_not_exist():
    return await get("anon_chat_does_not_exist")


async def anon_not_member():
    return await get("anon_not_member")


async def anon_limit():
    return await get("anon_limit")


async def anon_link():
    return await get("anon_link")


async def anon_attachments():
    return await get("anon_link")


async def anon_message(id, text):
    return await get("anon_message", id=id, text=text)


async def anon_sent(id, chatname):
    return await get("anon_sent", id=id, chatname=chatname)


async def anon_not_allowed():
    return await get("anon_not_allowed")


async def deanon_help():
    return await get("deanon_help")


async def deanon_target_not_found():
    return await get("deanon_target_not_found")


async def deanon(id, from_id, name, nickname, time):
    return await get(
        "deanon",
        id=id,
        from_id=from_id,
        from_name=nickname or name,
        time=datetime.fromtimestamp(time).strftime("%d.%m.%Y - %H:%M"),
    )


async def antispam_punishment(
    uid, name, nick, setting, punishment, violation_count, time=0
):
    if setting in settings.settings_meta.positions["antispam"]:
        if punishment == "mute":
            time = f" {time} минут" if int(time) < 44600 else "всегда"
        elif punishment == "ban":
            time = f" {time} дней" if int(time) < 3650 else "всегда"
        return await get(
            f"antispam_punishment_{punishment}",
            uid=uid,
            n=nick or name,
            time=time,
            violation_count=violation_count,
            code=list(settings.settings_meta.positions["antispam"].keys()).index(
                setting
            )
            + 1,
        )
    return await get(
        f"antispam_punishment_{setting}_{punishment}",
        uid=uid,
        n=nick or name,
        time=time,
        violation_count=violation_count,
    )


async def nightmode_start(start, end):
    return await get("nightmode_start", start=start, end=end)


async def nightmode_end():
    return await get("nightmode_end")


async def commandcooldown(time):
    return await get(
        "commandcooldown",
        time=utils.pluralize_words(time, ["секунду", "секунды", "секунд"]),
    )


async def captcha(uid, n, ctime, punishment: str):
    if punishment == "kick":
        punishment = "кикнуты"
    elif punishment.startswith("mute"):
        t = punishment.split("|")[-1]
        punishment = (
            f"замучены на {utils.pluralize_words(int(t), ('час', 'часа', 'часов'))}"
        )
    elif punishment.startswith("ban"):
        t = punishment.split("|")[-1]
        punishment = (
            f"забанены на {utils.pluralize_words(int(t), ('день', 'дня', 'дней'))}"
        )
    return await get(
        "captcha",
        uid=uid,
        n=n,
        time=utils.pluralize_words(ctime, ("минута", "минуты", "минут")),
        punishment=punishment,
    )


async def captcha_punish(uid, n, punishment):
    ctime = None
    if punishment.startswith("mute"):
        ctime = punishment.split("|")[-1]
        punishment = punishment.split("|")[0]
    elif punishment.startswith("ban"):
        ctime = punishment.split("|")[-1]
        punishment = punishment.split("|")[0]
    return await get(f"captcha_punishment_{punishment}", uid=uid, n=n, time=ctime)


async def captcha_pass(uid, n, date):
    return await get("captcha_pass", uid=uid, n=n, date=date)


async def punishlist_delall_done(punish):
    return await get(
        "punishlist_delall_done",
        punish={"mute": "муты", "ban": "баны", "warn": "варны"}[punish],
    )


async def timeout(activated):
    return await get(
        "timeout",
        activated='Для активации нажмите "Включить"'
        if not activated
        else 'Для деактивации нажмите "Выключить"',
    )


async def timeout_settings():
    return await get("timeout_settings")


async def chats(chats_count, res, mode: enums.ChatsMode, page=0):
    def shorten(text, length=20):
        return text if len(text) <= length else text[: length - 3] + "..."

    return await get(
        "chats",
        chats_count=chats_count,
        type="🏆 PREMIUM" if mode == enums.ChatsMode.premium else "Обычные",
        chats="\n".join(
            f"[{k}]. [{chat[0].replace('https://', '')}|Чат ({chat[1][1].members_count} уч.)] | {shorten(chat[2])}"
            for k, chat in enumerate(res, start=1 + page * 15)
        ),
    )


async def setprem(id):
    return await get("setprem", id=id)


async def setprem_hint():
    return await get("setprem_hint")


async def delprem(id):
    return await get("delprem", id=id)


async def delprem_hint():
    return await get("delprem_hint")


async def premchat(uid, name):
    return await get("premchat", uid=uid, name=name)


async def premlist(prem):
    return await get("premlist") + "\n" + "\n".join([str(i[0]) for i in prem])


async def transfer_limit(u_prem):
    return await get("transfer_limit_prem" if u_prem else "transfer_limit")


async def code(code):
    return await get("code", code=code)


async def guess_hint():
    return await get("guess_hint")


async def guess_notenoughcoins():
    return await get("guess_notenoughcoins")


async def guess_not_allowed():
    return await get("guess_not_allowed")


async def guess_coins_minimum():
    return await get("guess_coins_minimum")


async def guess_win(bet, num, has_comission):
    return await get(
        "guess_win",
        bet=bet,
        num=num,
        com="" if not has_comission else " с учётом комиссии в 10%",
    )


async def guess_lose(bet, num):
    return await get("guess_lose", bet=bet, num=num)


async def antitag_on(uid, nick, name):
    return await get("antitag_on", uid=uid, n=nick or name)


async def antitag():
    return await get("antitag")


async def antitag_add(id, name, nick):
    return await get("antitag_add", uid=id, n=nick or name)


async def antitag_del(id, name, nick):
    return await get("antitag_del", uid=id, n=nick or name)


async def antitag_list(users, chat_id):
    return await get(
        "antitag_list",
        userslen=utils.pluralize_words(
            len(users), ("пользователь", "пользователя", "пользователей")
        ),
    ) + "".join(
        [
            f"[{k + 1}]. [id{i}|{await utils.get_user_nickname(i, chat_id) or await utils.get_user_name(i)}]\n"
            for k, i in enumerate(users)
        ]
    )


async def tagnotiferror():
    return await get("tagnotiferror")


async def promocreate_hint():
    return await get("promocreate_hint")


async def promocreate_alreadyexists(code):
    return await get("promocreate_alreadyexists", code=code)


async def promocreate(code, amnt, usage, date, promo_type, sub_needed):
    return await get(
        "promocreate",
        code=code,
        amnt=str(amnt) + (" опыта" if promo_type == "xp" else " монеток"),
        usage=f"\n🔘 Доступно использований: {usage}." if usage else "",
        date=f"\n🕒 Доступен до {date.strftime('%d.%m.%Y')}." if date else "",
        sub="\n✅ Подписка " + ("обязательна." if sub_needed else "не обязательна."),
    )


async def promodel_hint():
    return await get("promodel_hint")


async def promodel_notfound(code):
    return await get("promodel_notfound", code=code)


async def promodel(code):
    return await get("promodel", code=code)


async def promolist(promos):
    return await get(
        "promolist",
        promos="".join(
            [
                f"[{k + 1}]. {i[0]} - ({i[1]} исп.)\n"
                for k, i in enumerate(promos.items())
            ]
        ),
    )


async def promo_hint():
    return await get("promo_hint")


async def promo_not_member():
    return await get("promo_not_member")


async def promo_alreadyusedornotexists(uid, nick, name):
    return await get("promo_alreadyusedornotexists", uid=uid, n=nick or name)


async def promo(uid, nick, name, code, amnt, promo_type):
    return await get(
        "promo",
        uid=uid,
        n=nick or name,
        code=code,
        amnt=str(amnt) + (" опыта" if promo_type == "xp" else " монеток"),
    )


async def pmcmd():
    return await get("pmcmd")


async def pin_hint():
    return await get("pin_hint")


async def pin_cannot():
    return await get("pin_cannot")


async def unpin_notpinned():
    return await get("unpin_notpinned")


async def unpin_cannot():
    return await get("unpin_cannot")


async def import_settings(chid, name, import_settings):
    import_settings = {k: "🟢" if i else "🔴" for k, i in import_settings.items()}
    return await get(
        "import_settings",
        chid=chid,
        name=name,
        sys=import_settings["sys"],
        acc=import_settings["acc"],
        nicks=import_settings["nicks"],
        punishes=import_settings["punishes"],
        binds=import_settings["binds"],
    )


async def import_hint():
    return await get("import_hint")


async def import_notowner():
    return await get("delasync_not_owner")


async def import_(chid, name):
    return await get("import", chid=chid, name=name)


async def import_start(importchatid):
    return await get("import_start", chid=importchatid)


async def import_end(importchatid):
    return await get("import_end", chid=importchatid)


async def newpost(name, uid, addxp):
    return await get("newpost", n=name, uid=uid, addxp=addxp)


async def newpost_dup(name, uid, addxp):
    return await get("newpost_dup", n=name, uid=uid, addxp=addxp)


async def rename_hint():
    return await get("rename_hint")


async def rename_toolong():
    return await get("rename_toolong")


async def rename_error():
    return await get("rename_error")


async def rename(uid, name, nick):
    return await get("rename", uid=uid, n=nick or name)


async def scan_hint():
    return await get("scan_hint")


async def scan(url, threats, redirect, shortened):
    return await get(
        "scan",
        url=url,
        threats=f"🔴 В ссылке обнаружены вирусы: {', '.join(settings.google_threats.threats.get(i) or i for i in threats)}."
        if threats
        else "🟢 В ссылке не обнаружены вирусы.",
        redirect=f"🔴 В ссылке есть переадресация: {redirect}."
        if redirect
        else "🟢 В ссылке нет переадресаций.",
        shortened=f"🔴 Ссылка была сокращена: {shortened}."
        if shortened
        else "🟢 Не является короткой ссылкой.",
    )


async def rep_hint():
    return await get("rep_hint")


async def rep_myself():
    return await get("rep_myself")


async def rep_notinchat():
    return await get("rep_notinchat")


async def rep_limit(uprem, lasttime):
    timeleft = (lasttime + 86400) - time.time()
    return await get(
        "rep_limit",
        hours=utils.pluralize_hours((timeleft // 3600) * 3600),
        minutes=utils.pluralize_minutes(timeleft - (timeleft // 3600) * 3600),
    ) + (
        "\n⭐ С Premium-статусом лимит расширяется до 3 изменений в сутки."
        if not uprem
        else ""
    )


async def rep(isup, uid, uname, unick, id, name, nick, rep, reptop):
    return await get(
        "rep",
        up1="🟢" if isup else "🔴",
        up2="повысил" if isup else "понизил",
        uid=uid,
        un=unick or uname,
        id=id,
        n=nick or name,
        rep=f"{'+' if rep > 0 else ''}{rep}",
        reptop=reptop,
    )


async def invites(id, name, nick, invites):
    return await get("invites", id=id, n=nick or name, invites=invites)


async def block_chatblocked(id, reason):
    return await get(
        "block_chatblocked", id=id, reason=f"Комментарий: {reason}" if reason else ""
    )


async def block_userblocked(id, reason):
    return await get(
        "block_userblocked", id=id, reason=f"Комментарий: {reason}" if reason else ""
    )


async def block_blockeduserinvite(id, name, reason):
    return await get(
        "block_blockeduserinvite",
        id=id,
        n=name,
        reason=f"Комментарий: {reason}" if reason else "",
    )


async def block_chatunblocked(id):
    return await get("block_chatunblocked", id=id)


async def short_hint():
    return await get("short_hint")


async def short_failed():
    return await get("short_failed")


async def short(url, stat):
    return await get("short", url=url, stat=stat)


async def referralbonus(id, name, nickname, uid, uname, unickname):
    return await get(
        "referralbonus", id=id, n=nickname or name, uid=uid, un=unickname or uname
    )


async def allowinvite_hint():
    return await get("allowinvite_hint")


async def allowinvite_on():
    return await get("allowinvite_on")


async def allowinvite_off():
    return await get("allowinvite_off")


async def prempromocreate_hint():
    return await get("prempromocreate_hint")


async def prempromocreate_alreadyexists(code):
    return await get("prempromocreate_alreadyexists", code=code)


async def prempromocreate(code, val, date):
    return await get(
        "prempromocreate",
        code=code,
        val=val,
        date=f"\n🕒 Доступен до {date.strftime('%d.%m.%Y')} (включительно).",
    )


async def prempromodel_hint():
    return await get("prempromodel_hint")


async def prempromodel_notfound(code):
    return await get("prempromodel_notfound", code=code)


async def prempromodel(code):
    return await get("prempromodel", code=code)


async def prempromolist(promos):
    return await get(
        "prempromolist",
        promos="".join(
            [
                f"[{k + 1}]. {i[0]} - до {datetime.fromtimestamp(i[1]).strftime('%d.%m.%Y')}\n"
                for k, i in enumerate(promos)
            ]
        ),
    )


async def bindlist_hint():
    return await get("bindlist_hint")


async def bindlist(group_name, group):
    return await get(
        "bindlist",
        gr=group_name,
        grl=len(group),
        list="".join([f"\n➖ {id} | {n}" for id, n in group]),
    )


async def math_problem(math, level, xp):
    if level == 0:
        level = "📗 Легкий"
    elif level == 1:
        level = "📘 Средний"
    else:
        level = "📕 Сложный"
    return await get("math_problem", math=math, level=level, xp=xp)


async def math_winner(uid, name, nick, ans, xp, math):
    return await get(
        "math_winner", id=uid, n=nick or name, math=math.replace("?", ans), xp=xp
    )


async def premium_expire(uid, n, end):
    return await get("premium_expire", end=end, uid=uid, n=n)


async def filter():
    return await get("filter")


async def filter_punishments(punishment):
    return await get(
        "filter_punishments",
        p=("Удалять сообщение", "Замутить", "Заблокировать")[punishment],
    )


async def filter_list(filters, page):
    return await get(
        "filter_list",
        filters="\n".join(
            f'[{k + 1 + (page * 25)}]. {"📘" if i[0] else "📗"} | "{i[1]}"'
            for k, i in enumerate(filters)
        ),
    )


async def filteradd_hint():
    return await get("filteradd_hint")


async def filteradd(id, name, nick, word):
    return await get("filteradd", id=id, n=nick or name, word=word)


async def filteradd_dup(word):
    return await get("filteradd_dup", word=word)


async def filterdel_hint():
    return await get("filterdel_hint")


async def filterdel_not_found(word):
    return await get("filterdel_not_found", word=word)


async def filterdel(id, name, nick, word):
    return await get("filterdel", id=id, n=nick or name, word=word)


async def filterpunish_mute(uid, name, nick):
    return await get("filterpunish_mute", id=uid, n=nick or name)


async def filterpunish_ban(uid, name, nick):
    return await get("filterpunish_ban", id=uid, n=nick or name)


async def rewards_unsubbed(uid, name, nick):
    return await get("rewards_unsubbed", id=uid, n=nick or name)


async def rewards_collected(uid, name, nick, date):
    return await get("rewards_collected", id=uid, n=nick or name, date=date)


async def rewards_activated(uid, name, nick, timestamp, days):
    return await get(
        "rewards_activated",
        id=uid,
        n=nick or name,
        date_start=datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y"),
        date_end=datetime.fromtimestamp(timestamp + (86400 * days)).strftime(
            "%d.%m.%Y"
        ),
        days=days - int((time.time() - timestamp) / 86400),
    )


async def rewards(uid, name, nick, timestamp, days, xp):
    return await get(
        "rewards",
        id=uid,
        n=nick or name,
        date_start=datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y"),
        date_end=datetime.fromtimestamp(timestamp + (86400 * days)).strftime(
            "%d.%m.%Y"
        ),
        days=days,
        xp=xp,
    )


async def shop():
    return await get("shop")


async def shop_xp(coins, limit):
    return await get("shop_xp", coins=coins, limit=limit)


async def shop_bonuses(coins):
    return await get("shop_bonuses", coins=coins)


async def raid():
    return await get("raid")


async def raid_settings(trigger_status, trigger_invites, trigger_seconds):
    return await get(
        "raid_settings",
        trigger_status="Включено" if trigger_status else "Выключено",
        trigger_invites=trigger_invites,
        trigger_seconds=trigger_seconds,
    )


async def raid_trigger_set():
    return await get("raid_trigger_set")


async def rps_hint():
    return await get("rps_hint")


async def rps(uid, uname, unick, bet, id=None, name=None, nick=None):
    return await get(
        "rps",
        call=f"\n🔔 [id{uid}|{uname or unick}] вызвал сразиться пользователя — [id{id}|{name or nick}]\n"
        if id
        else "",
        uid=uid,
        uname=unick or uname,
        bet=bet,
    )


async def rps_play(uid, uname, unick, bet, id, name, nick):
    return await get(
        "rps_play",
        id=id,
        name=nick or name,
        uid=uid,
        uname=unick or uname,
        bet=bet,
    )


async def rps_end(win_id, win_name, win_nick, bet, win_pick, com):
    return await get(
        "rps_end",
        win_id=win_id,
        win_name=win_name,
        win_nick=win_nick,
        bet=bet,
        win_pick={"r": "камень", "p": "бумагу", "s": "ножницы"}[win_pick],
        lose_pick={"r": "ножницы", "p": "камень", "s": "бумагу"}[win_pick],
        com=f" с учётом комиссии {com}%" if com else "",
    )


async def rps_draw(bet, pick):
    return await get(
        "rps_draw",
        bet=bet,
        pick={"r": "камень", "p": "бумагу", "s": "ножницы"}[pick],
    )


async def rps_bet_limit():
    return await get("rps_bet_limit")


async def rps_not_enough_coins():
    return await get("rps_not_enough_coins")


async def up_cooldown(remaining):
    return await get(
        "up_cooldown",
        hours=utils.pluralize_hours(hours := ((remaining // 3600) * 3600)),
        minutes=utils.pluralize_minutes(remaining - hours),
    )


async def up_chat_is_not_premium():
    return await get("up_chat_is_not_premium")


async def up():
    return await get("up")


async def chats_not_allowed():
    return await get("chats_not_allowed")


async def unexpected_error():
    return await get("unexpected_error")


async def createlevel_hint(limit):
    return await get("createlevel_hint", limit=limit)


async def createlevel_level_limit(is_premium, level):
    limit = 10 if not is_premium else 50
    return await get(
        "createlevel_level_limit",
        limit=limit,
        add=", c Premium-статусом лимит расширяется на +40 уровней прав"
        if not is_premium
        else "",
    )


async def createlevel_char_limit():
    return await get("createlevel_char_limit")


async def createlevel_level_already_exists(level, name):
    return await get("createlevel_level_already_exists", level=level, name=name)


async def createlevel_name_already_exists(name):
    return await get("createlevel_name_already_exists", name=name)


async def createlevel_name_forbidden_chars(chars):
    return await get("createlevel_name_forbidden_chars", chars=chars)


async def createlevel(name, level):
    return await get("createlevel", name=name, level=level)


async def customlevel_settings(level, name, emoji, status, role_holders, commands):
    return await get(
        "customlevel_settings",
        level=level,
        name=name,
        emoji=emoji or "—",
        status="Вкл." if status else "Выкл.",
        role_holders=role_holders,
        commands=", ".join(commands) if commands else "—",
    )


async def customlevel_delete_yon(name, level):
    return await get("customlevel_delete_yon", name=name, level=level)


async def customlevel_delete(name, level):
    return await get("customlevel_delete", name=name, level=level)


async def customlevel_remove_all_yon(name, level):
    return await get("customlevel_remove_all_yon", name=name, level=level)


async def customlevel_remove_all(name, level, holders):
    return await get(
        "customlevel_remove_all",
        name=name,
        level=level,
        holders=utils.pluralize_words(
            holders, ("пользователя", "пользователей", "пользователей")
        ),
    )


async def customlevel_set_priority(limit):
    return await get("customlevel_set_priority", limit=limit)


async def customlevel_set_name():
    return await get("customlevel_set_name")


async def customlevel_set_emoji():
    return await get("customlevel_set_emoji")


async def customlevel_set_commands():
    return await get("customlevel_set_commands")


async def customlevel_set_commands_presets(name, level):
    return await get("customlevel_set_commands_presets", name=name, level=level)


async def customlevel_set_commands_done(name, level, commands, additional_text=""):
    return await get(
        "customlevel_set_commands_done",
        name=name,
        level=level,
        commands=", ".join(commands),
        add=additional_text,
    )


async def customlevel_set_priority_done(name, new_priority):
    return await get("customlevel_set_priority_done", name=name, np=new_priority)


async def customlevel_set_name_done(old_name, new_name):
    return await get("customlevel_set_name_done", nn=new_name, on=old_name)


async def customlevel_set_emoji_done(name, new_emoji):
    return await get("customlevel_set_emoji_done", ne=new_emoji, name=name)


async def levelmenu(levels, activated):
    return await get("levelmenu", levels=levels, activated=activated)


async def setlevel_hint():
    return await get("setlevel_hint")


async def setlevel_level_not_found(level):
    return await get("setlevel_level_not_found", level=level)


async def setlevel_level_too_high():
    return await get("setlevel_level_too_high")


async def setlevel_has_not_custom_level():
    return await get("setlevel_has_not_custom_level")


async def setlevel_to_level_higher():
    return await get("setlevel_to_level_higher")


async def setlevel(uid, unick, uname, level_name, level, id, nick, name):
    return await get(
        "setlevel",
        uid=uid,
        uname=unick or uname,
        level=level,
        levelname=level_name,
        id=id,
        name=nick or name,
    )


async def dellevel_hint():
    return await get("dellevel_hint")


async def dellevel_has_no_level():
    return await get("dellevel_has_no_level")


async def dellevel_has_not_custom_level():
    return await get("dellevel_has_not_custom_level")


async def dellevel(uid, unick, uname, level_name, level, id, nick, name):
    return await get(
        "dellevel",
        uid=uid,
        uname=unick or uname,
        level=level,
        levelname=level_name,
        id=id,
        name=nick or name,
    )


async def event(
    send_messages_base: int,
    send_messages: int,
    transfer_coins_base: int,
    transfer_coins: int,
    rep_users_base: int,
    rep_users: int,
    win_duels_base: int,
    win_duels: int,
    level_up: int,
    cases_recieved: int,
):
    now = datetime.now()
    til_reset = now.replace(hour=5)
    if til_reset <= now:
        til_reset += timedelta(days=1)
    return await get(
        "event",
        now=now.strftime("%d.%m.%Y"),
        til_reset=int((til_reset - now).total_seconds() // 3600),
        messages_e="1️⃣" if send_messages > 0 else "✅",
        messages=(
            f"{send_messages_base - send_messages}/"
            if send_messages > 0
            else ""
        )
        + f"{utils.pluralize_words(send_messages_base, ('сообщение', 'сообщения', 'сообщений'))}",
        transfer_e="2️⃣" if transfer_coins > 0 else "✅",
        transfer=(
            f"{transfer_coins_base - transfer_coins}/"
            if transfer_coins > 0
            else ""
        )
        + f"{utils.pluralize_words(transfer_coins_base, ('монетку', 'монетки', 'монеток'))}",
        rep_e="3️⃣" if rep_users > 0 else "✅",
        rep=(
            f"{rep_users_base - rep_users}/"
            if rep_users > 0
            else ""
        )
        + f"{utils.pluralize_words(rep_users_base, ('пользователю', 'пользователям', 'пользователям'))}",
        duels_e="4️⃣" if win_duels > 0 else "✅",
        duels=(
            f"{win_duels_base - win_duels}/"
            if win_duels > 0
            else ""
        )
        + f"{utils.pluralize_words(win_duels_base, ('раз', 'раза', 'раз'))}",
        lvlup_e="5️⃣" if level_up > 0 else "✅",
        cases=cases_recieved,
    )
