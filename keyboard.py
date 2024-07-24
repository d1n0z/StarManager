from vkbottle import Keyboard, Callback, OpenLink, KeyboardButtonColor

from config.config import TASKS_LOTS


def join(chid):
    kb = Keyboard(inline=True)

    kb.add(Callback('Начать', {"cmd": "join", "chat_id": chid}), KeyboardButtonColor.POSITIVE)

    return kb.get_json()


def rejoin(chid):
    kb = Keyboard(inline=True)

    kb.add(Callback('Активировать', {"cmd": "rejoin", "chat_id": chid, "activate": 1}), KeyboardButtonColor.POSITIVE)
    kb.add(Callback('Не активировать', {"cmd": "rejoin", "chat_id": chid, "activate": 0}), KeyboardButtonColor.POSITIVE)

    return kb.get_json()


def stats(uid, id):
    kb = Keyboard(inline=True)

    kb.add(Callback('Блоки', {"cmd": "bans", "uid": uid, "sender": id}), KeyboardButtonColor.PRIMARY)
    kb.add(Callback('Варны', {"cmd": "warns", "uid": uid, "sender": id}), KeyboardButtonColor.PRIMARY)
    kb.add(Callback('Муты', {"cmd": "mutes", "uid": uid, "sender": id}), KeyboardButtonColor.PRIMARY)

    return kb.get_json()


def nlist(uid, page):
    kb = Keyboard(inline=True)

    kb.add(Callback('⏪', {"cmd": "prev_page_nlist", "page": page, "uid": uid}), KeyboardButtonColor.NEGATIVE)
    kb.add(Callback('Без ников', {"cmd": "nonicklist", "uid": uid}), KeyboardButtonColor.PRIMARY)
    kb.add(Callback('⏩', {"cmd": "next_page_nlist", "page": page, "uid": uid}), KeyboardButtonColor.POSITIVE)

    return kb.get_json()


def nnlist(uid, page):
    kb = Keyboard(inline=True)

    kb.add(Callback('⏪', {"cmd": "prev_page_nnlist", "page": page, "uid": uid}), KeyboardButtonColor.NEGATIVE)
    kb.add(Callback('С никами', {"cmd": "nicklist", "uid": uid}), KeyboardButtonColor.PRIMARY)
    kb.add(Callback('⏩', {"cmd": "next_page_nnlist", "page": page, "uid": uid}), KeyboardButtonColor.POSITIVE)

    return kb.get_json()


def mutelist(uid, page):
    kb = Keyboard(inline=True)

    kb.add(Callback('⏪', {"cmd": "prev_page_mutelist", "page": page, "uid": uid}), KeyboardButtonColor.NEGATIVE)
    kb.add(Callback('⏩', {"cmd": "next_page_mutelist", "page": page, "uid": uid}), KeyboardButtonColor.POSITIVE)

    return kb.get_json()


def warnlist(uid, page):
    kb = Keyboard(inline=True)

    kb.add(Callback('⏪', {"cmd": "prev_page_warnlist", "page": page, "uid": uid}), KeyboardButtonColor.NEGATIVE)
    kb.add(Callback('⏩', {"cmd": "next_page_warnlist", "page": page, "uid": uid}), KeyboardButtonColor.POSITIVE)

    return kb.get_json()


def banlist(uid, page):
    kb = Keyboard(inline=True)

    kb.add(Callback('⏪', {"cmd": "prev_page_banlist", "page": page, "uid": uid}), KeyboardButtonColor.NEGATIVE)
    kb.add(Callback('⏩', {"cmd": "next_page_banlist", "page": page, "uid": uid}), KeyboardButtonColor.POSITIVE)

    return kb.get_json()


def demote_choose(uid, chat_id):
    kb = Keyboard(inline=True)

    kb.add(Callback('Без прав', {"cmd": "demote", "uid": uid, "chat_id": chat_id, "option": "lvl"}),
           KeyboardButtonColor.PRIMARY)
    kb.add(Callback('Всех', {"cmd": "demote", "uid": uid, "chat_id": chat_id, "option": "all"}),
           KeyboardButtonColor.PRIMARY)

    return kb.get_json()


