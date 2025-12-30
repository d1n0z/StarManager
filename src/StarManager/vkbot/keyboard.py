from typing import List, Optional

from vkbottle import Callback, Keyboard, KeyboardButtonColor, OpenLink

from StarManager.core import enums
from StarManager.core.config import settings
from StarManager.core.managers.custom_access_level import CachedCustomAccessLevelRow

NUMOJIS = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


def join(chid):
    kb = Keyboard(inline=True)

    kb.add(
        Callback("Начать", {"cmd": "join", "chat_id": chid}),
        KeyboardButtonColor.POSITIVE,
    )

    return kb.get_json()


def rejoin(chid):
    kb = Keyboard(inline=True)

    kb.add(
        Callback("Активировать", {"cmd": "rejoin", "chat_id": chid, "activate": 1}),
        KeyboardButtonColor.POSITIVE,
    )
    kb.add(
        Callback("Не активировать", {"cmd": "rejoin", "chat_id": chid, "activate": 0}),
        KeyboardButtonColor.POSITIVE,
    )

    return kb.get_json()


def stats(uid, id):
    kb = Keyboard(inline=True)

    kb.add(
        Callback("Блоки", {"cmd": "bans", "uid": uid, "sender": id}),
        KeyboardButtonColor.PRIMARY,
    )
    kb.add(
        Callback("Варны", {"cmd": "warns", "uid": uid, "sender": id}),
        KeyboardButtonColor.PRIMARY,
    )
    kb.add(
        Callback("Муты", {"cmd": "mutes", "uid": uid, "sender": id}),
        KeyboardButtonColor.PRIMARY,
    )

    return kb.get_json()


def nlist(uid, page, count):
    kb = Keyboard(inline=True)

    if page != 0:
        kb.add(
            Callback("⏪", {"cmd": "prev_page_nlist", "page": page - 1, "uid": uid}),
            KeyboardButtonColor.NEGATIVE,
        )
    kb.add(
        Callback("Без ников", {"cmd": "nonicklist", "uid": uid}),
        KeyboardButtonColor.SECONDARY,
    )
    if count > 30:
        kb.add(
            Callback("⏩", {"cmd": "next_page_nlist", "page": page + 1, "uid": uid}),
            KeyboardButtonColor.POSITIVE,
        )

    return kb.get_json()


def nnlist(uid, page, count):
    kb = Keyboard(inline=True)

    if page != 0:
        kb.add(
            Callback("⏪", {"cmd": "prev_page_nnlist", "page": page - 1, "uid": uid}),
            KeyboardButtonColor.NEGATIVE,
        )
    kb.add(
        Callback("С никами", {"cmd": "nicklist", "uid": uid}),
        KeyboardButtonColor.SECONDARY,
    )
    if count > 30:
        kb.add(
            Callback("⏩", {"cmd": "next_page_nnlist", "page": page + 1, "uid": uid}),
            KeyboardButtonColor.POSITIVE,
        )

    return kb.get_json()


def mutelist(uid, page, count):
    kb = Keyboard(inline=True)

    if count:
        kb.add(
            Callback("Снять все муты", {"cmd": "mutelist_delall", "uid": uid}),
            KeyboardButtonColor.POSITIVE,
        )
        kb.row()
    if page != 0:
        kb.add(
            Callback("⏪", {"cmd": "prev_page_mutelist", "page": page - 1, "uid": uid}),
            KeyboardButtonColor.NEGATIVE,
        )
    if count > (30 * (page + 1)):
        kb.add(
            Callback("⏩", {"cmd": "next_page_mutelist", "page": page + 1, "uid": uid}),
            KeyboardButtonColor.POSITIVE,
        )

    return kb.get_json()


def warnlist(uid, page, count):
    kb = Keyboard(inline=True)

    if count:
        kb.add(
            Callback("Снять все варны", {"cmd": "warnlist_delall", "uid": uid}),
            KeyboardButtonColor.POSITIVE,
        )
        kb.row()
    if page != 0:
        kb.add(
            Callback("⏪", {"cmd": "prev_page_warnlist", "page": page - 1, "uid": uid}),
            KeyboardButtonColor.NEGATIVE,
        )
    if count > 30:
        kb.add(
            Callback("⏩", {"cmd": "next_page_warnlist", "page": page + 1, "uid": uid}),
            KeyboardButtonColor.POSITIVE,
        )

    return kb.get_json()


def banlist(uid, page, count):
    kb = Keyboard(inline=True)

    if count:
        kb.add(
            Callback("Снять все баны", {"cmd": "banlist_delall", "uid": uid}),
            KeyboardButtonColor.POSITIVE,
        )
        kb.row()
    if page != 0:
        kb.add(
            Callback("⏪", {"cmd": "prev_page_banlist", "page": page, "uid": uid}),
            KeyboardButtonColor.NEGATIVE,
        )
    if count > (30 * (page + 1)):
        kb.add(
            Callback("⏩", {"cmd": "next_page_banlist", "page": page, "uid": uid}),
            KeyboardButtonColor.POSITIVE,
        )

    return kb.get_json()


def demote_choose(uid, chat_id):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Без прав",
            {"cmd": "demote", "uid": uid, "chat_id": chat_id, "option": "lvl"},
        ),
        KeyboardButtonColor.PRIMARY,
    )
    kb.add(
        Callback(
            "Всех", {"cmd": "demote", "uid": uid, "chat_id": chat_id, "option": "all"}
        ),
        KeyboardButtonColor.PRIMARY,
    )

    return kb.get_json()


def demote_accept(uid, chat_id, option):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Да",
            {"cmd": "demote_accept", "uid": uid, "chat_id": chat_id, "option": option},
        ),
        KeyboardButtonColor.POSITIVE,
    )
    kb.add(
        Callback("Нет", {"cmd": "demote_disaccept", "uid": uid, "chat_id": chat_id}),
        KeyboardButtonColor.NEGATIVE,
    )

    return kb.get_json()


def statuslist(uid, page, count):
    kb = Keyboard(inline=True)

    if page != 0:
        kb.add(
            Callback("⏪", {"cmd": "prev_page_mutelist", "page": page, "uid": uid}),
            KeyboardButtonColor.NEGATIVE,
        )
    if count > (30 * (page + 1)):
        kb.add(
            Callback("⏩", {"cmd": "next_page_mutelist", "page": page, "uid": uid}),
            KeyboardButtonColor.POSITIVE,
        )

    return kb.get_json()


