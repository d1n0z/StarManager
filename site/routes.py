import sys
import time
import traceback
from datetime import datetime
from typing import Optional

import enums
import httpx
import models
import pydantic
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import JSONResponse
from vkbottle_types.objects import UsersFields
from yookassa import Configuration, Payment

sys.path.append("../")
from Bot import utils
from config import config
from db import smallpool as pool

router = APIRouter()

templates = Jinja2Templates(directory="static/templates")

oauth = OAuth()
oauth.register(
    name="vk",
    client_id=config.VK_APP_ID,
    client_secret=config.VK_APP_SECRET,
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
        context={**config.data, "user": request.session.get("user")},
    )


@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="contact.html",
        context={**config.data, "user": request.session.get("user")},
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
        request=request, name="payment.html", context={**config.data, "user": user}
    )


@router.get("/login")
async def login(request: Request):
    return await oauth.vk.authorize_redirect(
        request, request.url_for("auth_vk_callback")
    )


@router.get("/auth/vk/callback")
async def auth_vk_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return HTMLResponse("Ошибка: отсутствует код авторизации", status_code=400)

    redirect_uri = str(request.url_for("auth_vk_callback"))

    params = {
        "client_id": config.VK_APP_ID,
        "client_secret": config.VK_APP_SECRET,
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

    # Получим данные о пользователе
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
    async with (await pool()).acquire() as conn:
        lvl, xp = await conn.fetchrow(
            "select lvl, xp from xp where uid=$1", user.id
        ) or (1, 0)
        chats = await conn.fetchval(
            "select count(*) as c from userjoineddate where uid=$1", user.id
        )
        rep = (
            await conn.fetchval("select rep from reputation where uid=$1", user.id) or 0
        )
        if rep > 0:
            rep = "+" + str(rep)
        premium = (
            await conn.fetchval("select time from premium where uid=$1", user.id) or 0
        )
        paymenthistory = await conn.fetch(
            "select date, type, sum, comment from paymenthistory where uid=$1", user.id
        )
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
            **config.data,
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
                await config.api.users.get(
                    user_ids=[
                        await utils.getIDFromMessage(data.data.gift_link, None, 1)
                        or None
                    ]
                )
            )[0]
        except Exception:
            raise HTTPException(status_code=400, detail="Пользователь не существует.")
    else:
        try:
            recipient = (await config.api.users.get(user_ids=[user.id]))[0]
        except Exception:
            traceback.print_exc()
            return JSONResponse(
                status_code=401,
                content={"detail": "auth_required", "redirect_url": "/login"},
            )

    if data.type == "subscription":
        if hasattr(data.data, "duration"):
            cost = origcost = config.PREMIUM_COST[data.data.duration]  # type: ignore
        else:
            raise HTTPException(
                status_code=400, detail="Не указана длительность подписки."
            )
    elif data.type == "chat":
        cost = origcost = config.data["premiumchat"]
        chat_id: int = data.data.chat_id  # type: ignore
        async with (await pool()).acquire() as conn:
            if await conn.fetchval(
                "select premium from publicchats where chat_id=$1", chat_id
            ):
                raise HTTPException(
                    status_code=400, detail="У этой беседы уже есть Premium-статус."
                )
        try:
            chat = await config.api.messages.get_conversation_members(
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
async def yookassa(request: Request):
    if request.method != "POST":
        return RedirectResponse(url="/", status_code=303)
    payment = models.Payment(**(await request.json())["object"])

    async with (await pool()).acquire() as conn:
        if not await conn.fetchval(
            "update payments set success=1 where id=$1 returning 1", payment.order_id
        ):
            return JSONResponse(content="YES")
        if payment.personal_promo:
            await conn.execute(
                "delete from prempromo where id=$1", payment.personal_promo
            )
            await conn.execute(
                "update premiumexpirenotified set date=0 where uid=$1", payment.from_id
            )

    text = f"Номер: <b>#{payment.order_id}</b>\n"
    if payment.chat_id:
        payment_type = "Premium-беседа"
        text += f"""Тип: <code>"Premium-беседа"</code>
ID беседы: <code>{payment.chat_id}</code>\n"""
    elif payment.coins:
        payment_type = utils.pointWords(
            payment.coins, ("монетка", "монетки", "монеток")
        )
        text += f"""Тип: <code>"Монетки"</code>
Количество: <code>{utils.pointWords(payment.coins, ("монетка", "монетки", "монеток"))}</code>\n"""
    else:
        days = list(config.PREMIUM_COST.keys())[
            list(config.PREMIUM_COST.values()).index(payment.cost)
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
    text = "\n".join([f"{emojis[k]} {i}" for k, i in enumerate(text.split("\n"))])

    async with httpx.AsyncClient() as client:
        await client.get(
            f"https://api.telegram.org/bot{config.TG_TOKEN}/sendMessage",
            params={
                "chat_id": config.TG_CHAT_ID,
                "message_thread_id": config.TG_PREMIUM_THREAD_ID,
                "parse_mode": "html",
                "disable_web_page_preview": True,
                "text": text,
            },
        )

    async with (await pool()).acquire() as conn:
        if payment.chat_id:
            if not await conn.fetchval(
                "update publicchats set premium=true where chat_id=$1 returning 1",
                payment.chat_id,
            ):
                await conn.execute(
                    "insert into publicchats (chat_id, premium, isopen) values ($1, true, false)",
                    payment.chat_id,
                )
        elif payment.coins:
            await utils.addUserCoins(payment.to_id, payment.coins)
        else:
            user_premium = await conn.fetchval(
                "select time from premium where uid=$1", payment.to_id
            )
            if user_premium is None:
                await conn.execute(
                    "insert into premium (uid, time) VALUES ($1, $2)",
                    payment.to_id,
                    int(days * 86400 + time.time()),
                )
            else:
                await conn.execute(
                    "update premium set time = $1 where uid=$2",
                    int(days * 86400 + user_premium),
                    payment.to_id,
                )

    Configuration.account_id = config.YOOKASSA_MERCHANT_ID
    Configuration.secret_key = config.YOOKASSA_TOKEN
    Payment.capture(payment.yookassa_order_id)

    if payment.chat_id:
        user = (await config.api.users.get(user_ids=[payment.from_id]))[0]
        msg = (
            f"⭐️ [id{user.id}|{user.first_name} {user.last_name}], вы успешно приобрели Premium-статус для беседы "
            f"id{payment.chat_id}, поздравляю! Чтобы узнать все подробности и возможности Premium-статуса, вы можете "
            f"ознакомиться с информацией по ссылке — vk.cc/cJuJpg\n\n📗 Номер платежа: #{payment.order_id}\n📗 Время "
            f"покупки: {datetime.now().strftime('%d.%m.%Y / %H:%M:%S')}"
        )
    elif payment.coins:
        user = (await config.api.users.get(user_ids=[payment.from_id]))[0]
        msg = (
            f"⭐️ [id{user.id}|{user.first_name} {user.last_name}], вы успешно приобрели {utils.pointWords(payment.coins, ('монетку', 'монетки', 'монеток'))}"
            f"! Вы можете обменять их с помощью команды /shop, передать с помощью /transfer или попробовать сыграть: /duel, /guess.\n\n📗 Номер платежа: #{payment.order_id}\n📗 Время "
            f"покупки: {datetime.now().strftime('%d.%m.%Y / %H:%M:%S')}"
        )
    elif payment.to_id != payment.from_id:
        user = (await config.api.users.get(user_ids=[payment.to_id]))[0]  # type: ignore
        fromuser = (await config.api.users.get(user_ids=[payment.from_id]))[0]
        msg = (
            f"🎁 [id{user.id}|{user.first_name} {user.last_name}], вы получили Premium-подписку в подарок от "
            f"пользователя [id{fromuser.id}|{fromuser.first_name} {fromuser.last_name}]. Чтобы узнать все "
            f"подробности и возможности Premium-статуса, вы можете ознакомиться с информацией по ссылке — "
            f"vk.cc/cJuJpg\n\n📗 Номер платежа: #{payment.order_id}\n📗 Время "
            f"покупки: {datetime.now().strftime('%d.%m.%Y / %H:%M:%S')}"
        )
    else:
        user = (await config.api.users.get(user_ids=[payment.from_id]))[0]
        msg = (
            f"⭐️ [id{user.id}|{user.first_name} {user.last_name}], вы успешно приобрели Premium-подписку сроком на "
            f"{days} дней, поздравляю! Чтобы узнать все подробности и возможности Premium-пользователей, вы можете "
            f"ознакомиться с информацией по ссылке — vk.cc/cJuJpg\n\n📗 Номер платежа: #{payment.order_id}\n📗 Время "
            f"покупки: {datetime.now().strftime('%d.%m.%Y / %H:%M:%S')}"
        )
    try:
        await config.api.messages.send(user_id=payment.to_id, message=msg, random_id=0)
    except Exception:
        passd

    if payment.delete_cmid:
        try:
            await config.api.messages.delete(
                group_id=config.GROUP_ID,
                delete_for_all=True,
                peer_id=payment.to_id,
                cmids=payment.delete_cmid,
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

    return JSONResponse(content="YES")


@router.get("/api/leaderboard/{category}", response_model=models.LeaderboardPage)
async def get_leaderboard(
    category: enums.LeaderboardType,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    search: Optional[str] = Query(None, min_length=1),
):
    base_query, paginated_query = category.get_queries()

    if search:
        search_pattern = f"%{search}%"
        filter_clause = "WHERE (u.first_name || ' ' || u.last_name) ILIKE $1 OR u.domain ILIKE $1"
        base_query = f"SELECT * FROM ({base_query}) AS v JOIN usernames u ON u.id = v.uid {filter_clause}"
        paginated_query = f"{base_query} ORDER BY v.value DESC OFFSET $2 LIMIT $3"

    async with (await pool()).acquire() as conn:
        if search:
            records = await conn.fetch(paginated_query, search_pattern, offset, limit)
            total = await conn.fetchval(f"SELECT COUNT(*) FROM ({base_query}) AS sub", search_pattern)
        else:
            records = await conn.fetch(paginated_query, offset, limit)
            total = await conn.fetchval(f"SELECT COUNT(*) FROM ({base_query}) AS sub")

    user_ids = list({record["uid"] for record in records})
    user_data = await config.api.users.get(
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
            f"{config.LEAGUE[record['league'] - 1]} | {record['lvl']} уровень"
            if category == enums.LeaderboardType.LEAGUES
            else str(record["value"])
        )

        items.append(
            models.LeaderboardItem(
                place=offset + i + 1,
                avatar=pydantic.HttpUrl(url=avatar_url),
                username=username,
                domain=user.domain or f'id{user.id}',
                value=value,
            )
        )

    return models.LeaderboardPage(total=total, items=items)


@router.get("/leaderboard")
async def leaderboard():
    return "test"
