import asyncio
import locale
import os
import tempfile
import time
from ast import literal_eval
from datetime import date, datetime
from typing import Iterable, Any
from urllib.parse import urlparse

import dns.resolver
import pysafebrowsing
import requests
import urllib3
import xmltodict
from cache.async_lru import AsyncLRU
from cache.async_ttl import AsyncTTL
from memoization import cached
from multicolorcaptcha import CaptchaGenerator
from nudenet import NudeDetector
from vkbottle import PhotoMessageUploader
from vkbottle.tools.mini_types.bot.foreign_message import ForeignMessageMin
from vkbottle_types.objects import MessagesMessage, MessagesMessageAttachmentType, MessagesSendUserIdsResponseItem

from config.config import (api, vk_api_session, GROUP_ID, SETTINGS, PATH,
                           NSFW_CATEGORIES, SETTINGS_ALT, SETTINGS_DEFAULTS, PREMMENU_DEFAULT, PREMMENU_TURN,
                           LEAGUE_LVL, IMPORTSETTINGS_DEFAULT, GOOGLE_TOKEN, PREFIX)
from db import pool

_hiddenalbumuid = None


@AsyncTTL(time_to_live=300, maxsize=0)
async def getUserName(uid: int) -> str:
    if uid < 0:
        return await getGroupName(uid)
    async with (await pool()).acquire() as conn:
        if name := await conn.fetchval('select name from usernames where uid=$1', uid):
            return name
        name = await api.users.get(user_ids=uid)
        if not name:
            return 'UNKNOWN'
        await conn.execute('insert into usernames (uid, name) values ($1, $2)',
                           uid, f"{name[0].first_name} {name[0].last_name}")
        return f"{name[0].first_name} {name[0].last_name}"


async def kickUser(uid: int, chat_id: int) -> bool:
    try:
        await api.messages.remove_chat_user(chat_id=chat_id, member_id=uid)
        if (await getChatSettings(chat_id))['main']['deleteAccessAndNicknameOnLeave']:
            async with (await pool()).acquire() as conn:
                await conn.execute('delete from accesslvl where chat_id=$1 and uid=$2', chat_id, uid)
                await conn.execute('delete from nickname where chat_id=$1 and uid=$2', chat_id, uid)
            await setChatMute(uid, chat_id, 0)
    except:
        return False
    return True


async def deleteMessages(cmids: int | Iterable[int], chat_id: int) -> bool:
    try:
        await api.messages.delete(group_id=GROUP_ID, delete_for_all=True, peer_id=chat_id + 2000000000, cmids=cmids)
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
        if len(data) < place and not reply:
            return 0
        if reply is not None:
            return reply.from_id
        try:
            if data[place - 1].count('[id') != 0:
                id = data[place - 1][data[place - 1].find('[id') + 3:data[place - 1].find('|')]
            elif data[place - 1].count('[club') != 0:
                id = '-' + data[place - 1][data[place - 1].find('[club') + 5:data[place - 1].find('|')]
            elif data[place - 1].count('vk.') != 0:
                id = data[place - 1][data[place - 1].find('vk.'):]
                id = id[id.find('/') + 1:]
                try:
                    id = await api.users.get(user_ids=id)
                    id = id[0].id
                except:
                    id = int(id)
            elif data[place - 1].isdigit():
                id = data[place - 1]
            elif data[place - 1].count('@id') != 0:
                id = data[place - 1][data[place - 1].find('@id') + 3:]
            else:
                return 0
        except IndexError:
            return 0

        return int(id)
    except:
        return 0


async def sendMessageEventAnswer(event_id: Any, user_id: int, peer_id: int, event_data: str | None = None) -> bool:
    try:
        await api.messages.send_message_event_answer(event_id=event_id, user_id=user_id,
                                                     peer_id=peer_id, event_data=event_data)
    except:
        return False
    return True


async def sendMessage(peer_ids: int | Iterable[int], msg: str | None = None, kbd: str | None = None,
                      photo: str | None = None) -> list[MessagesSendUserIdsResponseItem] | int | bool:
    try:
        return await api.messages.send(random_id=0, peer_ids=peer_ids, message=msg,
                                       keyboard=kbd, attachment=photo, disable_mentions=1)
    except:
        return False


