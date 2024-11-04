import locale
import os
import tempfile
import time
import traceback
from ast import literal_eval
from datetime import date, datetime
from typing import Iterable, Any

import requests
import urllib3
import validators
import xmltodict
from memoization import cached
from multicolorcaptcha import CaptchaGenerator
from nudenet import NudeDetector
from vkbottle import PhotoMessageUploader
from vkbottle.bot import Bot
from vkbottle.tools.mini_types.bot.foreign_message import ForeignMessageMin
from vkbottle_types.objects import MessagesMessage, MessagesMessageAttachmentType, MessagesSendUserIdsResponseItem

from config.config import (API, VK_API_SESSION, VK_TOKEN_GROUP, GROUP_ID, TASKS_DAILY, PREMIUM_TASKS_DAILY,
                           PREMIUM_TASKS_DAILY_TIERS, TASKS_WEEKLY, PREMIUM_TASKS_WEEKLY, SETTINGS, PATH,
                           NSFW_CATEGORIES, SETTINGS_ALT, SETTINGS_DEFAULTS, MAIN_DEVS, PREMMENU_DEFAULT, PREMMENU_TURN)
from db import pool


async def getUserName(uid: int) -> str:
    if uid < 0:
        return await getGroupName(uid)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            name = await c.execute('select name from usernames where uid=%s', (uid,))
            if name := await name.fetchone():
                return name[0]
            name = await API.users.get(user_ids=uid)
            if not name:
                return 'UNKNOWN'
            await c.execute('insert into usernames (uid, name) values (%s, %s)',
                            (uid, f"{name[0].first_name} {name[0].last_name}"))
            await conn.commit()
            return f"{name[0].first_name} {name[0].last_name}"


async def kickUser(uid: int, chat_id: int) -> bool:
    try:
        await API.messages.remove_chat_user(chat_id=chat_id, member_id=uid)
        if (await getChatSettings(chat_id))['main']['deleteAccessAndNicknameOnLeave']:
            async with (await pool()).connection() as conn:
                async with conn.cursor() as c:
                    await c.execute('delete from accesslvl where chat_id=%s and uid=%s', (chat_id, uid))
                    await c.execute('delete from nickname where chat_id=%s and uid=%s', (chat_id, uid))
                    await conn.commit()
    except:
        return False
    return True


async def deleteMessages(cmids: int | Iterable[int], chat_id: int) -> bool:
    try:
        await API.messages.delete(group_id=GROUP_ID, delete_for_all=True, peer_id=chat_id + 2000000000, cmids=cmids)
    except:
        return False
    return True


async def getIDFromMessage(message: str, reply: ForeignMessageMin | None, place: int = 2) -> int:
    """
    The getIDFromMessage function is used to get the ID of a user from a message.

    :param message: Get the message text
    :param reply: Get the reply_message object
    :param place: Determine which part of the message to get the id from
    :return: The user's id
    """
    data = message.split()
    try:
        if len(data) >= place or reply:
            if reply is None:
                try:
                    if data[place - 1].count('[id') != 0:
                        id = data[place - 1][data[place - 1].find('[id') + 3:data[place - 1].find('|')]
                    elif data[place - 1].count('[club') != 0:
                        id = '-' + data[place - 1][data[place - 1].find('[club') + 5:data[place - 1].find('|')]
                    elif data[place - 1].count('vk.') != 0:
                        id = data[place - 1][data[place - 1].find('vk.'):]
                        id = id[id.find('/') + 1:]
                        try:
                            id = await API.users.get(user_ids=id)
                            id = id[0].id
                        except:
                            traceback.print_exc()
                            id = int(id)
                    elif data[place - 1].isdigit():
                        id = data[place - 1]
                    elif data[place - 1].count('@id') != 0:
                        id = data[place - 1][data[place - 1].find('@id') + 3:]
                    else:
                        id = False
                except IndexError:
                    id = False
            else:
                id = reply.from_id
        else:
            id = False

        return int(id)
    except:
        return 0


async def sendMessageEventAnswer(event_id: Any, user_id: int, peer_id: int, event_data: str | None = None) -> bool:
    try:
        await API.messages.send_message_event_answer(event_id=event_id, user_id=user_id,
                                                     peer_id=peer_id, event_data=event_data)
    except:
        return False
    return True


