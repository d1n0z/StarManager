import datetime
import json
import time

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    ChatMemberAdministrator,
    ChatMemberMember,
    ChatMemberOwner,
    Message,
)
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.payload import decode_payload
from loguru import logger

from StarManager.core.config import settings
from StarManager.core.db import smallpool as pool
from StarManager.core.utils import addUserXP, archive_report, getUserName, pointWords
from StarManager.tgbot import keyboard, states

router: Router = Router()


@router.callback_query(keyboard.Callback.filter(F.type == "joingiveaway"))
async def joingiveaway(query: CallbackQuery, bot: Bot):
    try:
        member = await bot.get_chat_member(
            chat_id=settings.telegram.public_chat_id, user_id=query.from_user.id
        )
        if not isinstance(
            member, (ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember)
        ):
            raise Exception
    except Exception:
        return await query.answer(
            text="Вы не являетесь участником группы.", show_alert=True
        )
    async with (await pool()).acquire() as conn:
        async with conn.transaction():
            linked = await conn.fetchval(
                "select exists(select 1 from tglink where tgid=$1)", query.from_user.id
            )
    if not linked:
        return await query.answer(
            text="Ваш аккаунт не привязан к профилю ВКонтакте.", show_alert=True
        )

    async with (await pool()).acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "insert into tggiveawayusers (tgid) values ($1) on conflict (tgid) do nothing",
                query.from_user.id,
            )
            count = await conn.fetchval("select count(*) as c from tggiveawayusers")
    try:
        if isinstance(query.message, Message):
            await query.message.edit_reply_markup(
                reply_markup=keyboard.joingiveaway(count)
            )
    except Exception:
        pass
    await query.answer(text="Вы успешно участвуете в конкурсе.", show_alert=True)


@router.message(CommandStart(deep_link=True))
async def startdeep(
    message: Message, state: FSMContext, command: CommandObject, bot: Bot
):
    await message.delete()
    payload = decode_payload(command.args or "")
    if not payload.isdigit():
        payload = 0
    async with (await pool()).acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "insert into tgwaitingforsubscription (tgid) values ($1) on conflict (tgid) do nothing ",
                from_id := message.from_user.id,  # type: ignore
            )
    msg = await bot.send_message(
        chat_id=from_id,
        reply_markup=keyboard.check(int(payload)),
        text=f'<b>⭐️ Добро пожаловать, <a href="tg://user?id={from_id}">{message.from_user.first_name}'  # type: ignore
        f'</a>.\n\nЧтобы использовать бота вы должны присоединиться к <a href="'
        f'{(await bot.create_chat_invite_link(settings.telegram.public_chat_id)).invite_link}">нашей группе</a>.</b>',
    )
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == "start"))
@router.message(CommandStart(), F.chat.type == "private")
async def start(message: Message | CallbackQuery, state: FSMContext, bot: Bot):
    async with (await pool()).acquire() as conn:
        async with conn.transaction():
            if await conn.fetchval(
                "select 1 from tgwaitingforsubscription where tgid=$1",
                from_id := message.from_user.id,  # type: ignore
            ):
                return
            vkid = await conn.fetchval("select vkid from tglink where tgid=$1", from_id)
    if isinstance(message, Message):
        await message.delete()
    if not vkid:
        msg = await bot.send_message(
            chat_id=from_id,
            reply_markup=keyboard.link(),
            text=f'<b>⭐️ Добро пожаловать, <a href="tg://user?id={from_id}">{message.from_user.first_name}'  # type: ignore
            f"</a>.\n\nЗдесь вы можете привязать свой аккаунт ВКонтакте для получения опыта в случае победы в "
            f"конкурсе.\n\nКроме того, вы можете получать по 150 опыта за каждого приглашенного друга в нашу "
            f"группу.</b>",
        )
    else:
        msg = await bot.send_message(
            chat_id=from_id,
            reply_markup=keyboard.unlink(),
            text=f'<b>⭐️ Добро пожаловать, <a href="https://vk.com/id{vkid}">{await getUserName(vkid)}</a>.\n\n'
            f"Вы успешно привязали профиль ВК, теперь в случае выигрыша опыт автоматически будет выдан на аккаунт."
            f"\n\nКроме того, вы можете получать по 150 опыта за каждого приглашенного друга в нашу группу.</b>",
        )
    await state.clear()
    await state.update_data(msg=msg)


