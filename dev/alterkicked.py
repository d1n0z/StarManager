from unused.olddb import dbhandle, getChat

tables = dbhandle.get_tables()
for i in tables:
    try:
        x = getChat(i)
        x.update(kicked=0).execute()
        dbhandle.execute_sql(f'ALTER TABLE "{i}" ALTER COLUMN kicked TYPE integer USING (kicked::integer);')
    except:
        pass
