import logging
import sys
import time
import traceback
from datetime import datetime
from typing import Optional

import httpx
import pydantic
from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from yookassa import Configuration, Payment

sys.path.append('../')
from config import config
from db import smallpool as pool

logger = logging.getLogger(__name__)
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

app.add_middleware(SessionMiddleware, secret_key=config.VK_APP_SECRET)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static/templates")

oauth = OAuth()
oauth.register(
    name='vk',
    client_id=config.VK_APP_ID,
    client_secret=config.VK_APP_SECRET,
    access_token_url='https://oauth.vk.com/access_token',
    authorize_url='https://oauth.vk.com/authorize',
    api_base_url='https://api.vk.com/method/',
    client_kwargs={'scope': 'email', 'token_endpoint_auth_method': 'client_secret_post'}
)


class Subscription(BaseModel):
    type: str
    duration: Optional[int] = None
    gift: Optional[bool] = False
    gift_link: Optional[str] = None
    promo: Optional[str] = None
    payment: str
    chat_id: Optional[int] = Field(None, ge=1, le=2147483647)


class User(BaseModel):
    id: int
    name: str
    photo: Optional[str] = None
    email: Optional[str] = None


class PromoCheck(BaseModel):
    promo: str


async def get_current_user(request: Request):
    if not request or not request.session:
        return None
    user = request.session.get("user")
    return user


@app.exception_handler(404)
async def notfound(*_, **__):
    return RedirectResponse("/")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={**config.data, "user": request.session.get("user")}
    )


@app.get("/payment", response_class=HTMLResponse)
async def payment(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="payment.html",
        context={**config.data, "user": request.session.get("user")}
    )


@app.get("/login")
async def login(request: Request):
    return await oauth.vk.authorize_redirect(request, request.url_for("auth_vk_callback"))


@app.get("/auth/vk/callback")
async def auth_vk_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return HTMLResponse("Ошибка: отсутствует код авторизации", status_code=400)

    redirect_uri = str(request.url_for("auth_vk_callback"))

    params = {
        "client_id": config.VK_APP_ID,
        "client_secret": config.VK_APP_SECRET,
        "redirect_uri": redirect_uri,
        "code": code
    }

    async with httpx.AsyncClient() as client:
        token_resp = await client.get("https://oauth.vk.com/access_token", params=params)
        token_data = token_resp.json()

    if "error" in token_data:
        return HTMLResponse(f"Ошибка VK: {token_data}", status_code=400)

    access_token = token_data["access_token"]
    user_id = token_data["user_id"]
    email = token_data.get("email")

    # Получим данные о пользователе
    async with httpx.AsyncClient() as client:
        user_resp = await client.get("https://api.vk.com/method/users.get",
                                     params={"access_token": access_token, "user_ids": user_id,
                                             "v": "5.131", "fields": "photo_200"})
        user_data = user_resp.json()

    user = user_data["response"][0]
    request.session["user"] = User(id=user["id"], name=user["first_name"] + ' ' + user["last_name"],
                                   photo=user.get("photo_200"), email=email).model_dump()

    return RedirectResponse(url="/")


@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/")


@app.post("/api/validate-promo")
async def validate_promo(request: Request):
    try:
        data = PromoCheck(**(await request.json()))
    except pydantic.ValidationError:
        raise HTTPException(status_code=400, detail="Неверный формат промокода")

    async with (await pool()).acquire() as conn:
        promo_exists = await conn.fetchval('select val from prempromo where promo=$1', data.promo)

    if promo_exists is not None:
        return JSONResponse(content={"valid": True, "discount": promo_exists})
    else:
        raise HTTPException(status_code=400, detail="Промокод не найден")


