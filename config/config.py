from ast import literal_eval

from vk_api import vk_api
from vkbottle import API
from configparser import ConfigParser

config = ConfigParser()
config.read('/root/StarManager/config/config.ini')  # write existing path here

VK_TOKEN_GROUP = config['VK']['VK_TOKEN_GROUP']
GROUP_ID = int(config['VK']['GROUP_ID'])  # without "-"
VK_TOKEN_IMPLICIT_FLOW = config['VK']['VK_TOKEN_IMPLICIT_FLOW']
VK_APP_ID = config['VK']['VK_APP_ID']
VK_APP_SECRET = config['VK']['VK_APP_SECRET']

LVL_NAMES = ["Обычный Пользователь", "Смотрящий", "Модератор", "Старший Модератор", "Администратор",
             "Спец администратор", "Руководитель", "Владелец", "DEV"]

COMMANDS = {
    "start": 0, "help": 0, "id": 0, "stats": 0, "report": 0, "mtop": 0, "q": 0, "premium": 0, "bonus": 0, "transfer": 0,
    "duel": 0, "cmd": 0, "premmenu": 0, "test": 0, "task": 0, "getdev": 0, "anon": 0, "chatid": 0, "prefix": 0,

    "kick": 1, "mute": 1, "warn": 1, "clear": 1, "staff": 1, "olist": 1, "getnick": 1, "snick": 1, "rnick": 1,
    "nlist": 1, "check": 1, "mkick": 1,

    "unmute": 2, "unwarn": 2, "mutelist": 2, "warnlist": 2, "setaccess": 2, "delaccess": 2,

    "ban": 3, "unban": 3, "kickmenu": 3, "banlist": 3, "timeout": 3, "zov": 3, "inactive": 3,

    "gkick": 4, "gban": 4, "gunban": 4, "gmute": 4, "gunmute": 4, "gwarn": 4, "gunwarn": 4, "gsnick": 4, "grnick": 4,
    "gzov": 4,

    "skick": 5, "sban": 5, "sunban": 5, "ssnick": 5, "srnick": 5, "szov": 5, "chat": 5,

    "demote": 6, "gsetaccess": 6, "resetnick": 6, "resetaccess": 6, "gdelaccess": 6, "ssetaccess": 6, "sdelaccess": 6,
    "chatlimit": 6, "notif": 6, "ignore": 6, "unignore": 6, "ignorelist": 6, "purge": 6,

    "mygroups": 7, "creategroup": 7, "delgroup": 7, "levelname": 7, "resetlevel": 7, "async": 7, "bind": 7, "unbind": 7,
    "delasync": 7, "addfilter": 7, "delfilter": 7, "filterlist": 7, "gaddfilter": 7, "gdelfilter": 7, "listasync": 7,
    "editlevel": 7, "giveowner": 7, "settings": 7,

    "botinfo": 8, "msg": 8, "blacklist": 8, "addblack": 8, "delblack": 8, "setstatus": 8, "delstatus": 8, "inflist": 8,
    "statuslist": 8, "cmdcount": 8, "infban": 8, "infunban": 8, "getlink": 8, "backup": 8, "gps": 8, "checkleaved": 8,
    "reportwarn": 8, "reboot": 8, "sudo": 8, "givexp": 8, "reimport": 8, "resetlvl": 8, "getuserchats": 8, "helpdev": 8,
    "getchats": 8, "gettransferhistory": 8, "gettransferhistoryto": 8, "gettransferhistoryfrom": 8, "lvlunban": 8,
    "getmessageshistory": 8, "lvlban": 8, "lvlbanlist": 8, "msgscount": 8, "msgsaverage": 8, "mwaverage": 8,
    "chatsstats": 8,
}
PM_COMMANDS = [
    "anon", "deanon",
]
COMMANDS_DESC = {
    "task": "/task - Открыть меню заданий.",
    "kick": "/kick - Исключить пользователя.",
    "mute": "/mute - Заблокировать чат пользователю.",
    "warn": "/warn - Выдать предупреждение пользователю.",
    "check": "/check - История наказаний пользователя.",
    "clear": "/clear - Очистить сообщение.",
    "staff": "/staff - Список администраторов беседы.",
    "snick": "/snick - Установить никнейм.",
    "rnick": "/rnick - Удалить никнейм.",
    "nlist": "/nlist - Список пользователей с никнеймами.",
    "getnick": "/getnick - Узнать пользователя по никнейму.",
    "olist": "/olist - пользователи онлайн.",
    "unmute": "/unmute - Снять блокировку чата.",
    "unwarn": "/unwarn - Снять предупреждение.",
    "mutelist": "/mutelist - Список пользователей с блокировкой чата.",
    "warnlist": "/warnlist - Список пользователей с предупреждениями.",
    "ban": "/ban - Заблокировать пользователя.",
    "unban": "/unban - Разблокировать пользователя.",
    "banlist": "/banlist - Список заблокированных пользователей.",
    "timeout": "/timeout - Режим тишины.",
    "zov": "/zov - Вызвать всех участников беседы.",
    "inactive": "/inactive - Исключить неактивных пользователей.",
    "kickmenu": "/kickmenu - Меню исключения пользователей.",
    "gkick": "/gkick - Глобально исключить пользователя.",
    "gban": "/gban - Глобально заблокировать пользователя.",
    "gunban": "/gunban - Глобально разблокировать пользователя.",
    "gmute": "/gmute - Глобально ограничить чат пользователя.",
    "gunmute": "/gunmute - Глобально снять ограничение чата пользователю.",
    "gwarn": "/gwarn - Глобально выдать варн пользователю.",
    "gunwarn": "/gunwarn - Глобально снять варн пользователю.",
    "gsnick": "/gsnick - Глобально установить никнейм пользователю.",
    "grnick": "/grnick - Глобально удалить никнейм пользователю.",
    "gzov": "/gzov - Глобально вызвать всех участников беседы.",
    "skick": "/skick - Исключить пользователя в группе бесед.",
    "sban": "/sban - Заблокировать пользователя в группе бесед.",
    "sunban": "/sunban - Разблокировать пользователя в группе бесед.",
    "ssnick": "/ssnick - Установить никнейм пользователю в группе бесед.",
    "srnick": "/srnick - Удалить никнейм пользователю в группе бесед,",
    "chat": "/chat - Информация о чате.",
    "szov": "/szov - Вызвать участников в группе бесед.",
    "setaccess": "/setaccess - Выдать уровень прав пользователю.",
    "delaccess": "/delaccess - Снять уровень прав пользователю.",
    "demote": "/demote - Расформировать беседу.",
    "gsetaccess": "/gsetaccess - Выдать уровень прав пользователю глобально.",
    "gdelaccess": "/gdelaccess - Снять уровень прав пользователю глобально.",
    "ssetaccess": "/ssetaccess - Выдать уровень прав пользователю в группе бесед.",
    "sdelaccess": "/sdelaccess - Снять уровень прав пользователю в группе бесед.",
    "mygroups": "/mygroups - Список созданных групп.",
    "creategroup": "/creategroup - Создать группу бесед.",
    "delgroup": "/delgroup - Удалить группу бесед.",
    "listasync": "/listasync - Список глобальных бесед",
    "async": "/async - Привязать беседу к глобальным беседам.",
    "delasync": "/delasync - Отвязать беседу от глобальных бесед.",
    "bind": "/bind - Привязать беседу к группе бесед.",
    "unbind": "/unbind - Отвязать беседу из группы бесед.",
    "addfilter": "/addfilter - Добавить слово в фильтр.",
    "delfilter": "/delfilter - Удалить слово из фильтра.",
    "filterlist": "/filterlist - Посмотреть фильтр-слов.",
    "gaddfilter": "/gaddfilter - Глобально добавить слово в фильтр.",
    "gdelfilter": "/gdelfilter - Глобально удалить слово из фильтра.",
    "giveowner": "/giveowner - Передать права владельца.",
    "premmenu": "/premmenu - Меню премиум возможностей.",
    "mkick": "/mkick - Исключить сразу несколько пользователей.",
    "editlevel": "/editlevel - Изменить уровень прав для команд.",
    "levelname": "/levelname - Изменить название для уровней прав.",
    "resetlevel": "/resetlevel - Восстановить стандартное название уровней прав.",
    "addprefix": "/addprefix - Добавить персональный префикс для команд.",
    "delprefix": "/delprefix - Удалить персональный префикс для команд.",
    "listprefix": "/listprefix - Список персональных префиксов.",
    "ignore": "/ignore - Добавить пользователя в игнор бота.",
    "unignore": "/unignore - Удалить пользователя из игнор бота.",
    "ignorelist": "/ignorelist - Список игнорируемых пользователей ботом.",
    "chatlimit": "/chatlimit - Установить медленный режим в чате.",
    "id": "/id - Краткая информация пользователя.",
    "stats": "/stats - Статистика пользователя.",
    "mtop": "/mtop - Топ активных пользователей.",
    "q": "/q - Выйти из беседы.",
    "report": "/report - Обратится в поддержку.",
    "bonus": "/bonus - Ежедневный бонус.",
    "premium": "/premium - Информация о Premium.",
    "duel": "/duel - Дуэль с пользователями.",
    "cmd": "/cmd - Изменения названия команд.",
    "transfer": "/transfer - Передать опыт другому пользователю.",
    "chatid": "/chatid - Узнать ID беседы.",
    "resetaccess": "/resetaccess - удалить уровень прав всем пользователям беседы.",
    "resetnick": "/resetnick - удалить ники всех пользователей беседы.",
    "purge": "/purge - очищает беседу от ненужной информации.",
    "chatsstats": "/chatsstats - информация по беседам.",
}