def settings_(uid):
    kb = Keyboard(inline=True)
    kb.add(Callback("➖ Основные", {"uid": uid, "cmd": "settings", "category": "main"}))
    kb.add(
        Callback(
            "🎮 Развлекательные",
            {"uid": uid, "cmd": "settings", "category": "entertaining"},
        )
    )
    kb.row()
    kb.add(
        Callback(
            "⛔️ Анти-Спам", {"uid": uid, "cmd": "settings", "category": "antispam"}
        )
    )
    kb.add(
        Callback(
            "🌓 Ночной режим",
            {
                "uid": uid,
                "cmd": "change_setting",
                "category": "main",
                "setting": "nightmode",
            },
        )
    )
    kb.row()
    kb.add(
        Callback(
            "💬 Приветствие",
            {
                "uid": uid,
                "cmd": "change_setting",
                "category": "main",
                "setting": "welcome",
            },
        )
    )
    kb.add(
        Callback(
            "🔢 Каптча",
            {
                "uid": uid,
                "cmd": "change_setting",
                "category": "main",
                "setting": "captcha",
            },
        )
    )
    kb.row()
    kb.add(
        Callback(
            "🗑️ Автоудаление",
            {
                "uid": uid,
                "cmd": "change_setting",
                "category": "main",
                "setting": "autodelete",
            },
        )
    )
    # if uid in DEVS:
    #     kb.add(Callback('⭐️ Star protect', {"uid": uid, "cmd": "settings", "category": 'protect'}))

    return kb.get_json()


def chat(uid, ispublic=False):
    kb = Keyboard(inline=True)

    kb.add(Callback("⚙️ Настройки беседы", {"uid": uid, "cmd": "settings_menu"}))
    kb.row()
    kb.add(
        Callback(
            "Сделать приватной" if ispublic else "Сделать публичной",
            {"uid": uid, "cmd": "turnpublic"},
        ),
        KeyboardButtonColor.POSITIVE if ispublic else KeyboardButtonColor.NEGATIVE,
    )

    return kb.get_json()


def settings_goto(uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("Назад", {"uid": uid, "cmd": "settings_menu"}))

    return kb.get_json()


def settings_antispam(uid):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "💬 Сообщения",
            {"uid": uid, "cmd": "settings_menu_antispam", "setting": "msgs"},
        )
    )
    kb.add(
        Callback(
            "⛔️ Спам-фильтр",
            {"uid": uid, "cmd": "settings_menu_antispam", "setting": "spam"},
        )
    )
    kb.row()
    kb.add(
        Callback(
            "🔞 NSFW",
            {
                "uid": uid,
                "cmd": "change_setting",
                "category": "antispam",
                "setting": "disallowNSFW",
            },
        )
    )
    kb.add(Callback("Назад", {"uid": uid, "cmd": "settings_menu"}))

    return kb.get_json()


def settings_antispam_msgs(uid):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Сообщений в минуту",
            {
                "uid": uid,
                "cmd": "change_setting",
                "category": "antispam",
                "setting": "messagesPerMinute",
            },
        )
    )
    kb.row()
    kb.add(
        Callback(
            "Длина сообщений",
            {
                "uid": uid,
                "cmd": "change_setting",
                "category": "antispam",
                "setting": "maximumCharsInMessage",
            },
        )
    )
    kb.row()
    kb.add(Callback("Назад", {"uid": uid, "cmd": "settings", "category": "antispam"}))

    return kb.get_json()


def settings_antispam_spam(uid):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Ссылки на ВК",
            {
                "uid": uid,
                "cmd": "change_setting",
                "category": "antispam",
                "setting": "vkLinks",
            },
        )
    )
    kb.row()
    kb.add(
        Callback(
            "Пересылки",
            {
                "uid": uid,
                "cmd": "change_setting",
                "category": "antispam",
                "setting": "forwardeds",
            },
        )
    )
    kb.row()
    kb.add(
        Callback(
            "Ссылки",
            {
                "uid": uid,
                "cmd": "change_setting",
                "category": "antispam",
                "setting": "disallowLinks",
            },
        )
    )
    kb.row()
    kb.add(Callback("Назад", {"uid": uid, "cmd": "settings", "category": "antispam"}))

    return kb.get_json()


def settings_category(uid, category, chat_settings):
    if category == "antispam":
        return settings_antispam(uid)
    kb = Keyboard(inline=True)
    c = 1
    for k, i in chat_settings.items():
        name = settings.settings_meta.positions[category][k][not i]
        if k in settings.settings_meta.countable_no_category:
            continue
        if name in ["Вкл.", "Выкл."]:
            color = KeyboardButtonColor.NEGATIVE if i else KeyboardButtonColor.POSITIVE
        else:
            color = KeyboardButtonColor.PRIMARY
        name = "Включить" if name == "Вкл." else name
        name = "Выключить" if name == "Выкл." else name
        if k in settings.settings_meta.countable:
            name = "Настроить"
            color = KeyboardButtonColor.PRIMARY
        name = f"{NUMOJIS[c]} " + name
        kb.add(
            Callback(
                name,
                {
                    "uid": uid,
                    "cmd": "change_setting",
                    "category": category,
                    "setting": k,
                },
            ),
            color,
        )
        if c % 2 == 0:
            kb.row()
        c += 1
    if c % 2 == 1:
        kb.row()
    kb.add(Callback("Назад", {"uid": uid, "cmd": "settings_menu"}))

    return kb.get_json()


def settings_change_countable(
    uid,
    category,
    setting=None,
    chat_settings=None,
    altsettings=None,
    onlybackbutton=False,
):
    kb = Keyboard(inline=True)
    if setting in settings.settings_meta.subcats and setting:
        kb.add(
            Callback(
                "Назад",
                {
                    "uid": uid,
                    "cmd": f"settings_menu_{category}",
                    "setting": settings.settings_meta.subcats[setting],
                },
            )
        )
    elif setting not in settings.settings_meta.countable_no_category:
        kb.add(Callback("Назад", {"uid": uid, "cmd": "settings", "category": category}))
    else:
        if onlybackbutton:
            kb.add(
                Callback(
                    "Назад",
                    {
                        "uid": uid,
                        "cmd": "change_setting",
                        "category": category,
                        "setting": setting,
                    },
                )
            )
        else:
            kb.add(Callback("Назад", {"uid": uid, "cmd": "settings_menu"}))
    if onlybackbutton:
        return kb.get_json()

    c = 1
    if setting and chat_settings:
        for i in settings.settings_meta.countable_changemenu[setting]:
            color = KeyboardButtonColor.PRIMARY
            if isinstance(i["button"], str):
                name = i["button"]
            else:
                name = i["button"][chat_settings[category][setting]]
                if i["button"] in (
                    ["Выкл.", "Вкл."],
                    ["Вкл.", "Выкл."],
                    ["Включить", "Выключить"],
                    ["Выключить", "Включить"],
                ):
                    color = (
                        KeyboardButtonColor.NEGATIVE
                        if chat_settings[category][setting]
                        else KeyboardButtonColor.POSITIVE
                    )
                elif i["action"] == "turnalt" and altsettings:
                    color = (
                        KeyboardButtonColor.POSITIVE
                        if altsettings[category][setting]
                        else KeyboardButtonColor.NEGATIVE
                    )
                else:
                    raise Exception
            if chat_settings[category][setting] or (
                i["button"]
                in (
                    ["Выкл.", "Вкл."],
                    ["Вкл.", "Выкл."],
                    ["Включить", "Выключить"],
                    ["Выключить", "Включить"],
                )
                and c <= 2
            ):
                if c % 2 == 0:
                    kb.row()
                kb.add(
                    Callback(
                        name,
                        {
                            "uid": uid,
                            "cmd": "settings_change_countable",
                            "action": i["action"],
                            "category": category,
                            "setting": setting,
                        },
                    ),
                    color,
                )
                c += 1

    return kb.get_json()


