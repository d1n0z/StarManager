from unused.olddb import dbhandle, getChat

tables = dbhandle.get_tables()
for i in tables:
    try:
        if len(str(i)) > 7:
            getChat(i).drop_table()
    except:
        pass