# chat ids
DAILY_TO = int(config['SERVICE']['DAILY_TO'])
BACKUPS_TO = int(config['SERVICE']['BACKUPS_TO'])
REPORT_TO = int(config['SERVICE']['REPORT_TO'])
CHEATING_TO = int(config['SERVICE']['CHEATING_TO'])

REPORT_CD = 300  # cooldown in seconds

NEWSEASON_REWARDS = [45, 40, 30, 20, 15, 7, 7, 7, 7, 7]

TASKS_DAILY = {
    'sendmsgs': 300,
    'sendvoice': 30,
    'duelwin': 15
}
PREMIUM_TASKS_DAILY = {
    'cmds': 50,
    'stickers': 100
}
PREMIUM_TASKS_DAILY_TIERS = {
    'sendmsgs': 600,
    'sendvoice': 60,
    'duelwin': 25,
    'cmds': 100,
    'stickers': 200
}
TASKS_WEEKLY = {
    'bonus': 6,
    'dailytask': 7,
    'sendmsgs': 10000
}
PREMIUM_TASKS_WEEKLY = {
    'lvlup': 10,
    'duelwin': 60
}

TASKS_LOTS = {5: 1, 20: 5, 40: 10, 80: 3}

DEVS = literal_eval(config['SERVICE']['DEVS'])
ADMINS = literal_eval(config['SERVICE']['ADMINS'])
MAIN_DEVS = literal_eval(config['SERVICE']['MAIN_DEVS'])
DEVS_COLORS = literal_eval(config['SERVICE']['DEVS_COLORS'])