def demote_accept(uid, chat_id, option):
    kb = Keyboard(inline=True)

    kb.add(Callback('Да', {"cmd": "demote_accept", "uid": uid, "chat_id": chat_id, "option": option}),
           KeyboardButtonColor.POSITIVE)
    kb.add(Callback('Нет', {"cmd": "demote_disaccept", "uid": uid, "chat_id": chat_id}), KeyboardButtonColor.NEGATIVE)

    return kb.get_json()


def statuslist(uid, page):
    kb = Keyboard(inline=True)

    kb.add(Callback('⏪', {"cmd": "prev_page_mutelist", "page": page, "uid": uid}), KeyboardButtonColor.NEGATIVE)
    kb.add(Callback('⏩', {"cmd": "next_page_mutelist", "page": page, "uid": uid}), KeyboardButtonColor.POSITIVE)

    return kb.get_json()


def settings(uid, settings: dict):
    kb = Keyboard(inline=True)
    k = 0
    for e, i in settings.items():
        k += 1
        if i == 0:
            color = KeyboardButtonColor.NEGATIVE
        else:
            color = KeyboardButtonColor.POSITIVE
        kb.add(Callback(f'{k}', {"uid": uid, "cmd": "change_setting", "setting": f"{e}", "setting_pos": i,
                                 "settings": f"{settings}"}), color)

    return kb.get_json()


def premium():
    kb = Keyboard(inline=True)

    kb.add(OpenLink(label='Написать', link="https://vk.com/im?sel=697163236"))

    return kb.get_json()


def giveowner(chat_id, chid, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback('Да', {"cmd": "giveowner", "chat_id": chat_id, "uid": uid, "chid": chid}),
           KeyboardButtonColor.POSITIVE)
    kb.add(Callback('Нет', {"cmd": "giveowner_no", "chat_id": chat_id}), KeyboardButtonColor.NEGATIVE)

    return kb.get_json()


def mtop(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback('✨ Уровни', {"cmd": "top_lvls", "chat_id": chat_id, "uid": uid}))
    kb.add(Callback('⚔ Дуэли', {"cmd": "top_duels", "chat_id": chat_id, "uid": uid}))

    return kb.get_json()


def top_lvls(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback('◀ Назад', {"cmd": "mtop", "chat_id": chat_id, "uid": uid}), KeyboardButtonColor.NEGATIVE)
    kb.add(Callback('🥨 В беседе', {"cmd": "top_lvls_in_group", "chat_id": chat_id, "uid": uid}),
           KeyboardButtonColor.SECONDARY)

    return kb.get_json()


def top_lvls_in_group(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback('◀ Назад', {"cmd": "mtop", "chat_id": chat_id, "uid": uid}), KeyboardButtonColor.NEGATIVE)
    kb.add(Callback('🥯 Общее', {"cmd": "top_lvls", "chat_id": chat_id, "uid": uid}), KeyboardButtonColor.SECONDARY)

    return kb.get_json()


def top_duels(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback('◀ Назад', {"cmd": "mtop", "chat_id": chat_id, "uid": uid}), KeyboardButtonColor.NEGATIVE)
    kb.add(Callback('🥨 В беседе', {"cmd": "top_duels_in_group", "chat_id": chat_id, "uid": uid}),
           KeyboardButtonColor.SECONDARY)

    return kb.get_json()


def top_duels_in_group(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback('◀ Назад', {"cmd": "mtop", "chat_id": chat_id, "uid": uid}), KeyboardButtonColor.NEGATIVE)
    kb.add(Callback('🥯 Общее', {"cmd": "top_duels", "chat_id": chat_id, "uid": uid}), KeyboardButtonColor.SECONDARY)

    return kb.get_json()


def premmenu(uid, settings):
    kb = Keyboard(inline=True)

    k = 0
    for e, i in settings.items():
        k += 1
        if i:
            color = KeyboardButtonColor.POSITIVE
        else:
            color = KeyboardButtonColor.NEGATIVE
        kb.add(Callback(f'{k}', {"uid": uid, "cmd": f"{e}", "setting": i}), color)

    return kb.get_json()


def pm_market():
    kb = Keyboard(inline=True)

    kb.add(OpenLink(label='Купить', link='https://star-manager.ru'), KeyboardButtonColor.POSITIVE)

    return kb.get_json()


