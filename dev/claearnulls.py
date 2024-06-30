from unused.olddb import dbhandle, getChat

tables = dbhandle.get_tables()
for i in tables:
    try:
        x = getChat(i)
        x.update(kicked=0).where(x.kicked.is_null()).execute()
        x.update(global_warn=0).where(x.global_warn.is_null()).execute()
        x.update(global_ban=0).where(x.global_ban.is_null()).execute()
        x.update(premium=0).where(x.premium.is_null()).execute()
    except:
        pass