async def editMessage(msg: str, peer_id: int, cmid: int, kb=None, attachment=None) -> bool:
    try:
        return await api.messages.edit(peer_id=peer_id, message=msg, disable_mentions=1,
                                       conversation_message_id=cmid, keyboard=kb, attachment=attachment)
    except:
        return False


@AsyncTTL(time_to_live=300, maxsize=0)
async def getChatName(chat_id: int = None) -> str:
    async with (await pool()).acquire() as conn:
        if name := await conn.fetchval('select name from chatnames where chat_id=$1', chat_id):
            return name
        try:
            chatname = await api.messages.get_conversations_by_id(peer_ids=chat_id + 2000000000, group_id=GROUP_ID)
            chatname = chatname.items[0].chat_settings.title
        except:
            chatname = 'UNKNOWN'
        await conn.execute('insert into chatnames (chat_id, name) values ($1, $2)', chat_id, chatname)
    return chatname


@AsyncTTL(time_to_live=300, maxsize=0)
async def getGroupName(group_id: int) -> str:
    async with (await pool()).acquire() as conn:
        if name := await conn.fetchval('select name from groupnames where group_id=$1', -abs(group_id)):
            return name
        name = await api.groups.get_by_id(group_ids=abs(group_id))
        name = name.groups[0].name
        await conn.execute('insert into groupnames (group_id, name) values ($1, $2)', -abs(group_id), name)
        return name


@AsyncTTL(maxsize=0)
async def isChatAdmin(id: int, chat_id: int) -> bool:
    try:
        status = await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        for i in status.items:
            if i.member_id == id and (i.is_admin or i.is_owner):
                return True
    except:
        pass
    return False


@AsyncTTL(maxsize=0)
async def getChatOwner(chat_id: int) -> int | bool:
    try:
        status = await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        for i in status.items:
            if i.is_owner:
                return i.member_id
    except:
        pass
    return False


@AsyncTTL(maxsize=0)
async def getChatMembers(chat_id: int) -> int | bool:
    try:
        status = await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)
        return len(status.items)
    except:
        return False


async def setChatMute(uid: int | Iterable[int], chat_id: int, mute_time: int | float | None = None) -> Any:
    try:
        if mute_time is None or mute_time > 0:
            payload = {'peer_id': chat_id + 2000000000, 'member_ids': uid, 'action': 'ro'}
            if mute_time is not None:
                payload['for'] = int(mute_time)
            return vk_api_session.method('messages.changeConversationMemberRestrictions', payload)
        else:
            return vk_api_session.method('messages.changeConversationMemberRestrictions',
                                         {'peer_id': chat_id + 2000000000, 'member_ids': uid, 'action': 'rw'})
    except:
        return


async def uploadImage(file: str, uid: int | None = None, count: int = 0, delay: float = 1) -> str | None:
    if not uid:
        uid = await getHiddenAlbumUser()
    try:
        photo = await PhotoMessageUploader(api).upload(file_source=file, peer_id=uid)
        if not photo:
            raise Exception
        return photo
    except Exception as e:
        if 'internal' in str(e).lower() or 'access' in str(e).lower():
            async with (await pool()).acquire() as conn:
                await conn.execute('insert into hiddenalbumserverinternalerror (uid) values ($1)', uid)
            global _hiddenalbumuid
            _hiddenalbumuid = None
            uid = await getHiddenAlbumUser()
        if 'too many' in str(e).lower():
            await asyncio.sleep(1)
        if count != 2:
            await asyncio.sleep(delay)
            return await uploadImage(file, uid, count + 1, delay + 1)
        raise e


@AsyncLRU(maxsize=0)
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


@AsyncTTL(time_to_live=2, maxsize=0)
async def getUserAccessLevel(uid: int, chat_id: int, none: Any = 0) -> int | Any:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval(
            'select access_level from accesslvl where chat_id=$1 and uid=$2', chat_id, uid) or none


async def getUserLastMessage(uid: int, chat_id: int, none: Any = 'Неизвестно') -> int | Any:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval(
            'select last_message from lastmessagedate where chat_id=$1 and uid=$2', chat_id, uid) or none


