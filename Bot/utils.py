import locale
import time
import traceback
from ast import literal_eval
from datetime import date

import requests
import urllib3
import validators
import xmltodict
from vkbottle import PhotoMessageUploader
from vkbottle.bot import Bot

from nudenet import NudeDetector
import tempfile
import os
import sys

from vkbottle_types.objects import MessagesMessage, MessagesMessageAttachmentType

from config.config import (API, VK_API_SESSION, VK_TOKEN_GROUP, GROUP_ID, TASKS_DAILY, PREMIUM_TASKS_DAILY,
                           PREMIUM_TASKS_DAILY_TIERS, TASKS_WEEKLY, PREMIUM_TASKS_WEEKLY, SETTINGS, PATH,
                           NSFW_CATEGORIES, SETTINGS_COUNTABLE)
from db import (CMDNames, UserNames, ChatNames, GroupNames, AccessLevel, LastMessageDate, Nickname, Mute, Warn, Ban,
                XP, Premium, PremMenu, CMDLevels, Messages, DuelWins, Settings, TasksDaily, TasksWeekly, Coins,
                LvlBanned, AntispamMessages, AntispamURLExceptions)


class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


def namesAsCommand(cmd, uid) -> list:
    cmds = [cmd]
    for i in CMDNames.select().where(CMDNames.cmd == cmd, CMDNames.uid == uid):
        cmds.append(i.name)
    return cmds


async def getUserName(uid) -> str:
    name = UserNames.get_or_none(UserNames.uid == uid)
    if name is None:
        name = await API.users.get(user_ids=uid)
        name = f"{name[0].first_name} {name[0].last_name}"
        name = UserNames.create(uid=uid, name=name)
    return name.name


async def kickUser(uid, chat_id) -> bool:
    try:
        await API.messages.remove_chat_user(chat_id=chat_id, member_id=uid)
        if (await getChatSettings(chat_id))['main']['deleteAccessAndNicknameOnLeave']:
            if u := AccessLevel.get_or_none(AccessLevel.uid == uid, AccessLevel.chat_id == chat_id):
                u.delete_instance()
            if u := Nickname.get_or_none(Nickname.uid == uid, Nickname.chat_id == chat_id):
                u.delete_instance()
    except:
        return False
    return True


async def deleteMessages(cmids, chat_id) -> bool:
    try:
        await API.messages.delete(group_id=GROUP_ID, delete_for_all=True, peer_id=chat_id + 2000000000, cmids=cmids)
    except:
        return False
    return True


async def getIDFromMessage(message, place=2) -> int:
    """
    The getIDFromMessage function is used to get the ID of a user from a message.

    :param message: Get the message object that was sent
    :param place: Determine which part of the message to get the id from
    :return: The user's id
    """
    data = message.text.split()
    try:
        if len(data) >= place or message.reply_message:
            if message.reply_message is None:
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
                id = message.reply_message.from_id
        else:
            id = False

        return int(id)
    except:
        return 0


async def sendMessageEventAnswer(event_id, user_id, peer_id, event_data=None) -> bool:
    try:
        await API.messages.send_message_event_answer(event_id, user_id, peer_id, event_data)
    except:
        return False
    return True


async def sendMessage(peer_id, msg, kbd=None):
    try:
        return await API.messages.send(random_id=0, peer_id=peer_id, message=msg, keyboard=kbd, disable_mentions=1)
    except:
        traceback.print_exc()
        return False


def NAsendMessage(chat_id, msg):
    VK_API_SESSION.method('messages.send', {
        'chat_id': chat_id,
        'message': msg,
        'random_id': 0
    })


async def editMessage(msg, peer_id, cmid, kb=None) -> bool:
    try:
        await API.messages.edit(peer_id, msg, disable_mentions=1, conversation_message_id=cmid, keyboard=kb)
    except:
        return False
    return True


async def getChatName(chat_id=None) -> str:
    name = ChatNames.get_or_none(ChatNames.chat_id == chat_id)
    if name is None:
        try:
            chatname = await API.messages.get_conversations_by_id(peer_ids=chat_id + 2000000000, group_id=GROUP_ID)
            chatname = chatname.items[0].chat_settings.title
            name = ChatNames.create(chat_id=chat_id, name=chatname)
        except:
            return 'UNKNOWN'
    return name.name


async def getGroupName(group_id) -> str:
    name = GroupNames.get_or_none(GroupNames.group_id == group_id)
    if name is None:
        name = await API.groups.get_by_id(group_id=abs(group_id))
        name = name[0].name
        name = GroupNames.create(group_id=group_id, name=name)
    return name.name


async def getUserTask(uid, task, tier) -> TasksDaily:
    task = TasksDaily.get_or_create(uid=uid, task=task, tier=tier, defaults={'count': 0})[0]
    return task


async def isChatAdmin(id, chat_id) -> bool:
    try:
        status = await API.messages.get_conversation_members(chat_id + 2000000000)
        for i in status.items:
            if i.member_id == id and (i.is_admin or i.is_owner):
                return True
    except:
        pass
    return False


