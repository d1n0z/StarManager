import traceback

import sys
sys.path.append('../')

for i in dbhandle.get_tables():
    try:
        print(
            dbhandle.execute_sql(f'DELETE FROM "{i}" a USING ( SELECT MIN(ctid) as ctid, uid FROM "{i}" GROUP BY uid HAVING'
                             f' COUNT(*) > 1 ) b WHERE a.uid = b.uid AND a.ctid <> b.ctid;'))
    except:
        traceback.print_exc()
