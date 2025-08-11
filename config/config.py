import platform
from ast import literal_eval
from configparser import ConfigParser

from vk_api import vk_api
from vkbottle import API

config = ConfigParser()
config.read(
    f"{__file__.replace('config.py', '')}config{'' if platform.system() == 'Linux' else '2'}.ini"
)
# remove this weird path, use your own

PATH = config["SERVICE"]["PATH"]

VK_TOKEN_GROUP = config["VK"]["VK_TOKEN_GROUP"]
VK_TOKEN_IMPLICIT_FLOW = config["VK"]["VK_TOKEN_IMPLICIT_FLOW"]
VK_SERVICE_TOKEN = config["VK"]["VK_SERVICE_TOKEN"]
GROUP_ID = abs(int(config["VK"]["GROUP_ID"]))
VK_APP_ID = config["VK"]["VK_APP_ID"]
VK_APP_SECRET = config["VK"]["VK_APP_SECRET"]


LVL_NAMES = [
    "Обычный Пользователь",
    "Смотрящий",
    "Модератор",
    "Старший Модератор",
    "Администратор",
    "Спец администратор",
    "Руководитель",
    "Владелец",
    "DEV",
]

COMMANDS = {
    "start": 0,
    "help": 0,
    "id": 0,
    "stats": 0,
    "top": 0,
    "q": 0,
    "premium": 0,
    "bonus": 0,
    "transfer": 0,
    "duel": 0,
    "cmd": 0,
    "premmenu": 0,
    "test": 0,
    "getdev": 0,
    "anon": 0,
    "chatid": 0,
    "prefix": 0,
    "deanon": 0,
    "chats": 0,
    "catalog": 0,
    "guess": 0,
    "promo": 0,
    "rep": 0,
    "report": 0,
    "short": 0,
    "rewards": 0,
    "shop": 0,
    "kick": 1,
    "mute": 1,
    "warn": 1,
    "clear": 1,
    "staff": 1,
    "olist": 1,
    "getnick": 1,
    "snick": 1,
    "rnick": 1,
    "nlist": 1,
    "check": 1,
    "mkick": 1,
    "scan": 1,
    "invited": 1,
    "unmute": 2,
    "unwarn": 2,
    "mutelist": 2,
    "warnlist": 2,
    "setaccess": 2,
    "delaccess": 2,
    "ban": 3,
    "unban": 3,
    "kickmenu": 3,
    "banlist": 3,
    "timeout": 3,
    "zov": 3,
    "inactive": 3,
    "gkick": 4,
    "gban": 4,
    "gunban": 4,
    "gmute": 4,
    "gunmute": 4,
    "gwarn": 4,
    "gunwarn": 4,
    "gsnick": 4,
    "grnick": 4,
    "gzov": 4,
    "skick": 5,
    "sban": 5,
    "sunban": 5,
    "ssnick": 5,
    "srnick": 5,
    "szov": 5,
    "chat": 5,
    "antitag": 5,
    "pin": 5,
    "unpin": 5,
    "demote": 6,
    "gsetaccess": 6,
    "resetnick": 6,
    "resetaccess": 6,
    "gdelaccess": 6,
    "ssetaccess": 6,
    "sdelaccess": 6,
    "chatlimit": 6,
    "notif": 6,
    "ignore": 6,
    "unignore": 6,
    "ignorelist": 6,
    "purge": 6,
    "rename": 6,
    "mygroups": 7,
    "creategroup": 7,
    "delgroup": 7,
    "levelname": 7,
    "resetlevel": 7,
    "async": 7,
    "bind": 7,
    "unbind": 7,
    "delasync": 7,
    "filter": 7,
    "filteradd": 7,
    "filterdel": 7,
    "listasync": 7,
    "editlevel": 7,
    "giveowner": 7,
    "settings": 7,
    "import": 7,
    "bindlist": 7,
    "botinfo": 8,
    "msg": 8,
    "blacklist": 8,
    "addblack": 8,
    "delblack": 8,
    "setstatus": 8,
    "delstatus": 8,
    "statuslist": 8,
    "cmdcount": 8,
    "block": 8,
    "unblock": 8,
    "getlink": 8,
    "backup": 8,
    "reboot": 8,
    "sudo": 8,
    "givexp": 8,
    "resetlvl": 8,
    "getuserchats": 8,
    "helpdev": 8,
    "getchats": 8,
    "gettransferhistory": 8,
    "gettransferhistoryto": 8,
    "gettransferhistoryfrom": 8,
    "lvlunban": 8,
    "lvlban": 8,
    "lvlbanlist": 8,
    "msgscount": 8,
    "msgsaverage": 8,
    "mwaverage": 8,
    "chatsstats": 8,
    "setprem": 8,
    "delprem": 8,
    "premlist": 8,
    "repban": 8,
    "repunban": 8,
    "repbanlist": 8,
    "linked": 8,
    "cmdstats": 8,
    "promocreate": 8,
    "promodel": 8,
    "promolist": 8,
    "blocklist": 8,
    "allowinvite": 8,
    "prempromocreate": 8,
    "prempromodel": 8,
    "prempromolist": 8,
    "bonuslist": 8,
    "rewardscount": 8,
    "givecoins": 8,
}
PM_COMMANDS = ["anon", "deanon", "code", "report", "premium"]
COMMANDS_DESC = {
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
    "settings": "/settings - Настройки беседы.",
    "mygroups": "/mygroups - Список созданных групп.",
    "creategroup": "/creategroup - Создать группу бесед.",
    "delgroup": "/delgroup - Удалить группу бесед.",
    "listasync": "/listasync - Список глобальных бесед",
    "async": "/async - Привязать беседу к глобальным беседам.",
    "delasync": "/delasync - Отвязать беседу от глобальных бесед.",
    "bind": "/bind - Привязать беседу к группе бесед.",
    "unbind": "/unbind - Отвязать беседу из группы бесед.",
    "filteradd": "/filteradd - Добавить слово в фильтр.",
    "filterdel": "/filterdel - Удалить слово из фильтра.",
    "filter": "/filter - Настройки фильтра слов.",
    "giveowner": "/giveowner - Передать права владельца.",
    "premmenu": "/premmenu - Меню премиум возможностей.",
    "mkick": "/mkick - Исключить сразу несколько пользователей.",
    "editlevel": "/editlevel - Изменить уровень прав для команд.",
    "levelname": "/levelname - Изменить название для уровней прав.",
    "resetlevel": "/resetlevel - Восстановить стандартное название уровней прав.",
    "prefix": "/prefix - Управление префиксами.",
    "ignore": "/ignore - Добавить пользователя в игнор бота.",
    "unignore": "/unignore - Удалить пользователя из игнор бота.",
    "ignorelist": "/ignorelist - Список игнорируемых пользователей ботом.",
    "chatlimit": "/chatlimit - Установить медленный режим в чате.",
    "id": "/id - Краткая информация пользователя.",
    "stats": "/stats - Статистика пользователя.",
    "top": "/top - Топ активных пользователей.",
    "q": "/q - Выйти из беседы.",
    "report": "/report (в личные сообщения) - Обратится в поддержку.",
    "bonus": "/bonus - Ежедневный бонус.",
    "premium": "/premium - Информация о Premium.",
    "duel": "/duel - Дуэль с пользователями.",
    "shop": "/shop - Магазин обмена Star-монеток.",
    "cmd": "/cmd - Изменения названия команд.",
    "transfer": "/transfer - Передать монетки другому пользователю.",
    "chatid": "/chatid - Узнать ID беседы.",
    "resetaccess": "/resetaccess - удалить уровень прав всем пользователям беседы.",
    "resetnick": "/resetnick - удалить ники всех пользователей беседы.",
    "purge": "/purge - очищает беседу от ненужной информации.",
    "guess": "/guess - Угадать число.",
    "antitag": "/antitag - Запретить упоминание пользователя.",
    "pin": "/pin - Закрепить сообщение.",
    "unpin": "/unpin - Открепить сообщение.",
    "import": "/import - Импортировать настройки из других бесед.",
    "rename": "/rename - Изменить название беседы.",
    "scan": "/scan - Сканировать ссылки на наличие вирусов.",
    "anon": "/anon (в личные сообщения) - Отправить анонимное сообщение.",
    "deanon": "/deanon (в личные сообщения) - Узнать отправителя анонимного сообщения.",
    "notif": "/notif - Настройка напоминаний в беседе.",
    "rep": "/rep - Изменить репутацию пользователя.",
    "invited": "/invited - Количество приглашенных участников.",
    "bindlist": "/bindlist - Список привязанных к указанной группе бесед.",
    "botinfo": "/botinfo - Информация по боту(не работает).",
    "msg": "/msg - отправить сообщения во все беседы.",
    "blacklist": "/blacklist - Список пользователей в черном списке.",
    "addblack": "/addblack - Добавить пользователя в черный список.",
    "delblack": "/delblack - Удалить пользователя из черного списка.",
    "setstatus": "/setstatus - Установить Premium-подписку.",
    "delstatus": "/delstatus - Убрать Premium-подписку.",
    "statuslist": "/statuslist - Список пользователей с Premium-подпиской.",
    "cmdcount": "/cmdcount - Статистика команд.",
    "block": "/block - Заблокировать пользователя.",
    "unblock": "/unblock - Разблокировать пользователя.",
    "getlink": "/getlink - Получить ссылку-приглашение в беседу.",
    "backup": "/backup - Сделать бэкап.",
    "reboot": "/reboot - Перезагрузить бота.",
    "sudo": "/sudo - Отправить sudo-команду на сервер.",
    "givexp": "/givexp - Выдать монетки пользователю.",
    "givecoins": "/givecoins - Выдать Star-монетки пользователю.",
    "resetlvl": "/resetlvl - Сбросить прогресс(монетки, уровень и лигу) пользователя.",
    "getuserchats": "/getuserchats - Список бесед пользователя.",
    "helpdev": "/helpdev - Информация по dev-командам.",
    "getchats": "/getchats - Список бесед.",
    "gettransferhistory": "/gettransferhistory - Логи /transfer.",
    "gettransferhistoryto": "/gettransferhistoryto - Логи /transfer пользователю.",
    "gettransferhistoryfrom": "/gettransferhistoryfrom - Логи /transfer от пользователя.",
    "lvlban": "/lvlban - Заблокировать прогресс пользователя.",
    "lvlunban": "/lvlunban - Разблокировать прогресс пользователя.",
    "lvlbanlist": "/lvlbanlist - Список пользователей с заблокированным прогрессом.",
    "msgscount": "/msgscount - Статистика сообщений.",
    "msgsaverage": "/msgsaverage - Статистика message_handle.",
    "mwaverage": "/mwaverage - Статистика mw.",
    "chatsstats": "/chatsstats - Статистика чатов с включенной капчей и ночного режима.",
    "setprem": "/setprem - Установить Premium-статус беседы.",
    "delprem": "/delprem - Убрать Premium-статус беседы.",
    "premlist": "/premlist - Список бесед с Premium-статусом.",
    "repban": "/repban - Заблокировать отправку репортов пользователю.",
    "repunban": "/repunban - Разблокировать отправку репортов пользователю.",
    "repbanlist": "/repbanlist - Список пользователей с заблокированной отправкой репортов.",
    "linked": "/linked - Список пользователей, привязавших Telegram.",
    "cmdstats": "/cmdstats - Количество использований команды.",
    "promocreate": "/promocreate - Создать промокод.",
    "promodel": "/promodel - Удалить промокод.",
    "promolist": "/promolist - Список промокодов.",
    "blocklist": "/blocklist - Список заблокированных пользователей.",
    "allowinvite": "/allowinvite - Разрешить/запретить бонусы реферальной системы в чате.",
    "prempromocreate": "/prempromocreate - Создать промокод на сайте.",
    "prempromodel": "/prempromodel - Удалить промокод на сайте.",
    "prempromolist": "/prempromolist - Список промокодов на сайте.",
    "bonuslist": "/bonuslist - Статистика команды /bonus.",
}
COMMANDS_PREMIUM = [
    "premmenu",
    "mkick",
    "ignore",
    "unignore",
    "ignorelist",
    "chatlimit",
    "editlevel",
    "levelname",
    "resetlevel",
    "anon",
    "deanon",
    "prefix",
]
COMMANDS_COOLDOWN = {
    "guess": 10,
    "transfer": 10,
    "duel": 15,
    "stats": 15,
}

