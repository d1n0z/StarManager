from vk_api import vk_api
from vkbottle import API

VK_TOKEN_GROUP = 'vk1.a.sy4kF7qjJVCY0gW0SXq8PONiOOVMo5Z_mkKCDt7wkGZR522poe45kFJuX0p74eiqYXFofGEtOBmrC71NAWxsMtEi0OPyOOqeDWnipkrdfkMm9IEWiBii_7Ba92eHgInZqP9HKQW2EWx4G5LE9wjz2peyUmi7YUyb94SpNXRFWjlpAV-rV3cJ5exgVLmrc7gIuRjjr83Jy-7HP3f-ANSEzw'  # NOQA
# VK_TOKEN_GROUP = 'vk1.a.dhOHo6AGo1f6lp0gFKNxMfjmfYYtiL9oTx1JjQSQXUH9OFdXqKW0jjaXS7stEQpvesgDh5474e7o_12GOGB2HKSLq77EDl6vusPKtOK2R1zsd2XphG745MKVXvzCcXPQqtRrGwEkRwbRhN9UtHTOOharzyGGqh0CMC8r-IE3-ZpaNt9CdwbZaEaEgYcxo02aVdhJb0L8GwLKzt6XRIlA2w'  # NOQA
GROUP_ID = 222139436
# GROUP_ID = 221799601
VK_TOKEN_IMPLICIT_FLOW = 'vk1.a.tH-LdK3dufQPKEcdcaG8v0SbanerIgwsbk6_4yCLrN1kAc5Vx1I_knKKVSSe-5IYxbTCSJFljzCwpsUGAq00o6aTtqvVn97c4gmaxucRSZUlLaoCbXxBdO8csqKuJKb7mLbX8yVLW5cwcvrDiulrgMAArIZ8P56yAqpLsXai3Y0rqLj_dRKMgk4LzHZdn5wZ'  # NOQA
VK_APP_ID = '51888124'
VK_APP_SECRET = 'xrcHBQwXLeRQAKGoSifl'

LVL_NAMES = ["Обычный Пользователь", "Смотрящий", "Модератор", "Старший Модератор", "Администратор",
             "Спец администратор", "Руководитель", "Владелец", "DEV"]

COMMANDS = {"start": 0, "help": 0, "id": 0, "stats": 0, "report": 0, "mtop": 0, "q": 0, "premium": 0, "bonus": 0,
            "transfer": 0, "rewards": 0, "duel": 0, "cmd": 0, "resetcmd": 0, "cmdlist": 0, "premmenu": 0, "test": 0,
            "addprefix": 0, "delprefix": 0, "getdev": 0, "listprefix": 0, "task": 0, "kick": 1, "mute": 1, "warn": 1,
            "usermute": 1, "userwarn": 1, "clear": 1, "staff": 1, "olist": 1, "snick": 1, "rnick": 1, "nlist": 1,
            "getnick": 1, "mkick": 1, "unmute": 2, "unwarn": 2, "mutelist": 2, "warnlist": 2, "setaccess": 2,
            "delaccess": 2, "ban": 3, "unban": 3, "userban": 3, "kickmenu": 3, "banlist": 3, "timeout": 3, "zov": 3,
            "inactive": 3, "gkick": 4, "gban": 4, "gunban": 4, "gmute": 4, "gunmute": 4, "gwarn": 4, "gunwarn": 4,
            "gsnick": 4, "grnick": 4, "gzov": 4, "welcome": 4, "delwelcome": 4, "skick": 5, "sban": 5, "sunban": 5,
            "ssnick": 5, "srnick": 5, "szov": 5, "chat": 5, "demote": 6, "gsetaccess": 6, "resetnick": 6,
            "resetaccess": 6, "gdelaccess": 6, "ssetaccess": 6, "sdelaccess": 6, "chatlimit": 6, "notif": 6,
            "ignore": 6, "unignore": 6, "ignorelist": 6, "mygroups": 7, "creategroup": 7, "delgroup": 7, "levelname": 7,
            "resetlevel": 7, "async": 7, "delasync": 7, "bind": 7, "unbind": 7, "addfilter": 7, "delfilter": 7,
            "filterlist": 7, "gaddfilter": 7, "gdelfilter": 7, "listasync": 7, "editlevel": 7, "giveowner": 7,
            "settings": 7, "botinfo": 8, "msg": 8, "blacklist": 8, "addblack": 8, "delblack": 8, "setstatus": 8,
            "delstatus": 8, "statuslist": 8, "cmdcount": 8, "infban": 8, "infunban": 8, "getlink": 8, "backup": 8,
            "gps": 8, "checkleaved": 8, "reportwarn": 8, "reboot": 8, "sudo": 8, "givexp": 8, "reimport": 8,
            "resetlvl": 8, "getuserchats": 8, "getchats": 8, "helpdev": 8, "inflist": 8}
