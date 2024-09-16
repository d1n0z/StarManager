import re

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

import keyboard
import messages
from Bot.checkers import haveAccess
from Bot.rules import SearchCMD
from Bot.utils import getUserPremium, getUserName, getUserNickname, getChatName, getUserAccessLevel, getIDFromMessage
from config.config import API, COMMANDS, LVL_NAMES
from db import GPool, ChatGroups, Filters, CMDLevels, AccessNames

bl = BotLabeler()


@bl.chat_message(SearchCMD('async'))
async def asynch(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    gpool = GPool.get_or_none(uid=uid, chat_id=chat_id)
    if gpool is not None:
        msg = messages.async_already_bound()
        await message.reply(disable_mentions=1, message=msg)
        return
    bound = len(GPool.select().where(GPool.uid == uid, GPool.chat_id == chat_id))
    u_premium = await getUserPremium(uid)
    if not ((not u_premium and bound < 30) or (u_premium and bound < 100)):
        msg = messages.async_limit()
        await message.reply(disable_mentions=1, message=msg)
        return
    GPool.create(uid=uid, chat_id=chat_id)
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.async_done(uid, u_name, u_nickname)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('delasync'))
async def delasync(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) == 2 and data[1].isdigit():
        delchid = int(data[1])
    else:
        delchid = chat_id
    uid = message.from_id
    gpool = GPool.get_or_none(GPool.uid == uid, GPool.chat_id == delchid)
    if gpool is None:
        msg = messages.delasync_already_unbound()
        await message.reply(disable_mentions=1, message=msg)
        return
    gpool.delete_instance()
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    chat_name = await getChatName(delchid)
    msg = messages.delasync_done(uid, u_name, u_nickname, chat_name)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('creategroup'))
async def creategroup(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        msg = messages.creategroup_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    group_name = message.text[13:]
    pattern = re.compile(r"[a-zA-Z0-9]")
    if len(pattern.findall(group_name)) != len(group_name) or len(group_name) > 16:
        msg = messages.creategroup_incorrect_name()
        await message.reply(disable_mentions=1, message=msg)
        return

    uid = message.from_id
    u_premium = await getUserPremium(uid)
    if len(set(i.group for i in ChatGroups.select().where(ChatGroups.uid == uid))) > 5 and not u_premium:
        msg = messages.creategroup_premium()
        await message.reply(disable_mentions=1, message=msg)
        return

    if ChatGroups.get_or_none(ChatGroups.group == group_name, ChatGroups.uid == uid) is not None:
        msg = messages.creategroup_already_created(group_name)
        await message.reply(disable_mentions=1, message=msg)
        return
    ChatGroups.create(uid=uid, chat_id=chat_id, group=group_name)
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.creategroup_done(uid, u_name, u_nickname, group_name)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('bind'))
async def bind(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        msg = messages.bind_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    group_name = ' '.join(data[1:])
    uid = message.from_id
    gr = ChatGroups.get_or_none(ChatGroups.group == group_name, ChatGroups.uid == uid)
    if gr is None:
        msg = messages.bind_group_not_found(group_name)
        await message.reply(disable_mentions=1, message=msg)
        return

    gr = ChatGroups.get_or_none(ChatGroups.group == group_name, ChatGroups.chat_id == chat_id)
    if gr is not None:
        msg = messages.bind_chat_already_bound(group_name)
        await message.reply(disable_mentions=1, message=msg)
        return

    ChatGroups.create(uid=uid, chat_id=chat_id, group=group_name)
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.bind(uid, u_name, u_nickname, group_name)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('unbind'))
async def unbind(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.split()
    if len(data) <= 1:
        msg = messages.unbind_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    group_name = message.text[8:]
    gr = ChatGroups.get_or_none(ChatGroups.group == group_name)
    if gr is None:
        msg = messages.unbind_group_not_found(group_name)
        await message.reply(disable_mentions=1, message=msg)
        return

    gr = ChatGroups.get_or_none(ChatGroups.group == group_name, ChatGroups.chat_id == chat_id)
    if gr is None:
        msg = messages.unbind_chat_already_unbound(group_name)
        await message.reply(disable_mentions=1, message=msg)
        return
    gr.delete_instance()

    uid = message.from_id
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.unbind(uid, u_name, u_nickname, group_name)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('delgroup'))
async def delgroup(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    if len(data) <= 1:
        msg = messages.delgroup_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    group_name = message.text[10:]

    gr = ChatGroups.select().where(ChatGroups.group == group_name, ChatGroups.uid == uid)
    if len(gr) <= 0:
        msg = messages.delgroup_not_found(group_name)
        await message.reply(disable_mentions=1, message=msg)
        return

    ChatGroups.delete().where(ChatGroups.group == group_name, ChatGroups.uid == uid).execute()
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.delgroup(uid, u_name, u_nickname, group_name)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('mygroups'))
async def mygroups(message: Message):
    uid = message.from_id
    groups = ChatGroups.select().where(ChatGroups.uid == uid)
    msg = '🟣 Список ваших групп (Всего: %s)\n\n'
    lengroups = 0
    if len(groups) > 0:
        for item in groups:
            lengr = len(ChatGroups.select().where(ChatGroups.group == item.group, ChatGroups.uid == uid))
            if item.group not in msg:
                lengroups += 1
                msg += f'➖ {lengroups} | {item.group} | Количество бесед : {lengr}\n'
        msg = msg.replace('%s', f'{lengroups}')
    else:
        msg = messages.mygroups_no_groups()
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('addfilter'))
async def addfilter(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.lower().split()
    if len(data) <= 1:
        msg = messages.addfilter_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    addfilter = ' '.join(data[1:])
    uid = message.from_id
    u_name = await getUserName(uid)
    Filters.get_or_create(filter=addfilter, chat_id=chat_id)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.addfilter(uid, u_name, u_nickname)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('delfilter'))