def duel(uid, xp):
    kb = Keyboard(inline=True)

    kb.add(Callback('Сразиться', {'cmd': 'duel', 'uid': uid, 'xp': xp}), KeyboardButtonColor.SECONDARY)

    return kb.get_json()


def resetnick_accept(uid, chat_id):
    kb = Keyboard(inline=True)

    kb.add(Callback('Да', {"cmd": "resetnick_accept", "uid": uid, "chat_id": chat_id}), KeyboardButtonColor.POSITIVE)
    kb.add(Callback('Нет', {"cmd": "resetnick_disaccept", "uid": uid, "chat_id": chat_id}),
           KeyboardButtonColor.NEGATIVE)

    return kb.get_json()


def resetaccess_accept(uid, chat_id, lvl):
    kb = Keyboard(inline=True)

    kb.add(Callback('Да', {"cmd": "resetaccess_accept", "uid": uid, "chat_id": chat_id, "lvl": lvl}),
           KeyboardButtonColor.POSITIVE)
    kb.add(Callback('Нет', {"cmd": "resetaccess_disaccept", "uid": uid, "chat_id": chat_id, "lvl": lvl}),
           KeyboardButtonColor.NEGATIVE)

    return kb.get_json()


def report(uid, repid, chat_id, text):
    kb = Keyboard(inline=True)

    kb.add(Callback('Ответить', {"cmd": "answer_report", "uid": uid, "chat_id": chat_id, "repid": repid, "text": text}),
           KeyboardButtonColor.POSITIVE)
    kb.add(Callback('Варн', {"cmd": "warn_report", "uid": uid, "chat_id": chat_id, "repid": repid}),
           KeyboardButtonColor.NEGATIVE)

    return kb.get_json()


def kickmenu(uid):
    kb = Keyboard(inline=True)

    kb.add(Callback('Исключить без ников', {"cmd": "kick_nonick", "sender": uid, "uid": uid}),
           KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Callback('Исключить с никами', {"cmd": "kick_nick", "sender": uid, "uid": uid}), KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Callback('Исключить удалённых', {"cmd": "kick_banned", "sender": uid, "uid": uid}),
           KeyboardButtonColor.PRIMARY)

    return kb.get_json()


def rewards(uid):
    kb = Keyboard(inline=True)

    kb.add(Callback('Обновить', {"cmd": "refresh_rewards", "sender": uid, "uid": uid}), KeyboardButtonColor.POSITIVE)

    return kb.get_json()


def notif(uid):
    kb = Keyboard(inline=True)

    kb.add(Callback('Напоминания беседы', {"cmd": "notif", "sender": uid, "uid": uid}), KeyboardButtonColor.POSITIVE)

    return kb.get_json()


def notif_list(uid, notifs, page=1):
    kb = Keyboard(inline=True)
    kx = 4
    ttlx = 0
    ppgg = (page * 8) - 8
    if page > 1:
        ppgg += 1
        kb.add(Callback(f'<<', payload={"cmd": "notif", "page": page - 1, "uid": uid, "sender": uid}))
        kx -= 1
        ttlx -= 1
    if len(notifs) > 8 * page:
        kb.add(Callback(f'>>', payload={"cmd": "notif", "page": page + 1, "uid": uid, "sender": uid}))
        kx -= 1
        ttlx -= 1
    notifs = notifs[ppgg:]

    for k, i in enumerate(notifs):
        if i.status == 1:
            c = KeyboardButtonColor.POSITIVE
        else:
            c = KeyboardButtonColor.NEGATIVE
        kb.add(Callback(f'{k + 1 + ppgg}', {"cmd": "notif_select", "sender": uid, "uid": uid, "name": i.name}), c)
        if k == kx:
            kb.row()
        if k + 1 == 10 + ttlx:
            break

    return kb.get_json()