# chat ids
DAILY_TO = int(config["SERVICE"]["DAILY_TO"])
REPORT_TO = int(config["SERVICE"]["REPORT_TO"])
STATUSCHECKER_TO = int(config["SERVICE"]["STATUSCHECKER_TO"])
STATUSCHECKER_CMD = "/duel"
MATHGIVEAWAYS_TO = int(config["SERVICE"]["MATHGIVEAWAYS_TO"])

PHOTO_NOT_FOUND = config["SERVICE"]["PHOTO_NOT_FOUND"]

REPORT_CD = 300  # cooldown in seconds

DEV_TGID = literal_eval(config["SERVICE"]["DEV_TGID"])
DEVS = literal_eval(config["SERVICE"]["DEVS"])
ADMINS = literal_eval(config["SERVICE"]["ADMINS"])
MAIN_DEVS = literal_eval(config["SERVICE"]["MAIN_DEVS"])

PREFIX = ["/", "!", ".", "+"]

LVL_BANNED_COMMANDS = ["bonus", "transfer", "duel", "guess", "promo", "shop"]

LEAGUE_LVL = [0, 200, 400, 600, 800, 999]
LEAGUE = ["Бронза", "Серебро", "Золото", "Платина", "Алмаз", "Легенда"]
CREATEGROUPLEAGUES = [6, 7, 8, 9, 9, 9]
CMDLEAGUES = [10, 12, 15, 19, 19, 19]

