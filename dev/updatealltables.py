# from db import cursor
#
# query = "SELECT table_name FROM information_schema.tables WHERE table_type='BASE TABLE' AND table_schema = 'users'"
# cursor.execute(query)
# tables = cursor.fetchall()
# for ind, i in enumerate(tables):
#     query = f"ALTER TABLE `{i[0]}` ADD `kicked` TINYINT(1) NOT NULL DEFAULT '0' AFTER `last_warns_dates`;"
#     try:
#         cursor.execute(query)
#     except:
#         pass