async def sendMessage(peer_ids: int | Iterable[int], msg: str | None = None, kbd: str | None = None,
                      photo: str | None = None) -> list[MessagesSendUserIdsResponseItem] | int | bool:
    try:
        return await API.messages.send(random_id=0, peer_ids=peer_ids, message=msg,
                                       keyboard=kbd, attachment=photo, disable_mentions=1)
    except:
        return False


async def editMessage(msg: str, peer_id: int, cmid: int, kb=None) -> bool:
    try:
        return await API.messages.edit(peer_id=peer_id, message=msg, disable_mentions=1,
                                       conversation_message_id=cmid, keyboard=kb)
    except:
        return False


async def getChatName(chat_id: int = None) -> str:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            name = await c.execute('select name from chatnames where chat_id=%s', (chat_id,))
            if name := await name.fetchone():
                return name[0]
            try:
                chatname = await API.messages.get_conversations_by_id(peer_ids=chat_id + 2000000000, group_id=GROUP_ID)
                chatname = chatname.items[0].chat_settings.title
            except:
                chatname = 'UNKNOWN'
            await c.execute('insert into chatnames (chat_id, name) values (%s, %s)', (chat_id, chatname))
            await conn.commit()
            return chatname


async def getGroupName(group_id: int) -> str:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            name = await c.execute('select name from groupnames where group_id=%s', (-abs(group_id),))
            if name := await name.fetchone():
                return name[0]
            name = await API.groups.get_by_id(group_ids=abs(group_id))
            name = name.groups[0].name
            await c.execute('insert into groupnames (group_id, name) values (%s, %s)', (-abs(group_id), name))
            await conn.commit()
            return name


async def isChatAdmin(id: int, chat_id: int) -> bool:
    try:
        status = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        for i in status.items:
            if i.member_id == id and (i.is_admin or i.is_owner):
                return True
    except:
        pass
    return False


async def getChatOwner(chat_id: int) -> int | bool:
    try:
        status = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        for i in status.items:
            if i.is_owner:
                return i.member_id
    except:
        pass
    return False


async def getChatMembers(chat_id: int) -> int | bool:
    try:
        status = await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        return len(status.items)
    except:
        return False


async def setChatMute(id: int | Iterable[int], chat_id: int, mute_time: int | float) -> Any:
    try:
        if mute_time > 0:
            return VK_API_SESSION.method('messages.changeConversationMemberRestrictions',
                                         {'peer_id': chat_id + 2000000000, 'member_ids': id, 'for': int(mute_time),
                                          'action': 'ro'})
        else:
            return VK_API_SESSION.method('messages.changeConversationMemberRestrictions',
                                         {'peer_id': chat_id + 2000000000, 'member_ids': id, 'action': 'rw'})
    except:
        traceback.print_exc()
        return


async def uploadImage(file: str, c: int = 0) -> str | None:
    bot = Bot(VK_TOKEN_GROUP)
    photo_uploader = PhotoMessageUploader(bot.api)
    try:
        photo = await photo_uploader.upload(file_source=file)
        if photo is None:
            raise ValueError
        if c == 6:
            raise Exception
        return photo
    except ValueError:
        return await uploadImage(file, c + 1)
    except Exception as e:
        raise Exception('Uploading failed after 6 retries') from e


async def getRegDate(id: int, format: str = '%d %B %Y', none: Any = 'Не удалось определить') -> str | Any:
    try:
        urlmanager = urllib3.PoolManager()
        response = urlmanager.request('GET', f'https://vk.com/foaf.php?id={id}')
        try:
            data = xmltodict.parse(response.data)
            data = data['rdf:RDF']['foaf:Person']['ya:created']['@dc:date'][:10].replace('-', '.').split('.')
        except:
            data = response.data.decode('latin-1')
            data = data[data.find('<ya:created dc:date="') + 21:]
            data = data[:data.find('"')]
            data = data[:data.find('T')].replace('-', '.').split('.')

        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        data = date(year=int(data[0]), month=int(data[1]), day=int(data[2]))
        return data.strftime(format)
    except:
        return none