def notification(uid, status, name):
    kb = Keyboard(inline=True)

    kb.add(Callback('Назад', {"cmd": "notif", "sender": uid, "uid": uid}), KeyboardButtonColor.NEGATIVE)
    if status == 1:
        kb.add(
            Callback('Выключить', {"cmd": "notification_status", "sender": uid, "uid": uid, "turn": 0, "name": name}),
            KeyboardButtonColor.NEGATIVE)
    else:
        kb.add(Callback('Включить', {"cmd": "notification_status", "sender": uid, "uid": uid, "turn": 1, "name": name}),
               KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Callback('Текст', {"cmd": "notification_text", "sender": uid, "uid": uid, "name": name}),
           KeyboardButtonColor.SECONDARY)
    kb.add(Callback('Время', {"cmd": "notification_time", "sender": uid, "uid": uid, "name": name}),
           KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Callback('Теги', {"cmd": "notification_tag", "sender": uid, "uid": uid, "name": name}),
           KeyboardButtonColor.SECONDARY)
    kb.add(Callback('Удалить', {"cmd": "notification_delete", "sender": uid, "uid": uid, "name": name}),
           KeyboardButtonColor.NEGATIVE)

    return kb.get_json()


def notification_Callback(uid, name):
    kb = Keyboard(inline=True)

    kb.add(Callback(f'Назад', {"cmd": "notif_select", "sender": uid, "uid": uid, "name": name}),
           KeyboardButtonColor.NEGATIVE)

    return kb.get_json()


def notification_time(uid, name):
    kb = Keyboard(inline=True)

    kb.add(Callback(f'Назад', {"cmd": "notif_select", "sender": uid, "uid": uid, "name": name}),
           KeyboardButtonColor.NEGATIVE)
    kb.add(Callback('Один раз',
                    {"cmd": "notification_time_change", "sender": uid, "uid": uid, "name": name, "type": "single"}),
           KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Callback('Каждый день',
                    {"cmd": "notification_time_change", "sender": uid, "uid": uid, "name": name, "type": "everyday"}),
           KeyboardButtonColor.SECONDARY)
    kb.add(Callback('Каждые XX минут',
                    {"cmd": "notification_time_change", "sender": uid, "uid": uid, "name": name, "type": "everyxmin"}),
           KeyboardButtonColor.SECONDARY)

    return kb.get_json()