def settings_set_punishment(uid, category, setting):
    kb = Keyboard(inline=True)
    kb.add(
        Callback(
            "Назад",
            {
                "uid": uid,
                "cmd": "change_setting",
                "category": category,
                "setting": setting,
            },
        ),
        KeyboardButtonColor.NEGATIVE,
    )
    kb.row()
    if (
        setting not in settings.settings_meta.countable_punishment_no_delete_message
        and category != "antispam"
    ):
        kb.add(
            Callback(
                "Удалить сообщение",
                {
                    "uid": uid,
                    "cmd": "settings_set_punishment",
                    "action": "deletemessage",
                    "category": category,
                    "setting": setting,
                },
            )
        )
        kb.row()
    kb.add(
        Callback(
            "Без наказания",
            {
                "uid": uid,
                "cmd": "settings_set_punishment",
                "action": "",
                "category": category,
                "setting": setting,
            },
        )
    )
    if category == "antispam":
        kb.row()
        kb.add(
            Callback(
                "Предупреждение",
                {
                    "uid": uid,
                    "cmd": "settings_set_punishment",
                    "action": "warn",
                    "category": category,
                    "setting": setting,
                },
            )
        )
    kb.add(
        Callback(
            "Замутить",
            {
                "uid": uid,
                "cmd": "settings_set_punishment",
                "action": "mute",
                "category": category,
                "setting": setting,
            },
        )
    )
    kb.row()
    kb.add(
        Callback(
            "Исключить",
            {
                "uid": uid,
                "cmd": "settings_set_punishment",
                "action": "kick",
                "category": category,
                "setting": setting,
            },
        )
    )
    kb.add(
        Callback(
            "Заблокировать",
            {
                "uid": uid,
                "cmd": "settings_set_punishment",
                "action": "ban",
                "category": category,
                "setting": setting,
            },
        )
    )

    return kb.get_json()


def settings_set_preset(uid, category, setting, data):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Назад",
            {
                "uid": uid,
                "cmd": "change_setting",
                "category": category,
                "setting": setting,
            },
        ),
        KeyboardButtonColor.NEGATIVE,
    )
    kb.row()
    for i in settings.settings_meta.preset_buttons[setting]:
        kb.add(
            Callback(
                str(i["name"]),
                {
                    "uid": uid,
                    "cmd": "settings_set_preset",
                    "action": i["action"],
                    "category": category,
                    "setting": setting,
                    "data": i,
                },
            ),
            KeyboardButtonColor.POSITIVE
            if setting == "forwardeds" and (data or 0) == i["value"]
            else None,
        )
        kb.row()

    return kb.get_json()


def settings_setlist(uid, category, setting, type):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Список исключений",
            {"uid": uid, "cmd": "settings_exceptionlist", "setting": setting},
        )
    )
    kb.row()
    kb.add(
        Callback(
            "Добавить",
            {
                "uid": uid,
                "cmd": "settings_listaction",
                "setting": setting,
                "type": type,
                "action": "add",
                "category": category,
            },
        )
    )
    kb.add(
        Callback(
            "Удалить",
            {
                "uid": uid,
                "cmd": "settings_listaction",
                "setting": setting,
                "type": type,
                "action": "remove",
                "category": category,
            },
        )
    )
    kb.row()
    kb.add(
        Callback(
            "Назад",
            {
                "uid": uid,
                "cmd": "change_setting",
                "category": category,
                "setting": setting,
            },
        ),
        KeyboardButtonColor.NEGATIVE,
    )

    return kb.get_json()


def settings_set_welcome(uid, text, img, url):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Назад",
            {
                "uid": uid,
                "cmd": "change_setting",
                "category": "main",
                "setting": "welcome",
            },
        )
    )
    kb.add(
        Callback("Установить текст", {"uid": uid, "cmd": "settings_set_welcome_text"})
    )
    kb.row()
    kb.add(Callback("Изображение", {"uid": uid, "cmd": "settings_set_welcome_photo"}))
    kb.add(Callback("URL-кнопка", {"uid": uid, "cmd": "settings_set_welcome_url"}))
    if text or img or url:
        kb.row()
    k = 0
    if text and ((img and url) or (not img and not url) or not url):
        kb.add(
            Callback(
                "Удалить текст", {"uid": uid, "cmd": "settings_unset_welcome_text"}
            ),
            KeyboardButtonColor.NEGATIVE,
        )
        k = 1
    if img and ((text and url) or (not text and not url) or not url):
        kb.add(
            Callback(
                "Удалить изображение",
                {"uid": uid, "cmd": "settings_unset_welcome_photo"},
            ),
            KeyboardButtonColor.NEGATIVE,
        )
        if k:
            kb.row()
    if url:
        kb.add(
            Callback(
                "Удалить кнопку", {"uid": uid, "cmd": "settings_unset_welcome_url"}
            ),
            KeyboardButtonColor.NEGATIVE,
        )

    return kb.get_json()


def premium():
    kb = Keyboard(inline=True)

    kb.add(OpenLink(label="Написать", link="https://vk.com/im?sel=697163236"))

    return kb.get_json()


def giveowner(chat_id, chid, uid):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Да", {"cmd": "giveowner", "chat_id": chat_id, "uid": uid, "chid": chid}
        ),
        KeyboardButtonColor.POSITIVE,
    )
    kb.add(
        Callback("Нет", {"cmd": "giveowner_no", "chat_id": chat_id}),
        KeyboardButtonColor.NEGATIVE,
    )

    return kb.get_json()


def top(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "✨ Лиги",
            {"cmd": "top_leagues", "league": 1, "chat_id": chat_id, "uid": uid},
        )
    )
    kb.add(Callback("⚔ Дуэли", {"cmd": "top_duels", "chat_id": chat_id, "uid": uid}))
    kb.row()
    kb.add(Callback("📊 Репутация", {"cmd": "top_rep", "chat_id": chat_id, "uid": uid}))
    kb.add(Callback("🔢 Примеры", {"cmd": "top_math", "chat_id": chat_id, "uid": uid}))
    kb.row()
    kb.add(Callback("🎁 Бонус", {"cmd": "top_bonus", "chat_id": chat_id, "uid": uid}))
    kb.add(Callback("🪙 Монетки", {"cmd": "top_coins", "chat_id": chat_id, "uid": uid}))

    return kb.get_json()


def top_leagues(chat_id, uid, league, availableleagues):
    kb = Keyboard(inline=True)

    kb.add(Callback("◀ Назад", {"cmd": "top", "chat_id": chat_id, "uid": uid}))
    c = 0
    for k, i in enumerate(settings.leagues.leagues):
        if k not in availableleagues:
            continue
        if c % 2 == 0:
            kb.row()
        kb.add(
            Callback(
                i,
                {"cmd": "top_leagues", "league": k + 1, "chat_id": chat_id, "uid": uid},
            ),
            KeyboardButtonColor.POSITIVE
            if k + 1 == league
            else KeyboardButtonColor.NEGATIVE,
        )
        c += 1

    return kb.get_json()