@router.message(Command("info"), F.chat.type == "private")
async def info(message: Message, state: FSMContext, bot: Bot):
    if (from_id := message.from_user.id) not in settings.telegram.admins:  # type: ignore
        return

    await message.delete()
    data = message.text.split()  # type: ignore
    if len(data) not in (1, 2) or (len(data) == 2 and not data[1].isdigit()):
        msg = await bot.send_message(
            chat_id=from_id,
            text="Usage: /info <optional:tg_user_id>.",
            parse_mode=None,
        )
        await state.clear()
        await state.update_data(msg=msg)
    answered_by = None if len(data) == 1 else data[1]

    now = datetime.datetime.now()
    today_start = datetime.datetime(now.year, now.month, now.day)
    today_timestamp = int(today_start.timestamp())
    week_start = today_start - datetime.timedelta(days=today_start.weekday())
    week_timestamp = int(week_start.timestamp())

    async with (await pool()).acquire() as conn:
        if answered_by is not None:
            stats = await conn.fetchrow(
                "select count(*) filter (where time >= $1 and answered_by = $3), count(*) filter (where time >= $2 and answered_by = $3), count(*) filter (where answered_by = $3) from reports",
                today_timestamp,
                week_timestamp,
                int(answered_by),
            )
        else:
            stats = await conn.fetchrow(
                "select count(*) filter (where time >= $1), count(*) filter (where time >= $2), count(*) from reports",
                today_timestamp,
                week_timestamp,
            )
    formatted_date = today_start.strftime("%d.%m.%Y")

    msg = await bot.send_message(
        chat_id=from_id,
        text=f"""📘 СТАТИСТИКА РЕПОРТОВ
├─ За день ({formatted_date}): {stats[0]} шт.
├─ За неделю: {stats[1]} шт.
└─ За всё время: {stats[2]} шт.""",
    )
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == "link"))
async def link(query: CallbackQuery, state: FSMContext, bot: Bot):
    msg = await bot.send_message(
        chat_id=query.from_user.id,
        reply_markup=keyboard.back(),
        text='<b>📝 Откройте <a href="https://vk.com/im?sel=-222139436">личные сообщения с ботом Star Manager</a> во ВКонтакте и отправьте команду <code>/code</code>. Бот отправит вам код, который необходимо ввести сюда.</b>',
    )
    await state.clear()
    await state.set_state(states.Link.link.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == "unlink"))