CONTACT_ADMIN = "https://vk.com/andrey_mala"


def SETTINGS():
    return {
        "main": {
            "kickInvitedByNoAccess": 1,
            "kickLeaving": 1,
            "deleteAccessAndNicknameOnLeave": 0,
            "disallowPings": 0,
            "disallowStickers": 0,
            "nightmode": 0,
            "welcome": 0,
            "captcha": 0,
            "autodelete": 0,
        },
        "entertaining": {
            "allowDuel": 1,
            "allowGuess": 1,
            "allowTransfer": 1,
            "allowAnon": 1,
        },
        "antispam": {
            "messagesPerMinute": 0,
            "maximumCharsInMessage": 0,
            "disallowLinks": 0,
            "disallowNSFW": 0,
            "vkLinks": 0,
            "forwardeds": 0,
        },
        "protect": {"enable": 0},
    }


def SETTINGS_ALT():
    return {
        "main": {
            "welcome": 0,
        },
        "entertaining": {},
        "antispam": {
            "messagesPerMinute": 1,
            "maximumCharsInMessage": 1,
            "vkLinks": 1,
            "forwardeds": 1,
        },
        "protect": {},
    }


SETTINGS_POSITIONS = {
    "main": {
        "kickInvitedByNoAccess": ["Выкл.", "Вкл."],
        "kickLeaving": ["Выкл.", "Вкл."],
        "deleteAccessAndNicknameOnLeave": ["Выкл.", "Вкл."],
        "disallowPings": ["Выкл.", "Вкл."],
        "disallowStickers": ["Выкл.", "Вкл."],
        "nightmode": ["Выкл.", "Вкл."],
        "welcome": ["Выкл.", "Вкл."],
        "captcha": ["Выкл.", "Вкл."],
        "autodelete": ["Выкл.", "Вкл."],
    },
    "entertaining": {
        "allowDuel": ["Выкл.", "Вкл."],
        "allowGuess": ["Выкл.", "Вкл."],
        "allowTransfer": ["Выкл.", "Вкл."],
        "allowAnon": ["Выкл.", "Вкл."],
    },
    "antispam": {
        "messagesPerMinute": ["Выкл.", "Вкл."],
        "maximumCharsInMessage": ["Выкл.", "Вкл."],
        "disallowLinks": ["Выкл.", "Вкл."],
        "disallowNSFW": ["Выкл.", "Вкл."],
        "vkLinks": ["Выкл.", "Вкл."],
        "forwardeds": ["Выкл.", "Вкл."],
    },
    "protect": {
        "enable": ["Выкл.", "Вкл."],
    },
}
SETTINGS_COUNTABLE = [
    "messagesPerMinute",
    "maximumCharsInMessage",
    "disallowLinks",
    "disallowNSFW",
    "vkLinks",
    "forwardeds",
    "nightmode",
    "welcome",
    "captcha",
    "autodelete",
]
SETTINGS_COUNTABLE_MULTIPLE_ARGUMENTS = ["nightmode", "welcome"]
SETTINGS_COUNTABLE_NO_PUNISHMENT = ["nightmode", "welcome", "autodelete"]
SETTINGS_COUNTABLE_NO_CATEGORY = ["nightmode", "welcome", "captcha", "autodelete"]
SETTINGS_COUNTABLE_PUNISHMENT_NO_DELETE_MESSAGE = ["messagesPerMinute", "captcha"]
SETTINGS_COUNTABLE_SPECIAL_LIMITS = {
    "captcha": range(1, 61),
    "autodelete": range(300, 86400),
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
        {"action": "turnalt", "button": ["Удаление сообщения", "Удаление сообщения"]},
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
        {"action": "turnalt", "button": ["Удаление сообщения", "Удаление сообщения"]},
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
    "vkLinks": [
        {"action": "turn", "button": ["Включить", "Выключить"]},
        {"action": "setPunishment", "button": "Наказание"},
        {"action": "turnalt", "button": ["Удаление сообщения", "Удаление сообщения"]},
        {"action": "setWhitelist", "button": "Исключения"},
    ],
    "forwardeds": [
        {"action": "turn", "button": ["Включить", "Выключить"]},
        {"action": "setPreset", "button": "Типы"},
        {"action": "setPunishment", "button": "Наказание"},
        {"action": "turnalt", "button": ["Удаление сообщения", "Удаление сообщения"]},
        {"action": "setWhitelist", "button": "Исключения"},
    ],
    "autodelete": [
        {"action": "turn", "button": ["Включить", "Выключить"]},
        {"action": "set", "button": "Время"},
    ],
}
SETTINGS_PRESET_BUTTONS = {
    "forwardeds": [
        {"value": 0, "name": "Все", "action": "setValue"},
        {"value": 1, "name": "Пользователи", "action": "setValue"},
        {"value": 2, "name": "Сообщества", "action": "setValue"},
    ],
}
SETTINGS_ALT_TO_DELETE = [
    "messagesPerMinute",
    "maximumCharsInMessage",
    "vkLinks",
    "forwardeds",
]
SETTINGS_SUBCATS = {
    "messagesPerMinute": "msgs",
    "maximumCharsInMessage": "msgs",
    "disallowLinks": "spam",
    "vkLinks": "spam",
    "forwardeds": "spam",
}

