import calendar
import time
import traceback
from ast import literal_eval
from datetime import datetime

from Bot.utils import getUserNickname, pointMinutes, pointDays, pointHours
from config.config import COMMANDS, LVL_NAMES, COMMANDS_DESC, TASKS_LOTS, TASKS_DAILY, PREMIUM_TASKS_DAILY, \
    PREMIUM_TASKS_DAILY_TIERS, TASKS_WEEKLY, PREMIUM_TASKS_WEEKLY
from db import AccessNames


def join():
    return '''📢 Привет! Для начала работы, нужно выдать боту администратора и нажать Начать'''


def rejoin():
    return '''📢 В данной беседе уже имеются сохранённые настройки, вы хотите чтобы я активировал их?'''


def rejoin_activate():
    return '''✅ Данные успешно восстановлены, Вы подключили бота к беседе! Чтобы узнать подробности напишите /help'''


def start():
    return '''🎉 Вы подключили бота к беседе! Чтобы узнать подробности напишите /help'''


def id(uid, data, name, url):
    return f"📗 Краткая информация о [id{uid}|{name}]\n\n" \
           f"🆔 ID Вконтакте: {uid}\n" \
           f"🔗 Оригинальная ссылка: {url}\n" \
           f"📅 Зарегистрирован: {data}"


def mtop(res, names):
    msg = '⭐ TOP 10 пользователей по сообщениям\n\n'
    for index, item in enumerate(res):
        try:
            name = f"{names[index].first_name} {names[index].last_name}"
            addmsg = f"[{index + 1}]. [id{names[index].id}|{name}] - {item.messages} сообщений\n"
            if addmsg not in msg:
                msg += addmsg
        except:
            pass
    return msg


def stats(uid, name, u_msgs, u_nickname, date, u_last_message, u_warns, joined, mute, ban,
          last_mute_admin, last_mute_reason, last_ban_admin, last_ban_reason, ref, lvl_name):
    if u_nickname is None or u_nickname == '':
        u_nickname = 'Отсутствует'

    if ref is None:
        ref = "По ссылке"

    msg = f"""🌐 Подробная информация - [id{uid}|{name}]

👑 Уровень прав: {lvl_name}
🔱 Установленный ник: {u_nickname}
💌 Сообщений отправлено: {u_msgs}

📅 Дата регистрации: {date}
🚀 Последняя активность: {u_last_message}
🕘 Присоединился к беседе: {joined}"""
    if ref is not None:
        msg += f'\n👤 Пригласил: {ref}\n\n'
    else:
        msg += '\n\n'

    if u_warns > 0:
        msg += f"⛔ Предупреждение: {u_warns} / 3\n"
    if mute > 0 and int((mute - time.time()) / 60) + 1 > 0:
        msg += f"⛔ Блокировка чата: {int((mute - time.time()) / 60) + 1} минут | {last_mute_admin} | " \
               f"{last_mute_reason}\n"
    if ban > 0 and int((ban - time.time()) / 86400) + 1 > 0:
        msg += f"⛔ Блокировка в беседе: {int((ban - time.time()) / 86400) + 1} дней | {last_ban_admin} | " \
               f"{last_ban_reason}"
    return msg


def help(page=0, cmds=COMMANDS):
    if page == 8:
        return '''⭐️ Команды Premium пользователей

/premmenu - Меню премиум возможностей.
/mkick - Исключить сразу несколько пользователей.
/editlevel - Изменить уровень прав для команд.
/levelname - Изменить название для уровней прав.
/resetlevel - Восстановить стандартное название уровней прав.
/addprefix - Добавить персональный префикс для команд.
/delprefix - Удалить персональный префикс для команд.
/listprefix - Список персональных префиксов.
/ignore - Добавить пользователя в игнор бота.
/unignore - Удалить пользователя из игнор бота.
/ignorelist - Список игнорируемых пользователей ботом.
/chatlimit - Установить медленный режим в чате.

💬 Для подробного ознакомления с командами и возможностей Premium перейдите в статью - vk.cc/crO08V'''

    descs = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []}
    # print(cmds)
    for k, i in cmds.items():
        try:
            descs[int(i)].append(COMMANDS_DESC[k])
        except:
            pass  # traceback.print_exc()
    # print(descs)
    msg = None
    if page == 0:
        msg = f'⭐️ Команды пользователя\n\n'
    if page == 1:
        msg = f'⭐️ Команды следящего\n'
    if page == 2:
        msg = f'⭐️ Команды модератора\n'
    if page == 3:
        msg = f'⭐️ Команды старшего модератора\n'
    if page == 4:
        msg = f'⭐️ Команды администратора\n'
    if page == 5:
        msg = f'⭐️ Команды спец администратора\n'
    if page == 6:
        msg = f'⭐️ Команды руководителя\n'
    if page == 7:
        msg = f'⭐️ Команды владельца\n'
    # print(page)
    for i in descs[page]:
        msg += f'{i}\n'
    # print(descs[page])
    msg += '\n💬 Для подробного ознакомления с командами перейдите в статью - vk.cc/crO08V'
    return msg


def helpdev():
    return '''⭐️ Команды DEV\n
/botinfo - инфа по боту(не работает)
/msg - отправляет сообщения во все беседы, в консоли пишет прогресс
/blacklist - список челов в бл
/addblack - добавляет в бл
/delblack - удаляет с бл
/setstatus - УСТАНАВЛИВАЕТ премиум на кол-во дней
/delstatus - удаляет премиум
/statuslist - список челов с премиум
/cmdcount - топ по командам(не работает)
/inflist - список бесконечно забаненных
/infban - бесконечный бан челу или беседе
/infunban - анбан чела или беседы
/getlink - отправляет ссылку на беседу
/backup - создаёт бэкап 
/reportwarn - варн репорту
/reboot - перезагружает сервер
/sudo - отправляет команду "sudo ..." на сервер
/givexp - выдает опыт
/resetlvl - удаляет опыт и монетки
/getuserchats - топ чатов пользователя по сообщениям
/getchats - топ всех чатов по сообщениям
/gettransferhistoryto - показывает историю переводов пользователю
/gettransferhistoryfrom - показывает историю переводов пользователя
/gettransferhistory - показывает общую историю переводов пользователя
/helpdev - команды DEV'''


def help_closed():
    return '⚠ Я не могу писать вам сообщения, отправьте мне в личные сообщения "Начать" и введите команду снова.'


def help_sent(id, name, nick):
    if nick is not None:
        n = nick
    else:
        n = name
    return f'✅ [id{id}|{n}], вам был отправлен список команд в личные сообщения. '


def query_error():
    return '''❌ Ошибка в запросе'''


def report(uid, name, report, repid, chatid, chatname):
    return f'''🟣 Обращение #{repid}
🟣 Пользователь: [id{uid}|{name}]
🟣 Беседа: {chatid} | {chatname}

💬 Обращение:{report}'''


def report_cd():
    return f'🕒 Следующее обращение будет доступно через 5 минут.'


def report_answering(repid):
    return f'🟣 Введите ответ на обращение #{repid}'


def report_sent(rep_id):
    return f'📌 Обращение #{rep_id} было отправлено поддержке, ожидайте ответа в данном чате.'


def report_empty():
    return '👤 Для обращения в поддержку пожалуйста напишите /report TEXT. Затем ожидайте ответа.'


def report_answer(ansing_id, ansing_name, repid, ans, qusing_id, quesing_name):
    return f'''🔔 Ответ на обращение #{repid}
👤 Отправитель: [id{qusing_id}|{quesing_name}]
👤 Администратор: [id{ansing_id}|{ansing_name}]

💬 Ответ: {ans}'''


def report_answered(ansing_id, ansing_name, repid, ans, report, uid, name, chatid, chatname):
    return f'''🟣 Ответ на обращение #{repid}
🟣 Администратор: [id{ansing_id}|{ansing_name}]
🟣 Пользователь: [id{uid}|{name}]
🟣 Беседа: {chatid} | {chatname}

💬 Обращение: {report}
💬 Ответ: {ans}'''


def kick_hint():
    return '🔔 Чтобы исключить пользователя из чата, используйте /kick @VK Причина (Пример: /kick @andrey_mala Тест)'


def kick(u_name, u_nick, uid, ch_name, ch_nick, id, cause):
    if id < 0:
        i = 'club'
        id = abs(id)
    else:
        i = 'id'
    u_name = u_nick if u_nick is not None else u_name
    ch_name = ch_nick if ch_nick is not None else ch_name
    return f'💬 [id{uid}|{u_name}] исключил(-а) из беседы пользователя [{i}{id}|{ch_name}] по причине: "{cause}"'


def kick_error():
    return '⚠ Указанный пользователь не является участником данной беседы, либо же имеет статус выше Вашего. '


def kick_access(id, name, nick):
    if id < 0:
        i = 'club'
        id = abs(id)
    else:
        i = 'id'
    return (f'⚠ Не могу кикнуть пользователя [{i}{id}|{nick if nick is not None and len(nick) > 0 else name}] так как'
            f' у данного пользователя есть статус администратора беседы')


def kick_myself():
    return '📛Нельзя кикнуть самого себя'


def kick_higher():
    return '⛔Вы не можете кикнуть пользователя выше Ваших прав'


def mute_hint():
    return '🔔 Чтобы выдать пользователю блокировку чата введите /mute @VK time(в минутах) причина.' \
           ' (пример: /mute @andrey_mala 30 Тест)'


def mute(name, nick, id, mutingname, mutingnick, mutingid, cause, time):
    if cause != '':
        cause = ' по причине: ' + cause
    n = nick if nick is not None else name
    mn = mutingnick if mutingnick is not None else mutingname
    return f'💬  Пользователь [id{id}|{n}] выдал блокировку чата пользователю ' \
           f'- [id{mutingid}|{mn}] на {time} минут{cause}'


def mute_error():
    return '⚠ Указанный пользователь не является участником данной беседы, либо же имеет статус выше Вашего. '


def mute_myself():
    return '📛 Нельзя замутить самого себя'


def unmute_myself():
    return '📛 Нельзя размутить самого себя'


def mute_higher():
    return '⛔ Вы не можете замутить пользователя выше Ваших прав'


def access_dont_match():
    return '🔶 Недостаточно прав!'


def already_muted(name, nick, id, mute):
    time_left = int((mute - time.time()) / 60)
    n = nick if nick is not None else name
    return f"⚠ Пользователь [id{id}|{n}] уже имеет блокировку чата на {time_left} минут."


def usermutes(id, name, u_mutes_times, u_mutes_causes, u_mutes_names, u_mutes_dates, mute):
    msg = f"🌐 Информация о мутах - [id{id}|{name}]\n\n🟢 Всего получено мутов - {len(u_mutes_times)}"

    if mute > time.time():
        time_left = pointMinutes(mute)
        msg += f'🟢 Активный мут - {time_left} | {u_mutes_names[0]} | {u_mutes_causes[0]}'

    msg += "\n\n🛡 Последние 10 выданных мутов"

    if len(u_mutes_times) != 0:
        for index, item in enumerate(u_mutes_times):
            if index == 10:
                break
            msg += f'\n➖ {u_mutes_dates[index]} | {int(item / 60)} минут | ' \
                   f'{u_mutes_names[index]} | {u_mutes_causes[index]}'
    else:
        msg += '\n❗ Мутов не обнаружено'
    return msg


def userwarns(id, u_name, u_warns_times, u_warns_causes, u_warns_names, u_warns_dates, warns):
    msg = f"""🌐 Информация о варнах - [id{id}|{u_name}]

    🟢 Всего получено варнов - {warns}

    🛡 Последние 10 выданных варнов"""

    if len(u_warns_causes) != 0:
        for index, item in enumerate(u_warns_times):
            if index == 10:
                break
            msg += f'\n➖ {u_warns_dates[index]} | {u_warns_names[index]} | {u_warns_causes[index]}'
    else:
        msg += '\n❗ Варнов не обнаружено'
    return msg