def top_duels(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("◀ Назад", {"cmd": "top", "chat_id": chat_id, "uid": uid}))
    kb.add(
        Callback(
            "🥨 В беседе", {"cmd": "top_duels_in_chat", "chat_id": chat_id, "uid": uid}
        ),
        KeyboardButtonColor.SECONDARY,
    )

    return kb.get_json()


def top_duels_in_chat(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("◀ Назад", {"cmd": "top", "chat_id": chat_id, "uid": uid}))
    kb.add(Callback("🥯 Общее", {"cmd": "top_duels", "chat_id": chat_id, "uid": uid}))

    return kb.get_json()


def top_rep(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("◀ Назад", {"cmd": "top", "chat_id": chat_id, "uid": uid}))
    kb.add(
        Callback(
            "🔽 Отрицательные", {"cmd": "top_rep_neg", "chat_id": chat_id, "uid": uid}
        ),
        KeyboardButtonColor.NEGATIVE,
    )
    kb.add(
        Callback(
            "🥨 В беседе", {"cmd": "top_rep_in_chat", "chat_id": chat_id, "uid": uid}
        ),
        KeyboardButtonColor.SECONDARY,
    )

    return kb.get_json()


def top_rep_neg(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("◀ Назад", {"cmd": "top", "chat_id": chat_id, "uid": uid}))
    kb.add(
        Callback(
            "🔼 Положительные", {"cmd": "top_rep", "chat_id": chat_id, "uid": uid}
        ),
        KeyboardButtonColor.POSITIVE,
    )
    kb.add(
        Callback(
            "🥨 В беседе",
            {"cmd": "top_rep_in_chat_neg", "chat_id": chat_id, "uid": uid},
        ),
        KeyboardButtonColor.SECONDARY,
    )

    return kb.get_json()


def top_rep_in_chat(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("◀ Назад", {"cmd": "top", "chat_id": chat_id, "uid": uid}))
    kb.add(
        Callback(
            "🔽 Отрицательные",
            {"cmd": "top_rep_in_chat_neg", "chat_id": chat_id, "uid": uid},
        ),
        KeyboardButtonColor.NEGATIVE,
    )
    kb.add(Callback("🥯 Общее", {"cmd": "top_rep", "chat_id": chat_id, "uid": uid}))

    return kb.get_json()


def top_rep_in_chat_neg(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("◀ Назад", {"cmd": "top", "chat_id": chat_id, "uid": uid}))
    kb.add(
        Callback(
            "🔼 Положительные",
            {"cmd": "top_rep_in_chat", "chat_id": chat_id, "uid": uid},
        ),
        KeyboardButtonColor.POSITIVE,
    )
    kb.add(Callback("🥯 Общее", {"cmd": "top_rep_neg", "chat_id": chat_id, "uid": uid}))

    return kb.get_json()


def top_math(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("◀ Назад", {"cmd": "top", "chat_id": chat_id, "uid": uid}))

    return kb.get_json()


def top_bonus(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("◀ Назад", {"cmd": "top", "chat_id": chat_id, "uid": uid}))
    kb.add(
        Callback(
            "🥨 В беседе", {"cmd": "top_bonus_in_chat", "chat_id": chat_id, "uid": uid}
        ),
        KeyboardButtonColor.SECONDARY,
    )

    return kb.get_json()


def top_bonus_in_chat(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("◀ Назад", {"cmd": "top", "chat_id": chat_id, "uid": uid}))
    kb.add(Callback("🥯 Общее", {"cmd": "top_bonus", "chat_id": chat_id, "uid": uid}))

    return kb.get_json()


def top_coins(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("◀ Назад", {"cmd": "top", "chat_id": chat_id, "uid": uid}))
    kb.add(
        Callback(
            "🥨 В беседе", {"cmd": "top_coins_in_chat", "chat_id": chat_id, "uid": uid}
        ),
        KeyboardButtonColor.SECONDARY,
    )

    return kb.get_json()


def top_coins_in_chat(chat_id, uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("◀ Назад", {"cmd": "top", "chat_id": chat_id, "uid": uid}))
    kb.add(Callback("🥯 Общее", {"cmd": "top_coins", "chat_id": chat_id, "uid": uid}))

    return kb.get_json()


def premmenu(uid, chat_settings, prem):
    kb = Keyboard(inline=True)

    k = 0
    for e, i in chat_settings.items():
        if e != "clear_by_fire" and not prem:
            continue
        k += 1
        if i:
            color = KeyboardButtonColor.POSITIVE
        elif i is not None:
            color = KeyboardButtonColor.NEGATIVE
        else:
            color = KeyboardButtonColor.PRIMARY
        kb.add(
            Callback(
                f"{k}",
                {
                    "uid": uid,
                    "cmd": "premmenu_turn"
                    if e in settings.premium_menu.turn
                    else "premmenu_action",
                    "setting": e,
                    "pos": i,
                },
            ),
            color,
        )

    return kb.get_json()


def premmenu_back(uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("Назад", {"uid": uid, "cmd": "premmenu"}))

    return kb.get_json()


def market():
    kb = Keyboard(inline=True)

    kb.add(
        OpenLink(label="Купить", link="https://star-manager.ru"),
        KeyboardButtonColor.POSITIVE,
    )
    kb.row()
    kb.add(
        OpenLink(
            label="Купить через бота",
            link=f"https://vk.com/im?sel=-{settings.vk.group_id}",
        ),
        KeyboardButtonColor.POSITIVE,
    )

    return kb.get_json()


def buy(uid):
    kb = Keyboard(inline=True)

    for i in settings.premium_cost.cost.keys():
        kb.add(Callback(f"{i} д.", {"cmd": "buy", "uid": uid, "days": i}))

    return kb.get_json()


def buy_order(url):
    kb = Keyboard(inline=True)

    kb.add(OpenLink(label="Оплатить", link=url), KeyboardButtonColor.POSITIVE)

    return kb.get_json()


def pm_market(uid):
    kb = Keyboard(inline=True)

    kb.add(
        OpenLink(label="Купить", link="https://star-manager.ru"),
        KeyboardButtonColor.POSITIVE,
    )
    kb.row()
    kb.add(
        Callback("Купить через бота", {"cmd": "market", "uid": uid}),
        KeyboardButtonColor.SECONDARY,
    )

    return kb.get_json()


def duel(uid, coins):
    kb = Keyboard(inline=True)

    kb.add(
        Callback("Сразиться", {"cmd": "duel", "uid": uid, "coins": coins}),
        KeyboardButtonColor.SECONDARY,
    )

    return kb.get_json()


def resetnick_accept(uid, chat_id):
    kb = Keyboard(inline=True)

    kb.add(
        Callback("Да", {"cmd": "resetnick_accept", "uid": uid, "chat_id": chat_id}),
        KeyboardButtonColor.POSITIVE,
    )
    kb.add(
        Callback("Нет", {"cmd": "resetnick_disaccept", "uid": uid, "chat_id": chat_id}),
        KeyboardButtonColor.NEGATIVE,
    )

    return kb.get_json()


