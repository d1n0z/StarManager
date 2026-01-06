import asyncio
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiogram
import httpx
import pydantic
from aiogram.exceptions import TelegramBadRequest
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from starlette.responses import JSONResponse
from vkbottle_types.objects import UsersFields
from yookassa import Configuration, Payment

from StarManager.core import managers, utils
from StarManager.core.config import api as vkapi
from StarManager.core.config import settings, sitedata
from StarManager.core.db import smallpool as pool
from StarManager.core.event_queue import event_queue
from StarManager.site import enums, models
from StarManager.site.utils import (
    check_tg_timings,
    get_vk_timeouts_count,
    record_vk_timeout,
)
from StarManager.vkbot.bot import bot as vkbot

router = APIRouter()

templates = Jinja2Templates(directory=Path(__file__).parent / "static" / "templates")

oauth = OAuth()
oauth.register(
    name="vk",
    client_id=settings.vk.app_id,
    client_secret=settings.vk.app_secret,
    access_token_url="https://oauth.vk.com/access_token",
    authorize_url="https://oauth.vk.com/authorize",
    api_base_url="https://api.vk.com/method/",
    client_kwargs={
        "scope": "email",
        "token_endpoint_auth_method": "client_secret_post",
    },
)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={**sitedata, "user": request.session.get("user")},
    )


@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="contact.html",
        context={**sitedata, "user": request.session.get("user")},
    )


@router.get("/payment", response_class=HTMLResponse)
async def payment(request: Request, promo: str | None = None):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    if not promo:
        async with (await pool()).acquire() as conn:
            availpromo = await conn.fetchval(
                "select promo from prempromo where uid=$1", user["id"]
            )
        if availpromo:
            return RedirectResponse(f"/payment?promo={availpromo}")
    return templates.TemplateResponse(
        request=request, name="payment.html", context={**sitedata, "user": user}
    )


@router.get("/login")
async def login(request: Request):
    return await oauth.vk.authorize_redirect(  # type: ignore
        request, str(request.url_for("auth_vk_callback")).replace("http", "https", 1)
    )


@router.get("/auth/vk/callback")
async def auth_vk_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return HTMLResponse("Ошибка: отсутствует код авторизации", status_code=400)

    redirect_uri = str(request.url_for("auth_vk_callback")).replace("http", "https", 1)

    params = {
        "client_id": settings.vk.app_id,
        "client_secret": settings.vk.app_secret,
        "redirect_uri": redirect_uri,
        "code": code,
    }

    async with httpx.AsyncClient() as client:
        token_resp = await client.get(
            "https://oauth.vk.com/access_token", params=params
        )
        token_data = token_resp.json()

    if "error" in token_data:
        return HTMLResponse(f"Ошибка VK: {token_data}", status_code=400)

    access_token = token_data["access_token"]
    user_id = token_data["user_id"]
    email = token_data.get("email")

    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://api.vk.com/method/users.get",
            params={
                "access_token": access_token,
                "user_ids": user_id,
                "v": "5.131",
                "fields": "photo_200",
            },
        )
        user_data = user_resp.json()

    user = user_data["response"][0]
    request.session["user"] = models.User(
        id=user["id"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        photo=user.get("photo_200"),
        email=email,
    ).model_dump()

    return RedirectResponse(url="/")


@router.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/")


@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    user = (
        models.User.model_construct(**request.session["user"])
        if "user" in request.session
        else None
    )
    if not user:
        return RedirectResponse(url="/login")
    lvl, xp = await managers.xp.get(user.id, ("lvl", "xp"))
    if lvl is None or xp is None:
        lvl, xp = 1, 0
    async with (await pool()).acquire() as conn:
        chats = await conn.fetchval(
            "select count(*) as c from userjoineddate where uid=$1", user.id
        )
        rep = (
            await conn.fetchval("select rep from reputation where uid=$1", user.id) or 0
        )
        if rep > 0:
            rep = "+" + str(rep)
        paymenthistory = await conn.fetch(
            "select date, type, sum, comment from paymenthistory where uid=$1", user.id
        )
    premium = await managers.premium.get(user.id)
    premium = premium.time if premium else 0
    paymenthistory = [
        models.PaymentHistory(
            date=datetime.fromtimestamp(int(i[0])).strftime("%d.%m.%Y"),
            type=i[1],
            sum=i[2],
            comment=i[3],
        )
        for i in paymenthistory
    ]
    if premium > 0:
        premium = f"{int((premium - time.time()) / 86400) + 1} дней"
    else:
        premium = "Отсутствует"
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            **sitedata,
            "user": request.session.get("user"),
            "lvl": lvl,
            "xp": int(xp),
            "xpneeded": 1000,
            "progress": xp / 1000 * 100,
            "chats": chats,
            "rep": str(rep),
            "premium": premium,
            "paymenthistory": paymenthistory,
        },
    )


