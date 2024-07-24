import traceback
from ast import literal_eval

from db import Warn

for i in Warn.select():
    try:
        l = literal_eval(i.last_warns_causes)
        for y in range(len(l)):
            if l[y] == '':
                l[y] = 'Без указания причины'
        i.last_warns_causes = l
        i.save()
        print(1)
    except:
        traceback.print_exc()