async def getUserAccessLevel(uid: int, chat_id: int, none: Any = 0) -> int | Any:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if ac := await (await c.execute('select access_level from accesslvl where chat_id=%s and uid=%s',
                                            (chat_id, uid))).fetchone():
                return ac[0]
            return none


async def getUserLastMessage(uid: int, chat_id: int, none: Any = 'Неизвестно') -> int | Any:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if lm := await (await c.execute('select last_message from lastmessagedate where chat_id=%s and uid=%s',
                                            (chat_id, uid))).fetchone():
                return lm[0]
            return none


async def getUserNickname(uid: int, chat_id: int, none: Any = None) -> str | Any:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if nick := await (await c.execute('select nickname from nickname where chat_id=%s and uid=%s',
                                              (chat_id, uid))).fetchone():
                return nick[0]
            return none


async def getUserMute(uid, chat_id, none=0) -> int:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if mute := await (await c.execute('select mute from mute where chat_id=%s and uid=%s',
                                              (chat_id, uid))).fetchone():
                return mute[0]
            return none


async def getUserWarns(uid, chat_id, none=0) -> int:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if warn := await (await c.execute('select warns from warn where chat_id=%s and uid=%s',
                                              (chat_id, uid))).fetchone():
                return warn[0]
            return none


async def getUserMuteInfo(uid, chat_id, none=None) -> dict:
    if none is None:
        none = {'times': [], 'causes': [], 'names': [], 'dates': []}
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            mute = await (await c.execute(
                'select last_mutes_times, last_mutes_causes, last_mutes_names, last_mutes_dates from mute where '
                'chat_id=%s and uid=%s', (chat_id, uid))).fetchone()
        if mute:
            return {
                'times': literal_eval(mute[0]), 'causes': literal_eval(mute[1]), 'names': literal_eval(mute[2]),
                'dates': literal_eval(mute[3])
            }
        return none


async def getUserBan(uid, chat_id, none=0) -> int:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if ban := await (await c.execute('select ban from ban where chat_id=%s and uid=%s',
                                             (chat_id, uid))).fetchone():
                return ban[0]
            return none


async def getChatAccessName(chat_id: int, lvl: int, none: Any = None) -> int | None:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if an := await (await c.execute('select name from accessnames where chat_id=%s and lvl=%s',
                                            (chat_id, lvl))).fetchone():
                return an[0]
            return none


async def getUserBanInfo(uid, chat_id, none=None) -> dict:
    if none is None:
        none = {'times': [], 'causes': [], 'names': [], 'dates': []}
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            ban = await (await c.execute(
                'select last_bans_times, last_bans_causes, last_bans_names, last_bans_dates from ban where chat_id=%s '
                'and uid=%s', (chat_id, uid))).fetchone()
    if ban:
        return {
            'times': literal_eval(ban[0]), 'causes': literal_eval(ban[1]), 'names': literal_eval(ban[2]),
            'dates': literal_eval(ban[3])
        }
    return none


async def getUserXP(uid, none=0) -> int:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if xp := await (await c.execute('select xp from xp where uid=%s', (uid,))).fetchone():
                return xp[0]
            return none


async def getUserLVL(xp):
    if xp > 100:
        return (xp - 100) // 200 + 2
    else:
        return 1


