import re

from unused.olddb import dbhandle, getChat

tables = dbhandle.get_tables()
for i in tables:
    try:
        chat = getChat(i)
        r = chat.select().where(chat.nickname.is_null(False))
        for y in r:
            if 48 >= len(y.nickname) != len(re.compile(r"[a-zA-Zа-яА-Я0-9.,:()_\-+| ]").findall(y.nickname)):
                chat.update(nickname=None).where(chat.uid == y.uid).execute()
    except:
        pass
