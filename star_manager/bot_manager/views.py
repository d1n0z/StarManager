import time
from ast import literal_eval
from datetime import datetime

import requests
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import Resolver404
from django.views.decorators.csrf import csrf_exempt
from social_django.models import UserSocialAuth
from yookassa import Payment, Configuration

from bot_manager.forms import *
from star_manager.settings import config, sdb


def index(request: HttpRequest):
    return render(request, "bot_manager/index.html", config.data)


@csrf_exempt
def yookassa(request: HttpRequest):
    if request.method != 'POST':
        return render(request, "bot_manager/index.html", config.data)
    query = literal_eval(request.body.decode('utf-8').replace('true', 'True').replace('false', 'False'))['object']
    order_id = int(query['metadata']['pid'])
    order_id_p = query['id']
    amnt = int(query['amount']['value'][:-3])

    with sdb.syncpool().connection() as conn:
        with conn.cursor() as c:
            if not c.execute('update payments set success=1 where id=%s', (order_id,)).rowcount:
                return
            uid = c.execute('select uid from payments where id=%s', (order_id,)).fetchone()[0]
            conn.commit()

    days = list(config.PREMIUM_COST.keys())[list(config.PREMIUM_COST.values()).index(int(amnt))]

    token = config.TG_TOKEN
    chat_id = config.TG_CHAT_ID
    thread_id = config.TG_PREMIUM_THREAD_ID

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {
        'chat_id': chat_id,
        'message_thread_id': thread_id,
        'text': f'💰 ID : {order_id} | IDP : {order_id_p} | Срок : {days} дней | Сумма : {amnt} рублей '
                f'| Пользователь : @id{uid} | Время : {datetime.now().strftime("%d.%m.%Y / %H:%M:%S")}'
    }
    requests.get(url, params)

    with sdb.syncpool().connection() as conn:
        with conn.cursor() as c:
            obj = c.execute('select time from premium where uid=%s', (uid,)).fetchone()
            if obj is None:
                c.execute('insert into premium (uid, time) VALUES (%s, %s)', (uid, days * 86400 + time.time()))
            else:
                c.execute('update premium set time = %s where uid=%s', (days * 86400 + obj[0], uid))
            conn.commit()

    Configuration.account_id = config.YOOKASSA_MERCHANT_ID
    Configuration.secret_key = config.YOOKASSA_TOKEN
    Payment.capture(order_id_p)

    token = config.VK_TOKEN_GROUP
    msg = (f"🟢 Заказ #{order_id} был успешно оплачен.\n\n"
           f"✨ Поздравляю вы получили Premium-подписку сроком на {days} дней.\n"
           "Чтобы узнать все подробности о Premium-подписке перейдите по ссылке — vk.cc/crO0a5")
    url = "https://api.vk.com/method/messages.send"
    params = {
        'user_id': uid,
        'message': msg,
        'random_id': 0,
        'access_token': token,
        'v': "5.199",
    }
    requests.get(url, params)

    return HttpResponse('YES', status=200)


def privacy(request: HttpRequest):
    return render(request, "bot_manager/privacy.html", config.data)


@login_required(login_url='/users/login')
def buy(request: HttpRequest):
    if request.method == 'POST':
        form = CostForm(request.POST)
        if form.is_valid():
            if '99' in request.POST:
                cost = '99.00'
            elif '249' in request.POST:
                cost = '249.00'
            elif '499' in request.POST:
                cost = '499.00'
            else:
                return render(request, "bot_manager/index.html", config.data)
            usersocial = UserSocialAuth.objects.select_related("user").filter(user_id=request.user.id)[0]
            user = User.objects.filter(id=request.user.id)[0]

            with sdb.syncpool().connection() as conn:
                with conn.cursor() as c:
                    oid = c.execute('select id from payments order by id desc limit 1').fetchone()
                    oid = 1 if oid is None else oid[0]
                    c.execute('insert into payments (id, uid, success) values (%s, %s, %s)',
                              (oid + 1, usersocial.uid, 0))
                    conn.commit()

            payment = {
                'amount': {
                    'value': cost,
                    'currency': 'RUB'
                },
                'receipt': {
                    'customer': {
                        'full_name': f'{user.last_name} {user.first_name}',
                        'email': config.data['email']
                    },
                    'items': [{
                        'description': 'Premium-статус',
                        'amount': {
                            'value': cost,
                            'currency': 'RUB'
                        },
                        'vat_code': 1,
                        'quantity': 1,
                    }]
                },
                'metadata': {
                    'pid': oid + 1
                },
                'merchant_customer_id': user.id,
                'confirmation': {
                    'type': 'redirect',
                    'locale': 'ru_RU',
                    'return_url': 'https://vk.com/star_manager'
                }
            }
            if user.email != '':
                payment['receipt']['customer']['email'] = user.email
                payment['receipt']['email'] = user.email
            Configuration.account_id = config.YOOKASSA_MERCHANT_ID
            Configuration.secret_key = config.YOOKASSA_TOKEN
            p = Payment.create(payment)

            return redirect(p.confirmation.confirmation_url)
    return render(request, "bot_manager/index.html", config.data)


def handler404(request: HttpRequest, exception: Resolver404):
    return render(request, "bot_manager/notfound.html", config.data)