def notification_tag(uid, name):
    kb = Keyboard(inline=True)

    kb.add(Callback(f'Назад', {"cmd": "notif_select", "sender": uid, "uid": uid, "name": name}),
           KeyboardButtonColor.NEGATIVE)
    kb.row()
    kb.add(
        Callback('Отключить', {"cmd": "notification_tag_change", "sender": uid, "uid": uid, "name": name, "type": "1"}),
        KeyboardButtonColor.SECONDARY)
    kb.add(Callback('Всех', {"cmd": "notification_tag_change", "sender": uid, "uid": uid, "name": name, "type": "2"}),
           KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(
        Callback('С правами', {"cmd": "notification_tag_change", "sender": uid, "uid": uid, "name": name, "type": "3"}),
        KeyboardButtonColor.SECONDARY)
    kb.add(
        Callback('Без прав', {"cmd": "notification_tag_change", "sender": uid, "uid": uid, "name": name, "type": "4"}),
        KeyboardButtonColor.SECONDARY)

    return kb.get_json()


def listasync(uid, total, page=1):
    kb = Keyboard(inline=True)

    if page > 1:
        kb.add(Callback('<<', payload={"cmd": "listasync", "sender": uid, "uid": uid, "page": page - 1}))
    if total > page * 10:
        kb.add(Callback('>>', payload={"cmd": "listasync", "sender": uid, "uid": uid, "page": page + 1}))

    return kb.get_json()


def help(uid, page=0, u_prem=0):
    kb = Keyboard(inline=True)
    colors = []
    for i in range(0, 8):
        if i == page:
            colors.append(KeyboardButtonColor.POSITIVE)
        else:
            colors.append(KeyboardButtonColor.SECONDARY)
    if not u_prem:
        colors.append(KeyboardButtonColor.NEGATIVE)
    elif page == 8:
        colors.append(KeyboardButtonColor.POSITIVE)
    else:
        colors.append(KeyboardButtonColor.SECONDARY)

    kb.add(Callback('Уровень 0', {"cmd": "help", "uid": uid, "page": 0, "prem": u_prem}), colors[0])
    kb.add(Callback('Уровень 1', {"cmd": "help", "uid": uid, "page": 1, "prem": u_prem}), colors[1])
    kb.row()
    kb.add(Callback('Уровень 2', {"cmd": "help", "uid": uid, "page": 2, "prem": u_prem}), colors[2])
    kb.add(Callback('Уровень 3', {"cmd": "help", "uid": uid, "page": 3, "prem": u_prem}), colors[3])
    kb.row()
    kb.add(Callback('Уровень 4', {"cmd": "help", "uid": uid, "page": 4, "prem": u_prem}), colors[4])
    kb.add(Callback('Уровень 5', {"cmd": "help", "uid": uid, "page": 5, "prem": u_prem}), colors[5])
    kb.row()
    kb.add(Callback('Уровень 6', {"cmd": "help", "uid": uid, "page": 6, "prem": u_prem}), colors[6])
    kb.add(Callback('Уровень 7', {"cmd": "help", "uid": uid, "page": 7, "prem": u_prem}), colors[7])
    kb.row()
    kb.add(Callback('Premium', {"cmd": "help", "uid": uid, "page": 8, "prem": u_prem}), colors[8])

    return kb.get_json()


def warn_report(uid, uwarns):
    kb = Keyboard(inline=True)

    kb.add(Callback('💚 Убрать 1 варн', {"cmd": "unwarn_report", "uid": uid, "warns": uwarns}))
    kb.row()
    kb.add(Callback('💛 Убрать 2 варна', {"cmd": "unwarn_report", "uid": uid, "warns": uwarns}))
    kb.row()
    kb.add(Callback('❤ Убрать 3 варна', {"cmd": "unwarn_report", "uid": uid, "warns": uwarns}))

    return kb.get_json()


def cmd(uid, page=0):
    kb = Keyboard(inline=True)

    kb.add(Callback('Мои ассоциации', {"cmd": "cmdlist", "uid": uid, "page": page}))

    return kb.get_json()


def cmdlist(uid, page, cmdslen):
    kb = Keyboard(inline=True)

    if page > 0:
        kb.add(Callback('<<', {"cmd": "cmdlist", "uid": uid, "page": page - 1}))
    if cmdslen > (10 * page) + 10:
        kb.add(Callback('>>', {"cmd": "cmdlist", "uid": uid, "page": page + 1}))

    return kb.get_json()


def tasks(uid):
    kb = Keyboard(inline=True)

    kb.add(Callback('Обмен', {"cmd": "task_trade", "uid": uid}), KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Callback('Еженедельные', {"cmd": "task_weekly", "uid": uid}))
    kb.add(Callback('Ежедневные', {"cmd": "task_daily", "uid": uid}))

    return kb.get_json()


def task_trade(uid, coins):
    kb = Keyboard(inline=True)

    kbdcolors = []
    for i in TASKS_LOTS.keys():
        kbdcolors.append(KeyboardButtonColor.NEGATIVE if coins < i else KeyboardButtonColor.POSITIVE)

    kb.add(Callback('Назад', {"cmd": "task", "uid": uid}))
    kb.row()
    kb.add(Callback('1', {"cmd": "task_trade_lot", "uid": uid, "lot": 1}), kbdcolors[0])
    kb.add(Callback('2', {"cmd": "task_trade_lot", "uid": uid, "lot": 2}), kbdcolors[1])
    kb.row()
    kb.add(Callback('3', {"cmd": "task_trade_lot", "uid": uid, "lot": 3}), kbdcolors[2])
    kb.add(Callback('4', {"cmd": "task_trade_lot", "uid": uid, "lot": 4}), kbdcolors[3])

    return kb.get_json()


def task_back(uid):
    kb = Keyboard(inline=True)

    kb.add(Callback('Назад', {"cmd": "task", "uid": uid}))

    return kb.get_json()


def gps(uid):
    kb = Keyboard(inline=True)

    kb.add(Callback('test', {"cmd": "test", "uid": uid}))

    return kb.get_json()


def check(uid, id):
    kb = Keyboard(inline=True)

    kb.add(Callback('Блокировки', {"cmd": "check", "uid": uid, "id": id, "check": "ban"}))
    kb.add(Callback('Предупреждения', {"cmd": "check", "uid": uid, "id": id, "check": "warn"}))
    kb.add(Callback('Муты', {"cmd": "check", "uid": uid, "id": id, "check": "mute"}))

    return kb.get_json()


def check_history(uid, id, punishment, isempty):
    kb = Keyboard(inline=True)

    kb.add(Callback('История', {"cmd": "check_history", "uid": uid, "id": id, "check": punishment, "ie": isempty}))

    return kb.get_json()