@router.post("/api/validate-promo")
async def validate_promo(request: Request):
    user = (
        models.User.model_construct(**request.session["user"])
        if "user" in request.session
        else None
    )
    try:
        data = models.PromoCheck(**(await request.json()))
    except pydantic.ValidationError:
        raise HTTPException(status_code=400, detail="Неверный формат промокода")

    async with (await pool()).acquire() as conn:
        promo_exists = await conn.fetchval(
            "select val from prempromo where promo=$1 and (uid=$2 or uid is null)",
            data.promo,
            user.id if user else None,
        )

    if promo_exists is not None:
        return JSONResponse(content={"valid": True, "discount": promo_exists})
    else:
        raise HTTPException(status_code=400, detail="Промокод не найден")


@router.post("/api/payment")
async def create_payment(request: Request, data: models.Item):
    user = (
        models.User.model_construct(**request.session["user"])
        if "user" in request.session
        else None
    )
    if not user:
        return JSONResponse(
            status_code=401,
            content={"detail": "auth_required", "redirect_url": "/login"},
        )

    from_id = user.id
    if data.type == "subscription" and (
        not hasattr(data.data, "duration") or not data.data.duration  # type: ignore
    ):
        raise HTTPException(status_code=400, detail="Не указана длительность подписки.")

    if data.type == "chat" and (
        not hasattr(data.data, "chat_id") or not data.data.chat_id  # type: ignore
    ):
        raise HTTPException(status_code=400, detail="Не указан ID чата.")

    if hasattr(data.data, "gift") and data.data.gift:  # type: ignore
        try:
            recipient = (
                await vkapi.users.get(
                    user_ids=[
                        await utils.search_id_in_message(data.data.gift_link, None, 1)  # type: ignore
                    ]  # type: ignore
                )
            )[0]
        except Exception:
            raise HTTPException(status_code=400, detail="Пользователь не существует.")
    else:
        try:
            recipient = (await vkapi.users.get(user_ids=[user.id]))[0]
        except Exception:
            traceback.print_exc()
            return JSONResponse(
                status_code=401,
                content={"detail": "auth_required", "redirect_url": "/login"},
            )

    if data.type == "subscription":
        if hasattr(data.data, "duration"):
            cost = origcost = settings.premium_cost.cost[data.data.duration]  # type: ignore
        else:
            raise HTTPException(
                status_code=400, detail="Не указана длительность подписки."
            )
    elif data.type == "chat":
        cost = origcost = sitedata["premiumchat"]
        chat_id: int = data.data.chat_id  # type: ignore
        chat = await managers.public_chats.get_chat(chat_id)
        if chat and chat.premium:
            raise HTTPException(
                status_code=400, detail="У этой беседы уже есть Premium-статус."
            )
        try:
            chat = await vkapi.messages.get_conversation_members(
                peer_id=2000000000 + chat_id
            )
            if not chat.items:
                raise Exception
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Не удалось найти беседу. Убедитесь, что бот добавлен в беседу "
                "и имеет статус администратора.",
            )
        if not [i for i in chat.items if i.member_id == int(recipient.id)]:
            raise HTTPException(
                status_code=400,
                detail="Вам нужно быть участником беседы, чтобы приобрести для неё Premium-статус.",
            )
    else:
        coins: int = data.data.value  # type: ignore
        cost = origcost = int(coins / 100 * 12.5)

    if hasattr(data.data, "promo") and data.data.promo:  # type: ignore
        async with (await pool()).acquire() as conn:
            promo = await conn.fetchrow(
                "select val, uid, id from prempromo where promo=$1",
                data.data.promo,  # type: ignore
            )
            cost = int(int(cost) * ((100 - promo[0]) / 100)) + 1
    else:
        promo = None

    payment = await utils.create_payment(
        cost,
        recipient.first_name,
        recipient.last_name,
        origcost,
        from_id,
        recipient.id,
        promo,
        chat_id if data.type == "chat" else None,
        coins if data.type == "coins" else None,
        user.email,
    )
    return JSONResponse(
        content={"valid": True, "payment_url": payment.confirmation.confirmation_url}  # type: ignore
    )