def resetaccess_accept(uid, chat_id, lvl):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Да",
            {"cmd": "resetaccess_accept", "uid": uid, "chat_id": chat_id, "lvl": lvl},
        ),
        KeyboardButtonColor.POSITIVE,
    )
    kb.add(
        Callback(
            "Нет",
            {
                "cmd": "resetaccess_disaccept",
                "uid": uid,
                "chat_id": chat_id,
                "lvl": lvl,
            },
        ),
        KeyboardButtonColor.NEGATIVE,
    )

    return kb.get_json()


def kickmenu(uid):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Исключить без ников", {"cmd": "kick_nonick", "sender": uid, "uid": uid}
        ),
        KeyboardButtonColor.PRIMARY,
    )
    kb.row()
    kb.add(
        Callback("Исключить с никами", {"cmd": "kick_nick", "sender": uid, "uid": uid}),
        KeyboardButtonColor.PRIMARY,
    )
    kb.row()
    kb.add(
        Callback(
            "Исключить удалённых", {"cmd": "kick_banned", "sender": uid, "uid": uid}
        ),
        KeyboardButtonColor.PRIMARY,
    )

    return kb.get_json()


def rewards(uid):
    kb = Keyboard(inline=True)

    kb.add(
        Callback("Обновить", {"cmd": "refresh_rewards", "sender": uid, "uid": uid}),
        KeyboardButtonColor.POSITIVE,
    )

    return kb.get_json()


def notif(uid):
    kb = Keyboard(inline=True)

    kb.add(
        Callback("Напоминания беседы", {"cmd": "notif", "sender": uid, "uid": uid}),
        KeyboardButtonColor.POSITIVE,
    )

    return kb.get_json()


def notif_list(uid, notifs, page=1):
    kb = Keyboard(inline=True)
    kx = 4
    ttlx = 0
    ppgg = (page * 8) - 8
    if page > 1:
        ppgg += 1
        kb.add(
            Callback(
                "<<",
                payload={"cmd": "notif", "page": page - 1, "uid": uid, "sender": uid},
            )
        )
        kx -= 1
        ttlx -= 1
    if len(notifs) > 8 * page:
        kb.add(
            Callback(
                ">>",
                payload={"cmd": "notif", "page": page + 1, "uid": uid, "sender": uid},
            )
        )
        kx -= 1
        ttlx -= 1
    notifs = notifs[ppgg:]

    for k, i in enumerate(notifs):
        if i[0] == 1:
            c = KeyboardButtonColor.POSITIVE
        else:
            c = KeyboardButtonColor.NEGATIVE
        kb.add(
            Callback(
                f"{k + 1 + ppgg}",
                {"cmd": "notif_select", "sender": uid, "uid": uid, "name": i[1]},
            ),
            c,
        )
        if k == kx:
            kb.row()
        if k + 1 == 10 + ttlx:
            break

    return kb.get_json()


def notification(uid, status, name):
    kb = Keyboard(inline=True)

    kb.add(
        Callback("Назад", {"cmd": "notif", "sender": uid, "uid": uid}),
        KeyboardButtonColor.NEGATIVE,
    )
    if status == 1:
        kb.add(
            Callback(
                "Выключить",
                {
                    "cmd": "notification_status",
                    "sender": uid,
                    "uid": uid,
                    "turn": 0,
                    "name": name,
                },
            ),
            KeyboardButtonColor.NEGATIVE,
        )
    else:
        kb.add(
            Callback(
                "Включить",
                {
                    "cmd": "notification_status",
                    "sender": uid,
                    "uid": uid,
                    "turn": 1,
                    "name": name,
                },
            ),
            KeyboardButtonColor.POSITIVE,
        )
    kb.row()
    kb.add(
        Callback(
            "Текст",
            {"cmd": "notification_text", "sender": uid, "uid": uid, "name": name},
        ),
        KeyboardButtonColor.SECONDARY,
    )
    kb.add(
        Callback(
            "Время",
            {"cmd": "notification_time", "sender": uid, "uid": uid, "name": name},
        ),
        KeyboardButtonColor.SECONDARY,
    )
    kb.row()
    kb.add(
        Callback(
            "Теги", {"cmd": "notification_tag", "sender": uid, "uid": uid, "name": name}
        ),
        KeyboardButtonColor.SECONDARY,
    )
    kb.add(
        Callback(
            "Удалить",
            {"cmd": "notification_delete", "sender": uid, "uid": uid, "name": name},
        ),
        KeyboardButtonColor.NEGATIVE,
    )

    return kb.get_json()


def notification_time(uid, name):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Назад", {"cmd": "notif_select", "sender": uid, "uid": uid, "name": name}
        ),
        KeyboardButtonColor.NEGATIVE,
    )
    kb.add(
        Callback(
            "Один раз",
            {
                "cmd": "notification_time_change",
                "sender": uid,
                "uid": uid,
                "name": name,
                "type": "single",
            },
        ),
        KeyboardButtonColor.SECONDARY,
    )
    kb.row()
    kb.add(
        Callback(
            "Каждый день",
            {
                "cmd": "notification_time_change",
                "sender": uid,
                "uid": uid,
                "name": name,
                "type": "everyday",
            },
        ),
        KeyboardButtonColor.SECONDARY,
    )
    kb.add(
        Callback(
            "Каждые XX минут",
            {
                "cmd": "notification_time_change",
                "sender": uid,
                "uid": uid,
                "name": name,
                "type": "everyxmin",
            },
        ),
        KeyboardButtonColor.SECONDARY,
    )

    return kb.get_json()


def notification_tag(uid, name):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Назад", {"cmd": "notif_select", "sender": uid, "uid": uid, "name": name}
        ),
        KeyboardButtonColor.NEGATIVE,
    )
    kb.row()
    kb.add(
        Callback(
            "Отключить",
            {
                "cmd": "notification_tag_change",
                "sender": uid,
                "uid": uid,
                "name": name,
                "type": "1",
            },
        ),
        KeyboardButtonColor.SECONDARY,
    )
    kb.add(
        Callback(
            "Всех",
            {
                "cmd": "notification_tag_change",
                "sender": uid,
                "uid": uid,
                "name": name,
                "type": "2",
            },
        ),
        KeyboardButtonColor.SECONDARY,
    )
    kb.row()
    kb.add(
        Callback(
            "С правами",
            {
                "cmd": "notification_tag_change",
                "sender": uid,
                "uid": uid,
                "name": name,
                "type": "3",
            },
        ),
        KeyboardButtonColor.SECONDARY,
    )
    kb.add(
        Callback(
            "Без прав",
            {
                "cmd": "notification_tag_change",
                "sender": uid,
                "uid": uid,
                "name": name,
                "type": "4",
            },
        ),
        KeyboardButtonColor.SECONDARY,
    )

    return kb.get_json()