async def getUserNickname(uid: int, chat_id: int, none: Any = None) -> str | Any:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval(
            'select nickname from nickname where chat_id=$1 and uid=$2', chat_id, uid) or none


async def getUserMute(uid, chat_id, none=0) -> int:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval(
            'select mute from mute where chat_id=$1 and uid=$2', chat_id, uid) or none


async def getUserWarns(uid, chat_id, none=0) -> int:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval('select warns from warn where chat_id=$1 and uid=$2', chat_id, uid) or none


async def getUserMuteInfo(uid, chat_id, none=None) -> dict:
    if none is None:
        none = {'times': [], 'causes': [], 'names': [], 'dates': []}
    async with (await pool()).acquire() as conn:
        mute = await conn.fetchrow('select last_mutes_times, last_mutes_causes, last_mutes_names, last_mutes_dates '
                                   'from mute where chat_id=$1 and uid=$2', chat_id, uid)
    if mute:
        return {'times': literal_eval(mute[0]), 'causes': literal_eval(mute[1]), 'names': literal_eval(mute[2]),
                'dates': literal_eval(mute[3])}
    return none


async def getUserBan(uid, chat_id, none=0) -> int:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval('select ban from ban where chat_id=$1 and uid=$2', chat_id, uid) or none


async def getChatAccessName(chat_id: int, lvl: int, none: Any = None) -> int | None:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval('select name from accessnames where chat_id=$1 and lvl=$2', chat_id, lvl) or none


async def getUserBanInfo(uid, chat_id, none=None) -> dict:
    if none is None:
        none = {'times': [], 'causes': [], 'names': [], 'dates': []}
    async with (await pool()).acquire() as conn:
        ban = await conn.fetchrow('select last_bans_times, last_bans_causes, last_bans_names, last_bans_dates '
                                  'from ban where chat_id=$1 and uid=$2', chat_id, uid)
    if ban:
        return {'times': literal_eval(ban[0]), 'causes': literal_eval(ban[1]), 'names': literal_eval(ban[2]),
                'dates': literal_eval(ban[3])}
    return none


async def getUserXP(uid, none=0) -> int:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval('select xp from xp where uid=$1', uid) or none


async def getUserLeague(uid, none=1) -> int:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval('select league from xp where uid=$1', uid) or none


async def getUserLVL(uid, none=0) -> int:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval('select lvl from xp where uid=$1', uid) or none


@AsyncLRU(maxsize=0)
async def getUserNeededXP(xp):
    return 1000 - xp


@AsyncTTL(time_to_live=120, maxsize=0)
async def getXPTop(returnval='count', limit: int = 10, league: int = 1, users: list = None) -> dict:
    async with (await pool()).acquire() as conn:
        if users is not None:
            top = await conn.fetch(
                'select uid, lvl, xp from xp where uid>0 and league=$1 and uid=ANY($2) order by lvl desc, xp desc '
                'limit $3', league, users, limit)
        else:
            top = await conn.fetch('select uid, lvl, xp from xp where uid>0 and league=$1 order by lvl desc, '
                                   'xp desc limit $2', league, limit)
    if returnval == 'count':
        return {i[0]: k + 1 for k, i in enumerate(top)}
    elif returnval == 'lvl':
        return {i[0]: i[1] for k, i in enumerate(top)}
    else:
        raise Exception('returnval must be "count" or "lvl"')


@AsyncTTL(time_to_live=16, maxsize=0)
async def getUserPremium(uid, none=0) -> int:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval('select time from premium where uid=$1', uid) or none


async def getUserPremmenuSetting(uid, setting, none):
    prem = await getUserPremium(uid)
    if not prem:
        return none
    async with (await pool()).acquire() as conn:
        return await conn.fetchval(
            ('select pos from premmenu where uid=$1 and setting=$2' if setting in PREMMENU_TURN else
             'select "value" from premmenu where uid=$1 and setting=$2'), uid, setting) or none