@router.post("/api/listener/yookassa")
@router.post("/api/listener/yookassa/")
async def yookassa(request: Request):
    try:
        logger.debug(f"New payment: {await request.json()}")
        if request.method != "POST":
            return RedirectResponse(url="/", status_code=303)

        payment = models.Payment(**(await request.json())["object"])
        Configuration.account_id = settings.yookassa.merchant_id
        Configuration.secret_key = settings.yookassa.token

        def _capture_and_return_yes():
            Payment.capture(payment.yookassa_order_id)
            return JSONResponse(content="YES")

        try:
            async with (await pool()).acquire() as conn:
                if not await conn.fetchval(
                    "update payments set success=1 where id=$1 and success=0 returning 1",
                    payment.order_id,
                ):
                    return _capture_and_return_yes()
                if payment.personal_promo:
                    await conn.execute(
                        "delete from prempromo where id=$1", payment.personal_promo
                    )
                    await conn.execute(
                        "update premiumexpirenotified set date=0 where uid=$1",
                        payment.from_id,
                    )
        except Exception:
            pass

        try:
            text = f"Номер: <b>#{payment.order_id}</b>\n"
            if payment.chat_id:
                payment_type = "Premium-беседа"
                text += f"""Тип: <code>"Premium-беседа"</code>
        ID беседы: <code>{payment.chat_id}</code>\n"""
            elif payment.coins:
                payment_type = utils.pluralize_words(
                    payment.coins, ("монетка", "монетки", "монеток")
                )
                text += f"""Тип: <code>"Монетки"</code>
        Количество: <code>{utils.pluralize_words(payment.coins, ("монетка", "монетки", "монеток"))}</code>\n"""
            else:
                days = list(settings.premium_cost.cost.keys())[
                    list(settings.premium_cost.cost.values()).index(payment.cost)
                ]
                payment_type = f"Premium-подписка ({days} дней)"
                text += f"""Тип: <code>"Premium-статус"</code>
        Срок: <code>{days} дней</code>\n"""

            text += f"""Сумма: <code>{payment.final_cost[:-3]} рублей</code>
        Покупатель: <a href="https://vk.com/id{payment.from_id}">@id{payment.from_id}</a>\n"""

            if not payment.chat_id:
                text += f'Получатель: <a href="https://vk.com/id{payment.to_id}">@id{payment.to_id}</a>\n'

            text += f"""Дата: <code>{datetime.now().strftime("%d.%m.%Y / %H:%M:%S")}</code>
        Способ: <code>Юкасса</code>
        Код платежа: <code>{payment.yookassa_order_id}</code>"""

            emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
            text = "\n".join(
                [f"{emojis[k]} {i}" for k, i in enumerate(text.split("\n"))]
            )

            if check_tg_timings():
                async with httpx.AsyncClient() as client:
                    await client.get(
                        f"https://api.telegram.org/bot{settings.telegram.token}/sendMessage",
                        params={
                            "chat_id": settings.telegram.chat_id,
                            "message_thread_id": settings.telegram.premium_thread_id,
                            "parse_mode": "html",
                            "disable_web_page_preview": True,
                            "text": text,
                        },
                    )
        except Exception:
            pass

        if payment.chat_id:
            await managers.public_chats.edit_premium(payment.chat_id, make_premium=True)
        elif payment.coins:
            await utils.add_user_coins(payment.to_id, payment.coins)
        elif payment.to_id:
            await managers.premium.add_premium(payment.to_id, days * 86400)

        if payment.chat_id:
            user = (await vkapi.users.get(user_ids=[payment.from_id]))[0]
            msg = (
                f"⭐️ [id{user.id}|{user.first_name} {user.last_name}], вы успешно приобрели Premium-статус для беседы "
                f"id{payment.chat_id}, поздравляю! Чтобы узнать все подробности и возможности Premium-статуса, вы можете "
                f"ознакомиться с информацией по ссылке — vk.cc/cJuJpg\n\n📗 Номер платежа: #{payment.order_id}\n📗 Время "
                f"покупки: {datetime.now().strftime('%d.%m.%Y / %H:%M:%S')}"
            )
        elif payment.coins:
            user = (await vkapi.users.get(user_ids=[payment.from_id]))[0]
            msg = (
                f"⭐️ [id{user.id}|{user.first_name} {user.last_name}], вы успешно приобрели {utils.pluralize_words(payment.coins, ('монетку', 'монетки', 'монеток'))}"
                f"! Вы можете обменять их с помощью команды /shop, передать с помощью /transfer или попробовать сыграть: /duel, /guess.\n\n📗 Номер платежа: #{payment.order_id}\n📗 Время "
                f"покупки: {datetime.now().strftime('%d.%m.%Y / %H:%M:%S')}"
            )
        elif payment.to_id != payment.from_id:
            user = (await vkapi.users.get(user_ids=[payment.to_id]))[0]  # type: ignore
            fromuser = (await vkapi.users.get(user_ids=[payment.from_id]))[0]
            msg = (
                f"🎁 [id{user.id}|{user.first_name} {user.last_name}], вы получили Premium-подписку в подарок от "
                f"пользователя [id{fromuser.id}|{fromuser.first_name} {fromuser.last_name}]. Чтобы узнать все "
                f"подробности и возможности Premium-статуса, вы можете ознакомиться с информацией по ссылке — "
                f"vk.cc/cJuJpg\n\n📗 Номер платежа: #{payment.order_id}\n📗 Время "
                f"покупки: {datetime.now().strftime('%d.%m.%Y / %H:%M:%S')}"
            )
        else:
            user = (await vkapi.users.get(user_ids=[payment.from_id]))[0]
            msg = (
                f"⭐️ [id{user.id}|{user.first_name} {user.last_name}], вы успешно приобрели Premium-подписку сроком на "
                f"{days} дней, поздравляю! Чтобы узнать все подробности и возможности Premium-пользователей, вы можете "
                f"ознакомиться с информацией по ссылке — vk.cc/cJuJpg\n\n📗 Номер платежа: #{payment.order_id}\n📗 Время "
                f"покупки: {datetime.now().strftime('%d.%m.%Y / %H:%M:%S')}"
            )
        try:
            await vkapi.messages.send(user_id=payment.to_id, message=msg, random_id=0)
        except Exception:
            pass

        if payment.delete_cmid:
            try:
                await vkapi.messages.delete(
                    group_id=settings.vk.group_id,
                    delete_for_all=True,
                    peer_id=payment.to_id,
                    cmids=payment.delete_cmid,  # type: ignore
                )
            except Exception:
                pass

        if payment.chat_id:
            comment = f"Для беседы id{payment.chat_id}"
        elif payment.to_id != payment.from_id:
            comment = f"Подарок для @id{payment.to_id}"
        else:
            comment = "-"
        try:
            async with (await pool()).acquire() as conn:
                await conn.execute(
                    "insert into paymenthistory (uid, pid, date, type, sum, comment) values ($1, $2, $3, $4, $5, $6)",
                    payment.from_id,
                    payment.order_id,
                    int(time.time()),
                    payment_type,
                    payment.final_cost,
                    comment,
                )
        except Exception:
            pass

        return _capture_and_return_yes()
    except Exception:
        logger.exception("Failed to capture payment:")
        raise