async def setChatMute(id, chat_id, mute_time):
    try:
        if mute_time > 0:
            return VK_API_SESSION.method('messages.changeConversationMemberRestrictions',
                                         {'peer_id': chat_id + 2000000000, 'member_ids': id, 'for': mute_time,
                                          'action': 'ro'})
        else:
            return VK_API_SESSION.method('messages.changeConversationMemberRestrictions',
                                         {'peer_id': chat_id + 2000000000, 'member_ids': id, 'action': 'rw'})
    except:
        return


async def uploadImage(file):
    bot = Bot(VK_TOKEN_GROUP)
    photo_uploader = PhotoMessageUploader(bot.api)
    try:
        photo = await photo_uploader.upload(file_source=file)
        return photo
    except:
        return None


async def getRegDate(id, format='%d %B %Y', none='Не удалось определить'):
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


async def getUserAccessLevel(uid, chat_id, none=0):
    ac = AccessLevel.get_or_none(AccessLevel.uid == uid, AccessLevel.chat_id == chat_id)
    if ac is not None:
        return ac.access_level
    return none


async def getUserLastMessage(uid, chat_id, none='Неизвестно'):
    lm = LastMessageDate.get_or_none(LastMessageDate.uid == uid, LastMessageDate.chat_id == chat_id)
    if lm is not None:
        return lm.last_message
    return none


async def getUserNickname(uid, chat_id, none=None) -> str | None:
    nick = Nickname.get_or_none(Nickname.uid == uid, Nickname.chat_id == chat_id)
    if nick is not None:
        return nick.nickname
    return none


async def getUserMute(uid, chat_id, none=0) -> int:
    mute = Mute.get_or_none(Mute.uid == uid, Mute.chat_id == chat_id)
    if mute is not None:
        return mute.mute
    return none


async def getUserWarns(uid, chat_id, none=0) -> int:
    warn = Warn.get_or_none(Warn.uid == uid, Warn.chat_id == chat_id)
    if warn is not None:
        return warn.warns
    return none


async def getUserMuteInfo(uid, chat_id, none=None) -> dict:
    if none is None:
        none = {'times': [], 'causes': [], 'names': [], 'dates': []}
    mute = Mute.get_or_none(Mute.uid == uid, Mute.chat_id == chat_id)
    if mute is not None:
        return {
            'times': literal_eval(mute.last_mutes_times),
            'causes': literal_eval(mute.last_mutes_causes),
            'names': literal_eval(mute.last_mutes_names),
            'dates': literal_eval(mute.last_mutes_dates)
        }
    return none


async def getUserBan(uid, chat_id, none=0) -> int:
    ban = Ban.get_or_none(Ban.uid == uid, Ban.chat_id == chat_id)
    if ban is not None:
        return ban.ban
    return none


async def getUserBanInfo(uid, chat_id, none=None) -> dict:
    if none is None:
        none = {'times': [], 'causes': [], 'names': [], 'dates': []}
    ban = Ban.get_or_none(Ban.uid == uid, Ban.chat_id == chat_id)
    if ban is not None:
        return {
            'times': literal_eval(ban.last_bans_times),
            'causes': literal_eval(ban.last_bans_causes),
            'names': literal_eval(ban.last_bans_names),
            'dates': literal_eval(ban.last_bans_dates)
        }
    return none


async def getUserXP(uid, none=0) -> int:
    xp = XP.get_or_none(XP.uid == uid)
    if xp is not None:
        return xp.xp
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
    if chat is not None:
        top = XP.select().where(XP.uid > 0, XP.uid << chat).order_by(XP.xp.desc())
    else:
        top = XP.select().where(XP.uid > 0).order_by(XP.xp.desc())
    if limit > 0:
        top = top.limit(limit)
    if returnval == 'count':
        return {i.uid: k + 1 for k, i in enumerate(top)}
    elif returnval == 'xp':
        return {i.uid: i.xp for k, i in enumerate(top)}
    elif returnval == 'lvl':
        return {i.uid: await getUserLVL(i.xp) for k, i in enumerate(top)}
    else:
        raise Exception('Incorrect returnval')


async def getUserPremium(uid, none=0) -> int:
    pr = Premium.get_or_none(Premium.uid == uid)
    if pr is not None:
        return pr.time
    return none


async def getUserPremmenuSetting(uid, setting, none):
    pm = PremMenu.get_or_none(PremMenu.setting == setting, PremMenu.uid == uid)
    if pm is not None:
        return pm.pos
    return none


async def getChatCommandLevel(chat_id, cmd, none):
    cacc = CMDLevels.get_or_none(CMDLevels.chat_id == chat_id, CMDLevels.cmd == cmd)
    if cacc is not None:
        return cacc.lvl
    return none


async def getUserMessages(uid, chat_id, none=0) -> int:
    ms = Messages.get_or_none(Messages.uid == uid, Messages.chat_id == chat_id)
    if ms is not None:
        return ms.messages
    return none