COMMANDS_DESC = {
    "task": "/task - Открыть меню заданий.",
    "kick": "/kick - Исключить пользователя.",
    "mute": "/mute - Заблокировать чат пользователю.",
    "warn": "/warn - Выдать предупреждение пользователю.",
    "usermute": "/usermute - История мутов пользователя.",
    "userwarn": "/userwarn - История предупреждений пользователя.",
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
    "userban": "/userban - История блокировок пользователя.",
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
    "welcome": "/welcome - Приветственное сообщение в беседе.",
    "delwelcome": "/delwelcome - Удалить приветственное сообщение.",
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
    "test": "/test - Узнать ID беседы.",
}

REPORT_TO = 3767
REPORT_CD = 300  # cooldown in seconds

BACKUPS_TO = 1842

NEWSEASON_REWARDS = [60, 45, 30, 15, 10, 7, 7, 7, 7, 7]

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

DEVS = [746110579, 697163236]
ADMINS = [697163236, 746110579]
MAIN_DEV = [746110579]
DEVS_COLOR = {746110579: (0, 255, 166), 697163236: (255, 0, 0)}

PREFIX = ["/", "!", ".", "+"]

PATH = "/root/StarManager/"

GWARN_TIME_LIMIT = 10
GWARN_PUNISHMENT = 10  # in seconds
GWARN_PUNISHMENTS_NAMES = ["5 минут", "30 минут", "48 часов", "30 дней"]

SETTINGS_STANDARD = {"setKick": 1, "setDuel": 1}

TASKS = []

FARM_CD = 7200  # in seconds
FARM_POST_ID = 110

PREMIUM_BONUS_POST_ID = 5592
PREMIUM_BONUS_DAYS = 5


def PREMIUM_BONUS_POST_WORKS_TIL():
    import datetime
    return datetime.datetime(year=2024, month=2, day=17).timestamp()


IMPLICIT_API = API(VK_TOKEN_IMPLICIT_FLOW)
API = API(VK_TOKEN_GROUP)
VK_API_SESSION = vk_api.VkApi(token=VK_TOKEN_GROUP, api_version='5.199')

PREMIUM_COST = {30: 99, 90: 249, 180: 499}

USER = "root"
PASSWORD = "7yjWb1ibIlwZW774TrY1NAFW7NGNYTxVtZzVkDTh6kQM12DHm1"
DATABASE = "starmanager"

TG_TOKEN = "6424903839:AAGTvGiB7Yj-1BFttLzsnQFJbU-GtxZxMHE"
TG_CHAT_ID = "-1002113202615"
TG_FREEKASSA_THREAD_ID = "3"
TG_API_HASH = '4155bc2051e95121aa1d638eddb9766f'
TG_API_ID = '23280673'

YOOKASSA_MERCHANT_ID = 348801
YOOKASSA_TOKEN = 'live_6hOqxppErM_Pxb5sIt_PyKaI-6C4o0hYD_t0Et6tXrw'

MEGA_LOGIN = "vk.star.manager@gmail.com"
MEGA_PASSWORD = 'StarManagerpass2020'

data = {
    'email': 'vk.star.manager@gmail.com',
    'vk': 'https://vk.com/star_manager',
    'vk_preminfo': 'https://vk.cc/crO0a5',
    'tg': 'https://t.me/star_manager_news',
}