PREFIX = ["/", "!", ".", "+"]

PATH = config['SERVICE']['PATH']

GWARN_TIME_LIMIT = 10
GWARN_PUNISHMENT = 10  # in seconds
GWARN_PUNISHMENTS_NAMES = ["5 минут", "30 минут", "48 часов", "30 дней"]

LVL_BANNED_COMMANDS = ['task', 'bonus', 'transfer', 'duel']


def SETTINGS():
    return {
        "main": {
            "kickInvitedByNoAccess": 1,
            "kickLeaving": 1,
            "kickBlockingViolator": 0,
            "deleteAccessAndNicknameOnLeave": 0,
            "nightmode": 0,
            "welcome": 0,
            "captcha": 0,
        },
        "entertaining": {
            "allowDuel": 1,
            "allowTransfer": 1,
            "allowTask": 1,
            "allowAnon": 1,
        },
        "antispam": {
            "messagesPerMinute": 0,
            "maximumCharsInMessage": 0,
            "disallowLinks": 0,
            "disallowNSFW": 0,
        },
        "protect": {
            "enable": 0
        }
    }


def SETTINGS_ALT():
    return {
        "main": {
            "welcome": 0,
        },
        "entertaining": {
        },
        "antispam": {
        },
        "protect": {
        }
    }