def listasync(uid, total, page=1):
    kb = Keyboard(inline=True)

    if page > 1:
        kb.add(
            Callback(
                "<<",
                payload={
                    "cmd": "listasync",
                    "sender": uid,
                    "uid": uid,
                    "page": page - 1,
                },
            )
        )
    if total > page * 10:
        kb.add(
            Callback(
                ">>",
                payload={
                    "cmd": "listasync",
                    "sender": uid,
                    "uid": uid,
                    "page": page + 1,
                },
            )
        )

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

    kb.add(
        Callback("Уровень 0", {"cmd": "help", "uid": uid, "page": 0, "prem": u_prem}),
        colors[0],
    )
    kb.add(
        Callback("Уровень 1", {"cmd": "help", "uid": uid, "page": 1, "prem": u_prem}),
        colors[1],
    )
    kb.row()
    kb.add(
        Callback("Уровень 2", {"cmd": "help", "uid": uid, "page": 2, "prem": u_prem}),
        colors[2],
    )
    kb.add(
        Callback("Уровень 3", {"cmd": "help", "uid": uid, "page": 3, "prem": u_prem}),
        colors[3],
    )
    kb.row()
    kb.add(
        Callback("Уровень 4", {"cmd": "help", "uid": uid, "page": 4, "prem": u_prem}),
        colors[4],
    )
    kb.add(
        Callback("Уровень 5", {"cmd": "help", "uid": uid, "page": 5, "prem": u_prem}),
        colors[5],
    )
    kb.row()
    kb.add(
        Callback("Уровень 6", {"cmd": "help", "uid": uid, "page": 6, "prem": u_prem}),
        colors[6],
    )
    kb.add(
        Callback("Уровень 7", {"cmd": "help", "uid": uid, "page": 7, "prem": u_prem}),
        colors[7],
    )
    kb.row()
    kb.add(
        Callback("Premium", {"cmd": "help", "uid": uid, "page": 8, "prem": u_prem}),
        colors[8],
    )

    return kb.get_json()


def cmd(uid, page=0):
    kb = Keyboard(inline=True)

    kb.add(Callback("Мои ассоциации", {"cmd": "cmdlist", "uid": uid, "page": page}))

    return kb.get_json()


def cmdlist(uid, page, cmdslen):
    kb = Keyboard(inline=True)

    if page > 0:
        kb.add(Callback("<<", {"cmd": "cmdlist", "uid": uid, "page": page - 1}))
    if cmdslen > (10 * page) + 10:
        kb.add(Callback(">>", {"cmd": "cmdlist", "uid": uid, "page": page + 1}))

    return kb.get_json()


def check(uid, id):
    kb = Keyboard(inline=True)

    kb.add(
        Callback("Блокировки", {"cmd": "check", "uid": uid, "id": id, "check": "ban"})
    )
    kb.add(
        Callback(
            "Предупреждения", {"cmd": "check", "uid": uid, "id": id, "check": "warn"}
        )
    )
    kb.add(Callback("Муты", {"cmd": "check", "uid": uid, "id": id, "check": "mute"}))

    return kb.get_json()


def check_history(uid, id, punishment, isempty):
    kb = Keyboard(inline=True)

    kb.add(
        Callback("Назад", {"cmd": "check_menu", "uid": uid, "id": id}),
        KeyboardButtonColor.NEGATIVE,
    )
    kb.add(
        Callback(
            "История",
            {
                "cmd": "check_history",
                "uid": uid,
                "id": id,
                "check": punishment,
                "ie": isempty,
            },
        )
    )

    return kb.get_json()


def punish_unpunish(uid, id, punish, cmid):
    kb = Keyboard(inline=True)

    if punish == "mute":
        name = "Размутить"
    elif punish == "ban":
        name = "Разбанить"
    elif punish == "warn":
        name = "Снять варн"
    else:
        return None

    kb.add(Callback(name, {"cmd": f"un{punish}", "uid": uid, "id": id, "cmid": cmid}))
    kb.row()
    deletemessages_add(kb, uid, [cmid])

    return kb.get_json()


def urlbutton(url, name, color=None):
    if not url:
        return
    kb = Keyboard(inline=True)
    kb.add(OpenLink(label=name, link=url), color=color)
    return kb.get_json()


def prefix(uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("Добавить префикс", {"cmd": "prefix_add", "uid": uid}))
    kb.add(Callback("Удалить префикс", {"cmd": "prefix_del", "uid": uid}))
    kb.row()
    kb.add(Callback("Список префиксов", {"cmd": "prefix_list", "uid": uid}))

    return kb.get_json()


def prefix_back(uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("Назад", {"cmd": "prefix", "uid": uid}))

    return kb.get_json()


def timeout(uid, silence):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Выключить" if silence else "Включить", {"cmd": "timeout_turn", "uid": uid}
        ),
        KeyboardButtonColor.NEGATIVE if silence else KeyboardButtonColor.POSITIVE,
    )
    if not silence:
        kb.add(Callback("Настройки", {"cmd": "timeout_settings", "uid": uid}))

    return kb.get_json()


def timeout_settings(
    uid, allowed, custom: bool = False, limit: int = 10, page: int = 0
):
    kb = Keyboard(inline=True)

    kb.add(Callback("Назад", {"cmd": "timeout", "uid": uid}))
    kb.add(
        Callback(
            "Стандартные" if custom else "Пользовательские",
            {"cmd": "timeout_settings", "uid": uid, "custom": not custom},
        )
    )
    kb.row()
    for i in range(
        (page * 6 + 1) if custom else 0,
        min((page + 1) * 6 + 1, (limit + 1)) if custom else 7,
    ):
        kb.add(
            Callback(
                f"Уровень {i}",
                {
                    "cmd": "timeout_settings_turn",
                    "uid": uid,
                    "lvl": i,
                    "custom": custom,
                    "page": page,
                },
            ),
            KeyboardButtonColor.POSITIVE
            if i in allowed
            else KeyboardButtonColor.NEGATIVE,
        )
        if i % 2 == 0:
            kb.row()
    if custom:
        if page != 0:
            kb.add(
                Callback(
                    "⏪",
                    {
                        "cmd": "timeout_settings",
                        "uid": uid,
                        "custom": custom,
                        "page": page - 1,
                    },
                )
            )
        maxpage = int(limit / 6)
        if page == 0 or page == maxpage:
            kb.add(Callback(f"[{page}/{maxpage}]", {"cmd": "_"}))
        if page < maxpage:
            kb.add(
                Callback(
                    "⏩",
                    {
                        "cmd": "timeout_settings",
                        "uid": uid,
                        "custom": custom,
                        "page": page + 1,
                    },
                )
            )

    return kb.get_json()


def chats(uid, total_chats: int, page: int, mode: enums.ChatsMode):
    kb = Keyboard(inline=True)

    if page != 0:
        kb.add(
            Callback(
                "⏪", {"cmd": "chats", "page": page - 1, "uid": uid, "mode": mode.value}
            )
        )
    kb.add(
        Callback(
            "Обычные" if mode == enums.ChatsMode.premium else "🏆 PREMIUM",
            {
                "cmd": "chats",
                "uid": uid,
                "mode": (
                    enums.ChatsMode.premium
                    if mode == enums.ChatsMode.all
                    else enums.ChatsMode.all
                ).value,
                "page": 0,
            },
        ),
        KeyboardButtonColor.SECONDARY if mode == enums.ChatsMode.all else None,
    )
    if total_chats > 15 * (page + 1):
        kb.add(
            Callback(
                "⏩", {"cmd": "chats", "page": page + 1, "uid": uid, "mode": mode.value}
            )
        )

    return kb.get_json()


