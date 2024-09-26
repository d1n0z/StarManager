import time
from ast import literal_eval

from config.config import GWARN_TIME_LIMIT
from db import LastFiveCommands, GlobalWarns


async def global_warn_handle(uid, cmd) -> None:
    res = LastFiveCommands.get_or_none(LastFiveCommands.uid == uid)
    if res is not None:
        cmds = literal_eval(res.cmds)
        cmd_time = literal_eval(res.cmd_time)
    else:
        res = LastFiveCommands.create(uid=uid, cmds='[]', cmd_time='[]')
        cmds = [1, 1]
        cmd_time = [1, 1]

    try:
        if time.time() - int(cmd_time[0]) <= int(GWARN_TIME_LIMIT) and cmds.count(cmds[0]) >= 5:
            gw = GlobalWarns.get_or_none(GlobalWarns.uid == uid)
            if gw is None:
                gw = GlobalWarns.create(uid=uid, warns=0, time=time.time())
            gw.warns += 1
            gw.save()
    except:
        pass

    cmds.insert(0, cmd)
    cmd_time.insert(0, int(time.time()))
    if len(cmds) > 5:
        cmds.pop()
        cmd_time.pop()

    res.cmds = f'{cmds}'
    res.cmd_time = f'{cmd_time}'
    return
