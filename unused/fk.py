import sys
import time
from datetime import datetime

import messages
from Bot.tgbot import getTGBot
from config.config import TG_CHAT_ID, TG_FREEKASSA_THREAD_ID, PREMIUM_COST
from unused.olddb import getPayments, getPremium
from config.config import VK_API_SESSION

order_id = sys.argv[1]
order_id_fk = sys.argv[2]
amount = sys.argv[3]

payments = getPayments()
payments.update(success=1).where(payments.id == order_id).execute()
payment = payments.select().where(payments.id == order_id)[0]
success = payment.success
order_id = payment.id
uid = payment.uid

days = list(PREMIUM_COST.keys())[list(PREMIUM_COST.values()).index(int(amount))]

bot = getTGBot()
bot.send_message(
    chat_id=TG_CHAT_ID,
    text=f'💰 ID : {order_id} | IDP : {order_id_fk} | '
         f'Срок : {days} дней | '
         f'Сумма : {amount} рублей | Пользователь : @id{uid} | '
         f'Время : {datetime.now().strftime("%Y.%-m.%-d / %H:%M:%S")}',
    message_thread_id=TG_FREEKASSA_THREAD_ID
)

prem = getPremium()
try:
    last_time = prem.select().where(prem.uid == uid)[0].unix_time - int(time.time())
    if last_time <= 0:
        last_time = 0
    prem.update(unix_time=time.time() + (days * 86400) + last_time).where(
        prem.uid == uid).execute()
except:
    prem.insert(uid=uid, unix_time=time.time() + (days * 86400)).execute()


msg = messages.payment_success(order_id, days)
VK_API_SESSION.method("messages.send", {
    'user_id': uid,
    'message': msg,
    'random_id': 0
})