def antitag(uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("Посмотреть список", {"cmd": "antitag_list", "uid": uid}))

    return kb.get_json()


def import_(uid, importchatid):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Начать", {"cmd": "import_start", "uid": uid, "importchatid": importchatid}
        )
    )
    kb.add(
        Callback(
            "Настроить",
            {"cmd": "import_settings", "uid": uid, "importchatid": importchatid},
        )
    )

    return kb.get_json()


def import_settings(uid, importchatid, chat_settings):
    kb = Keyboard(inline=True)

    for k, (kn, i) in enumerate(chat_settings.items()):
        if k and k % 3 == 0:
            kb.row()
        kb.add(
            Callback(
                f"[{k + 1}]. {'Выключить' if i else 'Включить'}",
                {
                    "cmd": "import_turn",
                    "uid": uid,
                    "importchatid": importchatid,
                    "setting": kn,
                },
            ),
            KeyboardButtonColor.NEGATIVE if i else KeyboardButtonColor.POSITIVE,
        )
    kb.add(
        Callback("Назад", {"cmd": "import", "uid": uid, "importchatid": importchatid}),
        KeyboardButtonColor.PRIMARY,
    )

    return kb.get_json()


def blocklist(uid):
    kb = Keyboard(inline=True)

    kb.add(
        Callback("Беседы", {"cmd": "blocklist_chats", "uid": uid}),
        KeyboardButtonColor.PRIMARY,
    )

    return kb.get_json()


def blocklist_chats(uid):
    kb = Keyboard(inline=True)

    kb.add(
        Callback("Пользователи", {"cmd": "blocklist", "uid": uid}),
        KeyboardButtonColor.PRIMARY,
    )

    return kb.get_json()


def block_chatblocked():
    kb = Keyboard(inline=True)
    kb.add(
        OpenLink(
            label="Связаться с администратором", link=settings.service.contact_admin
        )
    )
    return kb.get_json()


def bindlist(uid, group, page, count):
    kb = Keyboard(inline=True)

    if page != 0:
        kb.add(
            Callback(
                "⏪", {"cmd": "bindlist", "page": page - 1, "group": group, "uid": uid}
            )
        )
    if count > (15 * (page + 1)):
        kb.add(
            Callback(
                "⏩", {"cmd": "bindlist", "page": page + 1, "group": group, "uid": uid}
            )
        )

    return kb.get_json()


def premium_expire(promo):
    kb = Keyboard(inline=True)
    kb.add(
        OpenLink(
            label="✅ Продлить подписку",
            link=f"https://star-manager.ru/payment?promo={promo}",
        ),
        KeyboardButtonColor.POSITIVE,
    )
    return kb.get_json()


def filter(uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("Наказания", {"cmd": "filter_punishments", "uid": uid}))
    kb.add(Callback("Список запрещённых слов", {"cmd": "filter_list", "uid": uid}))

    return kb.get_json()


def filter_punishments(uid, pnt):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Удалить сообщение", {"cmd": "filter_punishments_set", "uid": uid, "set": 0}
        ),
        KeyboardButtonColor.POSITIVE if pnt == 0 else KeyboardButtonColor.NEGATIVE,
    )
    kb.add(
        Callback("Замутить", {"cmd": "filter_punishments_set", "uid": uid, "set": 1}),
        KeyboardButtonColor.POSITIVE if pnt == 1 else KeyboardButtonColor.NEGATIVE,
    )
    kb.add(
        Callback(
            "Заблокировать", {"cmd": "filter_punishments_set", "uid": uid, "set": 2}
        ),
        KeyboardButtonColor.POSITIVE if pnt == 2 else KeyboardButtonColor.NEGATIVE,
    )

    return kb.get_json()


def filter_list(uid, page, count):
    kb = Keyboard(inline=True)

    if page > 0:
        kb.add(Callback("⏪", {"cmd": "filter_list", "page": page - 1, "uid": uid}))
    if count > (25 * (page + 1)):
        kb.add(Callback("⏩", {"cmd": "filter_list", "page": page + 1, "uid": uid}))

    return kb.get_json()


def filteradd(uid, word, msg):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Добавить в связки", {"cmd": "filteradd", "word": word, "msg": msg, "uid": uid}
        )
    )

    return kb.get_json()


def filterdel(uid, word, msg):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Удалить в связке", {"cmd": "filterdel", "word": word, "msg": msg, "uid": uid}
        )
    )

    return kb.get_json()


def deletemessages_add(kb, uid, msgs: list):
    kb.add(
        Callback("Очистить", {"cmd": "deletemessages", "msgs": msgs, "uid": uid}),
        KeyboardButtonColor.POSITIVE,
    )


def deletemessages(uid, msgs: list):
    kb = Keyboard(inline=True)

    deletemessages_add(kb, uid, msgs)

    return kb.get_json()


def shop(uid):
    kb = Keyboard(inline=True)

    kb.add(Callback("Опыт", {"cmd": "shop_xp", "uid": uid}))
    kb.add(Callback("Бонусы", {"cmd": "shop_bonuses", "uid": uid}))

    return kb.get_json()


def shop_xp(uid, limit):
    kb = Keyboard(inline=True)

    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

    for k, xp in enumerate(settings.shop.xp.keys()):
        kb.add(
            Callback(
                emojis[k],
                {"cmd": "shop_buy", "uid": uid, "category": "xp", "option": xp},
            ),
            None
            if limit[k] < settings.shop.xp[xp]["limit"]
            else KeyboardButtonColor.NEGATIVE,
        )
    kb.row()
    kb.add(Callback("Назад", {"cmd": "shop", "uid": uid}))

    return kb.get_json()


def shop_bonuses(uid, activated_bonuses: list):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "1️⃣",
            {
                "cmd": "shop_buy",
                "uid": uid,
                "category": "bonuses",
                "option": 0,
            },
        ),
        None if not activated_bonuses[0] else KeyboardButtonColor.NEGATIVE,
    )
    kb.add(
        Callback(
            "2️⃣",
            {
                "cmd": "shop_buy",
                "uid": uid,
                "category": "bonuses",
                "option": 1,
            },
        ),
        None if not activated_bonuses[0] else KeyboardButtonColor.NEGATIVE,
    )
    kb.add(
        Callback(
            "3️⃣",
            {
                "cmd": "shop_buy",
                "uid": uid,
                "category": "bonuses",
                "option": 2,
            },
        ),
        None if not activated_bonuses[1] else KeyboardButtonColor.NEGATIVE,
    )
    kb.row()
    kb.add(Callback("Назад", {"cmd": "shop", "uid": uid}))

    return kb.get_json()


def raid(uid, status: bool):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Выключить" if status else "Включить", {"cmd": "raid_turn", "uid": uid}
        ),
        KeyboardButtonColor.NEGATIVE if status else KeyboardButtonColor.POSITIVE,
    )
    kb.add(Callback("Настройки", {"cmd": "raid_settings", "uid": uid}))

    return kb.get_json()


