from unused.olddb import dbhandle, getChat

tables = dbhandle.get_tables()
for i in tables:
    try:
        getChat(i).drop_table()
    except:
        pass