PREMMENU_DEFAULT = {"clear_by_fire": True, "border_color": None, "tagnotif": False}
PREMMENU_TURN = ["clear_by_fire", "tagnotif"]

SHOP_LOTS = {
    "xp": {
        500: {"cost": 180, "limit": 20},
        1000: {"cost": 340, "limit": 10},
        2500: {"cost": 800, "limit": 5},
        5000: {"cost": 1500, "limit": 3},
        10000: {"cost": 2800, "limit": 2},
    },
    "bonuses": {
        "Купить 2x опыта (3 дня)": {"active_for": 3 * 86400, "cost": 1200, "type": "xp_booster", "name": "2x опыта (3 дня)"},
        "Купить 2х опыта (7 дней)": {"active_for": 7 * 86400, "cost": 3000, "type": "xp_booster", "name": "2x опыта (7 дней)"},
        "Убрать комиссию (30 дней)": {"active_for": 30 * 86400, "cost": 10000, "type": "comission_removal", "name": "убрать комиссию (30 дней)"},
    },
}

FARM_CD = 7200  # in seconds
FARM_POST_ID = int(config["SERVICE"]["FARM_POST_ID"])

PREMIUM_BONUS_POST_ID = int(config["SERVICE"]["PREMIUM_BONUS_POST_ID"])
PREMIUM_BONUS_DAYS = 5