SETTINGS_POSITIONS = {
    "main": {
        "kickInvitedByNoAccess": ["Выкл.", "Вкл."],
        "kickLeaving": ["Выкл.", "Вкл."],
        "kickBlockingViolator": ["Удалить сообщ.", "Исключить"],
        "deleteAccessAndNicknameOnLeave": ["Выкл.", "Вкл."],
        "nightmode": ["Выкл.", "Вкл."],
        "welcome": ["Выкл.", "Вкл."],
        "captcha": ["Выкл.", "Вкл."],
    },
    "entertaining": {
        "allowDuel": ["Выкл.", "Вкл."],
        "allowTransfer": ["Выкл.", "Вкл."],
        "allowTask": ["Выкл.", "Вкл."],
        "allowAnon": ["Выкл.", "Вкл."],
    },
    "antispam": {
        "messagesPerMinute": ["Выкл.", "Вкл."],
        "maximumCharsInMessage": ["Выкл.", "Вкл."],
        "disallowLinks": ["Выкл.", "Вкл."],
        "disallowNSFW": ["Выкл.", "Вкл."],
    },
    "protect": {
        "enable": ["Выкл.", "Вкл."],
    }
}
SETTINGS_COUNTABLE = [
    "messagesPerMinute", "maximumCharsInMessage", "disallowLinks", "disallowNSFW", "nightmode", "welcome", "captcha",
]
SETTINGS_COUNTABLE_MULTIPLE_ARGUMENTS = [
    "nightmode", "welcome"
]
SETTINGS_COUNTABLE_NO_PUNISHMENT = [
    "nightmode", "welcome"
]
SETTINGS_COUNTABLE_NO_CATEGORY = [
    "nightmode", "welcome", "captcha"
]
SETTINGS_COUNTABLE_PUNISHMENT_NO_DELETE_MESSAGE = [
    "messagesPerMinute", "captcha"
]
SETTINGS_COUNTABLE_SPECIAL_LIMITS = {
    "captcha": range(1, 61)
}
SETTINGS_DEFAULTS = {
    "captcha": {"pos": 0, "value": 10, "punishment": "kick"},
}
SETTINGS_PREMIUM = [
    "captcha",
]
SETTINGS_COUNTABLE_CHANGEMENU = {
    "messagesPerMinute": [
        {"action": "turn", "button": ["Включить", "Выключить"]},
        {"action": "set", "button": "Количество"},
        {"action": "setPunishment", "button": "Наказание"},
    ],
    "captcha": [
        {"action": "turn", "button": ["Включить", "Выключить"]},
        {"action": "set", "button": "Время"},
        {"action": "setPunishment", "button": "Наказание"},
    ],
    "nightmode": [
        {"action": "turn", "button": ["Включить", "Выключить"]},
        {"action": "set", "button": "Установить время"},
    ],
    "welcome": [
        {"action": "turn", "button": ["Включить", "Выключить"]},
        {"action": "set", "button": "Установить сообщение"},
        {"action": "turnalt", "button": ["Удаление сообщения", "Удаление сообщения"]},
    ],
    "maximumCharsInMessage": [
        {"action": "turn", "button": ["Включить", "Выключить"]},
        {"action": "set", "button": "Количество"},
        {"action": "setPunishment", "button": "Наказание"},
    ],
    "disallowLinks": [
        {"action": "turn", "button": ["Включить", "Выключить"]},
        {"action": "setPunishment", "button": "Наказание"},
        {"action": "setWhitelist", "button": "Исключения"},
    ],
    "disallowNSFW": [
        {"action": "turn", "button": ["Включить", "Выключить"]},
        {"action": "setPunishment", "button": "Наказание"},
    ],
}
SETTINGS_COUNTABLE_CHANGEPUNISHMENTMESSAGE = {
    "mute": "мут на {count} минут",
    "ban": "бан на {count} дней",
}

