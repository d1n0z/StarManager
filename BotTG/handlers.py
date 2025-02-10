import traceback

from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.payload import decode_payload

from Bot.utils import getUserName, pointWords, addUserXP
from BotTG import keyboard, states
from config import config
from config.config import TG_PUBLIC_CHAT_ID
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
    try:
        await query.message.edit_reply_markup(reply_markup=keyboard.joingiveaway(count[0]))
    except:
        pass
    await query.answer(text='Вы успешно участвуете в конкурсе.', show_alert=True)


@router.message(CommandStart(deep_link=True))
async def startdeep(message: Message, state: FSMContext, command: CommandObject):
    await message.delete()
    payload = decode_payload(command.args)
    if not payload.isdigit():
        payload = 0
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            await c.execute('insert into tgwaitingforsubscription (tgid) values (%s) on conflict (tgid) do nothing ',
                            (message.from_user.id,))
            await conn.commit()
    msg = await message.bot.send_message(
        chat_id=message.from_user.id, reply_markup=keyboard.check(int(payload)),
        text=f'<b>⭐️ Добро пожаловать, <a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}'
             f'</a>.\n\nЧтобы использовать бота вы должны присоединиться к <a href="'
             f'{(await message.bot.create_chat_invite_link(TG_PUBLIC_CHAT_ID)).invite_link}">нашей группе</a>.</b>',)
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'start'))
@router.message(CommandStart(), F.chat.type == "private")
async def start(message: Message | CallbackQuery, state: FSMContext):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            if await (await c.execute('select id from tgwaitingforsubscription where tgid=%s',
                                      (message.from_user.id,))).fetchone():
                return
            if isinstance(message, Message):
                await message.delete()
            vkid = await (await c.execute('select vkid from tglink where tgid=%s', (message.from_user.id,))).fetchone()
    if not vkid:
        msg = await message.bot.send_message(
            chat_id=message.from_user.id, reply_markup=keyboard.link(),
            text=f'<b>⭐️ Добро пожаловать, <a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}'
                 f'</a>.\n\nЗдесь вы можете привязать свой аккаунт ВКонтакте для получения опыта в случае победы в '
                 f'конкурсе.\n\nКроме того, вы можете получать по 150 опыта за каждого приглашенного друга в нашу '
                 f'группу.</b>',)
    else:
        msg = await message.bot.send_message(
            chat_id=message.from_user.id, reply_markup=keyboard.unlink(),
            text=f'<b>⭐️ Добро пожаловать, <a href="https://vk.com/id{vkid[0]}">{await getUserName(vkid[0])}</a>.\n\n'
                 f'Вы успешно привязали профиль ВК, теперь в случае выигрыша опыт автоматически будет выдан на аккаунт.'
                 f'\n\nКроме того, вы можете получать по 150 опыта за каждого приглашенного друга в нашу группу.</b>',)
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'link'))
async def link(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(
        chat_id=query.from_user.id, reply_markup=keyboard.back(),
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
    msg = await query.bot.send_message(chat_id=query.from_user.id, reply_markup=keyboard.back(), text=text)
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'ref'))
async def ref(query: CallbackQuery, state: FSMContext):
    async with (await pool()).connection() as conn:
        async with conn.cursor() as c:
            cnt = (await (await c.execute('select count(*) as c from tgreferrals where fromtgid=%s',
                                          (query.from_user.id,))).fetchone())[0]
    msg = await query.bot.send_message(
        chat_id=query.from_user.id, reply_markup=keyboard.back(),
        text=f'<b>👤 Пригласите ваших друзей подписаться на нашу группу бота в Telegram и получайте за каждого друга '
             f'по 150 опыта. Для этого достаточно поделится ссылкой на вступление в чат:\n\n<code>'
             f'{await create_start_link(query.bot, str(query.from_user.id), encode=True)}</code>\n\n💡 '
             f'Вами приглашено: {pointWords(cnt, ("пользователь", "пользователя", "пользователей"))}</b>')
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.startswith('checksub_')))
async def checksub(query: CallbackQuery, state: FSMContext):
    try:
        member = await query.bot.get_chat_member(chat_id=config.TG_PUBLIC_CHAT_ID, user_id=query.from_user.id)
        if not isinstance(member, (ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember)):
            raise Exception
    except:
        return await query.answer(text='Вы не являетесь участником группы.', show_alert=True)
    if (ref := int(query.data.split(':')[-1].split('_')[-1])) and ref != query.from_user.id:
        async with (await pool()).connection() as conn:
            async with conn.cursor() as c:
                await c.execute('delete from tgwaitingforsubscription where tgid=%s', (query.from_user.id,))
                if not (await (await c.execute('select id from tgreferrals where tgid=%s',
                                               (query.from_user.id,))).fetchone()) and (
                        vkid := await (await c.execute('select vkid from tglink where tgid=%s', (ref,))).fetchone()):
                    await c.execute('insert into tgreferrals (fromtgid, tgid) values (%s, %s)',
                                    (int(ref), query.from_user.id))
                    await addUserXP(vkid[0], 150)
                    try:
                        await query.bot.send_message(
                            chat_id=ref, text=f'<b>🎁 Пользователь <a href="tg://user?id='
                                              f'{query.from_user.id}">{query.from_user.first_name}</a> подписался по '
                                              f'вашей ссылке, вы получили <code>+150 опыта</code>.</b>',)
                    except:
                        traceback.print_exc()
                await conn.commit()
    msg = await query.bot.send_message(
        chat_id=query.from_user.id, reply_markup=keyboard.link(),
        text=f'<b>⭐️ Добро пожаловать, <a href="tg://user?id={query.from_user.id}">{query.from_user.first_name}'
             f'</a>.\n\nЗдесь вы можете привязать свой аккаунт ВКонтакте для получения опыта в случае победы в '
             f'конкурсе.\n\nКроме того, вы можете получать по 150 опыта за каждого приглашенного друга в нашу '
             f'группу.</b>',)
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
    msg = await message.bot.send_message(chat_id=message.from_user.id, reply_markup=keyboard.back(), text=text)
    await state.update_data(msg=msg)