NSFW_CATEGORIES = [
    "BUTTOCKS_EXPOSED",
    "FEMALE_BREAST_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "ANUS_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
]

IMPORTSETTINGS_DEFAULT = {
    "sys": True,
    "acc": True,
    "nicks": True,
    "punishes": True,
    "binds": False,
}

api = API(VK_TOKEN_GROUP)
implicitapi = API(VK_TOKEN_IMPLICIT_FLOW)
vk_api_session = vk_api.VkApi(token=VK_TOKEN_GROUP, api_version="5.199")
service_vk_api_session = vk_api.VkApi(token=VK_SERVICE_TOKEN, api_version="5.199")

USER = config["DATABASE"]["USER"]
PASSWORD = config["DATABASE"]["PASSWORD"]
DATABASE = config["DATABASE"]["DATABASE"]
DATABASE_HOST = config["DATABASE"]["DATABASE_HOST"]
DATABASE_PORT = config["DATABASE"]["DATABASE_PORT"]
DATABASE_STR = (
    f"postgresql://{USER}:{PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE}"
)

TG_TOKEN = config["TELEGRAM"]["TG_TOKEN"]
TG_BOT_USERNAME = config["TELEGRAM"]["TG_BOT_USERNAME"]
TG_CHAT_ID = config["TELEGRAM"]["TG_CHAT_ID"]
TG_BACKUP_THREAD_ID = config["TELEGRAM"]["TG_BACKUP_THREAD_ID"]
TG_PREMIUM_THREAD_ID = config["TELEGRAM"]["TG_PREMIUM_THREAD_ID"]
TG_NEWCHAT_THREAD_ID = config["TELEGRAM"]["TG_NEWCHAT_THREAD_ID"]
TG_TRANSFER_THREAD_ID = config["TELEGRAM"]["TG_TRANSFER_THREAD_ID"]
TG_SHOP_THREAD_ID = config["TELEGRAM"]["TG_SHOP_THREAD_ID"]
TG_AUDIO_THREAD_ID = config["TELEGRAM"]["TG_AUDIO_THREAD_ID"]
TG_BONUS_THREAD_ID = config["TELEGRAM"]["TG_BONUS_THREAD_ID"]
TG_DUEL_THREAD_ID = config["TELEGRAM"]["TG_DUEL_THREAD_ID"]
TG_PUBLIC_CHAT_ID = config["TELEGRAM"]["TG_PUBLIC_CHAT_ID"]
TG_PUBLIC_GIVEAWAY_THREAD_ID = config["TELEGRAM"]["TG_PUBLIC_GIVEAWAY_THREAD_ID"]
TG_API_HASH = config["TELEGRAM"]["TG_API_HASH"]
TG_API_ID = config["TELEGRAM"]["TG_API_ID"]