async def addUserXP(uid, addxp):
    if not await getULvlBanned(uid):
        return
    u = XP.get_or_create(uid=uid, defaults={'xp': 0})[0]
    ul = await getUserLVL(u.xp)
    u.xp += addxp
    u.save()
    if await getUserLVL(u.xp) > ul:
        await addWeeklyTask(uid, 'lvlup')


async def getUserDuelWins(uid, none=0):
    dw = DuelWins.get_or_none(DuelWins.uid == uid)
    if dw is not None:
        return dw.wins
    return none


async def getChatSettings(chat_id):
    chatsettings = SETTINGS()
    for cat, settings in chatsettings.items():
        for setting, pos in settings.items():
            chatsetting = Settings.get_or_none(Settings.chat_id == chat_id, Settings.setting == setting)
            if chatsetting is None:
                continue
            chatsettings[cat][setting] = chatsetting.pos
    return chatsettings


async def turnChatSetting(chat_id, category, setting):
    s = Settings.get_or_create(chat_id=chat_id, setting=setting,
                               defaults={'pos': SETTINGS()[category][setting]})[0]
    s.pos = not s.pos
    s.save()
    return s.pos


async def setUserAccessLevel(uid, chat_id, access_level):
    ac = AccessLevel.get_or_create(uid=uid, chat_id=chat_id, defaults={'access_level': 0})[0]
    if access_level == 0:
        ac.delete_instance()
        return
    ac.access_level = access_level
    ac.save()


async def addDailyTask(uid, task, count=1):
    if not await getULvlBanned(uid):
        return
    t = TasksDaily.get_or_create(uid=uid, task=task)[0]
    t.count += count
    t.save()
    if t.count == (TASKS_DAILY | PREMIUM_TASKS_DAILY)[task]:
        if (task in PREMIUM_TASKS_DAILY and await getUserPremium(uid)) or task in TASKS_DAILY:
            c = Coins.get_or_create(uid=uid)[0]
            c.coins += 5
            c.save()
    if t.count == PREMIUM_TASKS_DAILY_TIERS[task] and await getUserPremium(uid):
        c = Coins.get_or_create(uid=uid)[0]
        c.coins += 5
        c.save()


async def addWeeklyTask(uid, task, count=1):
    if not await getULvlBanned(uid):
        return
    t = TasksWeekly.get_or_create(uid=uid, task=task)[0]
    t.count += count
    t.save()
    if t.count == (TASKS_WEEKLY | PREMIUM_TASKS_WEEKLY)[task]:
        if (task in PREMIUM_TASKS_WEEKLY and await getUserPremium(uid)) or task in TASKS_WEEKLY:
            c = Coins.get_or_create(uid=uid)[0]
            c.coins += 10
            c.save()


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
    usermessages = AntispamMessages.select().where(AntispamMessages.chat_id == chat_id, AntispamMessages.from_id == uid)
    if settings['antispam']['messagesPerMinute']:
        setting = Settings.get_or_none(Settings.chat_id == chat_id, Settings.setting == 'messagesPerMinute')
        if setting is not None and setting.value is not None:
            if len(usermessages) >= setting.value:
                return 'messagesPerMinute'
    if settings['antispam']['maximumCharsInMessage']:
        setting = Settings.get_or_none(Settings.chat_id == chat_id, Settings.setting == 'maximumCharsInMessage')
        if setting is not None and setting.value is not None:
            if len(message.text) >= setting.value:
                return 'maximumCharsInMessage'
    if settings['antispam']['disallowLinks']:
        data = message.text.split()
        for i in data:
            for y in i.split('/'):
                if (validators.url(y) or validators.domain(y)) and y not in ['vk.com', 'vk.ru']:
                    if AntispamURLExceptions.get_or_none(
                            AntispamURLExceptions.chat_id == chat_id,
                            AntispamURLExceptions.url == y.replace('https://', '').replace('/', '')) is None:
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


def pointDays(seconds):
    res = int(seconds // 86400)
    if res == 1:
        res = str(res) + ' день'
    elif 1 < res < 5:
        res = str(res) + ' дня'
    else:
        res = str(res) + ' дней'
    return res


def pointHours(seconds):
    res = int(seconds // 3600)
    if res in [23, 22, 4, 3, 2]:
        res = f'{res} часа'
    elif res in [21, 1]:
        res = f'{res} час'
    else:
        res = f'{res} часов'
    return res


def pointMinutes(seconds):
    res = int(seconds // 60)
    if res % 10 == 1 and res % 100 != 11:
        res = str(res) + ' минута'
    elif 2 <= res % 10 <= 4 and (res % 100 < 10 or res % 100 >= 20):
        res = str(res) + ' минуты'
    else:
        res = str(res) + ' минут'
    return res


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


async def getULvlBanned(uid) -> int:
    ban = LvlBanned.get_or_none(LvlBanned.uid == uid)
    if ban is not None:
        return 0
    return 1