def userbans(id, u_name, u_bans_times, u_bans_causes, u_bans_names, u_bans_dates, ban):
    msg = f"🌐 Информация о блокировки - [id{id}|{u_name}]\n\n🟢 Всего получено блокировок - {len(u_bans_times)}"

    if ban > time.time():
        time_left = pointDays(ban)
        msg += f'🟢 Активная блокировка - ' + f'{time_left} | {u_bans_names[0]} | {u_bans_causes[0]}'

    msg += "\n\n🛡 Последние 10 выданных блокировок"

    if len(u_bans_times) != 0:
        for index, item in enumerate(u_bans_times):
            if index == 10:
                break
            msg += f'\n➖ {u_bans_dates[index]} | {int(item / 86400)} дней | ' \
                   f'{u_bans_names[index]} | {u_bans_causes[index]}'
    else:
        msg += '\n❗Блокировок не обнаружено'
    return msg


def usermute_hint():
    return '🔔 Чтобы посмотреть информацию о мутах пользователя в беседе напишите /usermute @VK. (пример: /usermute ' \
           '@andrey_mala)'


def userwarn_hint():
    return '🔔 Чтобы посмотреть информацию о варнах пользователя в беседе напишите /userwarn @VK. (пример: /userwarn ' \
           '@andrey_mala)'


def warn_hint():
    return '🔔 Чтобы выдать пользователю предупреждение введите /warn @VK причина (пример: /warn @andrey_mala Тест)'


def warn(name, nick, uid, ch_name, ch_nick, id, cause):
    if cause != '':
        cause = ' по причине: ' + cause
    n = nick if nick is not None else name
    cn = ch_nick if ch_nick is not None else ch_name
    return f'💬  Пользователь [id{uid}|{n}] выдал варн пользователю - [id{id}|{cn}]{cause}'


def warn_kick(name, nick, uid, ch_name, ch_nick, id, cause):
    if cause != '':
        cause = ' по причине: ' + cause
    n = nick if nick is not None else name
    cn = ch_nick if ch_nick is not None else ch_name
    return f'💬  Пользователь [id{uid}|{n}] выдал последний варн пользователю ' \
           f'- [id{id}|{cn}]{cause}'


def warn_higher():
    return '⛔Вы не можете выдать варн пользователю выше Ваших прав'


def warn_myself():
    return '📛 Нельзя выдать варн самому себе'


def unwarn_myself():
    return '📛 Нельзя снять варн самому себе'


def clear(names, u_ids, u_name, uid):
    users = []
    for ind, item in enumerate(names):
        user = f"[id{u_ids[ind]}|{item}]"
        if user not in users:
            users.append(user)
    return f"[id{uid}|{u_name}] удалил сообщение от " + ", ".join(users) + "."


def clear_hint():
    return '🔔 Чтобы удалить сообщения перешлите или ответьте на них с командой (пример: /clear)'


def clear_higher():
    return '⛔Вы не можете удалить сообщения пользователя выше Ваших прав'


def clear_admin():
    return '⚠ Не могу удалить сообщение, поскольку пользователь является администратором беседы'


def snick_hint():
    return '🔔 Чтобы установить никнейм пользователю нужно ввести, /snick @VK nickname. (пример: /snick @andrey_mala ' \
           'Andrey_Mal)'


def snick_user_has_nick():
    return '⚠ У пользователя уже есть никнейм'


def snick_too_long_nickname():
    return '⚠ Никнейм не может содержать квадратные скобки("[]") и быть более чем 32 символа'


def snick_higher():
    return '⛔Вы не можете менять никнейм пользователя выше Ваших прав'


def snick(uid, u_name, u_nickname, id, ch_name, nickname, newnickname):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else ch_name
    return f'💬 Пользователь [id{uid}|{un}] установил новый ник [id{id}|{newnickname}] для пользователя - [id{id}|{n}].'


def rnick_hint():
    return '🔔 Чтобы удалить никнейм пользователю нужно ввести, /rnick @VK. (пример: /rnick @andrey_mala)'


def rnick_user_has_no_nick():
    return '⚠ У пользователя нет никнейма'


def rnick_higher():
    return '⛔Вы не можете удалить никнейм пользователя выше Ваших прав'


def rnick(uid, u_name, u_nick, id, name, nick):
    un = u_nick if u_nick is not None else u_name
    return f'💬 Пользователь [id{uid}|{un}] удалил ник [id{id}|{nick}] пользователю - [id{id}|{name}].'


def nlist(res, members, offset=0):
    msg = '💬 Список пользователей с никами\n\n'
    cnt = 0
    offcnt = 0
    for it in members:
        offcnt += 1
        if offcnt >= offset:
            if it.id >= 0 and it.first_name != 'DELETED' and it.last_name != 'DELETED':
                for item in res:
                    if it.id == item.uid:
                        cnt += 1
                        addmsg = f"{cnt + offset}. {item.nickname} - [id{item.uid}|{it.first_name} " \
                                 f"{it.last_name}]\n"
                        if addmsg not in msg:
                            msg += addmsg
        if cnt > 29:
            break
    return msg


def nnlist(members, page=0):
    msg = '💬 Список пользователей без ников\n\n'
    print(members)
    k = page * 30
    for i in members:
        try:
            if i.first_name != 'DELETED' and i.last_name != 'DELETED' and i.id > 0:
                addmsg = f"{k + 1}. [id{i.id}|{i.first_name} {i.last_name}]\n"
                if addmsg not in msg:
                    msg += addmsg
                    k += 1
        except:
            traceback.print_exc()
    return msg


async def staff(res, names, chat_id):
    msg = 'Список администраторов:\n\n'
    admins = {}
    included = []
    users = {'1': [], '2': [], '3': [], '4': [], '5': [], '6': [], '7': [], '8': []}
    for ind, item in enumerate(res[::-1]):
        x = {"uid": item.uid, "name": [f"{i.first_name} {i.last_name}" for i in names if i.id == item.uid][0],
             "nickname": await getUserNickname(item.uid, chat_id), "access_level": item.access_level}
        users[f'{item.access_level}'].append(x)
        admins[f'{item.access_level}'] = x
    for k, i in admins.items():
        try:
            if k == '1':
                try:
                    lvl_name = AccessNames.select().where(AccessNames.chat_id == chat_id, AccessNames.lvl == 1)[
                        0].name
                except:
                    lvl_name = LVL_NAMES[1]
                msg += f'[☀] {lvl_name}\n'
                for item in users['1']:
                    if item['access_level'] == 1:
                        if item['uid'] > 0:
                            if item['uid'] not in included:
                                if item['nickname'] is not None and item['nickname'] != '':
                                    msg += f"➖ [id{item['uid']}|{item['nickname']}]\n"
                                else:
                                    msg += f"➖ [id{item['uid']}|{item['name']}]\n"
                                included.append(item['uid'])
            if k == '2':
                try:
                    lvl_name = AccessNames.select().where(AccessNames.chat_id == chat_id, AccessNames.lvl == 2)[
                        0].name
                except:
                    lvl_name = LVL_NAMES[2]
                msg += f'[🔥] {lvl_name}\n'
                for item in users['2']:
                    if item['access_level'] == 2:
                        if item['uid'] > 0:
                            if item['uid'] not in included:
                                if item['nickname'] is not None and item['nickname'] != '':
                                    msg += f"➖ [id{item['uid']}|{item['nickname']}]\n"
                                else:
                                    msg += f"➖ [id{item['uid']}|{item['name']}]\n"
                                included.append(item['uid'])
            if k == '3':
                try:
                    lvl_name = AccessNames.select().where(AccessNames.chat_id == chat_id, AccessNames.lvl == 3)[
                        0].name
                except:
                    lvl_name = LVL_NAMES[3]
                msg += f'[🔥] {lvl_name}\n'
                for item in users['3']:
                    if item['access_level'] == 3:
                        if item['uid'] > 0:
                            if item['uid'] not in included:
                                if item['nickname'] is not None and item['nickname'] != '':
                                    msg += f"➖ [id{item['uid']}|{item['nickname']}]\n"
                                else:
                                    msg += f"➖ [id{item['uid']}|{item['name']}]\n"
                                included.append(item['uid'])
            if k == '4':
                try:
                    lvl_name = AccessNames.select().where(AccessNames.chat_id == chat_id, AccessNames.lvl == 4)[
                        0].name
                except:
                    lvl_name = LVL_NAMES[4]
                msg += f'[🔥] {lvl_name}\n'
                for item in users['4']:
                    if item['access_level'] == 4:
                        if item['uid'] > 0:
                            if item['uid'] not in included:
                                if item['nickname'] is not None and item['nickname'] != '':
                                    msg += f"➖ [id{item['uid']}|{item['nickname']}]\n"
                                else:
                                    msg += f"➖ [id{item['uid']}|{item['name']}]\n"
                                included.append(item['uid'])
            if k == '5':
                try:
                    lvl_name = AccessNames.select().where(AccessNames.chat_id == chat_id, AccessNames.lvl == 5)[
                        0].name
                except:
                    lvl_name = LVL_NAMES[5]
                msg += f'[✨] {lvl_name}\n'
                for item in users['5']:
                    if item['access_level'] == 5:
                        if item['uid'] > 0:
                            if item['uid'] not in included:
                                if item['nickname'] is not None and item['nickname'] != '':
                                    msg += f"➖ [id{item['uid']}|{item['nickname']}]\n"
                                else:
                                    msg += f"➖ [id{item['uid']}|{item['name']}]\n"
                                included.append(item['uid'])
            if k == '6':
                try:
                    lvl_name = AccessNames.select().where(AccessNames.chat_id == chat_id, AccessNames.lvl == 6)[
                        0].name
                except:
                    lvl_name = LVL_NAMES[6]
                msg += f'[⚡] {lvl_name}\n'
                for item in users['6']:
                    if item['access_level'] == 6:
                        if item['uid'] > 0:
                            if item['uid'] not in included:
                                if item['nickname'] is not None and item['nickname'] != '':
                                    msg += f"➖ [id{item['uid']}|{item['nickname']}]\n"
                                else:
                                    msg += f"➖ [id{item['uid']}|{item['name']}]\n"
                                included.append(item['uid'])
            if k == '7':
                try:
                    lvl_name = AccessNames.select().where(AccessNames.chat_id == chat_id, AccessNames.lvl == 7)[
                        0].name
                except:
                    lvl_name = LVL_NAMES[7]
                msg += f'[⭐] {lvl_name}\n'
                for item in users['7']:
                    if item['access_level'] == 7:
                        if item['uid'] > 0:
                            if item['uid'] not in included:
                                if item['nickname'] is not None and item['nickname'] != '':
                                    msg += f"➖ [id{item['uid']}|{item['nickname']}]\n"
                                else:
                                    msg += f"➖ [id{item['uid']}|{item['name']}]\n"
                                included.append(item['uid'])
        except:
            pass
    return msg


def unmute(uname, unickname, uid, name, nickname, id):
    un = unickname if unickname is not None else uname
    n = nickname if nickname is not None else name
    return f'💬 [id{uid}|{un}] размутил [id{id}|{n}]'


def unmute_no_mute(id, name, nickname):
    n = nickname if nickname is not None else name
    return f'⚠ У пользователя [id{id}|{n}] нет блокировки чата.'


def unmute_higher():
    return '⛔Вы не можете размутить пользователя выше Ваших прав'


def unmute_hint():
    return '🔔 Чтобы снять блокировку чата пользователю введите /unwarn @VK. причина (Пример: /unwarn @andrey_mala' \
           ' Тест)'


def unwarn(uname, unick, uid, name, nick, id):
    un = unick if unick is not None else uname
    n = nick if nick is not None else name
    return f'💬 [id{uid}|{un}] снял варн [id{id}|{n}]'


def unwarn_no_warns(id, name, nick):
    n = nick if nick is not None else name
    return f'⚠ У пользователя [id{id}|{n}] нет варнов.'


def unwarn_higher():
    return '⛔Вы не можете убрать варн пользователя выше Ваших прав'