@router.get("/api/leaderboard/{category}", response_model=models.LeaderboardPage)
async def get_leaderboard(
    category: enums.LeaderboardType,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    search: Optional[str] = Query(None, min_length=1),
):
    base_query, _ = category.get_queries()

    async with (await pool()).acquire() as conn:
        if search:
            search_pattern = f"%{search}%"
            uid_query = f"""
                WITH filtered AS (
                    SELECT v.uid
                    FROM ({base_query}) AS v
                    JOIN usernames u ON u.uid = v.uid
                    WHERE u.name ILIKE $1 OR u.domain ILIKE $1
                    OFFSET $2 LIMIT $3
                )
                SELECT v.*, u.name, u.domain
                FROM ({base_query}) AS v
                JOIN usernames u ON u.uid = v.uid
                WHERE v.uid IN (SELECT uid FROM filtered)
            """
            records = await conn.fetch(uid_query, search_pattern, offset, limit)

            total_query = f"""
                SELECT COUNT(*) 
                FROM ({base_query}) AS v
                JOIN usernames u ON u.uid = v.uid
                WHERE u.name ILIKE $1 OR u.domain ILIKE $1
            """
            total = await conn.fetchval(total_query, search_pattern)
        else:
            paginated_query = f"SELECT * FROM ({base_query}) AS v OFFSET $1 LIMIT $2"
            records = await conn.fetch(paginated_query, offset, limit)
            total = await conn.fetchval(f"SELECT COUNT(*) FROM ({base_query}) AS sub")

    user_ids = list({record["uid"] for record in records})
    user_data = await vkapi.users.get(
        user_ids=user_ids,
        fields=[UsersFields.PHOTO_MAX.value, UsersFields.DOMAIN.value],  # type: ignore
    )
    user_data = {user.id: user for user in user_data}

    items = []
    for i, record in enumerate(records):
        uid = record["uid"]
        user = user_data.get(uid)
        if user is None:
            continue

        avatar_url = user.photo_max or "https://vk.com/images/camera_100.png"
        username = f"{user.first_name} {user.last_name}"
        value = (
            f"{settings.leagues.leagues[record['league'] - 1]} | {record['lvl']} уровень"
            if category == enums.LeaderboardType.LEAGUES
            else str(record["value"])
        )

        items.append(
            models.LeaderboardItem(
                place=offset + i + 1,
                avatar=pydantic.HttpUrl(url=avatar_url),
                username=username,
                domain=user.domain or f"id{user.id}",
                value=value,
            )
        )

    return models.LeaderboardPage(total=total, items=items)