@app.post("/api/payment")
async def create_payment(request: Request):
    user = User.model_construct(**request.session['user']) if 'user' in request.session else None
    if not user:
        return JSONResponse(status_code=401, content={"detail": "auth_required", "redirect_url": "/login"})
    try:
        data = Subscription(**(await request.json()))
    except pydantic.ValidationError:
        raise HTTPException(status_code=400, detail="Проверьте правильность введённых данных.")
    if data.type == 'subscription' and not data.duration:
        raise HTTPException(status_code=400, detail="Не указана длительность подписки.")
    if data.type == 'chat' and not data.chat_id:
        raise HTTPException(status_code=400, detail="Не указан ID чата.")
    if data.gift:
        try:
            user = (await config.api.users.get(user_ids=data.gift_link.split('/')[-1]))[0]
        except:
            raise HTTPException(status_code=400, detail="Указанного пользователя не существует.")
    else:
        try:
            user = (await config.api.users.get(user_ids=user.id))[0]
        except:
            traceback.print_exc()
            return JSONResponse(status_code=401, content={"detail": "auth_required", "redirect_url": "/login"})

    if data.type == 'subscription':
        cost = origcost = config.PREMIUM_COST[data.duration]
    else:
        cost = origcost = config.data['premiumchat']
        async with (await pool()).acquire() as conn:
            if await conn.fetchval('select premium from publicchats where chat_id=$1', data.chat_id):
                raise HTTPException(status_code=400, detail="У этой беседы уже есть Premium-статус.")
        try:
            chat = await config.api.messages.get_conversation_members(peer_id=2000000000 + data.chat_id)
            if not chat.items:
                raise Exception
        except:
            raise HTTPException(status_code=400, detail="Не удалось найти беседу. Убедитесь, что бот добавлен в беседу "
                                                        "и имеет статус администратора.")
        if not [i for i in chat.items if i.member_id == int(user.id)]:
            raise HTTPException(
                status_code=400, detail="Вам нужно быть участником беседы, чтобы приобрести для неё Premium-статус.")

    async with (await pool()).acquire() as conn:
        oid = await conn.fetchval('select id from payments order by id desc limit 1')
        oid = 1 if oid is None else (oid + 1)
        await conn.execute('insert into payments (id, uid, success) values ($1, $2, $3)', oid, user.id, 0)
        if data.promo:
            promo = await conn.fetchval('select val from prempromo where promo=$1', data.promo)
            cost = int(int(cost) * ((100 - promo) / 100)) + 1

    payment = {
        'amount': {
            'value': str(cost) + '.00',
            'currency': 'RUB'
        },
        'receipt': {
            'customer': {
                'full_name': f'{user.last_name} {user.first_name}',
                'email': config.data['email']
            },
            'items': [{
                'description': 'Premium-статус' if origcost != config.data['premiumchat'] else 'Premium-беседа',
                'amount': {
                    'value': str(cost) + '.00',
                    'currency': 'RUB'
                },
                'vat_code': 1,
                'quantity': 1,
            }]
        },
        'metadata': {
            'pid': oid,
            'chat_id': 0 if origcost != config.data['premiumchat'] else data.chat_id,
            'origcost': origcost,
        },
        'merchant_customer_id': user.id,
        'confirmation': {
            'type': 'redirect',
            'locale': 'ru_RU',
            'return_url': 'https://vk.com/star_manager'
        }
    }
    if user.email:
        payment['receipt']['customer']['email'] = user.email
        payment['receipt']['email'] = user.email
    Configuration.account_id = config.YOOKASSA_MERCHANT_ID
    Configuration.secret_key = config.YOOKASSA_TOKEN
    p = Payment.create(payment)

    return JSONResponse(content={"valid": True, "payment_url": p.confirmation.confirmation_url})


@app.post("/api/listener/yookassa")
async def yookassa(request: Request):
    if request.method != 'POST':
        return RedirectResponse(url="/", status_code=303)
    query = (await request.json())['object']
    order_id = int(query['metadata']['pid'])
    chat_id = int(query['metadata']['chat_id'])
    order_id_p = query['id']

    async with (await pool()).acquire() as conn:
        if not await conn.fetchval('update payments set success=1 where id=$1 returning 1', order_id):
            return JSONResponse(content='YES')
        uid = await conn.fetchval('select uid from payments where id=$1', order_id)

    if chat_id == 0:
        val = list(
            config.PREMIUM_COST.keys())[list(config.PREMIUM_COST.values()).index(int(query['metadata']['origcost']))]
    else:
        val = chat_id

    async with httpx.AsyncClient() as client:
        await client.get(f"https://api.telegram.org/bot{config.TG_TOKEN}/sendMessage", params={
            'chat_id': config.TG_CHAT_ID,
            'message_thread_id': config.TG_PREMIUM_THREAD_ID,
            'text': f'💰 ID : {order_id} | IDP : {order_id_p} | ' +
                    (f'Срок : {val} дней' if chat_id == 0 else f'Беседа : {val}') +
                    f' | Сумма : {int(query["amount"]["value"][:-3])} рублей | Пользователь : @id{uid} | '
                    f'Время : {datetime.now().strftime("%d.%m.%Y / %H:%M:%S")}'
        })

    async with (await pool()).acquire() as conn:
        if chat_id == 0:
            lttime = await conn.fetchval('select time from premium where uid=$1', uid)
            if lttime is None:
                await conn.execute(
                    'insert into premium (uid, time) VALUES ($1, $2)', uid, int(val * 86400 + time.time()))
            else:
                await conn.execute('update premium set time = $1 where uid=$2', int(val * 86400 + lttime), uid)
        else:
            if not await conn.fetchval('update publicchats set premium = $1 where chat_id=$2 returning 1', True, val):
                await conn.execute(
                    'insert into publicchats (chat_id, premium, isopen) values ($1, $2, $3)', val, True, False)

    Configuration.account_id = config.YOOKASSA_MERCHANT_ID
    Configuration.secret_key = config.YOOKASSA_TOKEN
    Payment.capture(order_id_p)

    try:
        await config.api.messages.send(user_id=uid, message=(
                f"🟢 Заказ #{order_id} был успешно оплачен.\n\n✨ Поздравляю, вы получили " +
                (f"Premium-подписку сроком на {val} дней" if chat_id == 0 else f"Premium-статус для беседы id{val}") +
                "!\nЧтобы узнать все подробности о Premium-подписке перейдите по ссылке — vk.cc/crO0a5"), random_id=0)
    except:
        pass

    return JSONResponse(content='YES')