async def unlink(query: CallbackQuery, state: FSMContext, bot: Bot):
    async with (await pool()).acquire() as conn:
        async with conn.transaction():
            if await conn.fetchval(
                "update tglink set tgid=null where tgid=$1 returning 1",
                query.from_user.id,
            ):
                text = "<b>✅ Вы успешно отвязали аккаунт.</b>"
            else:
                text = "<b>⚠️ Аккаунт не привязан.</b>"
    msg = await bot.send_message(
        chat_id=query.from_user.id, reply_markup=keyboard.back(), text=text
    )
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == "ref"))
async def ref(query: CallbackQuery, state: FSMContext, bot: Bot):
    async with (await pool()).acquire() as conn:
        async with conn.transaction():
            cnt = await conn.fetchval(
                "select count(*) as c from tgreferrals where fromtgid=$1",
                query.from_user.id,
            )
    msg = await bot.send_message(
        chat_id=query.from_user.id,
        reply_markup=keyboard.back(),
        text=f"<b>👤 Пригласите ваших друзей подписаться на нашу группу бота в Telegram и получайте за каждого друга "
        f"по 150 опыта. Для этого достаточно поделится ссылкой на вступление в чат:\n\n<code>"
        f"{await create_start_link(bot, str(query.from_user.id), encode=True)}</code>\n\n💡 "
        f"Вами приглашено: {pointWords(cnt, ('пользователь', 'пользователя', 'пользователей'))}</b>",
    )
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.startswith("checksub_")))
async def checksub(query: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        member = await bot.get_chat_member(
            chat_id=settings.telegram.public_chat_id, user_id=query.from_user.id
        )
        if not isinstance(
            member, (ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember)
        ):
            raise Exception
    except Exception:
        return await query.answer(
            text="Вы не являетесь участником группы.", show_alert=True
        )
    if (
        ref := int(query.data.split(":")[-1].split("_")[-1])  # type: ignore
    ) and ref != query.from_user.id:
        async with (await pool()).acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "delete from tgwaitingforsubscription where tgid=$1",
                    query.from_user.id,
                )
                if not await conn.fetchval(
                    "select 1 from tgreferrals where tgid=$1", query.from_user.id
                ) and (
                    vkid := await conn.fetchval(
                        "select vkid from tglink where tgid=$1", ref
                    )
                ):
                    await conn.execute(
                        "insert into tgreferrals (fromtgid, tgid) values ($1, $2)",
                        int(ref),
                        query.from_user.id,
                    )
        await addUserXP(vkid, 150)
        try:
            await bot.send_message(
                chat_id=ref,
                text=f'<b>🎁 Пользователь <a href="tg://user?id='
                f'{query.from_user.id}">{query.from_user.first_name}</a> подписался по '
                f"вашей ссылке, вы получили <code>+150 опыта</code>.</b>",
            )
        except Exception:
            logger.exception("Checksub exception:")
    msg = await bot.send_message(
        chat_id=query.from_user.id,
        reply_markup=keyboard.link(),
        text=f'<b>⭐️ Добро пожаловать, <a href="tg://user?id={query.from_user.id}">{query.from_user.first_name}'
        f"</a>.\n\nЗдесь вы можете привязать свой аккаунт ВКонтакте для получения опыта в случае победы в "
        f"конкурсе.\n\nКроме того, вы можете получать по 150 опыта за каждого приглашенного друга в нашу "
        f"группу.</b>",
    )
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == "report_cancel"))
async def report_cancel(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.delete()  # type: ignore


@router.callback_query(keyboard.ReportCallback.filter())
async def report_callback_handler(
    query: CallbackQuery,
    callback_data: keyboard.ReportCallback,
    state: FSMContext,
    bot: Bot,
):
    action = callback_data.type
    if action == "answer":
        msg = await query.message.answer(  # type: ignore
            f"🟣 Введите ответ на обращение #{callback_data.report_id}:",
            reply_markup=keyboard.report_cancel(),
        )
        await state.clear()
        await state.set_state(states.Report.answer.state)
        await state.update_data(report_id=callback_data.report_id, msg=msg)
        return

    async with (await pool()).acquire() as conn:
        async with conn.transaction():
            report = await conn.fetchrow(
                "select uid, time, report_message_ids, report_text from reports where id=$1",
                callback_data.report_id,
            )
            if action == "ban":
                if not await conn.fetchval(
                    "select exists(select 1 from reportban where uid=$1 and time=0)",
                    report[0],
                ):
                    if not await conn.fetchval(
                        "update reportban set time = $1 where uid=$2 returning 1",
                        time.time() + 86400,
                        report[0],
                    ):
                        await conn.execute(
                            "insert into reportban (uid, time) values ($1, $2)",
                            report[0],
                            time.time() + 86400,
                        )
            elif action != "delete":
                raise Exception("Unknown ReportCallback action")
    message_ids = json.loads(report[2])
    await archive_report(
        message_ids, report[3], action, bot, callback_data.report_id, report[0]
    )


@router.message(states.Report.answer)
async def report_answer(message: Message, state: FSMContext, bot: Bot):
    await message.delete()

    report_id: int = (await state.get_data())["report_id"]
    await state.clear()

    async with (await pool()).acquire() as conn:
        report = await conn.fetchrow(
            "select uid, report_text, report_message_ids from reports where id=$1",
            report_id,
        )
        await conn.execute(
            "update reports set answered_by=$1 where id=$2",
            message.from_user.id,  # type: ignore
            report_id,
        )
    message_ids = json.loads(report[2])
    await archive_report(
        message_ids,
        report[1],
        "answer",
        bot,
        report_id,
        report[0],
        message.text,
    )


@router.message(states.Link.link)
async def link_s(message: Message, state: FSMContext, bot: Bot):
    await message.delete()

    await state.clear()
    async with (await pool()).acquire() as conn:
        async with conn.transaction():
            vkid = await conn.fetchval(
                "select vkid from tglink where code=$1", message.text
            )
            if not vkid:
                text = "<b>⚠️ Неверный код. Введите код из <code>/code</code>:</b>"
                await state.set_state(states.Link.link.state)
            else:
                text = f'<b>✅ Вы успешно привязали аккаунт(<a href="https://vk.com/id{vkid}">id{vkid}</a>).</b>'
                await conn.execute(
                    "update tglink set tgid = $1 where vkid=$2",
                    from_id := message.from_user.id,  # type: ignore
                    vkid,
                )
    msg = await bot.send_message(
        chat_id=from_id, reply_markup=keyboard.back(), text=text
    )
    await state.update_data(msg=msg)