@router.get("/leaderboard")
async def leaderboard():
    return PlainTextResponse("unexpected request")


@router.get("/health")
async def health(request: Request):
    import os
    import time

    import psutil

    from StarManager.core.event_loop_monitor import event_loop_monitor
    from StarManager.core.scheduler_monitor import scheduler_monitor

    start = time.time()
    try:
        db_pool = await pool()
        async with db_pool.acquire() as conn:
            await asyncio.wait_for(conn.fetchval("SELECT 1"), timeout=2)
        db_ok = True
        db_time = time.time() - start
        db_pool_size = db_pool.get_size()
        db_pool_free = db_pool.get_idle_size()
    except Exception:
        db_ok = False
        db_time = -1
        db_pool_size = -1
        db_pool_free = -1

    scheduler_ok, scheduler_msg = scheduler_monitor.is_healthy(max_delay=300)
    scheduler_jobs = scheduler_monitor.get_all_jobs()
    scheduler_running = (
        hasattr(request.app.state, "scheduler") and request.app.state.scheduler.running
    )

    loop_stats = event_loop_monitor.get_stats()

    process = psutil.Process(os.getpid())

    return JSONResponse(
        {
            "status": "ok" if (db_ok and scheduler_ok) else "degraded",
            "timestamp": time.time(),
            "vk_tasks": len(_vk_tasks),
            "vk_queued": event_queue.qsize(),
            "vk_tasks_completed": _vk_tasks_completed,
            "vk_tasks_timedout": await get_vk_timeouts_count(),
            "db": {
                "ok": db_ok,
                "response_time": round(db_time, 3),
                "pool_size": db_pool_size,
                "pool_free": db_pool_free,
                "pool_used": db_pool_size - db_pool_free if db_pool_size > 0 else -1,
            },
            "scheduler": {
                "ok": scheduler_ok,
                "running": scheduler_running,
                "message": scheduler_msg,
                "jobs": {
                    name: int(time.time() - last_run)
                    for name, last_run in scheduler_jobs.items()
                },
            },
            "event_loop": loop_stats,
            "system": {
                "memory_mb": round(process.memory_info().rss / 1024 / 1024, 1),
                "cpu_percent": process.cpu_percent(),
                "threads": process.num_threads(),
            },
        }
    )