async def getUserNeededXP(xp):
    if xp >= 100:
        xp -= 100
        return 200 - (xp - (xp // 200) * 200)
    else:
        return 100


async def getXPTop(returnval='count', limit=0, chat: list = None) -> dict:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if chat is not None:
                top = await (await c.execute('select uid, xp from xp where uid>0 and uid=ANY(%s) order by xp desc',
                                             (chat,))).fetchall()
            else:
                top = await (await c.execute('select uid, xp from xp where uid>0 order by xp desc')).fetchall()
    if limit > 0:
        top = top[:limit]
    if returnval == 'count':
        return {i[0]: k + 1 for k, i in enumerate(top)}
    elif returnval == 'xp':
        return {i[0]: i[1] for k, i in enumerate(top)}
    elif returnval == 'lvl':
        return {i[0]: await getUserLVL(i[1]) for k, i in enumerate(top)}
    else:
        raise Exception('returnval must be "count", "xp" or "lvl"')


async def getUserPremium(uid, none=0) -> int:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if pr := await (await c.execute('select time from premium where uid=%s', (uid,))).fetchone():
                return pr[0]
            return none


async def getUserPremmenuSetting(uid, setting, none):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if setting in PREMMENU_TURN:
                if pm := await (await c.execute('select pos from premmenu where uid=%s and setting=%s',
                                                (uid, setting))).fetchone():
                    return pm[0]
            else:
                if pm := await (await c.execute('select "value" from premmenu where uid=%s and setting=%s',
                                                (uid, setting))).fetchone():
                    return pm[0]
            return none


async def getUserPremmenuSettings(uid):
    settings = PREMMENU_DEFAULT.copy()
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            clear_by_fire = await (await c.execute(
                'select pos from premmenu where uid=%s and setting=%s', (uid, 'clear_by_fire'))).fetchone()
            if clear_by_fire is not None:
                settings['clear_by_fire'] = clear_by_fire[0]
            border_color = await (await c.execute(
                'select "value" from premmenu where uid=%s and setting=%s', (uid, 'border_color'))).fetchone()
            if border_color is not None:
                settings['border_color'] = border_color[0]
    return settings


async def getChatCommandLevel(chat_id, cmd, none):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if cacc := await (await c.execute('select lvl from commandlevels where chat_id=%s and cmd=%s',
                                              (chat_id, cmd))).fetchone():
                return cacc[0]
            return none


async def getUserMessages(uid, chat_id, none=0) -> int:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if ms := await (await c.execute('select messages from messages where chat_id=%s and uid=%s',
                                            (chat_id, uid))).fetchone():
                return ms[0]
            return none


async def addUserXP(uid, addxp, checklvlbanned=True):
    if checklvlbanned:
        if await getULvlBanned(uid):
            return
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if u := await (await c.execute('select id, xp from xp where uid=%s', (uid,))).fetchone():
                uxp = u[1]
                await c.execute('update xp set xp=xp+%s where id=%s', (addxp, u[0]))
            else:
                uxp = 0
                await c.execute('insert into xp (uid, xp) values (%s, %s)', (uid, addxp))
            await conn.commit()
    if await getUserLVL(uxp + addxp) > await getUserLVL(uxp):
        await addWeeklyTask(uid, 'lvlup')


async def getUserDuelWins(uid, none=0):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if dw := await (await c.execute('select wins from duelwins where uid=%s', (uid,))).fetchone():
                return dw[0]
            return none


async def getChatSettings(chat_id):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            dbchatsettings = {i[0]: i[1] for i in await (await c.execute(
                'select setting, pos from settings where chat_id=%s', (chat_id,))).fetchall()}
    chatsettings = SETTINGS()
    for cat, settings in chatsettings.items():
        for setting, pos in settings.items():
            if setting not in dbchatsettings:
                continue
            chatsettings[cat][setting] = dbchatsettings[setting]
    return chatsettings


async def getChatAltSettings(chat_id):
    chatsettings = SETTINGS_ALT()
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            for cat, settings in chatsettings.items():
                for setting, pos in settings.items():
                    chatsetting = await (await c.execute('select pos2 from settings where chat_id=%s and setting=%s',
                                                         (chat_id, setting))).fetchone()
                    if chatsetting is None:
                        continue
                    chatsettings[cat][setting] = chatsetting[0]
    return chatsettings


async def turnChatSetting(chat_id, category, setting, alt=False):
    defaults = SETTINGS_DEFAULTS[setting] if setting in SETTINGS_DEFAULTS else {'pos': SETTINGS()[category][setting]}

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update settings set ' +
                                    ('pos2=not pos2' if alt else 'pos=not pos') + ' where chat_id=%s and setting=%s',
                                    (chat_id, setting))).rowcount:
                await c.execute('insert into settings (chat_id, setting, pos) values (%s, %s, %s)',
                                (chat_id, setting, not defaults['pos']))
            await conn.commit()