TASKS = []

FARM_CD = 7200  # in seconds
FARM_POST_ID = int(config['SERVICE']['FARM_POST_ID'])

PREMIUM_BONUS_POST_ID = int(config['SERVICE']['PREMIUM_BONUS_POST_ID'])
PREMIUM_BONUS_DAYS = 5

NSFW_CATEGORIES = [
    "BUTTOCKS_EXPOSED",
    "FEMALE_BREAST_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "ANUS_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
]


def PREMIUM_BONUS_POST_WORKS_TIL():
    import datetime
    return datetime.datetime(year=2024, month=2, day=17).timestamp()


IMPLICIT_API = API(VK_TOKEN_IMPLICIT_FLOW)
API = API(VK_TOKEN_GROUP)
VK_API_SESSION = vk_api.VkApi(token=VK_TOKEN_GROUP, api_version='5.199')
VK_API_IMPLICIT_SESSION = vk_api.VkApi(token=VK_TOKEN_IMPLICIT_FLOW, api_version='5.199')

PREMIUM_COST = {30: 99, 90: 249, 180: 499}

USER = config['DATABASE']['USER']
PASSWORD = config['DATABASE']['PASSWORD']
DATABASE = config['DATABASE']['DATABASE']

TG_TOKEN = config['TELEGRAM']['TG_TOKEN']
TG_CHAT_ID = config['TELEGRAM']['TG_CHAT_ID']
TG_BACKUP_THREAD_ID = config['TELEGRAM']['TG_BACKUP_THREAD_ID']
TG_PREMIUM_THREAD_ID = config['TELEGRAM']['TG_PREMIUM_THREAD_ID']
TG_NEWCHAT_THREAD_ID = config['TELEGRAM']['TG_NEWCHAT_THREAD_ID']
TG_TRANSFER_THREAD_ID = config['TELEGRAM']['TG_TRANSFER_THREAD_ID']
TG_AUDIO_THREAD_ID = config['TELEGRAM']['TG_AUDIO_THREAD_ID']
TG_API_HASH = config['TELEGRAM']['TG_API_HASH']
TG_API_ID = config['TELEGRAM']['TG_API_ID']

YOOKASSA_MERCHANT_ID = int(config['YOOKASSA']['YOOKASSA_MERCHANT_ID'])
YOOKASSA_TOKEN = config['YOOKASSA']['YOOKASSA_TOKEN']

MEGA_LOGIN = config['MEGA']['MEGA_LOGIN']
MEGA_PASSWORD = config['MEGA']['MEGA_PASSWORD']
print(MEGA_LOGIN, MEGA_PASSWORD)

data = {
    'email': config['SOCIALS']['email'],
    'vk': config['SOCIALS']['vk'],
    'vk_preminfo': config['SOCIALS']['vk_preminfo'],
    'tg': config['SOCIALS']['tg'],
}
