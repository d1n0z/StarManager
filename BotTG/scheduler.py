import asyncio
import random
import traceback

import aiocron

from Bot.checkers import getULvlBanned
from Bot.utils import addUserXP, getUserName
from BotTG import keyboard
from BotTG.bot import bot
from config import config
from db import smallpool as pool


async def new():
    try:
        msg = await bot.send_message(
            chat_id=config.TG_PUBLIC_CHAT_ID, message_thread_id=config.TG_PUBLIC_GIVEAWAY_THREAD_ID,
            reply_markup=keyboard.joingiveaway(0),
            text=f'<b>🎁 Ежедневный конкурс на <code>999</code> опыта для <code>3</code> участников Telegram канала.'
                 f'</b>\n\n<blockquote><b>💬 Для участия в конкурсе вы должны быть подписаны на данный канал, а так же '
                 f'привязать профиль ВК для получения приза (<a href="https://t.me/{config.TG_BOT_USERNAME}?start=0">'
                 f'клик</a>). После выполнения всех условий нажмите кнопку "</b>Хочу участвовать<b>".</b></blockquote>'
                 f'\n\n<b>🕒 Окончание конкурса будет завтра в <code>09:00</code> по МСК</b>')
        async with (await pool()).acquire() as conn:
            async with conn.transaction():
                await conn.execute('insert into tggiveaways (mid) values ($1)', msg.message_id)
    except:
        traceback.print_exc()


async def end():
    try:
        winners = []
        async with (await pool()).acquire() as conn:
            async with conn.transaction():
                mid = await conn.fetch('select mid from tggiveaways')
                users = await conn.fetch('select tgid from tggiveawayusers')
                await conn.execute('delete from tggiveaways')
                await conn.execute('delete from tggiveawayusers')
                random.shuffle(users)
                for i in users:
                    user = await conn.fetchrow('select vkid, tgid from tglink where tgid=$1', i[0])
                    if user and not await getULvlBanned(user[0]):
                        winners.append(user)
                        if len(winners) == 3:
                            break
        for i in winners:
            await addUserXP(i[0], 999, False)
            try:
                await bot.send_message(
                    chat_id=i[1], text='<b>🎁 Поздравляем, вы выиграли 999 опыта в последнем конкурсе.</b>')
            except:
                pass
        emoji = ['🥇', '🥈', '🥉']
        text = '<b>🏆 Итоги ежедневного конкурса</b>\n\n'
        if winners:
            text += '<blockquote><b>'
            for k, i in enumerate(winners):
                text += f'{emoji[k]} Победитель: <a href="https://vk.com/id{i[0]}">{await getUserName(i[0])}</a>'
                if k - 1 != len(winners):
                    text += '\n'
            text += ('</b></blockquote>\n\n<b>💬 Призы в виде <code>999</code> опыта были начислены победителям на их '
                     'аккаунтах. Следующий конкурс в <code>10:00</code> МСК.</b>')
        else:
            text += '<b>⚠️ Никто не участвовал в этом конкурсе.</b>'
        await bot.edit_message_text(chat_id=config.TG_PUBLIC_CHAT_ID, message_id=mid[0], text=text)
    except:
        traceback.print_exc()


async def run(loop):
    asyncio.set_event_loop(loop)
    aiocron.crontab('0 10 * * *', func=new, loop=loop)
    aiocron.crontab('0 9 * * *', func=end, loop=loop)