async def getUserPremmenuSettings(uid):
    settings = PREMMENU_DEFAULT.copy()
    async with (await pool()).acquire() as conn:
        clear_by_fire = await conn.fetchval(
            'select pos from premmenu where uid=$1 and setting=$2', uid, 'clear_by_fire')
        if clear_by_fire is not None:
            settings['clear_by_fire'] = clear_by_fire
        border_color = await conn.fetchval(
            'select "value" from premmenu where uid=$1 and setting=$2', uid, 'border_color')
        if border_color is not None:
            settings['border_color'] = border_color
        tagnotif = await conn.fetchval('select pos from premmenu where uid=$1 and setting=$2', uid, 'tagnotif')
        if tagnotif is not None:
            settings['tagnotif'] = tagnotif
    return settings


async def getChatCommandLevel(chat_id, cmd, none):
    async with (await pool()).acquire() as conn:
        return await conn.fetchval(
            'select lvl from commandlevels where chat_id=$1 and cmd=$2', chat_id, cmd) or none


async def getUserMessages(uid, chat_id, none=0) -> int:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval(
            'select messages from messages where chat_id=$1 and uid=$2', chat_id, uid) or none


async def addUserXP(uid, addxp, checklvlbanned=True):
    async with (await pool()).acquire() as conn:
        if checklvlbanned:
            if (await conn.fetchval('select exists(select 1 from lvlbanned where uid=$1)', uid) or
                    await conn.fetchval("select exists(select 1 from blocked where uid=$1 and type='user')", uid)):
                return
        if u := await conn.fetchrow('select id, xp, lvl, league from xp where uid=$1', uid):
            uxp, ulvl, ulg = u[1] + addxp, u[2], u[3]
            ulvl += uxp // 1000
            uxp %= 1000
            if ulg != len(LEAGUE_LVL) and ulvl >= LEAGUE_LVL[ulg]:
                await conn.execute('update xp set xp = 0, league = $1, lvl = 1 where id=$2', ulg + 1, u[0])
                return
            await conn.execute('update xp set xp = $1, lvl = $2 where id=$3', uxp, ulvl, u[0])
        else:
            await conn.execute('insert into xp (uid, xp, lm, lvm, lsm, league, lvl) values ($1, $2, $3, $3, $3, 1, '
                               '1)', uid, addxp, time.time())


@AsyncTTL(time_to_live=120, maxsize=0)
async def getUserDuelWins(uid, none=0):
    async with (await pool()).acquire() as conn:
        return await conn.fetchval('select wins from duelwins where uid=$1', uid) or none


@AsyncTTL(time_to_live=5, maxsize=0)
async def getChatSettings(chat_id):
    async with (await pool()).acquire() as conn:
        dbchatsettings = {i[0]: i[1] for i in await conn.fetch(
            'select setting, pos from settings where chat_id=$1', chat_id)}
    chatsettings = SETTINGS()
    for cat, settings in chatsettings.items():
        for setting, pos in settings.items():
            if setting not in dbchatsettings:
                continue
            chatsettings[cat][setting] = dbchatsettings[setting]
    return chatsettings


@AsyncTTL(time_to_live=5, maxsize=0)
async def getChatAltSettings(chat_id):
    chatsettings = SETTINGS_ALT()
    async with (await pool()).acquire() as conn:
        for cat, settings in chatsettings.items():
            for setting, pos in settings.items():
                chatsetting = await conn.fetchval(
                    'select pos2 from settings where chat_id=$1 and setting=$2', chat_id, setting)
                if chatsetting is None:
                    continue
                chatsettings[cat][setting] = chatsetting
    return chatsettings


async def turnChatSetting(chat_id, category, setting, alt=False):
    defaults = SETTINGS_DEFAULTS[setting] if setting in SETTINGS_DEFAULTS else {'pos': SETTINGS()[category][setting]}
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval('update settings set ' + ('pos2=not pos2' if alt else 'pos=not pos') +
                                   ' where chat_id=$1 and setting=$2 returning 1', chat_id, setting):
            await conn.execute('insert into settings (chat_id, setting, ' + ('pos2' if alt else 'pos') +
                               ') values ($1, $2, $3)', chat_id, setting, not defaults['pos'])


