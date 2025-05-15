import telebot
import requests
import json
import os
import time
from datetime import datetime, timedelta

# بيانات البوت
TOKEN = '7269311808:AAGqrdBAJeFPbmiVotSb2Rus4_ktg5BjNac'
ADMIN_ID = '5000510953'
PROOF_CHANNEL_ID = -1002604421435
FORCE_SUB_CHANNEL = "zeedtek"
DJZ_REGISTRATION_URL = 'https://apim.djezzy.dz/oauth2/registration'
DJZ_TOKEN_URL = 'https://apim.djezzy.dz/oauth2/token'

# إعدادات البروكسي
PROXIES = {
    'http': 'http://4ozf98d598meqlt-country-dz:whdeajejjowefz3@rp.scrapegw.com:6060',
    'https': 'http://4ozf98d598meqlt-country-dz:whdeajejjowefz3@rp.scrapegw.com:6060'
}

# طباعة IP المتصل به
def print_current_ip():
    try:
        ip = requests.get("http://ipinfo.io/ip", proxies=PROXIES).text.strip()
        print(f"عنوان IP الحالي المستخدم: {ip}")
    except Exception as e:
        print(f"خطأ في جلب IP: {e}")

bot = telebot.TeleBot(TOKEN)
data_file = 'users.json'

def load_data():
    try:
        return json.load(open(data_file, 'r', encoding='utf-8')) if os.path.exists(data_file) else {}
    except Exception as e:
        print("خطأ في تحميل البيانات:", e)
        return {}

def save_data(data):
    try:
        json.dump(data, open(data_file, 'w', encoding='utf-8'), indent=2)
    except Exception as e:
        print("خطأ في حفظ البيانات:", e)

def hide_number(phone):
    return phone[:4] + '***' + phone[-2:]

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(f"@{FORCE_SUB_CHANNEL}", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"خطأ في التحقق من الاشتراك: {e}")
        return False

