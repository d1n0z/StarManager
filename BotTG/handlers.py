import traceback

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember, ChatMember

from Bot.utils import getUserName
from BotTG import keyboard, states, scheduler
from config import config
from db import pool

router: Router = Router()


@router.callback_query(keyboard.Callback.filter(F.type == 'joingiveaway'))
async def joingiveaway(query: CallbackQuery, state: FSMContext):
    try:
        member = await query.bot.get_chat_member(chat_id=config.TG_PUBLIC_CHAT_ID, user_id=query.from_user.id)
        if not isinstance(member, (ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember)):
            raise Exception
    except:
        return await query.answer(text='Вы не являетесь участником группы.', show_alert=True)
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            vkid = await (await c.execute('select vkid from tglink where tgid=%s', (query.from_user.id,))).fetchone()
    if not vkid:
        return await query.answer(text='Ваш аккаунт не привязан к профилю ВКонтакте.', show_alert=True)

    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into tggiveawayusers (tgid) values (%s) on conflict (tgid) do nothing',
                            (query.from_user.id,))
            await conn.commit()
            count = await (await c.execute('select count(*) as c from tggiveawayusers')).fetchone()
    await query.message.edit_reply_markup(reply_markup=keyboard.joingiveaway(count[0]))
    await query.answer(text='Вы успешно участвуете в конкурсе.', show_alert=True)


@router.message(CommandStart(), F.chat.type == "private")
async def start(message: Message | CallbackQuery, state: FSMContext):
    await message.delete()
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            vkid = await (await c.execute('select vkid from tglink where tgid=%s', (message.from_user.id,))).fetchone()
    if not vkid:
        msg = await message.bot.send_message(
            chat_id=message.chat.id, reply_markup=keyboard.link(),
            text=f'<b>⭐️ Добро пожаловать, <a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}'
                 f'</a>.\n\nЗдесь вы можете привязать свой аккаунт ВКонтакте для получения опыта в случае победы в '
                 f'конкурсе. Для привязки нажмите кнопку ниже.</b>',)
    else:
        msg = await message.bot.send_message(
            chat_id=message.chat.id, reply_markup=keyboard.unlink(),
            text=f'<b>⭐️ Добро пожаловать, <a href="https://vk.com/id{vkid[0]}">{await getUserName(vkid[0])}</a>.\n\n'
                 f'Вы успешно привязали профиль ВК, теперь в случае выигрыша опыт автоматически будет выдан на аккаунт.'
                 f' Если вы хотите удалить привязку воспользуйтесь кнопкой ниже.</b>',)
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'link'))
async def link(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text=f'<b>📝 Откройте <a href="https://vk.com/im?sel=-222139436">личные сообщения с ботом Star Manager</a> во '
             f'ВКонтакте и отправьте команду <code>/code</code>. Бот отправит вам код, который необходимо ввести сюда.'
             f'</b>')
    await state.clear()
    await state.set_state(states.Link.link.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'unlink'))
async def unlink(query: CallbackQuery, state: FSMContext):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if (await c.execute('update tglink set tgid=null where tgid=%s', (query.from_user.id,))).rowcount:
                text = f'<b>✅ Вы успешно отвязали аккаунт.</b>'
                await conn.commit()
            else:
                text = f'<b>⚠️ Аккаунт не привязан.</b>'
    msg = await query.bot.send_message(chat_id=query.from_user.id, text=text)
    await state.clear()
    await state.update_data(msg=msg)


@router.message(states.Link.link)
async def link(message: Message, state: FSMContext):
    await message.delete()

    await state.clear()
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            vkid = await (await c.execute('select vkid from tglink where code=%s', (message.text,))).fetchone()
            if not vkid:
                text = f'<b>⚠️ Неверный код. Введите код из <code>/code</code>:</b>'
                await state.set_state(states.Link.link.state)
            else:
                text = f'<b>✅ Вы успешно привязали аккаунт(<a href="https://vk.com/id{vkid[0]}">id{vkid[0]}</a>).</b>'
                await c.execute('update tglink set tgid = %s where vkid=%s', (message.from_user.id, vkid[0],))
                await conn.commit()
    msg = await message.bot.send_message(chat_id=message.from_user.id, text=text)
    await state.update_data(msg=msg)