async def setUserAccessLevel(uid, chat_id, access_level):
    async with (await pool()).acquire() as conn:
        if not access_level:
            await conn.execute('delete from accesslvl where chat_id=$1 and uid=$2', chat_id, uid)
        else:
            if not await conn.fetchval('update accesslvl set access_level = $1 where chat_id=$2 and uid=$3 '
                                       'returning 1', access_level, chat_id, uid):
                await conn.execute('insert into accesslvl (uid, chat_id, access_level) values ($1, $2, $3)',
                                   uid, chat_id, access_level)
    if await getSilence(chat_id):
        if access_level in await getSilenceAllowed(chat_id):
            await setChatMute(uid, chat_id, 0)
        else:
            await setChatMute(uid, chat_id)


async def getSilence(chat_id) -> bool:
    async with (await pool()).acquire() as conn:
        return await conn.fetchval(
            'select exists(select 1 from silencemode where chat_id=$1 and activated=True)', chat_id,)


@AsyncTTL(time_to_live=120, maxsize=0)
async def isChatMember(uid, chat_id):
    try:
        return uid in [i.member_id for i in
                       (await api.messages.get_conversation_members(peer_id=chat_id + 2000000000)).items]
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


def whoiscached(text):
    # return whois.whois(text)  # doesn't work
    try:
        if '.' not in text:
            return False
        dns.resolver.resolve(text, 'A')
        return True
    except:
        return False


def whoiscachedurl(text):
    # return whois.whois(text)  # doesn't work
    for i in text.split('/'):
        try:
            dns.resolver.resolve(i, 'A')
            return True
        except:
            continue


async def getUserPrefixes(u_prem, uid) -> list:
    if u_prem:
        async with (await pool()).acquire() as conn:
            prefixes = await conn.fetch('select prefix from prefix where uid=$1', uid)
        return PREFIX + [i[0] for i in prefixes]
    return PREFIX


async def antispamChecker(chat_id, uid, message: MessagesMessage, settings):
    if settings['antispam']['messagesPerMinute']:
        async with (await pool()).acquire() as conn:
            setting = await conn.fetchrow("select \"value\" from settings where chat_id=$1 and "
                                          "setting='messagesPerMinute'", chat_id)
            if setting is not None and setting[0] is not None:
                if await conn.fetchval('select count(*) as c from antispammessages where chat_id=$1 and '
                                       'from_id=$2', chat_id, uid) >= setting[0]:
                    return 'messagesPerMinute'
    if settings['antispam']['maximumCharsInMessage']:
        async with (await pool()).acquire() as conn:
            setting = await conn.fetchrow(
                'select "value" from settings where chat_id=$1 and setting=\'maximumCharsInMessage\'', chat_id)
        if setting and setting[0] is not None:
            if len(message.text) >= setting[0]:
                return 'maximumCharsInMessage'
    if settings['antispam']['disallowLinks'] and not any(
            message.text.startswith(i) for i in await getUserPrefixes(await getUserPremium(uid), uid)):
        data = message.text.split()
        async with (await pool()).acquire() as conn:
            for i in data:
                for y in i.split('/'):
                    if not whoiscached(y) or y in ['vk.com', 'vk.ru']:
                        continue
                    if not await conn.fetchval('select exists(select 1 from antispamurlexceptions where chat_id=$1'
                                               ' and url=$2)', chat_id, y.replace('https://', '').replace('/', '')):
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
    # if uid in DEVS:
    #     return False
    async with (await pool()).acquire() as conn:
        if s := await conn.fetchval('select time from speccommandscooldown where uid=$1 and time>$2 and cmd=$3',
                                    uid, time.time() - cd, cmd):
            return s
        await conn.execute(
            'insert into speccommandscooldown (time, uid, cmd) values ($1, $2, $3)', time.time(), uid, cmd)
    return False