async def setUserAccessLevel(uid, chat_id, access_level):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if access_level == 0:
                await c.execute('delete from accesslvl where chat_id=%s and uid=%s', (chat_id, uid))
            else:
                if not (await c.execute('update accesslvl set access_level = %s where chat_id=%s and uid=%s',
                                        (access_level, chat_id, uid))).rowcount:
                    await c.execute('insert into accesslvl (uid, chat_id, access_level) values (%s, %s, %s)',
                                    (uid, chat_id, access_level))
            await conn.commit()


async def addDailyTask(uid, task, count=1, checklvlbanned=True):
    if checklvlbanned:
        if await getULvlBanned(uid):
            return
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            t = await (await c.execute('select count from tasksdaily where uid=%s and task=%s', (uid, task))).fetchone()
            if t:
                await c.execute('update tasksdaily set count=count+%s where uid=%s and task=%s', (count, uid, task))
            else:
                await c.execute('insert into tasksdaily (uid, task, count) values (%s, %s, %s)', (uid, task, count))
            t = t[0] if t else 0
            if t + count == (TASKS_DAILY | PREMIUM_TASKS_DAILY)[task] or t + count == PREMIUM_TASKS_DAILY_TIERS:
                if (task in PREMIUM_TASKS_DAILY or task in PREMIUM_TASKS_DAILY_TIERS) and await getUserPremium(uid):
                    if not (await c.execute('update coins set coins=coins+10 where uid=%s', (uid,))).rowcount:
                        await c.execute('insert into coins (uid, coins) values (%s, 10)', (uid,))
                elif task in TASKS_DAILY:
                    if not (await c.execute('update coins set coins=coins+5 where uid=%s', (uid,))).rowcount:
                        await c.execute('insert into coins (uid, coins) values (%s, 5)', (uid,))
            await conn.commit()


async def addWeeklyTask(uid, task, count=1, checklvlbanned=True):
    if checklvlbanned:
        if await getULvlBanned(uid):
            return

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if not (await c.execute('update tasksweekly set count=count+%s where uid=%s and task=%s',
                                    (count, uid, task))).rowcount:
                await c.execute('insert into tasksweekly (uid, task, count) values (%s, %s, %s)', (uid, task, count))
            if ((await (await c.execute(
                    'select count from tasksweekly where uid=%s and task=%s', (uid, task))).fetchone()
            )[0] == (TASKS_WEEKLY | PREMIUM_TASKS_WEEKLY)[task] and
                    (task in TASKS_WEEKLY or (task in PREMIUM_TASKS_WEEKLY and await getUserPremium(uid)))):
                if not (await c.execute('update coins set coins=coins+10 where uid=%s', (uid,))).rowcount:
                    await c.execute('insert into coins (uid, coins) values (%s, 10)', (uid,))
            await conn.commit()


async def isChatMember(uid, chat_id):
    try:
        return uid in [i.member_id for i in
                       (await API.messages.get_conversation_members(peer_id=chat_id + 2000000000)).items]
    except:
        return False


async def NSFWDetector(pic_path):
    detector = NudeDetector()
    with open(pic_path, 'rb') as f:
        image_data = f.read()

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(image_data)
        temp_file_path = temp_file.name
    result = detector.detect(temp_file_path)
    os.unlink(temp_file_path)
    for i in result:
        if i['class'] in NSFW_CATEGORIES:
            if i['score'] > 0.3:
                return True
    return False