YOOKASSA_MERCHANT_ID = int(config["YOOKASSA"]["YOOKASSA_MERCHANT_ID"])
YOOKASSA_TOKEN = config["YOOKASSA"]["YOOKASSA_TOKEN"]

YANDEX_TOKEN = config["YANDEX"]["TOKEN"]

GOOGLE_TOKEN = config["GOOGLE"]["TOKEN"]
GOOGLE_THREATS = {
    "MALWARE": "вредоносное ПО",
    "SOCIAL_ENGINEERING": "социальная инженерия",
    "THREAT_TYPE_UNSPECIFIED": "тип угрозы не указан",
    "UNWANTED_SOFTWARE": "нежелательное ПО",
    "POTENTIALLY_HARMFUL_APPLICATION": "потенциально вредоносное приложение",
}

PREMIUM_COST = {30: 99, 90: 249, 180: 499}
data = {
    "email": config["SOCIALS"]["email"],
    "vk": config["SOCIALS"]["vk"],
    "vk_contact": config["SOCIALS"]["vk"].replace(".com", ".me"),
    "vk_preminfo": config["SOCIALS"]["vk_preminfo"],
    "tg": config["SOCIALS"]["tg"],
    "high": f"{PREMIUM_COST[180]}",
    "medium": f"{PREMIUM_COST[90]}",
    "low": f"{PREMIUM_COST[30]}",
    "premiumchat": "199",
}
