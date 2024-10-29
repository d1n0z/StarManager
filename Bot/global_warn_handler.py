import time
from ast import literal_eval

from config.config import GWARN_TIME_LIMIT
from db import pool


async def global_warn_handle(uid, cmd) -> None:
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            res = await (await c.execute(
                'select id, cmds, cmd_time from lastfivecommands where uid=%s', (uid,))).fetchone()
    if res:
        cmds = literal_eval(res[1])
        cmd_time = literal_eval(res[2])
    else:
        cmds = []
        cmd_time = []

    if cmds and cmd_time and time.time() - int(cmd_time[0]) <= int(GWARN_TIME_LIMIT) and cmds.count(cmds[0]) >= 5:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                if not (await c.execute('update globalwarns set warns=warns+1 where uid=%s', (uid,))).rowcount:
                    await c.execute(
                        'insert into globalwarns (uid, warns, time) values (%s, 1, %s)', (uid, int(time.time())))
                await conn.commit()

    cmds.insert(0, cmd)
    cmd_time.insert(0, int(time.time()))
    if len(cmds) > 5:
        cmds.pop()
        cmd_time.pop()
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if res:
                await c.execute('update lastfivecommands set cmds = %s, cmd_time = %s where id=%s',
                                (f'{cmds}', f'{cmd_time}', res[0]))
            else:
                await c.execute('insert into lastfivecommands (uid, cmds, cmd_time) values (%s, %s, %s)',
                                (uid, f'{cmds}', f'{cmd_time}'))
                await conn.commit()
    return