async def antispamChecker(chat_id, uid, message: MessagesMessage, settings):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if settings['antispam']['messagesPerMinute']:
                setting = await (await c.execute('select "value" from settings where chat_id=%s and '
                                                 'setting=\'messagesPerMinute\'', (chat_id,))).fetchone()
                if setting is not None and setting[0] is not None:
                    if (await (await c.execute('select count(*) as c from antispammessages where chat_id=%s and '
                                               'from_id=%s', (chat_id, uid))).fetchone())[0] >= setting[0]:
                        return 'messagesPerMinute'
            if settings['antispam']['maximumCharsInMessage']:
                setting = await (await c.execute('select "value" from settings where chat_id=%s and '
                                                 'setting=\'maximumCharsInMessage\'', (chat_id,))).fetchone()
                if setting is not None and setting[0] is not None:
                    if len(message.text) >= setting[0]:
                        return 'maximumCharsInMessage'
            if settings['antispam']['disallowLinks']:
                data = message.text.split()
                for i in data:
                    for y in i.split('/'):
                        if not validators.url(y) and not validators.domain(y) or y in ['vk.com', 'vk.ru']:
                            continue
                        if not await (await c.execute(
                                'select id from antispamurlexceptions where chat_id=%s and '
                                'url=%s', (chat_id, y.replace('https://', '').replace('/', '')))).fetchone():
                            return 'disallowLinks'
            if settings['antispam']['disallowNSFW']:
                for i in message.attachments:
                    if i.type != MessagesMessageAttachmentType.PHOTO:
                        continue
                    photo = i.photo.sizes[2]
                    for y in i.photo.sizes:
                        if y.width > photo.width:
                            photo = y
                    r = requests.get(photo.url)
                    filename = PATH + f'media/temp/{time.time()}.jpg'
                    with open(filename, "wb") as f:
                        f.write(r.content)
                        f.close()
                    r.close()
                    isNSFW = await NSFWDetector(filename)
                    if isNSFW:
                        return 'disallowNSFW'
    return False


async def speccommandscheck(uid: int, cmd: str, cd: int) -> int | bool:
    if uid in MAIN_DEVS:
        return False
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if s := await (await c.execute('select time from speccommandscooldown where uid=%s and time>%s and cmd=%s',
                                           (uid, int(time.time() - cd), cmd))).fetchone():
                return s[0]
            await c.execute('insert into speccommandscooldown (time, uid, cmd) values (%s, %s, %s)',
                            (int(time.time()), uid, cmd))
            await conn.commit()
    return False