def raid_settings(uid, trigger_status: bool):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Выключить" if trigger_status else "Включить",
            {"cmd": "raid_trigger_turn", "uid": uid},
        ),
        KeyboardButtonColor.NEGATIVE
        if trigger_status
        else KeyboardButtonColor.POSITIVE,
    )
    kb.add(Callback("Лимиты", {"cmd": "raid_trigger_set", "uid": uid}))

    return kb.get_json()


def rps(uid, bet, call_to):
    kb = Keyboard(inline=True)

    kb.add(
        Callback("Сразиться", {"cmd": "rps", "uid": call_to or uid, "bet": bet}),
        KeyboardButtonColor.SECONDARY,
    )

    return kb.get_json()


def rps_play(uid, bet):
    kb = Keyboard(inline=True)

    kb.add(
        Callback("Камень", {"cmd": "rps_play", "pick": "r", "uid": uid, "bet": bet}),
        KeyboardButtonColor.SECONDARY,
    )
    kb.add(
        Callback("Бумага", {"cmd": "rps_play", "pick": "p", "uid": uid, "bet": bet}),
        KeyboardButtonColor.SECONDARY,
    )
    kb.row()
    kb.add(
        Callback("Ножницы", {"cmd": "rps_play", "pick": "s", "uid": uid, "bet": bet}),
        KeyboardButtonColor.SECONDARY,
    )

    return kb.get_json()


def customlevel_to_settings(
    uid,
    level: int,
    label: str = "Настроить",
    kb: Optional[Keyboard] = None,
    clear_type_queue: bool = False,
):
    if kb is None:
        kb = Keyboard(inline=True)

    kb.add(
        Callback(
            label,
            {
                "cmd": "customlevel_settings",
                "uid": uid,
                "level": level,
                "clear": clear_type_queue,
                "page": 0,
            },
        ),
        KeyboardButtonColor.SECONDARY,
    )

    return kb.get_json()


def customlevel_settings(
    uid, level: CachedCustomAccessLevelRow, levelmenu_page: Optional[int] = None
):
    def _payload(action: str):
        return {
            "cmd": "customlevel_action",
            "action": action,
            "uid": uid,
            "level": level.access_level,
            "levelmenu_page": levelmenu_page,
        }

    kb = Keyboard(inline=True)

    if levelmenu_page is not None:
        kb.add(
            Callback("Назад", {"cmd": "levelmenu", "uid": uid, "page": levelmenu_page}),
            KeyboardButtonColor.PRIMARY,
        )
    kb.add(
        Callback("Выключить" if level.status else "Включить", _payload("turn")),
        KeyboardButtonColor.POSITIVE if level.status else KeyboardButtonColor.NEGATIVE,
    )
    kb.add(Callback("Удалить", _payload("delete")), KeyboardButtonColor.NEGATIVE)
    kb.row()
    kb.add(Callback("Приоритет", _payload("set_priority")))
    kb.add(Callback("Название", _payload("set_name")))
    kb.add(Callback("Эмодзи", _payload("set_emoji")))
    kb.row()
    kb.add(Callback("Команды", _payload("set_commands")), KeyboardButtonColor.PRIMARY)
    kb.add(
        Callback("Шаблоны", _payload("set_commands_presets")),
        KeyboardButtonColor.PRIMARY,
    )
    kb.row()
    kb.add(
        Callback("Забрать права", _payload("remove_all")), KeyboardButtonColor.NEGATIVE
    )

    return kb.get_json()


def customlevel_delete_yon(uid, level: int):
    kb = Keyboard(inline=True)

    customlevel_to_settings(uid, level, "Назад", kb)
    kb.add(
        Callback("Удалить", {"cmd": "customlevel_delete", "uid": uid, "level": level}),
        KeyboardButtonColor.NEGATIVE,
    )

    return kb.get_json()


def customlevel_remove_all_yon(uid, level: int):
    kb = Keyboard(inline=True)

    customlevel_to_settings(uid, level, "Назад", kb)
    kb.add(
        Callback(
            "Удалить", {"cmd": "customlevel_remove_all", "uid": uid, "level": level}
        ),
        KeyboardButtonColor.NEGATIVE,
    )

    return kb.get_json()


def customlevel_set_commands_presets(uid, level: int):
    kb = Keyboard(inline=True)

    customlevel_to_settings(uid, level, "Назад", kb)
    for k in range(0, 7):
        kb.add(
            Callback(
                f"[{k}] {settings.lvl_names[int(k)]}",
                {
                    "cmd": "customlevel_set_commands_preset",
                    "uid": uid,
                    "level": level,
                    "preset": k,
                },
            ),
        )
        if k % 2 == 0:
            kb.row()

    return kb.get_json()


def levelmenu(uid, levels: List[CachedCustomAccessLevelRow], page: int = 0):
    kb = Keyboard(inline=True)

    levels = sorted(levels, key=lambda x: x.access_level)

    if page != 0:
        kb.add(Callback("⏪", {"cmd": "levelmenu", "uid": uid, "page": page - 1}))
    if len(levels) > 6:
        kb.add(
            Callback(
                f"[{page}/{len(levels) // 6 + bool(len(levels) % 6)}]", {"cmd": "_"}
            )
        )
    if len(levels) > (6 * (page + 1)):
        kb.add(Callback("⏩", {"cmd": "levelmenu", "uid": uid, "page": page + 1}))
    kb.row()

    for k in range(6):
        try:
            level = levels[6 * page + k]
        except IndexError:
            break
        emoji = f"{level.emoji} " if level.emoji else ""
        kb.add(
            Callback(
                f"[{level.access_level}] {emoji}{level.name}",
                {
                    "cmd": "customlevel_settings",
                    "uid": uid,
                    "level": level.access_level,
                    "pre_page": page,
                },
            )
        )
        if k % 3 == 2:
            kb.row()

    return kb.get_json()


def staff(uid, custom: bool = True, levels: Optional[int] = None, page: int = 0):
    kb = Keyboard(inline=True)

    kb.add(
        Callback(
            "Пользовательские" if custom else "Стандартные",
            {"cmd": "staff", "uid": uid, "custom": custom, "pre_page": 0},
        ),
        KeyboardButtonColor.PRIMARY,
    )
    if custom and levels is not None:
        kb.row()
        if page != 0:
            kb.add(Callback("⏪", {"cmd": "staff", "uid": uid, "page": page - 1}))
        if levels > 10:
            kb.add(
                Callback(f"[{page}/{levels // 10 + bool(levels % 10)}]", {"cmd": "_"})
            )
        if levels > 10 * (page + 1):
            kb.add(Callback("⏩", {"cmd": "staff", "uid": uid, "page": page + 1}))

    return kb.get_json()


def event(uid):
    kb = Keyboard(inline=True)

    kb.add(
        Callback("❄️ Открыть кейс", {"cmd": "event_open", "uid": uid}),
        KeyboardButtonColor.PRIMARY,
    )

    return kb.get_json()