_vk_semaphore = asyncio.Semaphore(50)
_vk_tasks: set[asyncio.Task] = set()
_vk_tasks_completed = 0
_vk_tasks_completed_lock = asyncio.Lock()


async def process_vk_event(data, data_type):
    async def _process_with_limit():
        global _vk_tasks_completed

        start = time.time()
        event_info = f"{data_type}"
        text = ""
        if data_type == "message_new" and "object" in data:
            msg = data.get("object", {}).get("message", {})
            text = msg.get("text", "")[:50]
            event_info = f"message_new text='{text}'"

        try:
            async with asyncio.timeout(60):
                async with _vk_semaphore:
                    await vkbot.process_event(data)
                    async with _vk_tasks_completed_lock:
                        _vk_tasks_completed += 1
        except asyncio.TimeoutError:
            await record_vk_timeout()

            elapsed = time.time() - start
            logger.exception(f"TIMEOUT after {elapsed:.2f}s: {event_info}")
            logger.error(f"Event data: {json.dumps(data, ensure_ascii=False)[:500]}")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(f"Failed: {event_info}")

    task = asyncio.create_task(_process_with_limit())
    _vk_tasks.add(task)
    task.add_done_callback(_vk_tasks.discard)


@router.post("/api/listener/vk")
async def vk(request: Request):
    data = await request.json()

    if (data_type := data.get("type")) is None:
        return PlainTextResponse('Error: no "type" field.')
    if data_type == "confirmation":
        return PlainTextResponse(settings.vk.callback_confirmation_code)
    if data.get("secret") != settings.vk.callback_secret:
        return PlainTextResponse('Error: wrong "secret" key.')

    if len(_vk_tasks) > 200:
        queued_events = event_queue.qsize()
        if queued_events >= 1000:
            logger.warning(f"Queued {queued_events} events, dropping queue!")
            await event_queue.drop_all()
            queued_events = 0
            for task in list(_vk_tasks):
                try:
                    task.cancel()
                except Exception:
                    pass
            await asyncio.sleep(0)

            return PlainTextResponse("ok")
        else:
            try:
                await asyncio.wait_for(event_queue.put(data), timeout=0.5)
            except asyncio.TimeoutError:
                pass
            if (queued_events + 1) % 100 == 0:
                logger.warning(
                    f"Queued {queued_events + 1} events, tasks: {len(_vk_tasks)}"
                )

            return PlainTextResponse("ok")

    await process_vk_event(data, data_type)
    return PlainTextResponse("ok")


@router.post("/api/listener/tg")
async def tg_webhook(request: Request):
    data = await request.json()
    tg_bot = request.app.state.tg_bot
    try:
        await tg_bot.dp.feed_update(tg_bot.bot, aiogram.types.Update(**data))
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "query ID is invalid" in str(e):
            return PlainTextResponse("ok")
        logger.exception("Telegram webhook error")
    except Exception:
        logger.exception("Telegram webhook error")
    return PlainTextResponse("ok")