async def delfilter(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.lower().split()
    if len(data) <= 1:
        msg = messages.delfilter_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    delfilter = ' '.join(data[1:])

    filter = Filters.get_or_none(Filters.chat_id == chat_id, Filters.filter == delfilter)
    if filter is None:
        msg = messages.delfilter_no_filter()
        await message.reply(disable_mentions=1, message=msg)
        return
    filter.delete_instance()
    uid = message.from_id
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.delfilter(uid, u_name, u_nickname)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('filterlist'))
async def filterlist(message: Message):
    chat_id = message.peer_id - 2000000000
    filters = Filters.select().where(Filters.chat_id == chat_id)
    if len(filters) == 0:
        msg = '⚠ В данной беседе отсутствуют запрещённые слова, вы можете добавить используя /addfilter'
    else:
        msg = f'🟣 Список запрещенных слов (Всего : {len(filters)})\n\n'
        msg += '➖ Полный список : '
        for ind, item in enumerate(filters):
            msg += f'{item.filter} '
            if ind + 1 != len(filters):
                msg += ', '
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('gaddfilter'))
async def gaddfilter(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.lower().split()
    if len(data) <= 1:
        msg = messages.gaddfilter_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    try:
        pool = GPool.select().where(GPool.uid == GPool.get(GPool.chat_id == chat_id).uid).iterator()
        pool = [i.chat_id for i in pool]
        if len(pool) == 0:
            raise
    except:
        msg = messages.chat_unbound()
        await message.reply(disable_mentions=1, message=msg)
        return

    uid = message.from_id
    name = await getUserName(uid)
    if len(pool) == 0:
        msg = messages.chat_unbound()
        await message.reply(disable_mentions=1, message=msg)
        return
    kicker_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.gaddfilter_start(uid, kicker_name, u_nickname, len(pool))
    edit = await message.reply(disable_mentions=1, message=msg)
    addfilter = ' '.join(data[1:])
    success = 0
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        if not await haveAccess('gaddfilter', chat_id, u_acc):
            continue
        u_name = await getUserName(uid)
        Filters.get_or_create(filter=addfilter, chat_id=chat_id)

        if chat_id == edit.peer_id - 2000000000:
            u_nickname = await getUserNickname(uid, chat_id)
            msg = messages.addfilter(uid, u_name, u_nickname)
            await message.reply(disable_mentions=1, message=msg)
        success += 1

    msggkick = messages.gaddfilter(uid, name, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.message_id, message=msggkick)


@bl.chat_message(SearchCMD('gdelfilter'))
async def gdelfilter(message: Message):
    chat_id = message.peer_id - 2000000000
    data = message.text.lower().split()
    if len(data) <= 1:
        msg = messages.gdelfilter_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    try:
        pool = GPool.select().where(GPool.uid == GPool.get(GPool.chat_id == chat_id).uid).iterator()
        pool = [i.chat_id for i in pool]
        if len(pool) == 0:
            raise
    except:
        msg = messages.chat_unbound()
        await message.reply(disable_mentions=1, message=msg)
        return

    uid = message.from_id
    name = await getUserName(uid)
    if len(pool) == 0:
        msg = messages.chat_unbound()
        await message.reply(disable_mentions=1, message=msg)
        return
    kicker_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.gdelfilter_start(uid, kicker_name, u_nickname, len(pool))
    edit = await message.reply(disable_mentions=1, message=msg)
    delfilter = ' '.join(data[1:])
    success = 0
    for chat_id in pool:
        u_acc = await getUserAccessLevel(uid, chat_id)
        if not await haveAccess('grnick', chat_id, u_acc):
            continue
        u_name = await getUserName(uid)
        filter = Filters.get_or_none(Filters.chat_id == chat_id, Filters.filter == delfilter)
        if filter is not None:
            filter.delete_instance()
        if chat_id == edit.peer_id - 2000000000:
            u_nickname = await getUserNickname(uid, chat_id)
            msg = messages.delfilter(uid, u_name, u_nickname)
            await message.reply(disable_mentions=1, message=msg)
        success += 1

    msggkick = messages.gdelfilter(uid, name, len(pool), success)
    await API.messages.edit(peer_id=edit.peer_id, conversation_message_id=edit.message_id, message=msggkick)


@bl.chat_message(SearchCMD('editlevel'))
async def editlevel(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    u_premium = await getUserPremium(uid)
    if not u_premium:
        msg = messages.editlvl_no_premium()
        await message.reply(disable_mentions=1, message=msg)
        return
    data = message.text.split()
    if len(data) != 3:
        msg = messages.editlvl_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    try:
        command = data[1]
        given_lvl = int(data[2])
    except:
        msg = messages.editlvl_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if given_lvl < 0 or given_lvl > 7:
        msg = messages.editlvl_hint()
        await message.reply(disable_mentions=1, message=msg)
        return
    if command not in COMMANDS:
        msg = messages.editlvl_command_not_found()
        await message.reply(disable_mentions=1, message=msg)
        return
    bl = CMDLevels.get_or_none(CMDLevels.chat_id == chat_id, CMDLevels.cmd == command)
    if bl is not None:
        original_lvl = bl.lvl
        bl.lvl = given_lvl
        bl.save()
    else:
        original_lvl = COMMANDS[command]
        CMDLevels.create(chat_id=chat_id, lvl=given_lvl, cmd=command)
    u_name = await getUserName(uid)
    u_nickname = await getUserNickname(uid, chat_id)
    msg = messages.editlvl(uid, u_name, u_nickname, command, original_lvl, given_lvl)
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('giveowner'))
async def giveowner(message: Message):
    chat_id = message.peer_id - 2000000000
    id = await getIDFromMessage(message)
    if id is not None:
        kb = keyboard.giveowner(chat_id, id, message.from_id)
        msg = messages.giveowner_ask()
        await message.reply(disable_mentions=1, message=msg, keyboard=kb)
    else:
        msg = messages.giveowner_hint()
        await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('levelname'))