@cached
def pointDays(seconds):
    res = int(seconds // 86400)
    if res == 1:
        res = str(res) + ' день'
    elif 1 < res < 5:
        res = str(res) + ' дня'
    else:
        res = str(res) + ' дней'
    return res


@cached
def pointHours(seconds):
    res = int(seconds // 3600)
    if res in [23, 22, 4, 3, 2]:
        res = f'{res} часа'
    elif res in [21, 1]:
        res = f'{res} час'
    else:
        res = f'{res} часов'
    return res


@cached
def pointMinutes(seconds):
    res = int(seconds // 60)
    if res % 10 == 1 and res % 100 != 11:
        res = str(res) + ' минута'
    elif 2 <= res % 10 <= 4 and (res % 100 < 10 or res % 100 >= 20):
        res = str(res) + ' минуты'
    else:
        res = str(res) + ' минут'
    return res


@cached
def pointWords(value, words):
    """
    :param value
    :param words: e.g. (минута, минуты, минут)
    :return:
    """
    if value % 10 == 1 and value % 100 != 11:
        res = str(value) + f' {words[0]}'
    elif 2 <= value % 10 <= 4 and (value % 100 < 10 or value % 100 >= 20):
        res = str(value) + f' {words[1]}'
    else:
        res = str(value) + f' {words[2]}'
    return res


def chunks(li, n):
    for i in range(0, len(li), n):
        yield li[i:i + n]


async def getULvlBanned(uid) -> bool:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if await (await c.execute('select id from lvlbanned where uid=%s', (uid,))).fetchone():
                return True
            return False


async def generateCaptcha(uid, chat_id, exp):
    gen = CaptchaGenerator()
    image = gen.gen_math_captcha_image(difficult_level=2, multicolor=True)
    name = f'{PATH}media/temp/captcha{uid}_{chat_id}.png'
    image.image.save(name, 'png')
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            c = (await (await c.execute(
                'insert into captcha (chat_id, uid, exptime, result) values (%s, %s, %s, %s) returning id',
                (chat_id, uid, int(time.time() + exp * 60), str(image.equation_result)))).fetchone())[0]
    return name, c


async def punish(uid, chat_id, setting_id):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            setting = await (await c.execute('select punishment from settings where id=%s', (setting_id,))).fetchone()
            if setting[0] is None:
                return False
            punishment = setting[0].split('|')
            if punishment[0] == 'deletemessage':
                return False
            if punishment[0] == 'kick':
                await kickUser(uid, chat_id)
                return punishment
            elif punishment[0] == 'mute':
                ms = await (await c.execute(
                    'select last_mutes_times, last_mutes_causes, last_mutes_names, last_mutes_dates from mute where '
                    'chat_id=%s and uid=%s', (chat_id, uid))).fetchone()
                if ms is not None:
                    mute_times = literal_eval(ms[0])
                    mute_causes = literal_eval(ms[1])
                    mute_names = literal_eval(ms[2])
                    mute_dates = literal_eval(ms[3])
                else:
                    mute_times, mute_causes, mute_names, mute_dates = [], [], [], []

                mute_date = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
                mute_time = int(punishment[1]) * 60
                mute_times.append(mute_time)
                mute_causes.append('Нарушение правил беседы')
                mute_names.append(f'[club222139436|Star Manager]')
                mute_dates.append(mute_date)

                if not (await c.execute(
                        'update mute set mute = %s, last_mutes_times = %s, last_mutes_causes = %s, '
                        'last_mutes_names = %s, last_mutes_dates = %s where chat_id=%s and uid=%s',
                        (int(time.time() + mute_time), f"{mute_times}", f"{mute_causes}", f"{mute_names}",
                         f"{mute_dates}", chat_id, uid))).rowcount:
                    await c.execute(
                        'insert into mute (uid, chat_id, mute, last_mutes_times, last_mutes_causes, last_mutes_names, '
                        'last_mutes_dates) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (uid, chat_id, int(time.time() + mute_time), f"{mute_times}", f"{mute_causes}", f"{mute_names}",
                         f"{mute_dates}"))
                await conn.commit()

                await setChatMute(uid, chat_id, mute_time)
                return punishment
            elif punishment[0] == 'ban':
                ban_date = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
                res = await (await c.execute(
                    'select last_bans_times, last_bans_causes, last_bans_names, last_bans_dates from ban where '
                    'chat_id=%s and uid=%s', (chat_id, uid))).fetchone()
                if res is not None:
                    ban_times = literal_eval(res[0])
                    ban_causes = literal_eval(res[1])
                    ban_names = literal_eval(res[2])
                    ban_dates = literal_eval(res[3])
                else:
                    ban_times, ban_causes, ban_names, ban_dates = [], [], [], []

                ban_cause = 'Нарушение правил беседы'
                ban_time = int(punishment[1]) * 86400
                ban_times.append(ban_time)
                ban_causes.append(ban_cause)
                ban_names.append(f'[club222139436|Star Manager]')
                ban_dates.append(ban_date)

                if not (await c.execute(
                        'update ban set ban = %s, last_bans_times = %s, last_bans_causes = %s, last_bans_names = %s, '
                        'last_bans_dates = %s where chat_id=%s and uid=%s',
                        (int(time.time() + ban_time), f"{ban_times}", f"{ban_causes}", f"{ban_names}", f"{ban_dates}",
                            chat_id, uid))).rowcount:
                    await c.execute(
                        'insert into ban (uid, chat_id, ban, last_bans_times, last_bans_causes, last_bans_names, '
                        'last_bans_dates) values (%s, %s, %s, %s, %s, %s, %s)',
                        (uid, chat_id, int(time.time() + ban_time), f"{ban_times}", f"{ban_causes}", f"{ban_names}",
                         f"{ban_dates}"))
                await conn.commit()

                await kickUser(uid, chat_id)
                return punishment
    return False


async def getgpool(chat_id):
    try:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                chats = [i[0] for i in await (await c.execute(
                    'select chat_id from gpool where uid=(select uid from gpool where chat_id=%s)',
                    (chat_id,))).fetchall()]
        if len(chats) == 0:
            raise Exception
        return chats
    except:
        return False


async def getpool(chat_id, group):
    try:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                chats = [i[0] for i in await (await c.execute(
                    'select chat_id from chatgroups where "group"=%s and uid='
                    '(select uid from accesslvl where accesslvl.chat_id=%s and access_level>6 '
                    'order by access_level limit 1)', (group, chat_id,))).fetchall()]
        if len(chats) == 0:
            raise Exception
        return chats
    except:
        return False


def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