@cached
def pointDays(seconds):
    res = int(int(seconds) // 86400)
    if res == 1:
        res = str(res) + ' день'
    elif 1 < res < 5:
        res = str(res) + ' дня'
    else:
        res = str(res) + ' дней'
    return res


@cached
def pointHours(seconds):
    res = int(int(seconds) // 3600)
    if res in [23, 22, 4, 3, 2]:
        res = f'{res} часа'
    elif res in [21, 1]:
        res = f'{res} час'
    else:
        res = f'{res} часов'
    return res


@cached
def pointMinutes(seconds):
    res = int(int(seconds) // 60)
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


async def getURepBanned(uid) -> bool:
    async with (await pool()).acquire() as conn:
        if (t := await conn.fetchval('select time from reportban where uid=$1', uid)) and (
                not t or time.time() < t):
            return True
        return False


async def generateCaptcha(uid, chat_id, exp):
    gen = CaptchaGenerator()
    image = gen.gen_math_captcha_image(difficult_level=2, multicolor=True)
    name = f'{PATH}media/temp/captcha{uid}_{chat_id}.png'
    image.image.save(name, 'png')
    async with (await pool()).acquire() as conn:
        c = await conn.fetchval(
            'insert into captcha (chat_id, uid, exptime, result) values ($1, $2, $3, $4) returning id',
            chat_id, uid, time.time() + exp * 60, str(image.equation_result))
    return name, c


async def punish(uid, chat_id, setting_id):
    async with (await pool()).acquire() as conn:
        setting = await conn.fetchval('select punishment from settings where id=$1', setting_id)
    if setting is None:
        return False
    punishment = setting.split('|')
    if punishment[0] == 'deletemessage':
        return 'del'
    if punishment[0] == 'kick':
        await kickUser(uid, chat_id)
        return punishment
    elif punishment[0] == 'mute':
        async with (await pool()).acquire() as conn:
            ms = await conn.fetchrow(
                'select last_mutes_times, last_mutes_causes, last_mutes_names, last_mutes_dates from mute where '
                'chat_id=$1 and uid=$2', chat_id, uid)
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

        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                    'update mute set mute = $1, last_mutes_times = $2, last_mutes_causes = $3, '
                    'last_mutes_names = $4, last_mutes_dates = $5 where chat_id=$6 and uid=$7 returning 1',
                    time.time() + mute_time, f"{mute_times}", f"{mute_causes}", f"{mute_names}", f"{mute_dates}",
                    chat_id, uid):
                await conn.execute(
                    'insert into mute (uid, chat_id, mute, last_mutes_times, last_mutes_causes, last_mutes_names, '
                    'last_mutes_dates) VALUES ($1, $2, $3, $4, $5, $6, $7)', uid, chat_id, time.time() + mute_time,
                    f"{mute_times}", f"{mute_causes}", f"{mute_names}", f"{mute_dates}")

        await setChatMute(uid, chat_id, mute_time)
        return punishment
    elif punishment[0] == 'ban':
        ban_date = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
        async with (await pool()).acquire() as conn:
            res = await conn.fetchrow(
                'select last_bans_times, last_bans_causes, last_bans_names, last_bans_dates from ban where '
                'chat_id=$1 and uid=$2', chat_id, uid)
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

        async with (await pool()).acquire() as conn:
            if not await conn.fetchval(
                    'update ban set ban = $1, last_bans_times = $2, last_bans_causes = $3, last_bans_names = $4, '
                    'last_bans_dates = $5 where chat_id=$6 and uid=$7 returning 1',
                    time.time() + ban_time, f"{ban_times}", f"{ban_causes}", f"{ban_names}", f"{ban_dates}",
                    chat_id, uid):
                await conn.execute(
                    'insert into ban (uid, chat_id, ban, last_bans_times, last_bans_causes, last_bans_names, '
                    'last_bans_dates) values ($1, $2, $3, $4, $5, $6, $7)', uid, chat_id, time.time() + ban_time,
                    f"{ban_times}", f"{ban_causes}", f"{ban_names}", f"{ban_dates}")

        await kickUser(uid, chat_id)
        return punishment
    return False


async def getgpool(chat_id):
    try:
        async with (await pool()).acquire() as conn:
            chats = [i[0] for i in await conn.fetch(
                'select chat_id from gpool where uid=(select uid from gpool where chat_id=$1)', chat_id)]
        if len(chats) == 0:
            raise Exception
        return chats
    except:
        return False


async def getpool(chat_id, group):
    try:
        async with (await pool()).acquire() as conn:
            chats = [i[0] for i in await conn.fetch(
                'select chat_id from chatgroups where "group"=$1 and uid='
                '(select uid from accesslvl where accesslvl.chat_id=$2 and access_level>6 '
                'order by access_level limit 1)', group, chat_id)]
        if len(chats) == 0:
            raise Exception
        return chats
    except:
        return False


async def getSilenceAllowed(chat_id):
    async with (await pool()).acquire() as conn:
        lvls = await conn.fetchval('select allowed from silencemode where chat_id=$1', chat_id)
    if lvls is not None:
        return literal_eval(lvls)
    return []


async def getUserRep(uid):
    async with (await pool()).acquire() as conn:
        return await conn.fetchval('select rep from reputation where uid=$1', uid) or 0


async def getRepTop(uid):
    async with (await pool()).acquire() as conn:
        top = [i[0] for i in await conn.fetch('select uid from reputation order by rep desc')]
        allu = await conn.fetchval('select count(*) as c from allusers')
    return top.index(uid) if uid in top else allu


@cached
def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


async def chatPremium(chat_id, none=False):
    async with (await pool()).acquire() as conn:
        return await conn.fetchval('select premium from publicchats where chat_id=$1', chat_id) or none


async def ischatPubic(chat_id, none=False):
    async with (await pool()).acquire() as conn:
        return await conn.fetchval('select isopen from publicchats where chat_id=$1', chat_id) or none


@AsyncTTL(time_to_live=300, maxsize=0)
async def isMessagesFromGroupAllowed(uid):
    return (await api.messages.is_messages_from_group_allowed(group_id=GROUP_ID, user_id=uid)).is_allowed


async def getHiddenAlbumUser():
    global _hiddenalbumuid
    if _hiddenalbumuid:
        return _hiddenalbumuid
    async with (await pool()).acquire() as conn:
        userspool = await conn.fetch(
                'select uid from allusers where not uid=ANY($1) and uid>0',
                [i[0] for i in await conn.fetch('select uid from hiddenalbumserverinternalerror')])
    for i in userspool:
        if (await api.messages.is_messages_from_group_allowed(group_id=GROUP_ID, user_id=i[0])).is_allowed:
            _hiddenalbumuid = i[0]
            return _hiddenalbumuid
        await asyncio.sleep(0.51)


async def getImportSettings(uid, chat_id):
    async with (await pool()).acquire() as conn:
        if s := await conn.fetchrow('select sys, acc, nicks, punishes, binds from importsettings where uid=$1 and '
                                    'chat_id=$2', uid, chat_id):
            return {'sys': s[0], 'acc': s[1], 'nicks': s[2], 'punishes': s[3], 'binds': s[4]}
        return IMPORTSETTINGS_DEFAULT


async def turnImportSetting(chat_id, uid, setting):
    async with (await pool()).acquire() as conn:
        if not await conn.fetchval('update importsettings set ' + setting + '=not ' + setting +
                                   ' where chat_id=$1 and uid=$2 returning 1', chat_id, uid):
            defaults = IMPORTSETTINGS_DEFAULT.copy()
            defaults[setting] = not defaults[setting]
            await conn.execute(
                'insert into importsettings (uid, chat_id, sys, acc, nicks, punishes, binds) values ($1, $2, $3, $4'
                ', $5, $6, $7)', uid, chat_id, defaults['sys'], defaults['acc'], defaults['nicks'],
                defaults['punishes'], defaults['binds'])


@cached
def scanURLMalware(url):
    try:
        url = requests.get(url, allow_redirects=True, timeout=2).url
    except requests.RequestException:
        return []
    sb = pysafebrowsing.SafeBrowsing(key=GOOGLE_TOKEN)
    sb = sb.lookup_url(url)
    return sb['threats'] if 'threats' in sb and sb['threats'] else []


@cached
def scanURLRedirect(url):
    try:
        response = requests.get(url, allow_redirects=False, timeout=2)
        return response.headers.get('Location') if 300 <= response.status_code < 400 else None
    except requests.RequestException:
        return None


@cached
def scanURLShortened(url):
    try:
        response = requests.get(url, allow_redirects=True, timeout=2)
        return response.url if (
                urlparse(response.url).netloc.replace('www.', '') != urlparse(url).netloc.replace('www.', '')
        ) else False
    except requests.RequestException:
        return False


@cached
def beautifyNumber(n):
    return ''.join((i + ' ') if k % 3 == 2 and k != len(str(n)) - 1 else i for k, i in enumerate(str(n)[::-1]))[::-1]