def unwarn_hint():
    return '🔔 Чтобы снять варн пользователя введите /unwarn @VK. (Пример: /unwarn @andrey_mala)'


async def mutelist(res, names, mutedcount):
    msg = f'''💬 Список пользователей с блокировкой чата.
⚛ Всего в блокировке чата: {mutedcount} участников\n\n'''

    for ind, item in enumerate(res):
        if names[ind].first_name != 'DELETED' and names[ind].last_name != 'DELETED':
            nickname = await getUserNickname(item.uid, item.chat_id)
            if nickname is not None:
                name = nickname
            else:
                name = f"{names[ind].first_name} {names[ind].last_name}"
            if literal_eval(item.last_mutes_causes)[-1] is None or literal_eval(item.last_mutes_causes)[-1] == '':
                cause = "Без указания причины"
            else:
                cause = literal_eval(item.last_mutes_causes)[-1]
            addmsg = f"[{ind + 1}]. [id{item.uid}|{name}] | " \
                     f"{int((item.mute - time.time()) / 60)} минут | {cause} | Выдал: " \
                     f"{literal_eval(item.last_mutes_names)[-1]}\n"
            if addmsg not in msg:
                msg += addmsg
    return msg


async def warnlist(res, names, mutedcount):
    msg = f'''💬 Список пользователей с варнами.
⚛ Всего с варнами: {mutedcount} участников\n\n'''

    for ind, item in enumerate(res):
        if names[ind].first_name != 'DELETED' and names[ind].last_name != 'DELETED':
            nickname = await getUserNickname(item.uid, item.chat_id)
            if nickname is not None:
                name = nickname
            else:
                name = f"{names[ind].first_name} {names[ind].last_name}"
            if literal_eval(item.last_warns_causes)[-1] is None or literal_eval(item.last_warns_causes)[-1] == '':
                cause = "Без указания причины"
            else:
                cause = literal_eval(item.last_warns_causes)[-1]
            addmsg = f"[{ind + 1}]. [id{item.uid}|{name}] | " \
                     f"кол-во: {item.warns}/3 | {cause} | Выдал: " \
                     f"{literal_eval(item.last_warns_names)[-1]}\n"
            if addmsg not in msg:
                msg += addmsg
    return msg


def setacc_hint():
    return '🔔 Для выдачи прав пользователю используйте /setacces @VK 1-6 . (пример: /setacces @Andrey_mala 1)'


def setacc_myself():
    return '📛Нельзя установить доступ самому себе'


def setacc_higher():
    return f'Вы не можете выдать права пользователю выше ваших прав'


def setacc(uid, u_name, u_nick, acc, id, name, nick):
    if u_nick is not None:
        u_n = f'[id{uid}|{u_nick}]'
    else:
        u_n = f'[id{uid}|{u_name}]'
    if nick is not None:
        n = f'[id{id}|{nick}]'
    else:
        n = f'[id{id}|{name}]'
    return f'💬 Пользователь {u_n} установил уровень прав "{LVL_NAMES[acc]}" пользователю - {n}'


def setacc_already_have_acc(id, name, nick):
    if nick is not None:
        n = nick
    else:
        n = name
    return f'⚠ У пользователя [id{id}|{n}] уже имеется данные права'


def setacc_low_acc(acc):
    return f'📛 Вы не можете выдать права "{LVL_NAMES[acc]}" данному пользователю, недостаточно прав'


def delaccess_hint():
    return f'🔔 Для снятия прав пользователю используйте /delacces @VK . (пример: /delacces @Andrey_mala)'


def delaccess_myself():
    return '📛 Нельзя снять права самому себе'


def delaccess_noacc(id, name, nick):
    if nick is not None:
        n = nick
    else:
        n = name
    return f'⚠ Пользователь [id{id}|{n}] не имеет каких либо прав.'


def delaccess_higher():
    return '⛔Вы не можете снять права пользователя выше Ваших прав'


def delaccess(uid, uname, unick, id, name, nick):
    if unick is not None:
        un = unick
    else:
        un = uname
    if nick is not None:
        n = nick
    else:
        n = name
    return f'💬 Пользователь [id{uid}|{un}] забрал права пользователя - [id{id}|{n}].'


def timeout_hint():
    return '🔔 Для включение режима тишины напишите /timeout 1, для отключение /timeout 0.'


def timeouton(id, name, nickname):
    if nickname is not None:
        n = nickname
    else:
        n = name
    return f'💬 Пользователь [id{id}|{n}] включил режим тишины в данной беседе. Все новые сообщение от пользователей ' \
           f'будут удалены.'


def timeoutoff(id, name, nickname):
    if nickname is not None:
        n = nickname
    else:
        n = name
    return f'💬 Пользователь [id{id}|{n}] выключил режим тишины в данной беседе.'


def inactive_hint():
    return '🔔 Чтобы исключить неактивых пользователей напишите /inactive дней. (пример: /inactive 15)'


def inactive_no_results():
    return '⚠ За указанный период не найдено неактивных участников.'


def inactive(uid, name, nick, count):
    if int(count) > 0:
        if nick is not None:
            n = nick
        else:
            n = name
        return f"💬 [id{uid}|{n}] исключил {count} неактивных участников беседы."
    else:
        return f'💬 За указанный период времени неактивных участников беседы не найдено.'


def ban_hint():
    return '🔔 Чтобы заблокировать пользователя введите команду /ban @VK time(в днях) причина. ' \
           '(пример: /ban @andrey_mala 30 Тест)'


def ban(uid, u_name, u_nickname, id, name, nickname, cause, time):
    cause = f' по причине: "{cause}"' if cause is not None else ''
    n = u_nickname if u_nickname is not None else u_name
    bn = nickname if nickname is not None else name
    return f'⚡ Пользователь [id{uid}|{n}] заблокировал пользователя - [id{id}|{bn}] на {time} дней{cause}'


def ban_error():
    return '⚠ Указанный пользователь не является участником данной беседы, либо же имеет статус выше Вашего. '


def ban_maxtime():
    return '❌ Максимальный срок бана - 3650 дней'


def ban_myself():
    return '📛Нельзя заблокировать самого себя'


def ban_higher():
    return '⛔Вы не можете заблокировать пользователя выше Ваших прав'


def already_banned(name, nick, id, ban):
    time_left = (ban - time.time()) // 86400 + 1
    n = nick if nick is not None else name
    return f"⚠ Пользователь [id{id}|{n}] уже имеет блокировку на {time_left} дней."


def unban(uname, unick, uid, name, nick, id):
    un = unick if unick is not None else uname
    n = nick if nick is not None else name
    return f'💬 Пользователь [id{uid}|{un}] разбанил пользователя [id{id}|{n}]'


def unban_no_ban(id, name, nick):
    n = nick if nick is not None else name
    return f'⚠ У пользователя [id{id}|{n}] нет блокировки в данной беседе.'


def unban_higher():
    return '⛔Вы не можете разбанить пользователя выше Ваших прав'


def unban_hint():
    return '🔔 Чтобы разблокировать пользователя введите команду /unban @VK. (пример: /unban @andrey_mala)'


def async_already_bound():
    return '🔴 Данная беседа уже привязана к вашему списку бесед.'


def async_done(uid, u_name, u_nickname):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🟢 Пользователь [id{uid}|{n}] привязал данную беседу к общему списку бесед.'


def async_limit():
    return '⛔ В вашей связке бесед уже привязано 30 бесед. С Premium-статусом вы сможете получить больший лимит - ' \
           '100 привязок.'


def delasync_already_unbound():
    return '🔴 Данная беседа не привязана к вашему списку бесед.'


def delasync_not_owner():
    return f'🔴 Вы не являетесь владельцем указанной беседы'


def delasync_done(uid, u_name, u_nickname, chname=''):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    if chname != '':
        chname = f' "{chname}"'
    return f'🟢 Пользователь [id{uid}|{n}] отвязал беседу{chname} из общего списка бесед.'