async def levelname(message: Message):
    chat_id = message.peer_id - 2000000000
    u_premium = await getUserPremium(message.from_id)
    if not u_premium:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    data = message.text.split()
    try:
        lvl = int(data[1])
    except:
        msg = messages.levelname_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    if len(data) < 3 or lvl < 0 or lvl > 8:
        msg = messages.levelname_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    ac = AccessNames.get_or_create(chat_id=chat_id, lvl=lvl)[0]
    ac.name = ' '.join(data[2:])
    ac.save()

    uid = message.from_id
    name = await getUserName(uid)
    nick = await getUserNickname(uid, chat_id)

    msg = messages.levelname(uid, name, nick, lvl, ' '.join(data[2:]))
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('resetlevel'))
async def resetlevel(message: Message):
    chat_id = message.peer_id - 2000000000
    u_premium = await getUserPremium(message.from_id)
    if not u_premium:
        msg = messages.no_prem()
        await message.reply(disable_mentions=1, message=msg)
        return

    data = message.text.split()
    try:
        lvl = int(data[1])
    except:
        msg = messages.resetlevel_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    if len(data) < 2 or lvl < 0 or lvl > 8:
        msg = messages.resetlevel_hint()
        await message.reply(disable_mentions=1, message=msg)
        return

    ac = AccessNames.get_or_create(chat_id=chat_id, lvl=lvl)[0]
    ac.name = LVL_NAMES[lvl]
    ac.save()

    uid = message.from_id
    name = await getUserName(uid)
    nick = await getUserNickname(uid, chat_id)

    msg = messages.levelname(uid, name, nick, lvl, LVL_NAMES[lvl])
    await message.reply(disable_mentions=1, message=msg)


@bl.chat_message(SearchCMD('settings'))
async def settings(message: Message):
    msg = messages.settings()
    kb = keyboard.settings(message.from_id)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)


@bl.chat_message(SearchCMD('listasync'))
async def listasync(message: Message):
    uid = message.from_id
    chat_ids = [i.chat_id for i in GPool.select().where(GPool.uid == uid).iterator()]
    total = len(chat_ids)
    chat_ids = chat_ids[:15]
    names = []
    if len(chat_ids) > 0:
        for i in chat_ids:
            names.append(await getChatName(i))
    chats_info = [{"id": i, "name": names[k]} for k, i in enumerate(chat_ids)]

    msg = messages.listasync(chats_info, total)
    kb = keyboard.listasync(uid, total)
    await message.reply(disable_mentions=1, message=msg, keyboard=kb)
