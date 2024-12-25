import time
import traceback
from ast import literal_eval
from datetime import datetime

import requests
import vk_api.exceptions
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import Resolver404
from django.views.decorators.cache import never_cache
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
    chat_id = int(query['metadata']['chat_id'])
    order_id_p = query['id']
    amnt = int(query['amount']['value'][:-3])

    with sdb.syncpool().connection() as conn:
        with conn.cursor() as c:
            if not c.execute('update payments set success=1 where id=%s', (order_id,)).rowcount:
                return
            uid = c.execute('select uid from payments where id=%s', (order_id,)).fetchone()[0]
            conn.commit()

    if chat_id == 0:
        val = list(config.PREMIUM_COST.keys())[list(config.PREMIUM_COST.values()).index(int(amnt))]
    else:
        val = chat_id

    token = config.TG_TOKEN
    tgchat_id = config.TG_CHAT_ID
    thread_id = config.TG_PREMIUM_THREAD_ID

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {
        'chat_id': tgchat_id,
        'message_thread_id': thread_id,
        'text': f'💰 ID : {order_id} | IDP : {order_id_p} | ' +
                (f'Срок : {val} дней' if chat_id == 0 else f'Беседа : {val}') + f' | Сумма : {amnt} рублей '
                f'| Пользователь : @id{uid} | Время : {datetime.now().strftime("%d.%m.%Y / %H:%M:%S")}'
    }
    requests.get(url, params)

    with sdb.syncpool().connection() as conn:
        with conn.cursor() as c:
            if chat_id == 0:
                obj = c.execute('select time from premium where uid=%s', (uid,)).fetchone()
                if obj is None:
                    c.execute('insert into premium (uid, time) VALUES (%s, %s)', (uid, val * 86400 + time.time()))
                else:
                    c.execute('update premium set time = %s where uid=%s', (val * 86400 + obj[0], uid))
            else:
                if not c.execute('update publicchats set premium = %s where chat_id=%s', (True, val)).rowcount:
                    c.execute('insert into publicchats (chat_id, premium, isopen) values (%s, %s, %s)',
                              (val, True, False))
            conn.commit()

    Configuration.account_id = config.YOOKASSA_MERCHANT_ID
    Configuration.secret_key = config.YOOKASSA_TOKEN
    Payment.capture(order_id_p)

    token = config.VK_TOKEN_GROUP

    msg = (f"🟢 Заказ #{order_id} был успешно оплачен.\n\n"
           f"✨ Поздравляю, вы получили " +
           (f"Premium-подписку сроком на {val} дней" if chat_id == 0 else f"Premium-статус для беседы id{val}") +
           "!\nЧтобы узнать все подробности о Premium-подписке перейдите по ссылке — vk.cc/crO0a5")
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
        chatform = PremiumChatForm(request.POST)
        if form.is_valid() or chatform.is_valid():
            usersocial = UserSocialAuth.objects.select_related("user").filter(user_id=request.user.id)[0]
            if config.data['low'] in request.POST:
                cost = config.data['low']
            elif config.data['medium'] in request.POST:
                cost = config.data['medium']
            elif config.data['high'] in request.POST:
                cost = config.data['high']
            elif config.data['premiumchat'] in request.POST:
                cost = config.data['premiumchat']
                if not chatform.is_valid():
                    return render(request, "bot_manager/index.html", config.data | {'error': 'chatnone'})
                with sdb.syncpool().connection() as conn:
                    with conn.cursor() as c:
                        if (ch := c.execute('select premium from publicchats where chat_id=%s',
                                            (chatform.cleaned_data['chatid'],)).fetchone()) and ch[0]:
                            return render(request, "bot_manager/index.html", config.data | {'error': 'chatalready'})
                try:
                    chat = config.VK_API_SESSION.method('messages.getConversationMembers',
                                                        {'peer_id': 2000000000 + chatform.cleaned_data['chatid']})
                except vk_api.exceptions.ApiError:
                    return render(request, "bot_manager/index.html",
                                  config.data | {'error': 'chatnoacc'})
                if 'items' not in chat or not [i for i in chat['items'] if i['member_id'] == int(usersocial.uid) and
                                               'is_admin' in i and i['is_admin']]:
                    return render(request, "bot_manager/index.html",
                                  config.data | {'error': 'chatid'})
            else:
                return render(request, "bot_manager/index.html", config.data)
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
                    'value': cost + '.00',
                    'currency': 'RUB'
                },
                'receipt': {
                    'customer': {
                        'full_name': f'{user.last_name} {user.first_name}',
                        'email': config.data['email']
                    },
                    'items': [{
                        'description': 'Premium-статус' if cost != config.data['premiumchat'] else 'Premium-беседа',
                        'amount': {
                            'value': cost + '.00',
                            'currency': 'RUB'
                        },
                        'vat_code': 1,
                        'quantity': 1,
                    }]
                },
                'metadata': {
                    'pid': oid + 1,
                    'chat_id': 0 if cost != config.data['premiumchat'] else chatform.cleaned_data['chatid']
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


def chats(request: HttpRequest):
    with sdb.syncpool().connection() as conn:
        with conn.cursor() as c:
            allchats = c.execute('select chat_id, premium from publicchats where isopen=true order by id').fetchall()
            allmessages = {i[0]: sum(y[0] for y in c.execute('select messages from messages where chat_id=%s',
                                                             (i[0],)).fetchall()) for i in allchats}
            allsettings = {i[0]: c.execute(
                'select link, photo, name, members from publicchatssettings where chat_id=%s',
                (i[0],)).fetchone() for i in allchats}
    npchats, pchats = [], []
    for chat in allchats:
        try:
            if chat[0] in allsettings and allsettings[chat[0]]:
                chatss = {'photo': allsettings[chat[0]][1], 'name': allsettings[chat[0]][2],
                          'members': allsettings[chat[0]][3], 'messages': allmessages[chat[0]],
                          'url': allsettings[chat[0]][0]}
            else:
                link = config.VK_API_SESSION.method(
                    'messages.getInviteLink', {'peer_id': 2000000000 + chat[0], 'group_id': config.GROUP_ID})['link']
                vkchat = config.VK_API_SESSION.method('messages.getConversationsById',
                                                      {'peer_ids': 2000000000 + chat[0]})
                photo = config.VK_API_SESSION
                if ('items' in vkchat and len(vkchat['items']) and 'chat_settings' in vkchat['items'][0] and
                        'photo' in vkchat['items'][0]['chat_settings']):
                    if 'photo_200' in vkchat['items'][0]['chat_settings']['photo']:
                        photo = vkchat['items'][0]['chat_settings']['photo']['photo_200']
                    elif 'photo_100' in vkchat['items'][0]['chat_settings']['photo']:
                        photo = vkchat['items'][0]['chat_settings']['photo']['photo_100']
                    elif 'photo_50' in vkchat['items'][0]['chat_settings']['photo']:
                        photo = vkchat['items'][0]['chat_settings']['photo']['photo_50']
                chatss = {'photo': photo, 'name': vkchat['items'][0]['chat_settings']['title'],
                          'members': vkchat['items'][0]['chat_settings']['members_count'],
                          'messages': allmessages[chat[0]], 'url': link}
                with sdb.syncpool().connection() as conn:
                    with conn.cursor() as c:
                        try:
                            c.execute('insert into publicchatssettings '
                                      '(chat_id, link, photo, name, members, last_update) '
                                      'values (%s, %s, %s, %s, %s, %s)',
                                      (chat[0], link, photo, vkchat['items'][0]['chat_settings']['title'],
                                       vkchat['items'][0]['chat_settings']['members_count'], int(time.time())))
                            conn.commit()
                        except:
                            pass
            if chat[1]:
                pchats.append(chatss)
            else:
                npchats.append(chatss)
        except:
            traceback.print_exc()
    return render(request, "bot_manager/chats.html",
                  config.data | {'chatsmessages': sorted(npchats, key=lambda x: x['messages'], reverse=True),
                                 'chatsmembers': sorted(npchats, key=lambda x: x['members'], reverse=True),
                                 'premiumchats': pchats})


# noinspection PyUnusedLocal
def handler404(request: HttpRequest, exception: Resolver404):
    return render(request, "bot_manager/notfound.html", config.data)