def gkick(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователь [id{uid}|{n}] был исключен из ({success}/{chats}) бесед. '


def gkick_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "исключения" из связанных бесед ({chats})' \
           f' пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на полученный ' \
           f'результат.'


def gkick_hint():
    return '🔔 Чтобы исключить пользователя из всех бесед, используйте /gkick @VK Причина ' \
           '(Пример: /gkick @andrey_mala Тест)'


async def banlist(res, names, bancount):
    msg = f'''💬 Список пользователей с баном.
⚛ Всего в бане: {bancount} участников\n\n'''

    for ind, item in enumerate(res):
        if names[ind].first_name != 'DELETED' and names[ind].last_name != 'DELETED':
            nickname = await getUserNickname(item.uid, item.chat_id)
            if nickname is not None:
                name = nickname
            else:
                name = f"{names[ind].first_name} {names[ind].last_name}"
            if literal_eval(item.last_bans_causes)[-1] is None or literal_eval(item.last_bans_causes)[-1] == '':
                cause = "Без указания причины"
            else:
                cause = literal_eval(item.last_bans_causes)[-1]
            addmsg = f"[{ind + 1}]. [id{item.uid}|{name}] | " \
                     f"{int((item.ban - time.time()) / 86400) + 1} дней | {cause} | Выдал: " \
                     f"{literal_eval(item.last_bans_names)[-1]}\n"
            if addmsg not in msg:
                msg += addmsg
    return msg


def userban_hint():
    return '🔔 Чтобы посмотреть информацию о банах пользователя в беседе напишите /userban @VK. (пример: /userban ' \
           '@andrey_mala)'


def gban(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователь [id{uid}|{n}] был забанен в ({success}/{chats}) беседах.'


def gban_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "блокировки" из связанных бесед ({chats})' \
           f' пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на полученный ' \
           f'результат.'


def gban_hint():
    return '🔔 Чтобы забанить пользователя во всех беседах, используйте /gban @VK Время(дни) Причина ' \
           '(Пример: /gban @andrey_mala 1 Тест)'


def kick_banned(id, name, nick, btime, cause):
    if nick is not None:
        n = nick
    else:
        n = name
    if cause is None:
        cause = ''
    else:
        cause = f' по причине {cause}'
    return f'🚫 Пользователь [id{id}|{n}] находится в блокировке данной беседы на ' \
           f'{int((btime - time.time()) / 86400)} дней{cause}.'


def gunban(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователь [id{uid}|{n}] был разбанен в ({success}/{chats}) беседах. '


def gunban_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "разблокировки" из связанных бесед ({chats})' \
           f' пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на полученный ' \
           f'результат.'


def gunban_hint():
    return '🔔 Чтобы разблокировать пользователя во всех беседах введите команду /gunban @VK. ' \
           '(пример: /gunban @andrey_mala)'


def gmute(uid, u_name, u_nickname, chats, success):
    n = u_name if u_nickname is None else u_nickname
    return f'🗑 Операция завершена. Пользователь [id{uid}|{n}] был замучен в ({success}/{chats}) беседах.'


def gmute_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "мута" из связанных бесед ({chats})' \
           f' пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на полученный ' \
           f'результат.'


def gmute_hint():
    return '🔔 Чтобы выдать пользователю блокировку чата во всех беседах введите /gmute @VK time(в минутах) причина.' \
           ' (пример: /gmute @andrey_mala 30 Тест)'


def gunmute(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователь [id{uid}|{n}] был размучен в ({success}/{chats}) беседах.'


def gunmute_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "размута" из связанных бесед ({chats})' \
           f' пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на полученный ' \
           f'результат.'


def gunmute_hint():
    return '🔔 Чтобы размутить пользователя во всех беседах введите команду /gunmute @VK. ' \
           '(пример: /gunmute @andrey_mala)'


def gwarn(uid, u_name, u_nick, chats, success):
    un = u_nick if u_nick is not None else u_name
    return f'🗑 Операция завершена. Пользователю [id{uid}|{un}] был выдан варн в ({success}/{chats}) беседах.'


def gwarn_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "варна" из связанных бесед ({chats})' \
           f' пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на полученный ' \
           f'результат.'


def gwarn_hint():
    return '🔔 Чтобы выдать варн пользователю во всех беседах введите команду /gwarn @VK. причина ' \
           '(пример: /gwarn @andrey_mala тестовая причина)'


def gunwarn(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователю [id{uid}|{n}] был снят варн в ({success}/{chats}) беседах.'


def gunwarn_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "анварна" из связанных бесед ({chats})' \
           f' пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на полученный ' \
           f'результат.'


def gunwarn_hint():
    return '🔔 Чтобы снять варн пользователя во всех беседах введите команду /gunwarn @VK. ' \
           '(пример: /gunwarn @andrey_mala)'


def gsnick(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователю [id{uid}|{n}] был изменён никнейм в ({success}/{chats}) беседах.'


def gsnick_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "смены никнейма" из связанных бесед ({chats})' \
           f' пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на полученный ' \
           f'результат.'


def gsnick_hint():
    return '🔔 Чтобы установить никнейм пользователю во всех беседах введите команду /gsnick @VK. nickname' \
           '(пример: /gsnick @andrey_mala Andrey_Mal)'


def grnick(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователю [id{uid}|{n}] был удалён никнейм в ({success}/{chats}) беседах.'


def grnick_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "удаления никнейма" из связанных бесед ({chats})' \
           f' пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на полученный ' \
           f'результат.'


def grnick_hint():
    return '🔔 Чтобы удалить никнейм пользователю во всех беседах введите команду /grnick @VK.' \
           '(пример: /grnick @andrey_mala)'


def gdelaccess(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователю [id{uid}|{n}] был удалён уровень доступа в ({success}/{chats}) ' \
           f'беседах.'


def gdelaccess_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "удаления уровня доступа" из связанных бесед ' \
           f'({chats}) пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на ' \
           f'полученный результат.'


def gdelaccess_hint():
    return '🔔 Чтобы удалить уровень доступа пользователю во всех беседах введите команду /gdelaccess @VK.' \
           '(пример: /gdelaccess @andrey_mala)'


def gdelaccess_admin_unknown():
    return '📛 Не могу забрать права пользователя, который является администратором беседы'


def gdelaccess_admin(uid, u_name, u_nickname):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'📛 Не могу забрать права у пользователя [id{uid}|{n}] так как он является администратором беседы.'


def setaccess_myself():
    return '📛 Нельзя выдать права самому себе'


def gsetaccess(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователю [id{uid}|{n}] был изменён уровень доступа в ({success}/{chats}) ' \
           f'беседах.'


def gsetaccess_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "изменения уровня доступа" из связанных бесед ' \
           f'({chats}) пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на ' \
           f'полученный результат.'


def gsetaccess_hint():
    return '🔔 Чтобы установить уровень доступа пользователю во всех беседах введите команду /gsetaccess @VK. <1-6>' \
           '(пример: /gsetaccess @andrey_mala 3)'


def zov(uid, name, nickname, cause, members):
    if nickname is not None:
        n = nickname
    else:
        n = name
    call = [f"[id{i.member_id}|\u200b\u206c]" for i in members if i.member_id > 0]
    return f"""❗ Пользователь [id{uid}|{n}] вызвал Вас. [{len(call)}/{len(members)}]
💬 Причина вызова: {cause} {''.join(call)}"""


def zov_hint():
    return '🔔 Чтобы вызвать всех пользователей беседы введите команду /zov причина(пример: /zov test cause)'


def welcome(id, name, nickname):
    if nickname is not None:
        n = nickname
    else:
        n = name
    return f"💬 Пользователь [id{id}|{n}] установил новое приветствие для новых участников беседы."


def welcome_hint():
    return '🔔 Для установки приветственного сообщение новых участников напишите ' \
           '/welcome <text>. (пример: /welcome Добро пожаловать!) | ' \
           'Вы можете использовать переменную %name% в своём тексте.'


def delwelcome(id, name, nickname):
    if nickname is not None:
        n = nickname
    else:
        n = name
    return f"💬 Пользователь [id{id}|{n}] удалил приветственное сообщение для новых участников беседы."


def delwelcome_hint():
    return '🔔 Чтобы удалить сообщение для новых пользователей введите команду /delwelcome(пример: /delwelcome)'


def chat_unbound():
    return '❌ Беседа не привязана к глобальному пулу'


def gzov_start(uid, u_name, u_nickname, chats):
    if u_nickname is not None:
        un = u_nickname
    else:
        un = u_name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "вызова всех пользователей" во всех связанных ' \
           f'беседах({chats}). По завершении операции, бот изменит данное сообщение на ' \
           f'полученный результат.'


def gzov(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователь [id{uid}|{n}] вызвал всех пользователей в ({success}/{chats}) ' \
           f'беседах.'


def gzov_hint():
    return '🔔 Для того чтобы вызвать всех пользователей во всех беседах, пропишите ' \
           '/gzov <текст сообщения> (пример: /gzov тест)'


def creategroup_already_created(group):
    return f'🔴 У вас уже имеется группа с названием "{group}", используйте другое или удалите старое.'


def creategroup_done(uid, u_name, u_nickname, group):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🟢 Пользователь [id{uid}|{n}] создал новую группу бесед под названием "{group}".'


def creategroup_incorrect_name():
    return '⛔ Разрешено использовать в название группы только английские буквы и цифры, а также название должно быть' \
           ' не больше 16 символов.'


def creategroup_hint():
    return '🔔 Для создания группы бесед используйте /creategroup <Группа>. (пример: /creategroup admin)'


def creategroup_premium():
    return '⛔ Вы исчерпали лимит на создание групп. С Premium-статусом вы сможете создать до 30 групп.'


def bind_group_not_found(group):
    return f'⛔ Группы под названием "{group}" не существует. Пожалуйста, для началa создайте её, используя команду ' \
           f'/creategroup.'


def bind_chat_already_bound(group):
    return f'⛔ Данная беседа уже привязана к "{group}".'


def bind_hint():
    return '🔔 Чтобы привязать беседу к определенной группе бесед, напишите /bind <Группа>. ' \
           '(пример: /bind admin)'


def bind(uid, u_name, u_nickname, group):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🟢 Пользователь [id{uid}|{n}] привязал данную беседу к "{group}".'


def unbind_group_not_found(group):
    return f'⛔ Группы под названием "{group}" не существует. Пожалуйста, для началa создайте её, используя команду ' \
           f'/creategroup.'


def unbind_chat_already_unbound(group):
    return f'⛔ Данная беседа не привязана к "{group}".'


def unbind_hint():
    return '🔔 Чтобы отвязать беседу от определенной группы бесед, напишите /ubind <Группа>. ' \
           '(пример: /unbind admin)'


def unbind(uid, u_name, u_nickname, group):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🟢 Пользователь [id{uid}|{n}] отвязал данную беседу от "{group}".'


def delgroup_not_found(group):
    return f'⛔ Группы под названием "{group}" не существует. Пожалуйста, для началa создайте её, используя команду ' \
           f'/creategroup.'


def delgroup(uid, u_name, u_nickname, group):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🟢 Пользователь [id{uid}|{n}] удалил группу "{group}".'


def delgroup_hint():
    return '🔔 Чтобы удалить группу бесед, напишите /delgroup <Группа>. (пример: /delgroup admin)'


def s_invalid_group(group):
    return f'⚠ Группа бесед "{group}" не существует или не была привязана к данной беседе.'


def skick_hint():
    return '🔔 Для того чтобы исключить пользователя из определенной группы бесед, пропишите ' \
           '/skick <название группы> @VK <причина>. (пример: /skick admin @andrey_mala тест)'


def skick(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователь [id{uid}|{n}] был кикнут в ({success}/{chats}) беседах.'


def skick_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "исключения" из группы бесед "{group}" ({chats})' \
           f' пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на полученный ' \
           f'результат.'


def sban_hint():
    return '🔔 Для того чтобы забанить пользователя в определенной группе бесед, пропишите ' \
           '/sban <название группы> @VK <время> <причина>. (пример: /sban admin @andrey_mala 30 тест)'


def sban(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователь [id{uid}|{n}] был забанен в ({success}/{chats}) беседах.'


def sban_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "блокировки" в группе бесед "{group}" ({chats})' \
           f' пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на полученный ' \
           f'результат.'


def sunban_hint():
    return '🔔 Для того чтобы разбанить пользователя в определенной группе бесед, пропишите ' \
           '/sunban <название группы> @VK. (пример: /sunban admin @andrey_mala)'


def sunban(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователь [id{uid}|{n}] был разбанен в ({success}/{chats}) беседах.'


def sunban_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "разблокирования" в группе бесед "{group}" ({chats})' \
           f' пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на полученный ' \
           f'результат.'


def ssnick_hint():
    return '🔔 Для того чтобы сменить пользователю ник в определенной группе бесед, пропишите ' \
           '/ssnick <название группы> @VK. <nickname> (пример: /ssnick admin @andrey_mala test)'


def ssnick(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователю [id{uid}|{n}] был изменён никнейм в ({success}/{chats}) беседах.'


def ssnick_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "изменения никнейма" в группе бесед "{group}" ' \
           f'({chats}) пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на ' \
           f'полученный результат.'


def srnick_hint():
    return '🔔 Для того чтобы удалить пользователю ник в определенной группе бесед, пропишите ' \
           '/srnick <название группы> @VK. (пример: /srnick admin @andrey_mala)'


def srnick(uid, u_name, chats, success):
    return f'🗑 Операция завершена. Пользователю [id{uid}|{u_name}] был удалён никнейм в ({success}/{chats}) беседах.'


def srnick_start(uid, u_name, u_nickname, id, name, nickname, chats, group):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "удаления никнейма" в группе бесед "{group}" ' \
           f'({chats}) пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на ' \
           f'полученный результат.'


def szov_hint():
    return '🔔 Для того чтобы вызвать всех пользователей в определенной группе бесед, пропишите ' \
           '/szov <название группы> <текст сообщения> (пример: /szov admin тест)'


def szov_start(uid, u_name, u_nickname, chats, group):
    if u_nickname is not None:
        un = u_nickname
    else:
        un = u_name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "вызова всех пользователей" в группе бесед ' \
           f'"{group}" ({chats}). По завершении операции, бот изменит данное сообщение на ' \
           f'полученный результат.'


def szov(uid, u_name, u_nickname, group, pool, success):
    if u_nickname is not None:
        un = u_nickname
    else:
        un = u_name
    return f'🗑 Операция завершена. Пользователь [id{uid}|{un}] вызвал всех пользователей в группе бесед "{group}" ' \
           f'({success}/{pool}) '


def ssetaccess_hint():
    return '🔔 Для того чтобы установить уровень доступа пользователю в определенной группе бесед, пропишите ' \
           '/ssetaccess <название группы> @VK. <1-6> (пример: /ssetaccess admin @andrey_mala 6)'


def ssetaccess(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователю [id{uid}|{n}] был изменён уровень доступа в ({success}/{chats}) ' \
           f'беседах.'


def ssetaccess_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "изменения уровня доступа" из связанных бесед ' \
           f'({chats}) пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на ' \
           f'полученный результат.'


def sdelaccess_hint():
    return '🔔 Для того чтобы удалить уровень доступа пользователю в определенной группе бесед, пропишите ' \
           '/sdelaccess <название группы> @VK. (пример: /sdelaccess admin @andrey_mala)'


def sdelaccess(uid, u_name, u_nickname, chats, success):
    if u_nickname is not None:
        n = u_nickname
    else:
        n = u_name
    return f'🗑 Операция завершена. Пользователю [id{uid}|{n}] был удалён уровень доступа в ({success}/{chats}) ' \
           f'беседах.'


def sdelaccess_start(uid, u_name, u_nickname, id, name, nickname, chats):
    un = u_nickname if u_nickname is not None else u_name
    n = nickname if nickname is not None else name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "удаления уровня доступа" из связанных бесед ' \
           f'({chats}) пользователя [id{id}|{n}]. По завершении операции, бот изменит данное сообщение на ' \
           f'полученный результат.'


def demote_choose():
    return '''🔔 Для расформировки беседы вы можете ниже выбрать тип.

➖ Без уровней прав - Исключает пользователей которые не имеют права в беседе.
➖ Всех - Исключает всех пользователей даже с правами в беседе.'''


def demote_yon():
    return '⚠ Вы уверены что хотите расформировать данную беседу?'


def demote_disaccept():
    return '🟢 Расформировка данной беседы отменена.'


def demote_accept(id, name, nick):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return f'🟢 Пользователь [id{id}|{n}] расформировал данную беседу.'


def mygroups_no_groups():
    return '⚠ У вас нет созданных групп, вы можете создать их с помощью /creategroup'


def addfilter(id, name, nickname):
    if nickname is not None:
        n = nickname
    else:
        n = name
    return f"💬 Пользователь [id{id}|{n}] добавил новое запретное слово."


def addfilter_hint():
    return '🔔 Для установки запретных слов напишите /addfilter <text>. (пример: /addfilter тест)'


def delfilter(id, name, nickname):
    if nickname is not None:
        n = nickname
    else:
        n = name
    return f"💬 Пользователь [id{id}|{n}] удалил запретное слово."


def delfilter_hint():
    return '🔔 Для удаления запретных слов напишите /delfilter <text>. (пример: /delfilter тест)'


def delfilter_no_filter():
    return '⚠ В данной беседе нет такого фильтра.'


def gaddfilter_start(uid, u_name, u_nickname, chats):
    if u_nickname is not None:
        un = u_nickname
    else:
        un = u_name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "добавление фильтра" во всех связанных ' \
           f'беседах({chats}). По завершении операции, бот изменит данное сообщение на ' \
           f'полученный результат.'


def gaddfilter(uid, name, chats, success):
    return f'🗑 Операция завершена. Пользователь [id{uid}|{name}] добавил фильтр в ({success}/{chats}) беседах.'


def gaddfilter_hint():
    return '🔔 Для установки запретных слов во всех беседах напишите /gaddfilter <text>. (пример: /gaddfilter тест)'


def gdelfilter_start(uid, u_name, u_nickname, chats):
    if u_nickname is not None:
        un = u_nickname
    else:
        un = u_name
    return f'🔄 Пользователь [id{uid}|{un}] инициировал операцию "удаление фильтра" во всех связанных ' \
           f'беседах({chats}). По завершении операции, бот изменит данное сообщение на ' \
           f'полученный результат.'


def gdelfilter(uid, name, chats, success):
    return f'🗑 Операция завершена. Пользователь [id{uid}|{name}] удалил фильтр в ({success}/{chats}) беседах.'


def gdelfilter_hint():
    return '🔔 Для удаления запретных слов во всех беседах напишите /gdelfilter <text>. (пример: /gdelfilter тест)'


def editlvl_hint():
    return '🔔 Чтобы изменить уровень прав для определенной команды введите /editlevel <команда> <новый уровень 0-6>.' \
           ' (пример: /editlevel zov 4)'


def editlvl(id, name, nickname, cmd, beforelvl, lvl):
    if nickname is not None:
        n = nickname
    else:
        n = name
    return f"💬 Пользователь [id{id}|{n}] изменил уровень доступа для команды {cmd} с {beforelvl} до {lvl}."


def editlvl_command_not_found():
    return '⚠ Команда не найдена.'


def editlvl_no_premium():
    return '⛔ Изменять уровень доступа команд можно только с Premium-аккаунтом!'


def msg_hint():
    return '🔔 Чтобы отправить сообщение во все существующие беседы введите /msg <текст>(пример: /msg тест).'


def blocked():
    return '⚠ Вы находитесь в черном списке бота. Вы не можете приглашать бота в какие либо беседы. ' \
           'Бот будет автоматически удалён из данной беседы.'


def addblack_hint():
    return '🔔 Для добавления пользователя в черный список бота, напишите /addblack @VK. ' \
           '(пример: /addblack @andrey_mala)'


def addblack_myself():
    return '⛔Вы не можете добавить себя в чёрный список.'


def unban_myself():
    return '⛔Вы не можете разбанить себя.'


def addblack(uid, uname, unick, id, name, nick):
    if unick is not None:
        un = unick
    else:
        un = uname
    if nick is not None:
        n = nick
    else:
        n = name
    return f'✅ Пользователь [id{uid}|{un}] добавил пользователя [id{id}|{n}] в черный список бота.'


def blacked(id, name, nick):
    if nick is not None:
        n = nick
    else:
        n = name
    return f'⚠ Вы были добавлены в черный список бота пользователем [id{id}|{n}]. Возможность добавления бота в ' \
           f'беседы вам ограничена, однако вы все еще можете использовать команды бота в других беседах.'


def delblack_hint():
    return '🔔 Для удаление пользователя из черного списка бота, введите /delblack @VK. ' \
           '(пример: /delblack @andrey_mala)'


def delblack_myself():
    return '⛔Вы не можете удалить себя из чёрного списка.'


def delblack(uid, uname, unick, id, name, nick):
    if unick is not None:
        un = unick
    else:
        un = uname
    if nick is not None:
        n = nick
    else:
        n = name
    return f'✅ Пользователь [id{uid}|{un}] убрал пользователя [id{id}|{n}] из черного списка бота.'


def delblacked(id, name, nick):
    if nick is not None:
        n = nick
    else:
        n = name
    return f'✨ Пользователь - [id{id}|{n}], вынес Вас из черного списка бота, теперь вы снова можете пользоваться ' \
           f'ботом и приглашать его в свои беседы.'


def delblack_no_user(id, u_name, nick):
    if nick is not None:
        n = nick
    else:
        n = u_name
    return f'⚠ Пользователя [id{id}|{n}] нет в чёрном списке.'


def setstatus_hint():
    return '🔔 Для выдачи Premium-статуса пользователю, введите /setstatus @VK. дни (пример: /setstatus @andrey_mala 3)'


def setstatus(uid, uname, unick, id, name, nick):
    if unick is not None:
        un = unick
    else:
        un = uname
    if nick is not None:
        n = nick
    else:
        n = name
    return f'✅ Пользователь [id{uid}|{un}] выдал Premium-статус пользователю [id{id}|{n}].'


def delstatus_hint():
    return '🔔 Для снятия Premium-статуса пользователя, введите /delstatus @VK. (пример: /delstatus @andrey_mala)'


def delstatus(uid, uname, unick, id, name, nick):
    if unick is not None:
        un = unick
    else:
        un = uname
    if nick is not None:
        n = nick
    else:
        n = name
    return f'✅ Пользователь [id{uid}|{un}] снял Premium-статус пользователя [id{id}|{n}].'


def sgroup_unbound(group):
    return f'❌ Данная беседа не привязана к группе бесед "{group}"'


def statuslist(names, pp):
    msg = f'''💬 Список пользователей с Premium-статусом.
⚛ Всего с премиумом: %premium_status% участников\n\n'''

    ind = 0
    for _ in names:
        if names[ind].first_name != 'DELETED' and names[ind].last_name != 'DELETED':
            name = f"{names[ind].first_name} {names[ind].last_name}"
            np = pp[0]
            for i in pp:
                if i.uid == int(names[ind].id):
                    np = i
                    break
            addmsg = f"[{ind + 1}]. [id{names[ind].id}|{name}] | " \
                     f"Осталось: {int((np.time - time.time()) / 86400) + 1} дней\n"
            if addmsg not in msg:
                msg += addmsg
        ind += 1
    return msg.replace('%premium_status%', f'{ind}')


def settings(kwargs: dict):
    msg = "⚙ Настройки бота в беседе:"
    k = 0
    for e, i in kwargs.items():
        k += 1
        addmsg = ''
        if e == 'setKick':
            addmsg = f'\n[{k}]. Кикать гостей, приглашённых пользователями без прав'
            if i == 1:
                addmsg += ' ✔'
            else:
                addmsg += ' ❌'
        if e == 'setDuel':
            addmsg = f'\n[{k}]. Разрешить дуэли'
            if i == 1:
                addmsg += ' ✔'
            else:
                addmsg += ' ❌'
        if addmsg not in msg:
            msg += addmsg
    return msg


def giveStatus(date):
    return f'''✨ Поздравляю! Вы получили Premium подписку в боте Start Manager сроком на "{date}" дней.
💬 О всех возможностей вы можете узнать у нас в сообществе: @star_manager'''


def ugiveStatus(date, gave, name):
    return f'''✨ Поздравляю! Вы получили Premium подписку в боте Start Manager сроком на {date} дней.
💬 О всех возможностях вы можете узнать у нас в сообществе: @star_manager
⚙ Выдано пользователем - [id{gave}|{name}]'''


def udelStatus(uid, dev_name):
    return f'⚠ Пользователь - [id{uid}|{dev_name}] снял вам Premium статус. ' \
           f'Все ваши созданные ранее группы не будут удалены.'


def uexpStatus():
    return '🔔 Срок вашей Premium подписки закончился, вы можете купить заново либо продлить. ' \
           'Все ваши ранее созданные группы не будут удалены.'


def q(uid, name, nick):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return f'💬 Пользователь [id{uid}|{n}] покинул(-а) беседу и был(-а) исключён(-а).'


def q_fail(uid, name, nick):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return f'⚠️ [id{uid}|{n}], я не могу кикнуть с беседы, так как вы являетесь администратором данной беседы.'


def premium():
    return '''⭐ Информация о Premium подписке

💬 Premium подписка раскроет перед вами множество новых возможностей для контроля и управления вашими чатами. 
Приобретая её, вы делаете нашего бота ещё лучше и функциональнее, а так же вы получаете дополнительные привилегии.

💰Стоимость Premium подписки на 30 дней - 150 рублей
💰Стоимость Premium подписки на 90 дней - 400 рублей

➕ Узнать все возможности можно тут: vk.cc/******

👤 Если у вас появились вопросы или желание приобрести Premium, нажмите на кнопку ниже'''


def premium_sent(uid, name, nickname):
    if nickname is not None and len(nickname) >= 0:
        n = nickname
    else:
        n = name
    return f'''✨ [id{uid}|{n}], я отправил вам в личные сообщение информацию о Premium подписке.'''


def chat(uid, uname, chat_id, bind, gbind, muted, banned, users, time, prefix, chat_name):
    return f'''📜 Информация о беседе

👑 Владелец беседы: [{prefix}{uid}|{uname}]
🆔 ID беседы: {chat_id}
🔖 Название беседы: {chat_name}
⛓ Привязка к группе бесед: {bind}
⛓ Привязка к общему списку: {gbind}

🚫 Заблокированных пользователей: {banned}
🗯 Замученных пользователей: {muted}
👥 Всего участников в беседе: {users}

🕘 Бот был добавлен: {time}'''


def getnick(res, names, members, query):
    msg = '%553%\n\n'
    cnt = 0
    for it in members:
        if it.member_id < 0:
            members.remove(it)
    for ind, item in enumerate(res):
        for i in members:
            if i.member_id == item.uid and i.member_id > 0:
                try:
                    if names[ind].first_name != 'DELETED' and names[ind].last_name != 'DELETED':
                        cnt += 1
                        addmsg = f"{cnt}. {item.nickname} - [id{item.uid}|{names[ind].first_name} " \
                                 f"{names[ind].last_name}]\n"
                        if addmsg not in msg:
                            msg += addmsg
                except:
                    pass
    msg = msg.replace('%553%', f'💬 Найденные результаты с ником - "{query}" ({cnt})')
    return msg


def getnick_no_result(query):
    return f'⚠ Совпадений с ником "{query}" не найдены в беседе.'


def getnick_hint():
    return '🔔 Для поиска пользователя по нику в беседе, введите команду /genick NICK. Можно указывать часть ника. ' \
           '(пример: /getnick Andrey_Mal).'


def id_group():
    return '❌ Я не могу работать с сообществами, пожалуйста укажите пользователя.'


def id_deleted():
    return '❌ Пользователь удален или не существует.'


def clear_old():
    return '❌ Одно из выбранных вами сообщений слишком старое, невозможно удалить!'


def mkick_error():
    return '🔔 Чтобы исключить сразу несколько пользователей введите команду /mkick @user1 @user2 @user3 ... ' \
           '(пример: /mkick @andrey_mala @durov @id1020)'


def no_prem():
    return '✨ Данная команда доступна только для пользователей с Premium подпиской.'


def mkick_no_kick():
    return '⚠ Указанные пользователи не являются участниками данной беседы.'


def giveowner_hint():
    return '🔔 Чтобы передать права на беседу введите команду /giveowner @VK. (пример: /giveowner @andrey_mala)'


def giveowner_ask():
    return '❗ Вы уверены что ходите передать статус владельца беседы?'


def giveowner_no():
    return '🔴 Передача прав на беседу была отклонена.'


def giveowner(uid, unick, uname, id, nick, name):
    if unick is not None and len(unick) > 0:
        un = unick
    else:
        un = uname
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return f'🟣 Владелец беседы [id{uid}|{un}] передал права на данную беседу пользователю - [id{id}|{n}]. ' \
           f'Все привязки к данной беседы были сброшены.'


def bonus(id, nick, name, xp):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return f'🎁 Пользователь [id{id}|{n}] получил ежедневный бонус опыта в размере — {xp}.'


def bonus_time(id, nick, name, timeleft):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    hours = pointHours((timeleft // 3600) * 3600)
    minutes = pointMinutes(timeleft - (timeleft // 3600) * 3600)
    return f'🕒 [id{id}|{n}], ежедневный бонус еще не готов, попробуйте еще раз через — {hours} {minutes}'


def top_lvls(names, lvls, category='общее'):
    dl = calendar.monthrange(datetime.now().year, datetime.now().month)[1] - datetime.now().day + 1
    msg = f'⭐ TOP 10 пользователей по уровням\n⭐ Категория: {category}\n🕒 До сброса уровней: {dl} дней\n\n'
    for index, item in enumerate(list(lvls.values())):
        try:
            name = f"{names[index].first_name} {names[index].last_name}"
            addmsg = f"[{index + 1}]. [id{names[index].id}|{name}] - {item} уровень\n"
            if addmsg not in msg:
                msg += addmsg
        except:
            pass
    return msg


def top_duels(names, duels, category='общее'):
    msg = f'⭐ TOP 10 пользователей по победам в дуэлях\n⭐ Категория: {category}\n\n'
    for index, item in enumerate(list(duels.values())):
        try:
            name = f"{names[index].first_name} {names[index].last_name}"
            addmsg = f"[{index + 1}]. [id{names[index].id}|{name}] - {item} побед\n"
            if addmsg not in msg:
                msg += addmsg
        except:
            pass
    return msg


def premmenu(settings):
    msg = "🟣 Возможности и функции Premium:\n"
    k = 0
    for e, i in settings.items():
        k += 1
        if e == 'clear_by_fire':
            msg += f'\n[{k}]. Удаление сообщения с помощью реакции(🔥) '
            if i == 1:
                msg += '| ✔'
            else:
                msg += '| ❌'
        elif e == 'border_color':
            msg += f'\n[{k}]. Смена цвета рамки в /stats | 🛠 В разработке'
    return msg


def addprefix_hint():
    return '🔔 Чтобы добавить префикс введите команду /addprefix prefix(1-2 символа) (пример: /addprefix pr)'


def addprefix_max():
    return '❌ Вы достигли лимита префиксов (Всего доступно 3 префикса).'


def addprefix_too_long():
    return '❌ Префикс может быть длиной 1 либо 2 символа'


def addprefix(uid, name, nick, prefix):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return f'💬 Пользователь [id{uid}|{n}] установил свой префикс "{prefix}"'


def delprefix_hint():
    return '🔔 Чтобы удалить префикс введите команду /delprefix prefix(1-2 символа) (пример: /delprefix pr)'


def delprefix(uid, name, nick, prefix):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return f'💬 Пользователь [id{uid}|{n}] удалил свой префикс "{prefix}"'


def delprefix_not_found(prefix):
    return f'❌ Префикса "{prefix}" не существует'


def listprefix(uid, name, nick, prefixes):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    msg = f'''💬 Список префиксов пользователя [id{uid}|{n}]:\n\n'''
    if len(prefixes) == 0:
        msg += 'Префиксов не обнаружено. Используйте команду /addprefix'
    for i in prefixes:
        msg += f'➖ "{i.prefix}"\n'
    return msg


def levelname_hint():
    return '🔔 Чтобы изменить имя уровня доступа введите команду /levelname 0-7 name (пример: /levelname 0 обычн. юзер)'


def levelname(uid, name, nick, lvl, lvlname):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return f'💬 Пользователь [id{uid}|{n}] установил имя "{lvlname}" для уровня доступа "{lvl}"'


def resetlevel_hint():
    return '🔔 Чтобы сбросить имя уровня доступа введите команду /resetlevel 0-7 (пример: /resetlevel 0)'


def cmdcount(cmdcounter):
    summ = 0
    for i in cmdcounter:
        summ += i.count
    msg = '💬 Список использованых команд:\n\n'
    for i in cmdcounter:
        if i.cmd not in msg:
            msg += f'➖{i.cmd} | использовано: {i.count} раз | {str(i.count / summ * 100)[:5]}%\n'
    return msg


def lvl_up(lvl):
    return f'⭐ Вы повысили уровень с {lvl} на {lvl + 1}'


def ignore_hint():
    return '🔔 Чтобы Star Manager игнорировал команды определенного пользователя введите команду /ignore @VK. ' \
           '(пример: /ignore @andrey_mala)'


def ignore_not_found():
    return '❌ Пользователь является сообществом либо не сущетвует.'


def ignore(id, name, nick):
    if nick is not None:
        n = nick
    else:
        n = name
    return f'💬 Пользователь [id{id}|{n}] добавлен в список игнорируемых пользователей'


def unignore_hint():
    return '🔔 Чтобы Star Manager перестал игнорировать команды определенного пользователя введите команду ' \
           '/unignore @VK. (пример: /unignore @andrey_mala)'


def unignore_not_found():
    return '❌ Пользователь является сообществом либо не сущетвует.'


def unignore_not_ignored():
    return '❌ Пользователь не числится в списке игнорируемых.'


def unignore(id, name, nick):
    if nick is not None:
        n = nick
    else:
        n = name
    return f'💬 Пользователь [id{id}|{n}] исключён из списка игнорируемых пользователей'


def ignorelist(res, names):
    msg = f'💬 Список игнорируемых пользователей.\n⚛ Всего игнорируется: {len(res)} участников\n\n'
    k = 0
    for i in res:
        addmsg = f'➖ [id{i.uid}|{names[k]}]'
        if addmsg not in msg:
            msg += addmsg
        k += 1
    return msg


def chatlimit_hint():
    return '🔔 Чтобы установить медленный режим введите команду /chatlimit time(0 - выкл.) ' \
           '(пример: /chatlimit 1s(s - секунды, m - минуты, h - часы))'


def chatlimit(id, name, nick, t, postfix, lpos):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
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
        return f'💬 Пользователь [id{id}|{n}] установил медленный режим на {t} {postfix}'
    else:
        if lpos == 0:
            return f'❌ Медленный режим уже отключен.'
        else:
            return f'💬 Пользователь [id{id}|{n}] выключил медленный режим'


def pm():
    return '''✋ Добро пожаловать в Star Manager

⚜ Официальное сообщество — @star_manager
🌐 Функционал бота — vk.cc/crO08V
⭐ Узнать о Premium возможностях — vk.cc/crO0a5

📕 Если у вас возникли проблемы или баги, пожалуйста, сообщите нам — vk.cc/cr6TBd'''


def pm_market():
    return '✨ О Premium-подписке\n\n💬 Premium предоставляет вам дополнительные возможности и эксклюзивные функции ' \
           'для вашего аккаунта и бесед. Прежде чем сделать покупку, ознакомьтесь с подробной информацией о Premium, ' \
           'перейдя по следующей ссылке: vk.cc/crO0a5\n\n✳ Чтобы приобрести Premium, воспользуйтесь кнопкой ниже ' \
           'и перейдите на сайт оплаты. (star-manager.ru)'


def pm_market_buy(days, cost, last_payment, link):
    return f'🟣 Срок подписки: {days} дней\n🟣 Стоимость подписки: {cost} рублей\n🟣 Номер заказа: #{last_payment}\n' \
           f'\n💬 Для оплаты подписки, перейдите по ссылке, указанной ниже, и выберите удобный для вас способ оплаты.' \
           f' Затем вернитесь сюда и нажмите "Проверить оплату". При успешной оплате, наш бот автоматически предостав' \
           f'ит вам Premium-подписку на выбранный срок.\n\n🔥 Оплатить сейчас — {link}\n\n⚠ Пожалуйста, обратите вним' \
           f'ание, что данная ссылка для оплаты будет активна всего 10 минут. Если прошло больше времени, рекомендуем' \
           f' создать новый заказ.'


def payment_success(order_id, days):
    return f'''🟢 Заказ #{order_id} успешно был оплачен.

✨ Поздравляю вы получили Premium-подписку сроком на {days} дней. 
Чтобы узнать все подробности о Premium-подписке перейдите по ссылке — vk.cc/crO0a5'''


def cmd_changed_in_cmds():
    return '🚫 Вы не можете установить ассоциации используя оригинальные название команд'


def cmd_changed_in_users_cmds(cmd):
    return f"🚫 Данная ассоциация уже установлена для команды “{cmd}“"


def cmd_hint():
    return ("🔔 Здесь вы сможете устанавливать свои собственные ассоциации для команд. Чтобы установить новую ассоциаци"
            "ю напишите /cmd команда новое_название. (Пример: /cmd help помощь))\n\n💬 Ниже вы сможете найти список все"
            "х измененных команд. На одну команду можно устанавливать только одну ассоциацию.\n❗️ Чтобы удалить ассоциа"
            "цию для команды, достаточно написать /cmd команда, тем самым вы удалите её. (Пример: /cmd help)")


def cmd_prem():
    return '⛔ В вашей беседе уже изменено 10 команд. С Premium-статусом вы сможете менять команды без ограничений'


def cmd_set(uid, name, nick, cmd, changed):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return f'💬 Пользователь [id{uid}|{n}] установил название "{changed}" для команды "{cmd}"'


def resetcmd_hint():
    return '🔔 Чтобы удалить названия команд введите команду /resetcmd command (пример: /resetcmd ban)'


def resetcmd_not_found(cmd):
    return f'❌ Команда "{cmd}" не найдена'


def resetcmd_not_changed(cmd):
    return f'❌ Команда "{cmd}" не изменена'


def resetcmd(uid, name, nick, cmd, cmdname):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return f'💬 Пользователь [id{uid}|{n}] удалил название "{cmdname}" для команды "{cmd}"'


def cmd_char_limit():
    return '⛔ В команде разрешено использовать только русские и английские буквы и цифры, ' \
           'а также название должно быть не больше 32 символов.'


def cmdlist(cmdnames, page, cmdlen):
    msg = f'💬 Список изменённых команд.\n⚛ Всего изменено: {cmdlen} команд\n\n'
    c = page * 10
    for k, i in cmdnames.items():
        c += 1
        msg += f'[{c}] {k} - {i}\n'
    return msg


def listasync(chats, total):
    msg = '''🟣 Список привязанных бесед
🟣 Всего бесед: %total%\n'''

    for k, i in enumerate(chats[:10]):
        if i["name"] is not None:
            msg += f'\n➖ ID: {i["id"]} | Название: {i["name"]}'
        else:
            total -= 1
    msg = msg.replace('%total%', f'{total}')
    if total <= 0:
        msg = '⚠ Привязанных бесед не найдено. Для привязки беседы используйте команду /async'
    return msg


def duel_not_allowed():
    return '🔔 В этой беседе дуэли были отключены.'


def duel_hint():
    return '🔔 Чтобы вызвать участника на дуэль напишите /duel XP(50-ꝏ). (пример: /duel 100)'


def duel_uxp_not_enough(uid, name, nick):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return f'🚫 [id{uid}|{n}], у вас недостаточно опыта для создания дуэли.'


def duel_xp_minimum():
    return f'🚫 Разрешено сделать ставку от 50 до 500 XP.'


def duel(uid, name, nick, xp):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return f'🔥 Пользователь [id{uid}|{n}] создал дуэль на {xp} XP. Для того чтобы сразится в дуэли нажмите "Сразиться"'


def duel_res(uid, uname, unick, id, name, nick, xp, prem):
    if unick is not None and len(unick) > 0:
        un = unick
    else:
        un = uname
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    if prem is not None and int(prem) > 0:
        return f'🎁 Пользователь [id{uid}|{un}] выиграл в дуэли против [id{id}|{n}] и получил {xp} XP'
    else:
        return f'🎁 Пользователь [id{uid}|{un}] выиграл в дуэли против [id{id}|{n}] и получил {int(xp / 100 * 90)} ' \
               f'XP с учетом комиссии 10%'


def dueling():
    return '⚔'


def resetnick_yon():
    return '⚠ Вы уверены что хотите удалить ники всех пользователей беседы?'


def resetnick_accept(id, name):
    return f'🟢 Пользователь [id{id}|{name}] удалил ники всех пользователей беседы.'


def resetnick_disaccept():
    return '🟢 Удаление ников всех пользователей беседы отменено.'


def resetaccess_hint():
    return '🔔 Чтобы удалить удалить уровень прав всем пользователям беседы введите команду /resetaccess LVL[1-6] ' \
           '(пример: /resetaccess 1)'


def resetaccess_yon(lvl):
    return f'⚠ Вы уверены что хотите удалить уровень прав "{lvl}" всем пользователям беседы?'


def resetaccess_accept(id, name, lvl):
    return f'🟢 Пользователь [id{id}|{name}] удалил уровень прав "{lvl}" всем пользователей беседы.'


def resetaccess_disaccept(lvl):
    return f'🟢 Удаление уровня прав "{lvl}" всем пользователей беседы отменено.'


def olist(members):
    msg = f"""🟣 Пользователи онлайн
🟣 Всего в сети : {len(list(members.keys()))} человек\n\n"""
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
    return f'🎁 [id{uid}|{name}], вы получили +50 XP за коментарий'


def farm_cd(name, uid, timeleft):
    return f'🕒 [id{uid}|{name}], подождите ещё {int(timeleft / 60) + 1} минут для получения XP'


def kickmenu():
    return '📣 Дополнительные инструменты для работы с пользователями.\n💬 С данными инструментами вы сможете ' \
           'исключить пользователей из беседы по определенным категориям, которые предоставлены ниже.\n\n➖ ' \
           'Исключение пользователей без никнеймов.\n➖ Исключение пользователей с никнеймами.\n➖ Исключение ' \
           'удалённых пользователей ВКонтакте.'


def kickmenu_kick_nonick(uid, name, nick, kicked):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return f'💬 Пользователь [id{uid}|{n}] исключил всех пользователей без никнеймов. Количество исключенных — {kicked}'


def kickmenu_kick_nick(uid, name, nick, kicked):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return f'💬 Пользователь [id{uid}|{n}] исключил всех пользователей с никнеймами. Количество исключенных — {kicked}'


def kickmenu_kick_banned(uid, name, nick, kicked):
    if nick is not None and len(nick) > 0:
        n = nick
    else:
        n = name
    return f'💬 Пользователь [id{uid}|{n}] исключил всех удалённых пользователей. Количество исключенных — {kicked}'


def rewards(sub, wd):
    subs = wds = ''
    if sub >= 1:
        sub = 1
        subs = '✅'
    if wd >= 10:
        wd = 10
        wds = '✅'
    return f'''🎁 Доступные задания для получения призов.

[1] Подписаться на сообщество ВК ({sub}/1){subs}
[2] Выиграть в дуэлях 10 раз ({wd}/10){wds}'''


def lock(time):
    return f'🕒 Не так быстро! Для использования данной команды подождите {time} секунд.'


def send_notification(text, tagging):
    return f'{text}{tagging}'


def notif(notifs, activenotifs):
    return f'''
🔔 Система напоминаний в беседе, для создания нового напоминания напишите /notif <название>. (пример: /notif Задача #1)

💬 Для просмотра и настроек напоминаний нажмите кнопку ниже.

🟣 Всего напоминаний в беседе: {len(notifs)}
🟣 Активных напоминаний: {len(activenotifs)}'''


def notif_already_exist(name):
    return f'🚫 Напоминание "{name}" уже существует, используйте другое название.'


def notification(name, text, time, every, tag, status):
    msg = f'''🌐 Название: {name}
💬 Отправляемый текст: "{text}"

🕒 Время отправки: '''

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

    msg += '\n\n🟣 Статус: '

    if status == 0:
        msg += 'Выключено'
    elif status == 1:
        msg += 'Включено'

    return msg


def notification_changing_text():
    return '📝 Введите новый отправляемый текст'


def notification_changed_text(name):
    return f'✅ Вы успешно изменили текст напоминания "{name}"'


def notification_changing_time_choose():
    return '💬 Выберите один из вариантов промежутка отправки.'


def notification_changing_time_single():
    return '💬 Укажите время в формате ЧЧ:ММ по часовому поясу МСК. (пример: 12:00)'


def notification_changing_time_everyday():
    return '💬 Укажите время в формате ЧЧ:ММ по часовому поясу МСК. (пример: 12:00)'


def notification_changing_time_everyxmin():
    return '💬 Укажите время в формате минут. (пример: 60)'


def notification_changed_time(name):
    return f'✅ Вы успешно изменили текст напоминания "{name}"'


def notification_changing_time_error():
    return '❌ Неверный формат!'


def notification_delete(name):
    return f'✅ Напоминание "{name}" было удаленно.'


def notification_changing_tag_choose():
    return '💬 Выберите кого хотите упомянуть при отправке сообщения.'


def notification_changing_tag_changed(name):
    return f'✅ Вы успешно изменили теги напоминания "{name}"'


def notification_too_long_text(name):
    return (f'⚠ Ваше напоминание "{name}" имеет слишком длинный текст и было выключено. '
            f'Пожалуйста, уменьшите длину текста и включите напоминание заново')


def notifs(notifs):
    msg = '🔔 Список напоминаний в беседе\n\n'

    for k, i in enumerate(notifs):
        if i.status == 1:
            status = 'Включено'
        else:
            status = 'Выключено'
        msg += f'[{k + 1}]. {i.name} | {status}\n'

    return msg


def transfer_hint():
    return '🔔 Для передачи опыта другому пользователю, нужно написать /transfer @VK сумма. ' \
           'При переводе имеется комиссия 5% для обычных пользователей. (пример: /transfer @andrey_mala 100)'


def transfer_wrong_number():
    return '🚫 Минимальное количество опыта для перевода 50 - 500. Для Premium пользователей до 1500 опыта.'


def transfer_not_enough(uid, name, nickname):
    n = name if nickname is None else nickname
    return f'🚫 [id{uid}|{n}], у вас недостаточно опыта для перевода.'


def transfer_myself():
    return f'🚫 Вы не можете перевести XP самому себе.'


def transfer_community():
    return f'🚫 Вы не можете перевести XP сообществу.'


def transfer(uid, uname, id, name, xp, u_prem):
    if int(u_prem) == 0:
        return f'🔥 Пользователь [id{uid}|{uname}] передал {xp} XP пользователю [id{id}|{name}] с учётом комиссии 5%.'
    else:
        return f'🔥 Пользователь [id{uid}|{uname}] передал {xp} XP пользователю [id{id}|{name}].'


def notadmin():
    return '❌ Ошибка. Убедитесь, что бот владеет статусом администратора.'


def bot_info(chats, total_users, users, premium_users, all_groups, biggest_gpool, biggest_gpool_owner_name, max_pool,
             max_group_name, max_group_count, biggest_chat_id, biggest_chat_users, biggest_chat_owner_id,
             biggest_chat_owner_name):
    return f'''🟣 Общая статистика бота

➕ Всего бесед с ботом : {len(chats)} бесед.
➕ Всего в беседах : {total_users}
➕ Всего участников : {len(users)}
➕ Всего Premium у участников : {premium_users}
➕ Всего созданных групп : {len(all_groups)}

➖ Самый большой глобальный пул : [id{biggest_gpool}|{biggest_gpool_owner_name}] | {max_pool}
➖ Самая большая группа : {max_group_name} | {max_group_count}
➖ Самая большая беседа : ID: {biggest_chat_id} | USERS: {biggest_chat_users} | OWNER: [id{biggest_chat_owner_id}|{
    biggest_chat_owner_name}]'''


def warn_report(uid, name, uwarns, from_id, from_name):
    if uwarns <= 0:
        h = '💙'
    elif uwarns == 1:
        h = '💚'
    else:
        h = '💛'
    return (f'{h} Администратор [id{uid}|{name}] выдал варн пользователю [id{from_id}|{from_name}]. '
            f'Всего варнов: [{uwarns}/3]')


def unwarn_report(uid, name, uwarns, from_id, from_name):
    if uwarns <= 0:
        h = '💙'
    elif uwarns == 1:
        h = '💚'
    else:
        h = '💛'
    return (f'{h} Администратор [id{uid}|{name}] снял варн пользователю . [id{from_id}|{from_name}]'
            f'Всего варнов: [{uwarns}/3]')


def reportwarn(uid, name, uwarns):
    if uwarns <= 0:
        h = '💙'
    elif uwarns == 1:
        h = '💚'
    else:
        h = '💛'
    return f'{h} Всего варнов у [id{uid}|{name}]: [{uwarns}/3]'


def warn_report_ban(uid, name, from_id, from_name):
    return (f'❤ Администратор [id{uid}|{name}] заблокировал репорты пользователя [id{from_id}|{from_name}]. '
            f'Варнов: [3/3]')


def reboot():
    return '🔄 Выполняю перезагрузку сервера'


def like_premium_bonus(days):
    return f'''✨ Поздравляю вы получили Premium-подписку сроком на {days} дней. 
Чтобы узнать все подробности о Premium-подписке перейдите по ссылке — vk.cc/crO0a5'''


def givexp(uid, dev_name, id, u_name, xp):
    return f'🚽 Пользователь [id{uid}|{dev_name}] выдал {xp} XP пользователю [id{id}|{u_name}].'


def inprogress():
    return '🌌 Данная команда сейчас на доработке'


def msg(devmsg):
    return f'{devmsg}'


def stats_loading():
    return f'🔄 Загружаю статистику...'


def infunban_noban():
    return '❌ Указанный пользователь или беседа не находится в блокировке'


def infunban_hint():
    return ('🔔 Чтобы разбанить пользователя или беседу, используйте /infunban group|user id|@VK. '
            '(Пример: /infunban group 123\nПример: /infunban user @andrey_mala)')


def infunban():
    return '✅ Вы успешно разбанили данного пользователя или беседу'


def infban_hint():
    return ('🔔 Чтобы забанить пользователя или беседу, используйте /infban group|user id|@VK. '
            '(Пример: /infban group 123\nПример: /infban user @andrey_mala)')


def infban():
    return '✅ Вы успешно забанили данного пользователя или беседу'


def newseason_top(top, reward):
    return (f'⭐️ Этот сезон прошел и вы попали в топ 10 пользователей с наибольшим уровнем. Рейтинг уровней был '
            f'обнулен и вы получили приз за {top} место - Premium подписку сроком на {reward} дней.')


def newseason_post(top, season_start, season_end):
    msg = f'''
⭐️ Завершился сезон, и уровени всех пользователей были сброшены. 
Топ 10 пользователей с наивысшими уровнями получили заслуженные награды в виде Premium подписок.\n
✨ Список пользователей, занявших первые 10 мест:\n'''
    for i in top:
        msg += f'[id{i[0]}|{i[1]}] - {i[2]} уровень\n'
    msg += f'''
🌐 Новый сезон уже начался и продлится с {season_start} по {season_end}. 
Для участия достаточно просто повышать свой уровень и стремиться попасть в топ пользователей.
'''


def task(tasks, coins, streak):
    return ('⭐️ Задания - это отличный способ быстрее повысить уровень своего аккаунта и получить различные призы. '
            'Выполняя ежедневные и еженедельные задания, вы зарабатываете монеты Star, '
            'которые можно обменять на призы с помощью кнопки "Обмен" ниже. '
            'Для отслеживания заданий выберите нужную категорию ниже.\n\n'
            f'🪙 Star монет: {coins} шт.\n🟣 Заданий выполнено: {tasks} шт.\n🟣 Недель подряд: {streak}')


def task_trade(c):
    return f'''⭐️ Ваши Star монеты — {c} шт.

[1].  Обменять на 1 уровень | 5 🪙
[2].  Обменять на 5 уровней | 20 🪙
[3].  Обменять на 10 уровней | 40 🪙
[4].  Обменять на Premium 3 дня | 80 🪙

🎁 Для обмена нажмите нужную цифру ниже.'''


def task_trade_not_enough(c):
    return f'❌ Вам не хватает {c} 🪙'


def task_trade_lot(lot):
    buy = f'{TASKS_LOTS[list(TASKS_LOTS.keys())[lot - 1]]} '
    if lot < 4:
        buy += 'уровня'
    else:
        buy += 'дня Premium подписки'
    return '✅ Вы успешно купили ' + buy


def task_trade_lot_log(lot, id, name):
    buy = f'{TASKS_LOTS[list(TASKS_LOTS.keys())[lot - 1]]} '
    if lot < 4:
        buy += 'уровня'
    else:
        buy += 'дня Premium подписки'
    return f'✅ Пользователь [id{id}|{name}] успешно купил ' + buy


def task_weekly(prem, tasks):
    def point(num, maxv):
        return num if num < maxv else maxv
    count = [point(tasks[0], TASKS_WEEKLY["bonus"]) == TASKS_WEEKLY["bonus"],
             point(tasks[1], TASKS_WEEKLY["dailytask"]) == TASKS_WEEKLY["dailytask"],
             point(tasks[2], TASKS_WEEKLY["sendmsgs"]) == TASKS_WEEKLY["sendmsgs"]].count(True)
    if prem:
        count += [point(tasks[3], PREMIUM_TASKS_WEEKLY["lvlup"]) == PREMIUM_TASKS_WEEKLY["lvlup"],
                  point(tasks[4], PREMIUM_TASKS_WEEKLY["duelwin"]) == PREMIUM_TASKS_WEEKLY["duelwin"]].count(True)
    tl = datetime.now()
    tl = 24 * (7 - tl.weekday()) - tl.hour - 1
    hours = pointHours((tl % 24) * 3600)
    days = pointDays((tl // 24) * 86400)
    msg = f'''🟣 Выполнено заданий — {count} / {5 if prem else 3}
🟣 До сброса заданий — {days} {hours}\n
[1]. Забрать приз /bonus 6 раз | {point(tasks[0], TASKS_WEEKLY["bonus"])} / 6
[2]. Выполнить ежедневные задания 7 раз | {point(tasks[1], TASKS_WEEKLY["dailytask"])} / 7
[3]. Отправить 10.000 сообщений | {point(tasks[2], TASKS_WEEKLY["sendmsgs"])} / 10.000'''
    if prem:
        msg += f'''\n[4]. Повысить 10 уровней профиля | {point(tasks[3], PREMIUM_TASKS_WEEKLY["lvlup"])} / 10
[5]. Победить 60 раз в дуэлях | {point(tasks[4], PREMIUM_TASKS_WEEKLY["duelwin"])} / 60'''
    return msg + '''\n\n🪙 За каждое задание вы получаете +10 монет Star.'''


def task_daily(prem, tasks):
    def point(num, maxv):
        return num if num < maxv else maxv
    count = [point(tasks[0], TASKS_DAILY["sendmsgs"]) == TASKS_DAILY["sendmsgs"],
             point(tasks[1], TASKS_DAILY["sendvoice"]) == TASKS_DAILY["sendvoice"],
             point(tasks[2], TASKS_DAILY["duelwin"]) == TASKS_DAILY["duelwin"]].count(True)
    if prem:
        count += [point(tasks[3], PREMIUM_TASKS_DAILY["cmds"]) == PREMIUM_TASKS_DAILY["cmds"],
                  point(tasks[4], PREMIUM_TASKS_DAILY["stickers"]) == PREMIUM_TASKS_DAILY["stickers"]].count(True)
    tl = datetime.now()
    tl = 1440 - tl.hour * 60 - tl.minute
    hours = pointHours((tl // 60) * 3600)
    minutes = pointMinutes((tl % 60) * 60)

    msg = (f'🟣 Выполнено заданий — {count} / {5 if prem else 3}\n'
           f'🟣 До сброса заданий — {hours} {minutes}\n\n')
    if prem:
        if point(tasks[0], TASKS_DAILY["sendmsgs"]) == TASKS_DAILY["sendmsgs"]:
            msg += (f'[1.1]. Отправить 600 сообщений | '
                    f'{point(tasks[0], PREMIUM_TASKS_DAILY_TIERS["sendmsgs"])} / 600\n')
        else:
            msg += f'[1]. Отправить 300 сообщений | {point(tasks[0], TASKS_DAILY["sendmsgs"])} / 300\n'
        if point(tasks[1], TASKS_DAILY["sendvoice"]) == TASKS_DAILY["sendvoice"]:
            msg += (f'[2.1]. Отправить 60 голосовых сообщений | '
                    f'{point(tasks[1], PREMIUM_TASKS_DAILY_TIERS["sendvoice"])} / 60\n')
        else:
            msg += f'[2]. Отправить 30 голосовых сообщений | {point(tasks[1], TASKS_DAILY["sendvoice"])} / 30\n'
        if point(tasks[2], TASKS_DAILY["duelwin"]) == TASKS_DAILY["duelwin"]:
            msg += (f'[3.1]. Победить 25 раз в дуэлях | '
                    f'{point(tasks[2], PREMIUM_TASKS_DAILY_TIERS["duelwin"])} / 25\n')
        else:
            msg += f'[3]. Победить 15 раз в дуэлях | {point(tasks[2], TASKS_DAILY["duelwin"])} / 15\n'
        if point(tasks[3], PREMIUM_TASKS_DAILY["cmds"]) == PREMIUM_TASKS_DAILY["cmds"]:
            msg += (f'[4.1]. Использовать команды бота 100 раз | '
                    f'{point(tasks[3], PREMIUM_TASKS_DAILY_TIERS["cmds"])} / 100\n')
        else:
            msg += f'[4]. Использовать команды бота 50 раз | {point(tasks[3], PREMIUM_TASKS_DAILY["cmds"])} / 50\n'
        if point(tasks[4], PREMIUM_TASKS_DAILY["stickers"]) == PREMIUM_TASKS_DAILY["stickers"]:
            msg += (f'[5.1]. Отправить 200 стикеров | '
                    f'{point(tasks[4], PREMIUM_TASKS_DAILY_TIERS["stickers"])} / 200\n')
        else:
            msg += f'[5]. Отправить 100 стикеров | {point(tasks[4], PREMIUM_TASKS_DAILY["stickers"])} / 100\n'
    else:
        msg += f'''[1]. Отправить 300 сообщений | {point(tasks[0], TASKS_DAILY["sendmsgs"])} / 300
[2]. Отправить 30 голосовых сообщений | {point(tasks[1], TASKS_DAILY["sendvoice"])} / 30
[3]. Победить 15 раз в дуэлях | {point(tasks[2], TASKS_DAILY["duelwin"])} / 15\n'''

    return msg + '''\n🪙 За каждое задание вы получаете +5 монет Star.'''


def resetlvl(id, u_name):
    return (f'⛔️ Уважаемый, [id{id}|{u_name}]. Ваш прогресс в виде уровня был аннулирован из-за '
            f'нарушений правил использования сервиса.')


def resetlvlcomplete(id, u_name):
    return f'✝ Вы успешно сбросили уровень [id{id}|{u_name}].'


def check_help():
    return ('🔔 Чтобы посмотреть информацию о наказаниях пользователя в беседе напишите /check @VK. '
            '(пример: /check @andrey_mala)')


def check(id, name, nickname, ban, warn, mute):
    n = nickname if nickname is not None else name
    return f'''
⛔ Информация о нарушениях пользователя — [id{id}|{n}]
🆔 ID Вконтакте: {id}

➥ Активные блокировки : {pointDays(ban) if ban else "Отсутствуют"}
➥ Активные предупреждение : {f"{warn} из 3" if warn else "Отсутствуют"}
➥ Активный мут чата : {pointMinutes(mute) if mute else "Отсутствует"}

★ Для просмотра всех наказаний и активных выберите действие ниже.
'''


def check_ban(id, name, nickname, ban, ban_history, ban_date, ban_from, ban_reason, ban_time):
    n = nickname if nickname is not None else name
    msg = f'''
⛔️ Блокировки пользователя — [id{id}|{n}]

➜ Всего блокировок в беседе : {len(ban_history)}
➜ Активная блокировка : {pointDays(ban) if ban else "Отсутствует"}\n\n'''
    if ban:
        msg += f'★ {ban_date} | {ban_from} | {pointDays(ban_time)} | {ban_reason}'

    return msg


def check_mute(id, name, nickname, mute, mute_history, mute_date, mute_from, mute_reason, mute_time):
    n = nickname if nickname is not None else name
    msg = f'''
⛔️ Муты пользователя — [id{id}|{n}]

➜ Всего мутов в беседе : {len(mute_history)}
➜ Активный мут : {pointMinutes(mute) if mute else "Отсутствует"}\n\n'''
    if mute:
        msg += f'★ {mute_date} | {mute_from} | {pointMinutes(mute_time)} | {mute_reason}'

    return msg


def check_warn(id, name, nickname, warn, warn_history, warns_date, warns_from, warns_reason):
    n = nickname if nickname is not None else name
    msg = f'''
⛔️ Предупреждения пользователя — [id{id}|{n}]

➜ Всего предупреждений в беседе : {len(warn_history)}
➜ Активные предупреждения : {f"{warn} из 3" if warn else "Отсутствуют"}\n\n'''
    if warn:
        for k, _ in enumerate(warn_history[:warn]):
            msg += f'★ {warns_date[k]} | {warns_from[k]} | {warn - k} из 3 | {warns_reason[k]}\n'

    return msg


def check_history_ban(id, name, nickname, dates, names, times, causes):
    n = nickname if nickname is not None else name
    msg = f'🌐 История блокировок пользователя — [id{id}|{n}]\n\n'
    for k in range(len(times)):
        msg += f'★ {dates[k]} | {names[k]} | {pointDays(times[k])} | {causes[k]}\n'
    return msg


def check_history_mute(id, name, nickname, dates, names, times, causes):
    n = nickname if nickname is not None else name
    msg = f'🌐 История мутов пользователя — [id{id}|{n}]\n\n'
    for k in range(len(times)):
        msg += f'★ {dates[k]} | {names[k]} | {pointMinutes(times[k])} | {causes[k]}\n'
    return msg


def check_history_warn(id, name, nickname, dates, names, times, causes):
    n = nickname if nickname is not None else name
    msg = f'🌐 История предупреждений пользователя — [id{id}|{n}]\n\n'
    for k in range(len(times)):
        msg += f'★ {dates[k]} | {names[k]} | {causes[k]}\n'
    return msg