@bot.message_handler(commands=['start'])
def start(msg):
    try:
        if not is_subscribed(msg.from_user.id):
            join_msg = (
                "📢 للاستخدام، يجب عليك الاشتراك في القناة أولاً:\n"
                f"@{FORCE_SUB_CHANNEL}\n\n"
                "✅ بعد الاشتراك، اضغط /start مرة أخرى."
            )
            btn = telebot.types.InlineKeyboardMarkup()
            btn.add(telebot.types.InlineKeyboardButton("الاشتراك في القناة", url=f"https://t.me/{FORCE_SUB_CHANNEL}"))
            bot.send_message(msg.chat.id, join_msg, reply_markup=btn)
            return

        markup = telebot.types.ForceReply(selective=False)
        welcome = "مرحبا بك في بوت aissa"
        bot.send_message(msg.chat.id, welcome, reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(msg.chat.id, get_number)
    except Exception as e:
        print(f"خطأ في دالة start: {e}")

def get_number(msg):
    try:
        number = msg.text.strip()
        if number.startswith("07") and len(number) == 10:
            msisdn = "213" + number[1:]
            if send_otp(msisdn):
                bot.send_message(msg.chat.id, "تم إرسال رقم OTP مكون من 6 ارقام يرجا إدخاله بشكل صحيح✅🔠:")
                bot.register_next_step_handler_by_chat_id(msg.chat.id, lambda m: verify(m, msisdn))
            else:
                bot.send_message(msg.chat.id, "فشل إرسال OTP، حاول مجدداً.")
        else:
            bot.send_message(msg.chat.id, "رقم غير صحيح. أعد الإرسال.")
    except Exception as e:
        print(f"خطأ في دالة get_number: {e}")
        bot.send_message(msg.chat.id, "حدث خطأ، حاول مرة أخرى.")

def send_otp(msisdn):
    payload = f'msisdn={msisdn}&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&scope=smsotp'
    headers = {'User-Agent': 'Djezzy/2.6.7', 'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        res = requests.post(DJZ_REGISTRATION_URL, data=payload, headers=headers, proxies=PROXIES)
        return res.status_code == 200
    except Exception as e:
        print(f"خطأ في send_otp: {e}")
        return False

def verify(msg, msisdn):
    try:
        otp = msg.text.strip()
        payload = f'otp={otp}&mobileNumber={msisdn}&scope=openid&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&client_secret=MVpXHW_ImuMsxKIwrJpoVVMHjRsa&grant_type=mobile'
        headers = {'User-Agent': 'Djezzy/2.6.7', 'Content-Type': 'application/x-www-form-urlencoded'}
        res = requests.post(DJZ_TOKEN_URL, data=payload, headers=headers, proxies=PROXIES).json()
        if 'access_token' in res:
            token = res['access_token']
            apply_gift(msg.chat.id, msisdn, token, msg.from_user)
        else:
            bot.send_message(msg.chat.id, "OTP غير صحيح.")
    except Exception as e:
        print(f"خطأ في verify: {e}")
        bot.send_message(msg.chat.id, "خطأ أثناء التحقق.")

def apply_gift(chat_id, msisdn, token, user):
    data = load_data()
    user_id = str(user.id)
    now = datetime.now()

    if user_id in data:
        last_activation_str = data[user_id].get('last_activation')
        if last_activation_str:
            last_activation = datetime.strptime(last_activation_str, "%Y-%m-%d %H:%M:%S")
            delta = now - last_activation
            if delta < timedelta(days=7):
                remaining_time = timedelta(days=7) - delta
                remaining_days = remaining_time.days
                remaining_hours = remaining_time.seconds // 3600
                remaining_minutes = (remaining_time.seconds % 3600) // 60
                bot.send_message(
                    chat_id,
                    f"⏳ لقد قمت بتفعيل الهدية سابقاً.\n"
                    f"يرجى الإنتظار حتى إكتمال الأسبوع⏱️...\n"
                    f"الوقت المتبقي: {remaining_days} يوم / {remaining_hours} ساعة / {remaining_minutes} دقيقة."
                )
                return

    url = f'https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{msisdn}/subscription-product'
    payload = {
        'data': {
            'id': 'GIFTWALKWIN',
            'type': 'products',
            'meta': {
                'services': {
                    'steps': 10000,
                    'code': 'GIFTWALKWIN2GO',
                    'id': 'WALKWIN'
                }
            }
        }
    }
    headers = {
        'Authorization': f'Bearer {token}',
        'User-Agent': 'Djezzy/2.6.7',
        'Content-Type': 'application/json; charset=utf-8'
    }
    try:
        res = requests.post(url, json=payload, headers=headers, proxies=PROXIES).json()
        if res.get('message', '').startswith("the subscription to the product"):
            hidden = hide_number(msisdn)
            now_str = now.strftime('%Y-%m-%d %H:%M')

            data[user_id] = {'last_activation': now.strftime('%Y-%m-%d %H:%M:%S')}
            save_data(data)

            bot.send_message(chat_id, f"""✅ تم تفعيل هدية **2G** بنجاح!

📱 رقمك: `{hidden}`
🎁 العرض: 2 جيغا 
⏱️ التاريخ: {now_str}

✅ شكرا لاستخدامك بوت ZED """, parse_mode="Markdown")

            proof_message = (
                "✅ تم تفعيل هدية 2G جديدة\n\n"
                f"👤 المستخدم: @{user.username or 'لا يوجد'}\n"
                f"🆔 ID: `{user.id}`\n"
                f"📱 رقم الهاتف: `{hidden}`\n"
                f"⏱️ التاريخ: {now_str}"
            )
            bot.send_message(PROOF_CHANNEL_ID, proof_message, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "حدث خطأ أثناء التفعيل. حاول لاحقاً.")
    except Exception as e:
        print(f"خطأ في apply_gift: {e}")
        bot.send_message(chat_id, "خطأ أثناء التفعيل، حاول لاحقاً.")

# تشغيل البوت
print("البوت شغال...")
print_current_ip()

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"خطأ في polling: {e}")
        time.sleep(5)
