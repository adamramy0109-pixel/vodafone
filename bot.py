import os
import sys
import random
import string
import time
import json
import requests
import traceback
import threading
from threading import Thread
import telebot
from telebot import types 
from datetime import datetime, timedelta
import pytz
import io
import asyncio
import aiohttp
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed

# ====================================================================
# 1. الإعدادات الأساسية
# ====================================================================

MAIN_BOT_TOKEN = "8359658192:AAEckbi0ULFykk9eqBdLzKZ_FowqnGKXpJA"
ADMIN_BOT_TOKEN = "8167271730:AAHxMkkj0ObDCkXBfsU5nYWB0L6YbplnK6A"

OWNER_ID = 7701678114
ADMIN_ID = OWNER_ID
DEV_NAME = "月よの川「の川ソ"
DEV_USERNAME = "@DM_ZO"
DEV_USERNAME_MD = DEV_USERNAME.replace("_", "\\_")

REQUIRED_CHANNELS = [
    "@Medo16724",
    "@DMZO44",  
]

VODAFONE_CASH_NUMBER = "01019092631"

USERS_STATS_FILE = "users_stats.json"
OPERATION_COUNTER_FILE = "operation_counter.json"
FLEX_CACHE_FILE = "flex_cache.json"
SUBSCRIPTIONS_FILE = "subscriptions.json"
PENDING_SUBSCRIPTIONS_FILE = "pending_subscriptions.json"
BANNED_USERS_FILE = "banned_users.json"
SETTINGS_FILE = "settings.json"

USERS_STATS = {}
OPERATION_COUNTER = {}
FLEX_CACHE = {}
SUBSCRIPTIONS = {}
PENDING_SUBSCRIPTIONS = {}
BANNED_USERS = {}
SETTINGS = {"free_mode": False}

EGYPT_TZ = pytz.timezone('Africa/Cairo')

DAILY_LIMIT_WARNING_THRESHOLD = 30

SUBSCRIPTION_PLANS = {
    "30d": {"duration": 30*24, "price": 100, "label": "💎 اشتراك شهري - 100 جنيه"},
    "stars": {"duration": "stars", "price": 10, "label": "⭐ نجمة واحدة - 10 جنيه (لعملية واحدة)"}
}

DEFAULT_CONFIG = {
    'delays': {
        "after_invite_success": 15.0,
        "retry_delay": 15.0, 
        "wait_before_remove": 1800.0,
        "after_remove": 300.0,
        "after_accept_invite": 30.0,
        "after_quota_change": 5.0,
        "wait_before_accept_choice": 0
    },
    'retries': 3,
    'max_consecutive_fail': 5
}

# ====================================================================
# URLs و Headers
# ====================================================================
LOGIN_URL = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"
MOBILE_INVITE_URL = "https://mobile.vodafone.com.eg/services/dxl/cg/customerGroupAPI/customerGroup"
WEB_INVITE_URL = "https://web.vodafone.com.eg/services/dxl/cg/customerGroupAPI/customerGroup"
REMOVE_URL = "https://mobile.vodafone.com.eg/services/dxl/cg/customerGroupAPI/customerGroup"
AUTH_URL = 'https://web.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token'
FAMILY_API_URL_WEB = "https://web.vodafone.com.eg/services/dxl/cg/customerGroupAPI/customerGroup"
FAMILY_API_URL_MOBILE = "https://mobile.vodafone.com.eg/services/dxl/cg/customerGroupAPI/customerGroup"
CLIENT_SECRET = '95fd95fb-7489-4958-8ae6-d31a525cd20a'
CLIENT_ID = 'ana-vodafone-app'

MOBILE_HEADERS_TEMPLATE = {
    'User-Agent': "okhttp/4.12.0",
    'Connection': "Keep-Alive",
    'Accept': "application/json",
    'Accept-Encoding': "gzip",
    'api-version': "v2",
    'clientId': "AnaVodafoneAndroid",
    'Accept-Language': "ar",
    'Content-Type': "application/json; charset=UTF-8"
}

WEB_HEADERS_TEMPLATE = {
    'Accept': 'application/json',
    'Accept-Language': 'AR',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'https://web.vodafone.com.eg',
    'Referer': 'https://web.vodafone.com.eg/spa/familySharing',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'clientId': 'WebsiteConsumer',
    'api-version': 'v2'
}

MAIN_BOT_STATUS = "running"
QUOTA_BUTTON_TO_PERCENT = {1300: 10, 2600: 20, 5200: 40}
USER_STATE = {}
PAYMENT_STATE = {}
ACTIVE_OPERATIONS = {}
OPERATION_MESSAGES = {}
PENDING_ACCEPT_CHOICE = {}

# ====================================================================
# 2. تهيئة البوتات
# ====================================================================
try:
    main_bot = telebot.TeleBot(MAIN_BOT_TOKEN)
    admin_bot = telebot.TeleBot(ADMIN_BOT_TOKEN)
    print("✅ تم تهيئة البوتات بنجاح")
except Exception as e:
    print(f"❌ خطأ في تهيئة البوتات: {e}")
    sys.exit(1)

# ====================================================================
# 3. دوال تحميل وحفظ البيانات
# ====================================================================
def load_all_data():
    global USERS_STATS, OPERATION_COUNTER, FLEX_CACHE, SUBSCRIPTIONS, PENDING_SUBSCRIPTIONS, BANNED_USERS, SETTINGS
    try:
        with open(USERS_STATS_FILE, 'r', encoding='utf-8') as f:
            USERS_STATS = json.load(f)
            for user_id, data in USERS_STATS.items():
                if 'auto_accept' not in data:
                    data['auto_accept'] = True
    except FileNotFoundError:
        USERS_STATS = {}
    except Exception as e:
        print(f"❌ خطأ في تحميل الإحصائيات: {e}")
        USERS_STATS = {}
    
    try:
        with open(OPERATION_COUNTER_FILE, 'r', encoding='utf-8') as f:
            OPERATION_COUNTER = json.load(f)
    except FileNotFoundError:
        OPERATION_COUNTER = {}
    
    try:
        with open(FLEX_CACHE_FILE, 'r', encoding='utf-8') as f:
            FLEX_CACHE = json.load(f)
    except FileNotFoundError:
        FLEX_CACHE = {}
    
    try:
        with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            SUBSCRIPTIONS = json.load(f)
            for user_id, sub in SUBSCRIPTIONS.items():
                if 'stars' in sub and isinstance(sub['stars'], str):
                    sub['stars'] = int(sub['stars'])
    except FileNotFoundError:
        SUBSCRIPTIONS = {}
    
    try:
        with open(PENDING_SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            PENDING_SUBSCRIPTIONS = json.load(f)
    except FileNotFoundError:
        PENDING_SUBSCRIPTIONS = {}
    
    try:
        with open(BANNED_USERS_FILE, 'r', encoding='utf-8') as f:
            BANNED_USERS = json.load(f)
    except FileNotFoundError:
        BANNED_USERS = {}

    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            SETTINGS = json.load(f)
    except FileNotFoundError:
        SETTINGS = {"free_mode": False}

    # ===== تطبيق سعر الاشتراك المحفوظ (لو الأدمن غيّره قبل كده) =====
    if "monthly_price" in SETTINGS:
        try:
            saved_price = int(SETTINGS["monthly_price"])
            SUBSCRIPTION_PLANS["30d"]["price"] = saved_price
            SUBSCRIPTION_PLANS["30d"]["label"] = f"💎 اشتراك شهري - {saved_price} جنيه"
        except (TypeError, ValueError):
            pass

def save_all_data():
    try:
        with open(USERS_STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(USERS_STATS, f, ensure_ascii=False, indent=2)
        with open(OPERATION_COUNTER_FILE, 'w', encoding='utf-8') as f:
            json.dump(OPERATION_COUNTER, f, ensure_ascii=False, indent=2)
        with open(FLEX_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(FLEX_CACHE, f, ensure_ascii=False, indent=2)
        with open(SUBSCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(SUBSCRIPTIONS, f, ensure_ascii=False, indent=2)
        with open(PENDING_SUBSCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(PENDING_SUBSCRIPTIONS, f, ensure_ascii=False, indent=2)
        with open(BANNED_USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(BANNED_USERS, f, ensure_ascii=False, indent=2)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(SETTINGS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ خطأ في حفظ البيانات: {e}")

def get_next_operation_number(user_id):
    user_id_str = str(user_id)
    if user_id_str not in OPERATION_COUNTER:
        OPERATION_COUNTER[user_id_str] = 1
    else:
        OPERATION_COUNTER[user_id_str] += 1
    save_all_data()
    return OPERATION_COUNTER[user_id_str]

def update_user_stats(user_id, operation_success=False):
    if str(user_id) not in USERS_STATS:
        USERS_STATS[str(user_id)] = {
            'joined_date': get_egypt_time().isoformat(),
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'last_activity': get_egypt_time().isoformat(),
            'auto_accept': True
        }
    USERS_STATS[str(user_id)]['total_operations'] += 1
    USERS_STATS[str(user_id)]['last_activity'] = get_egypt_time().isoformat()
    if operation_success:
        USERS_STATS[str(user_id)]['successful_operations'] += 1
    else:
        USERS_STATS[str(user_id)]['failed_operations'] += 1
    save_all_data()

def init_user_stats(user_id):
    if str(user_id) not in USERS_STATS:
        USERS_STATS[str(user_id)] = {
            'joined_date': get_egypt_time().isoformat(),
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'last_activity': get_egypt_time().isoformat(),
            'auto_accept': True
        }
        save_all_data()

def get_egypt_time():
    return datetime.now(EGYPT_TZ)

def is_user_banned(user_id):
    user_id_str = str(user_id)
    if user_id_str not in BANNED_USERS:
        return False
    ban_data = BANNED_USERS[user_id_str]
    if 'banned_until' in ban_data:
        banned_until = ban_data['banned_until']
        if isinstance(banned_until, str):
            banned_until = datetime.fromisoformat(banned_until)
        if get_egypt_time() > banned_until:
            del BANNED_USERS[user_id_str]
            save_all_data()
            return False
    return True

def ban_user(user_id, reason="غير محدد", duration_hours=0):
    banned_until = None
    if duration_hours > 0:
        banned_until = get_egypt_time() + timedelta(hours=duration_hours)
    BANNED_USERS[str(user_id)] = {
        'banned_at': get_egypt_time().isoformat(),
        'reason': reason,
        'banned_by': ADMIN_ID
    }
    if banned_until:
        BANNED_USERS[str(user_id)]['banned_until'] = banned_until.isoformat()
    save_all_data()

def unban_user(user_id):
    if str(user_id) in BANNED_USERS:
        del BANNED_USERS[str(user_id)]
        save_all_data()
        return True
    return False

# ====================================================================
# 4. دوال الاشتراكات
# ====================================================================
def is_free_mode():
    return SETTINGS.get("free_mode", False)

def has_active_subscription(user_id):
    if str(user_id) == str(OWNER_ID):
        return True
    if is_free_mode():
        return True
    user_id_str = str(user_id)
    if user_id_str not in SUBSCRIPTIONS:
        return False
    sub = SUBSCRIPTIONS[user_id_str]
    if sub.get("status") != "active":
        return False
    if sub.get("plan") == "stars":
        return sub.get("stars", 0) > 0
    expiry_date_str = sub.get('expiry_date')
    if not expiry_date_str:
        return False
    expiry_date = datetime.fromisoformat(expiry_date_str)
    if get_egypt_time() > expiry_date:
        sub["status"] = "expired"
        save_all_data()
        return False
    return True

def has_sufficient_stars(user_id):
    if is_free_mode():
        return False
    user_id_str = str(user_id)
    if user_id_str not in SUBSCRIPTIONS:
        return False
    sub = SUBSCRIPTIONS[user_id_str]
    if sub.get("plan") != "stars" or sub.get("status") != "active":
        return False
    return sub.get("stars", 0) > 0

def deduct_star(user_id):
    user_id_str = str(user_id)
    if user_id_str not in SUBSCRIPTIONS:
        return False
    sub = SUBSCRIPTIONS[user_id_str]
    if sub.get("plan") != "stars" or sub.get("status") != "active":
        return False
    current_stars = sub.get("stars", 0)
    if current_stars <= 0:
        sub["status"] = "expired"
        save_all_data()
        return False
    sub["stars"] = current_stars - 1
    if sub["stars"] == 0:
        sub["status"] = "expired"
    save_all_data()
    return True

def add_subscription(user_id, days):
    user_id_str = str(user_id)
    expiry_date = get_egypt_time() + timedelta(days=days)
    if user_id_str not in SUBSCRIPTIONS:
        SUBSCRIPTIONS[user_id_str] = {
            'start_date': get_egypt_time().isoformat(),
            'expiry_date': expiry_date.isoformat(),
            'days_added': days,
            'status': 'active',
            'plan': 'manual'
        }
    else:
        current_expiry = datetime.fromisoformat(SUBSCRIPTIONS[user_id_str]['expiry_date'])
        new_expiry = current_expiry + timedelta(days=days)
        SUBSCRIPTIONS[user_id_str]['expiry_date'] = new_expiry.isoformat()
        SUBSCRIPTIONS[user_id_str]['days_added'] = SUBSCRIPTIONS[user_id_str].get('days_added', 0) + days
        SUBSCRIPTIONS[user_id_str]['status'] = 'active'
    save_all_data()
    return SUBSCRIPTIONS[user_id_str]

def remove_subscription(user_id):
    user_id_str = str(user_id)
    if user_id_str in SUBSCRIPTIONS:
        del SUBSCRIPTIONS[user_id_str]
        save_all_data()
        return True
    return False

def check_subscription_valid(user_id):
    return has_active_subscription(user_id)

def get_remaining_days(user_id):
    user_id_str = str(user_id)
    if user_id_str not in SUBSCRIPTIONS:
        return 0
    sub = SUBSCRIPTIONS[user_id_str]
    if sub.get("plan") == "stars":
        return sub.get("stars", 0)
    expiry_date = datetime.fromisoformat(sub['expiry_date'])
    remaining = expiry_date - get_egypt_time()
    return max(0, remaining.days)

def format_expiry_time(expiry_date):
    if isinstance(expiry_date, str):
        expiry_date = datetime.fromisoformat(expiry_date)
    now = get_egypt_time()
    remaining = expiry_date - now
    if remaining.days > 0:
        return f"{remaining.days} يوم {remaining.seconds // 3600} ساعة"
    else:
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        return f"{hours} ساعة {minutes} دقيقة"

def show_subscription_menu(chat_id, user_id=None):
    if user_id is None:
        user_id = chat_id
    markup = types.InlineKeyboardMarkup(row_width=1)
    plan = SUBSCRIPTION_PLANS["30d"]
    markup.add(types.InlineKeyboardButton(f"✨ {plan['label']}", callback_data="subscribe_30d"))
    if user_id != OWNER_ID:
        markup.add(types.InlineKeyboardButton("📊 حالة الاشتراك", callback_data="check_subscription_status"))
    markup.add(types.InlineKeyboardButton("👨‍💻 المطور @DM_ZO", url="https://t.me/DM_ZO"))
    markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_process"))
    message_text = "مرحباً بك في نظام فودافون فليكس المتقدم\n\n🕌 صلي علي النبي محمد ﷺ\n\n"
    if has_active_subscription(user_id):
        message_text += f"{get_subscription_info(user_id)}\n\n🚀 يمكنك الآن البدء في استخدام الخدمة المتكاملة!"
    else:
        message_text += "📋 اختر خطة الاشتراك المناسبة من القائمة:"
    try:
        main_bot.send_message(chat_id, message_text, reply_markup=markup)
    except Exception as e:
        print(f"❌ خطأ في إرسال رسالة القائمة: {e}")

def get_subscription_info(user_id):
    if user_id == OWNER_ID:
        return "👑 أنت الأدمن - لا تحتاج لاشتراك"
    if is_free_mode():
        return "🎁 الخدمة متاحة مجاناً للجميع الآن!"
    if str(user_id) not in SUBSCRIPTIONS:
        return "❌ ليس لديك اشتراك نشط. يرجى الاشتراك أولاً."
    sub = SUBSCRIPTIONS[str(user_id)]
    if sub.get("status") != "active":
        return "❌ اشتراكك غير نشط أو منتهي. يرجى التجديد."
    if sub.get("plan") == "stars":
        stars_count = sub.get("stars", 0)
        return f"⭐ اشتراكك بالنجوم نشط\n📦 عدد النجوم المتبقية: {stars_count}\n💡 كل عملية ناجحة تخصم نجمة واحدة."
    expiry_date = datetime.fromisoformat(sub['expiry_date'])
    remaining = expiry_date - get_egypt_time()
    days = remaining.days
    hours = remaining.seconds // 3600
    plan_label = SUBSCRIPTION_PLANS.get(sub.get("plan", ""), {}).get("label", "غير معروف")
    if remaining.total_seconds() <= 0:
        return f"❌ اشتراكك انتهى منذ: {abs(days)} يوم"
    time_left = f"{days} يوم {hours} ساعة" if days > 0 else f"{hours} ساعة"
    return f"✅ اشتراكك نشط\n📦 الخطة: {plan_label}\n⏰ المتبقي: {time_left}\n📅 ينتهي في: {expiry_date.strftime('%Y-%m-%d %I:%M %p')}"

def show_payment_instructions(chat_id, plan_id):
    plan = SUBSCRIPTION_PLANS[plan_id]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💸 بدء عملية الدفع", callback_data=f"start_payment_{plan_id}"))
    markup.add(types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_subscribe"))
    markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_process"))
    message_text = f"""
💳 دفع رسوم الاشتراك
🕌 صلي علي النبي محمد ﷺ
📦 الخطة: {plan['label']}
💰 السعر: {plan['price']} جنيه مصري
📱 رقم الكاش: {VODAFONE_CASH_NUMBER}
📋 طريقة الدفع:
1. تحويل المبلغ {plan['price']} جنيه إلى الرقم: {VODAFONE_CASH_NUMBER}
2. احتفظ برقم الذي تم التحويل منه وصورة الإيصال
3. اضغط على زر "💸 بدء عملية الدفع"
4. اتبع التعليمات لإدخال رقم التحويل وإرسال صورة الإيصال
5. سيتم مراجعة طلبك من قبل الأدمن خلال دقائق
📞 للتواصل مع الدعم: @DM_ZO
    """
    main_bot.send_message(chat_id, message_text, reply_markup=markup)

def start_payment_process(chat_id, plan_id):
    if plan_id not in SUBSCRIPTION_PLANS:
        main_bot.send_message(chat_id, "❌ خطة الاشتراك غير موجودة.")
        return
    plan = SUBSCRIPTION_PLANS[plan_id]
    try:
        admin_bot.send_chat_action(ADMIN_ID, "typing")
    except Exception as e:
        main_bot.send_message(chat_id, "❌ غير قادر على التواصل مع المسؤول\n\nيرجى التواصل مع @DM_ZO مباشرة.")
        return
    PAYMENT_STATE[chat_id] = {'step': 'waiting_transfer_number', 'plan_id': plan_id, 'transfer_number': None}
    cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel_markup.add(types.KeyboardButton("❌ إلغاء العملية"))
    main_bot.send_message(
        chat_id,
        f"💸 بدء عملية الدفع\n\n🕌 صلي علي النبي محمد ﷺ\n\n📦 الخطة: {plan['label']}\n💰 المبلغ: {plan['price']} جنيه\n\n📱 الخطوة 1 من 2:\nأرسل رقم الذي تم التحويل منه:",
        reply_markup=cancel_markup
    )

def request_receipt_photo(chat_id, plan_id, transfer_number):
    if plan_id not in SUBSCRIPTION_PLANS:
        main_bot.send_message(chat_id, "❌ خطة الاشتراك غير موجودة.")
        return
    plan = SUBSCRIPTION_PLANS[plan_id]
    if not transfer_number or len(transfer_number.strip()) < 5:
        main_bot.send_message(chat_id, "❌ رقم التحويل غير صالح. يرجى البدء من جديد.")
        if chat_id in PAYMENT_STATE:
            del PAYMENT_STATE[chat_id]
        return
    PAYMENT_STATE[chat_id] = {'step': 'waiting_receipt', 'plan_id': plan_id, 'transfer_number': transfer_number.strip()}
    cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel_markup.add(types.KeyboardButton("❌ إلغاء العملية"))
    main_bot.send_message(
        chat_id,
        f"📸 الخطوة 2 من 2:\n\n✅ تم حفظ رقم التحويل: {transfer_number}\n\nالآن يرجى إرسال صورة إيصال التحويل:\n\n💳 المبلغ: {plan['price']} جنيه\n📱 إلى الرقم: {VODAFONE_CASH_NUMBER}",
        reply_markup=cancel_markup
    )

def send_subscription_request_to_admin(user_id, plan_id, transfer_number, file_id=None, file_type='photo'):
    try:
        plan = SUBSCRIPTION_PLANS[plan_id]
        try:
            user_info = main_bot.get_chat(user_id)
            username = user_info.username if user_info.username else 'N/A'
            first_name = user_info.first_name if user_info.first_name else 'غير معروف'
        except:
            username = 'N/A'
            first_name = 'غير معروف'
        start_date = get_egypt_time()
        end_date = None
        if plan_id != "stars":
            end_date = start_date + timedelta(hours=plan["duration"])
        subscription_data = {
            "user_id": user_id, "user_name": first_name, "plan": plan_id, "price": plan["price"],
            "duration": plan.get("duration", 0), "payment_number": transfer_number, "screenshot_id": file_id,
            "start_date": start_date.isoformat(), "request_date": get_egypt_time().isoformat(), "status": "pending"
        }
        if end_date:
            subscription_data["end_date"] = end_date.isoformat()
        if plan_id == "stars":
            subscription_data["stars"] = 0
        PENDING_SUBSCRIPTIONS[str(user_id)] = subscription_data
        save_all_data()
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ الموافقة", callback_data=f"approve_sub_{user_id}"),
            types.InlineKeyboardButton("❌ الرفض", callback_data=f"reject_sub_{user_id}")
        )
        if plan_id == "stars":
            message_text = f"🆕 طلب اشتراك جديد (نجوم) ⭐\n🕌 صلي علي النبي محمد ﷺ\n👤 المستخدم: {first_name}\n🆔 ID: {user_id}\n📱 Username: @{username}\n📦 الخطة: {plan['label']}\n💰 السعر: {plan['price']} جنيه للنجمة\n🔢 رقم التحويل: {transfer_number}\n⏰ وقت الطلب: {get_egypt_time().strftime('%Y-%m-%d %I:%M %p')}\n\nيرجى الرد بعدد النجوم:\n/addstars {user_id} 5"
        else:
            message_text = f"🆕 طلب اشتراك جديد\n🕌 صلي علي النبي محمد ﷺ\n👤 المستخدم: {first_name}\n🆔 ID: {user_id}\n📱 Username: @{username}\n📦 الخطة: {plan['label']}\n💰 السعر: {plan['price']} جنيه\n🔢 رقم التحويل: {transfer_number}\n⏰ وقت الطلب: {get_egypt_time().strftime('%Y-%m-%d %I:%M %p')}\n📅 تاريخ الانتهاء: {end_date.strftime('%Y-%m-%d %I:%M %p') if end_date else 'غير محدد'}"
        if file_id:
            try:
                if file_type == 'photo':
                    admin_bot.send_photo(ADMIN_ID, file_id, caption=message_text, reply_markup=markup)
                    return True
                elif file_type == 'document':
                    admin_bot.send_document(ADMIN_ID, file_id, caption=message_text, reply_markup=markup)
                    return True
            except:
                pass
        admin_bot.send_message(ADMIN_ID, message_text, reply_markup=markup)
        return True
    except Exception as e:
        print(f"❌ خطأ في إرسال الطلب للأدمن: {e}")
        return False

def handle_subscription_approval(call, target_user_id):
    try:
        load_all_data()
        user_id_str = str(target_user_id)
        if user_id_str not in PENDING_SUBSCRIPTIONS:
            admin_bot.answer_callback_query(call.id, "❌ طلب الاشتراك غير موجود.")
            return
        sub_data = PENDING_SUBSCRIPTIONS[user_id_str]
        plan_id = sub_data["plan"]
        if plan_id not in SUBSCRIPTION_PLANS:
            admin_bot.answer_callback_query(call.id, "❌ خطة الاشتراك غير موجودة.")
            return
        plan = SUBSCRIPTION_PLANS[plan_id]
        stars_count = sub_data.get("stars", 1) if plan_id == "stars" else 0
        subscription_entry = {
            "plan": plan_id, "start_date": sub_data["start_date"], "status": "active",
            "transaction_number": sub_data["payment_number"], "payment_screenshot": sub_data.get("screenshot_id", "")
        }
        if plan_id == "stars":
            subscription_entry["stars"] = stars_count
            subscription_entry["expiry_date"] = None
        else:
            subscription_entry["expiry_date"] = sub_data["end_date"]
        SUBSCRIPTIONS[user_id_str] = subscription_entry
        del PENDING_SUBSCRIPTIONS[user_id_str]
        save_all_data()
        try:
            if plan_id == "stars":
                success_message = f"🎉 تم تفعيل اشتراكك بالنجوم بنجاح!\n🕌 صلي علي النبي محمد ﷺ\n⭐ عدد النجوم: {stars_count}"
            else:
                end_date = datetime.fromisoformat(sub_data['end_date'])
                success_message = f"🎉 تم تفعيل اشتراكك بنجاح!\n🕌 صلي علي النبي محمد ﷺ\n📦 الخطة: {plan['label']}\n⏰ ينتهي في: {end_date.strftime('%Y-%m-%d %I:%M %p')}"
            main_bot.send_message(target_user_id, success_message)
        except Exception as e:
            print(f"❌ خطأ في إرسال رسالة التأكيد: {e}")
        admin_bot.answer_callback_query(call.id, "✅ تمت الموافقة على الاشتراك")
        try:
            new_caption = f"✅ تمت الموافقة\n👤 {sub_data['user_name']}\n🆔 {target_user_id}\n📦 {plan['label']}\n⏰ {get_egypt_time().strftime('%Y-%m-%d %I:%M %p')}"
            if hasattr(call.message, 'caption'):
                admin_bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=new_caption, reply_markup=None)
            else:
                admin_bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=new_caption, reply_markup=None)
        except:
            pass
    except Exception as e:
        print(f"❌ خطأ في معالجة الموافقة: {e}")
        admin_bot.answer_callback_query(call.id, "❌ حدث خطأ")

def handle_subscription_rejection(call, target_user_id):
    try:
        load_all_data()
        user_id_str = str(target_user_id)
        if user_id_str not in PENDING_SUBSCRIPTIONS:
            admin_bot.answer_callback_query(call.id, "❌ طلب الاشتراك غير موجود.")
            return
        sub_data = PENDING_SUBSCRIPTIONS[user_id_str]
        try:
            main_bot.send_message(target_user_id, "❌ تم رفض طلب اشتراكك\n\n🕌 صلي علي النبي محمد ﷺ\n\nيرجى التواصل مع @DM_ZO للاستفسار.", reply_markup=types.ReplyKeyboardRemove())
        except:
            pass
        del PENDING_SUBSCRIPTIONS[user_id_str]
        save_all_data()
        admin_bot.answer_callback_query(call.id, "❌ تم رفض الاشتراك")
        try:
            new_caption = f"❌ تم رفض الاشتراك\n👤 {sub_data['user_name']}\n🆔 {target_user_id}\n⏰ {get_egypt_time().strftime('%Y-%m-%d %I:%M %p')}"
            if hasattr(call.message, 'caption'):
                admin_bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=new_caption, reply_markup=None)
            else:
                admin_bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=new_caption, reply_markup=None)
        except:
            pass
    except Exception as e:
        print(f"❌ خطأ في معالجة الرفض: {e}")
        admin_bot.answer_callback_query(call.id, "❌ حدث خطأ")

def get_admin_stats():
    total_users = len(USERS_STATS)
    total_operations = sum(stats.get('total_operations', 0) for stats in USERS_STATS.values())
    successful_operations = sum(stats.get('successful_operations', 0) for stats in USERS_STATS.values())
    active_operations = sum(len(ops) for ops in ACTIVE_OPERATIONS.values())
    subscribed_users = len(SUBSCRIPTIONS)
    banned_users = len(BANNED_USERS)
    pending_requests = len(PENDING_SUBSCRIPTIONS)
    plan_stats = {}
    total_stars = 0
    for sub in SUBSCRIPTIONS.values():
        plan = sub.get('plan')
        if plan in SUBSCRIPTION_PLANS:
            plan_stats[plan] = plan_stats.get(plan, 0) + 1
        if 'stars' in sub and sub.get('status') == 'active':
            total_stars += sub.get('stars', 0)
    return {
        'total_users': total_users, 'total_operations': total_operations, 'successful_operations': successful_operations,
        'active_operations': active_operations, 'bot_status': MAIN_BOT_STATUS, 'subscribed_users': subscribed_users,
        'banned_users': banned_users, 'pending_requests': pending_requests, 'plan_stats': plan_stats,
        'total_stars': total_stars, 'free_mode': is_free_mode()
    }

# ====================================================================
# 5. دوال جلب بيانات الفليكسات
# ====================================================================
def login_and_get_token(phone, password):
    payload = {
        'grant_type': "password", 'username': phone, 'password': password,
        'client_secret': "95fd95fb-7489-4958-8ae6-d31a525cd20a", 'client_id': "ana-vodafone-app"
    }
    headers = {
        'User-Agent': "okhttp/4.12.0", 'Accept': "application/json, text/plain, */*", 'Accept-Encoding': "gzip",
        'silentLogin': "true", 'x-agent-operatingsystem': "15", 'clientId': "AnaVodafoneAndroid",
        'Accept-Language': "ar", 'x-agent-device': "Samsung SM-A165F", 'x-agent-version': "2025.12.2",
        'x-agent-build': "1080", 'digitalId': "25VT5Q5QWG8DK", 'device-id': "b26ba335813fad21"
    }
    try:
        response = requests.post(LOGIN_URL, data=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('access_token')
    except Exception as e:
        print(f"❌ خطأ في تسجيل الدخول: {e}")
        return None

def get_consumption_data(token, phone):
    url = "https://mobile.vodafone.com.eg/services/dxl/usage/usageConsumptionReport"
    params = {'@type': "aggregated", 'bucket.product.publicIdentifier': phone}
    headers = {
        'User-Agent': "okhttp/4.12.0", 'Connection': "Keep-Alive", 'Accept': "application/json",
        'Accept-Encoding': "gzip", 'api-host': "usageConsumptionHost", 'useCase': "aggregated",
        'Authorization': f"Bearer {token}", 'api-version': "v2", 'device-id': "b26ba335813fad21",
        'clientId': "AnaVodafoneAndroid", 'msisdn': phone,
        'Content-Type': "application/json", 'Accept-Language': "ar"
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None

def extract_flex_data(consumption_data):
    if not consumption_data:
        return None
    current_flex = None; flex_remaining = None; next_cycle_flex = None; renewal_date = None
    for item in consumption_data:
        item_type = item.get("@type", "")
        if item_type == "FLEX":
            for bucket in item.get("bucket", []):
                if bucket.get("usageType") == "flex":
                    for balance in bucket.get("bucketBalance", []):
                        if balance.get("@type") == "Remaining":
                            current_flex = balance["remainingValue"]
                            valid_for = balance.get("validFor")
                            if valid_for and valid_for.get("endDateTime"):
                                renewal_date = valid_for["endDateTime"]
        elif item_type == "OTHERS":
            for bucket in item.get("bucket", []):
                usage_type = bucket.get("usageType", "")
                if usage_type == "count":
                    for balance in bucket.get("bucketBalance", []):
                        if balance.get("@type") == "Remaining":
                            flex_remaining = balance["remainingValue"]
                elif usage_type == "limit":
                    for balance in bucket.get("bucketBalance", []):
                        if balance.get("@type") == "Remaining":
                            next_cycle_flex = balance["remainingValue"]
    return {"current_flex": current_flex, "flex_remaining": flex_remaining, "next_cycle_flex": next_cycle_flex, "renewal_date": renewal_date}

def format_flex_value(flex_data):
    if not flex_data:
        return "غير متاح"
    amount = flex_data.get("amount", 0); units = flex_data.get("units", "")
    if units == "minutes": return f"{amount} دقيقة"
    elif units == "GB": return f"{amount} جيجابايت"
    elif units == "SMS": return f"{amount} رسالة"
    elif units == "LE": return f"{amount} جنيه"
    else: return f"{amount} {units}"

def get_flex_data(owner_number, owner_password):
    token = login_and_get_token(owner_number, owner_password)
    if not token: return None
    consumption_data = get_consumption_data(token, owner_number)
    if not consumption_data: return None
    return extract_flex_data(consumption_data)

# ====================================================================
# 5.5 كشف الحد اليومي للطلبات
# ====================================================================
def get_daily_request_limit(owner_number, owner_password):
    try:
        token, _ = login(owner_number, owner_password)
    except Exception as e:
        return None, None, f"فشل تسجيل الدخول: {str(e)[:100]}"

    dummy_member = "01111111111"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
        "Connection": "keep-alive",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/json",
        "Accept-Language": "EN",
        "Authorization": f"Bearer {token}",
        "msisdn": owner_number,
        "clientId": "WebsiteConsumer",
        "Origin": "https://web.vodafone.com.eg",
        "Referer": "https://web.vodafone.com.eg/spa/familySharing"
    }
    payload = {
        "name": "FlexFamily",
        "type": "FamilyRemoveMember",
        "category": [{"value": "47", "listHierarchyId": "TemplateID"}],
        "parts": {
            "member": [
                {"id": [{"value": owner_number, "schemeName": "MSISDN"}], "type": "Owner"},
                {"id": [{"value": dummy_member, "schemeName": "MSISDN"}], "type": "Member"}
            ],
            "characteristicsValue": {
                "characteristicsValue": [
                    {"characteristicName": "Disconnect", "value": "0"},
                    {"characteristicName": "LastMemberDeletion", "value": "1"}
                ]
            }
        }
    }
    try:
        res = requests.patch(FAMILY_API_URL_WEB, data=json.dumps(payload), headers=headers, timeout=15)
        limit_day = res.headers.get("x-ratelimit-limit-day") or res.headers.get("X-RateLimit-Limit-Day")
        remaining_day = res.headers.get("x-ratelimit-remaining-day") or res.headers.get("X-RateLimit-Remaining-Day")
        return limit_day, remaining_day, None
    except Exception as e:
        return None, None, f"خطأ في الطلب: {str(e)[:100]}"

def format_daily_limit_message(owner_number, limit_day, remaining_day):
    try:
        limit_int = int(limit_day)
        remaining_int = int(remaining_day)
        used = max(limit_int - remaining_int, 0)
        percent = int((used / limit_int) * 100) if limit_int > 0 else 0
        filled = min(int(percent / 10), 10)
        bar = "🟩" * filled + "⬜" * (10 - filled)
        return (
            f"📊 **الحد اليومي للطلبات**\n"
            f"📱 **الرقم:** {owner_number}\n\n"
            f"📈 **الحد الإجمالي اليومي:** {limit_int}\n"
            f"📉 **المتبقي اليوم:** {remaining_int}\n"
            f"🔢 **المستخدم:** {used} طلب ({percent}%)\n"
            f"{bar}\n\n"
            f"♥ صلي علي النبي محمد ﷺ"
        )
    except (TypeError, ValueError):
        return (
            f"📊 **الحد اليومي للطلبات**\n"
            f"📱 **الرقم:** {owner_number}\n\n"
            f"⚠️ لم يتمكن الفودافون من إرجاع الحد اليومي حالياً (غير معروف)\n\n"
            f"ℹ️ ده معناه إما الحساب مفيهوش حدود واضحة، أو الـ API مرجعتش القيمة هذه المرة.\n"
            f"جرب تاني بعد شوية.\n\n"
            f"♥ صلي علي النبي محمد ﷺ"
        )

# ====================================================================
# 5.6 دوال جلب الدعوات المعلقة - معدلة للـ Web API
# ====================================================================
def get_family_info(token, owner_number):
    """جلب بيانات العائلة الكاملة - بإستخدام Web API"""
    url = "https://web.vodafone.com.eg/services/dxl/cg/customerGroupAPI/customerGroup?type=Family"
    headers = {
        'Authorization': f"Bearer {token}",
        'api-version': "v2",
        'clientId': "WebsiteConsumer",
        'msisdn': owner_number,
        'Content-Type': "application/json",
        'Accept': "application/json",
        'Accept-Language': "ar",
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        'Origin': "https://web.vodafone.com.eg",
        'Referer': "https://web.vodafone.com.eg/spa/familySharing"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"❌ خطأ في جلب البيانات: {e}")
    return None

def parse_pending_invitations(data):
    """استخراج الدعوات المعلقة النشطة فقط"""
    if not data:
        return []
    
    # لو البيانات جاية من Web API
    if isinstance(data, list) and len(data) > 0:
        family = data[0]
    else:
        family = data
    
    pending_list = []
    members = family.get('parts', {}).get('member', [])
    
    for member in members:
        # الحالة 5 = دعوة معلقة
        if member.get('status') == '5':
            member_info = {
                'number': member.get('id', [{}])[0].get('value', ''),
                'type': member.get('type', ''),
                'flex': None,
                'expire_date': None
            }
            
            # جلب التفاصيل
            chars = member.get('characteristic', {}).get('characteristicsValue', [])
            for char in chars:
                if char.get('characteristicName') == 'flex':
                    member_info['flex'] = char.get('value')
                elif char.get('characteristicName') == 'invitationExpireDate':
                    member_info['expire_date'] = char.get('value')
            
            pending_list.append(member_info)
    
    return pending_list

def show_pending_invitations_ui(chat_id, owner_number, pending_invites):
    """عرض الدعوات المعلقة النشطة مع أزرار القبول والإلغاء"""
    if not pending_invites:
        main_bot.send_message(chat_id, "✅ **لا توجد دعوات معلقة نشطة!**\n\n♥ صلي علي النبي محمد ﷺ", parse_mode="Markdown")
        return
    message = "📋 **الدعوات المعلقة النشطة**\n\n"
    message += f"👤 **الأونر:** {owner_number}\n"
    message += f"🔢 **عدد الدعوات:** {len(pending_invites)}\n\n"
    message += "━━━━━━━━━━━━━━━━━\n"
    for idx, invite in enumerate(pending_invites, 1):
        message += f"\n**الدعوة #{idx}**\n"
        message += f"📱 **الرقم:** {invite['number']}\n"
        message += f"💎 **الفليكس:** {invite['flex'] if invite['flex'] else 'غير محدد'}\n"
        message += f"⏰ **تنتهي:** {invite['expire_date'] if invite['expire_date'] else 'غير محدد'}\n"
        message += "━━━━━━━━━━━━━━━━━\n"
    message += f"\n♥ صلي علي النبي محمد ﷺ"
    markup = types.InlineKeyboardMarkup()
    for invite in pending_invites:
        member_num = invite['number']
        markup.add(
            types.InlineKeyboardButton(
                f"✅ قبول {member_num}",
                callback_data=f"accept_pending_{owner_number}_{member_num}"
            ),
            types.InlineKeyboardButton(
                f"❌ إلغاء {member_num}",
                callback_data=f"cancel_pending_{owner_number}_{member_num}"
            )
        )
    main_bot.send_message(chat_id, message, reply_markup=markup, parse_mode="Markdown")

# ====================================================================
# 6. دوال الإرسال والقبول
# ====================================================================
def login(msisdn, password):
    payload = {
        'grant_type': 'password',
        'username': msisdn,
        'password': password,
        'client_secret': '95fd95fb-7489-4958-8ae6-d31a525cd20a',
        'client_id': 'ana-vodafone-app'
    }
    headers = {
        'User-Agent': "okhttp/4.12.0",
        'Accept': "application/json, text/plain, */*",
        'silentLogin': "true",
        'x-agent-operatingsystem': "13",
        'clientId': "AnaVodafoneAndroid",
        'Accept-Language': "en",
        'x-agent-device': "Xiaomi M2102J20SG",
        'x-agent-version': "2026.2.1",
        'x-agent-build': "1200",
        'digitalId': "244BQYOGFM0IM",
        'device-id': "b83aab2d8fa633da"
    }
    resp = requests.post(LOGIN_URL, data=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data['access_token'], data.get('refresh_token')

def get_invite_payload(owner, member, quota_percent):
    return {
        "name": "FlexFamily",
        "type": "SendInvitation",
        "category": [
            {"listHierarchyId": "PackageID", "value": "523"},
            {"listHierarchyId": "TemplateID", "value": "47"},
            {"listHierarchyId": "TierID", "value": "523"},
            {"listHierarchyId": "familybehavior", "value": "percentage"}
        ],
        "parts": {
            "member": [
                {"id": [{"schemeName": "MSISDN", "value": owner}], "type": "Owner"},
                {"id": [{"schemeName": "MSISDN", "value": member}], "type": "Member"}
            ],
            "characteristicsValue": {
                "characteristicsValue": [
                    {"characteristicName": "quotaDist1", "value": str(quota_percent), "type": "percentage"}
                ]
            }
        }
    }


# ====================================================================
# دوال متقدمة سريعة - لزيادة النجاح بدون تأخير إضافي
# ====================================================================

def get_random_agent_headers():
    """توليد x-agent headers عشوائية - سريع جداً"""
    os_versions = [13, 14, 15, 16]
    devices = [
        {"device": "Xiaomi M2101K7BG", "version": "2026.2.1", "build": "1200"},
        {"device": "Realme RMX3760", "version": "2026.4.1", "build": "1139"},
        {"device": "Xiaomi M2102J20SG", "version": "2025.11.1", "build": "1063"},
        {"device": "HONOR DNY-NX9", "version": "2025.11.1", "build": "1063"},
        {"device": "Samsung SM-A165F", "version": "2025.12.2", "build": "1080"},
    ]
    device = random.choice(devices)
    return {
        'x-agent-operatingsystem': str(random.choice(os_versions)),
        'x-agent-device': device['device'],
        'x-agent-version': device['version'],
        'x-agent-build': device['build'],
    }

def get_random_user_agent():
    """توليد User-Agent عشوائي"""
    agents = [
        "okhttp/4.12.0",
        "Mozilla/5.0 (Linux; Android 11; Pixel 5)",
        "Mozilla/5.0 (Linux; Android 12; SM-G960F)",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    ]
    return random.choice(agents)

def get_phone_variants(number):
    """توليد صيغ مختلفة من الرقم - سريع"""
    variants = []
    clean = number.replace(" ", "").replace("-", "")
    
    if clean.startswith('0'):
        variants.append(clean)  # 01234567890
        variants.append('2' + clean[1:])  # 201234567890 (دولي)
    elif clean.startswith('2'):
        variants.append(clean)  # 201234567890
        variants.append('0' + clean[1:])  # 01234567890
    else:
        variants.append(clean)
    
    return variants

def create_payload_variant(owner, member, quota_value):
    """إنشاء payload بصيغ مختلفة - random choice"""
    variant_type = random.choice([1, 2])
    
    base = {
        "name": "FlexFamily", 
        "type": "SendInvitation", 
        "category": [
            {"value": "523", "listHierarchyId": "PackageID"}, 
            {"value": "47", "listHierarchyId": "TemplateID"},
        ], 
        "parts": {
            "member": [
                {"id": [{"value": owner, "schemeName": "MSISDN"}], "type": "Owner"},
                {"id": [{"value": member, "schemeName": "MSISDN"}], "type": "Member"}
            ], 
            "characteristicsValue": {
                "characteristicsValue": [
                    {"characteristicName": "quotaDist1", "value": str(quota_value), "type": "percentage"}
                ]
            }
        }
    }
    
    # صيغة بدون type (محتمل تشتغل أحسن)
    if variant_type == 2:
        base["parts"]["characteristicsValue"]["characteristicsValue"][0].pop("type")
    
    return base


def send_invitation_sync(owner, member, token, quota_percent, source_type='mobile', index=0):
    """إرسال محسّن سريع - مع تنويع headers و payloads و صيغ أرقام"""
    
    device_variants = [
        "b26ba335813fad21", "53a5c7cdda114b09", "b83aab2d8fa633da",
        "81bfbfaa09602859", "ba4068643748bc78", "25vt5q5qwg8dk01a",
    ]
    
    phone_variants = get_phone_variants(member)
    
    for phone_variant in phone_variants:
        for attempt in range(5):
            try:
                if source_type == 'mobile':
                    headers = MOBILE_HEADERS_TEMPLATE.copy()
                    headers['Authorization'] = f'Bearer {token}'
                    headers['msisdn'] = owner
                    headers['device-id'] = random.choice(device_variants)
                    headers['User-Agent'] = get_random_user_agent()
                    
                    agent_headers = get_random_agent_headers()
                    headers.update(agent_headers)
                    
                    payload = create_payload_variant(owner, phone_variant, quota_percent)
                    
                    url = MOBILE_INVITE_URL
                    resp = requests.post(url, json=payload, headers=headers, timeout=45)
                else:
                    headers = WEB_HEADERS_TEMPLATE.copy()
                    headers['Authorization'] = f'Bearer {token}'
                    headers['msisdn'] = owner
                    headers['User-Agent'] = get_random_user_agent()
                    
                    agent_headers = get_random_agent_headers()
                    headers.update(agent_headers)
                    
                    payload = create_payload_variant(owner, phone_variant, quota_percent)
                    
                    cookies = {'GUEST_LANGUAGE_ID': 'ar_SA', 'firstLogin': 'true', 'msisdn': owner}
                    url = WEB_INVITE_URL
                    resp = requests.post(url, json=payload, headers=headers, cookies=cookies, timeout=45)
                
                if resp.status_code in (200, 201):
                    return True
                    
            except requests.exceptions.RequestException:
                if attempt < 4:
                    delay = (2 ** attempt) + random.uniform(0.5, 1.5)
                    time.sleep(delay)
    
    return False

def remove_member_sync(owner, member, token):
    REMOVE_PAYLOAD_TEMPLATE = {
        "category": [{"listHierarchyId": "TemplateID", "value": "47"}],
        "createdBy": {"value": "MobileApp"},
        "parts": {
            "characteristicsValue": {
                "characteristicsValue": [
                    {"characteristicName": "Disconnect", "value": "0"},
                    {"characteristicName": "LastMemberDeletion", "value": "1"}
                ]
            },
            "member": [
                {"id": [{"schemeName": "MSISDN", "value": ""}], "type": "Owner"},
                {"id": [{"schemeName": "MSISDN", "value": ""}], "type": "Member"}
            ]
        },
        "type": "FamilyRemoveMember"
    }
    payload = json.loads(json.dumps(REMOVE_PAYLOAD_TEMPLATE))
    payload['parts']['member'][0]['id'][0]['value'] = owner
    payload['parts']['member'][1]['id'][0]['value'] = member

    device_variants = [
        {"device-id": "b26ba335813fad21", "x-agent-operatingsystem": "13", "x-agent-device": "Xiaomi M2101K7BG", "x-agent-version": "2026.2.1", "x-agent-build": "1200"},
        {"device-id": "53a5c7cdda114b09", "x-agent-operatingsystem": "15", "x-agent-device": "Realme RMX3760", "x-agent-version": "2026.4.1", "x-agent-build": "1139"},
        {"device-id": "b83aab2d8fa633da", "x-agent-operatingsystem": "13", "x-agent-device": "Xiaomi M2102J20SG", "x-agent-version": "2025.11.1", "x-agent-build": "1063"},
        {"device-id": "81bfbfaa09602859", "x-agent-operatingsystem": "16", "x-agent-device": "HONOR DNY-NX9", "x-agent-version": "2025.11.1", "x-agent-build": "1063"},
        {"device-id": "ba4068643748bc78", "x-agent-operatingsystem": "15", "x-agent-device": "HONOR ALI-NX1", "x-agent-version": "2025.11.1.1", "x-agent-build": "1064"},
        {"device-id": "25vt5q5qwg8dk01a", "x-agent-operatingsystem": "15", "x-agent-device": "Samsung SM-A165F", "x-agent-version": "2025.12.2", "x-agent-build": "1080"},
    ]
    base_headers = {
        'User-Agent': "okhttp/4.12.0",
        'Connection': "Keep-Alive",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json; charset=UTF-8",
        'Authorization': f'Bearer {token}',
        'api-version': "v2",
        'clientId': "AnaVodafoneAndroid",
        'msisdn': owner,
        'Accept-Language': "ar"
    }

    tried_codes = []
    for variant in device_variants:
        headers = {**base_headers, **variant}
        try:
            resp = requests.patch(REMOVE_URL, json=payload, headers=headers, timeout=30)
            tried_codes.append(resp.status_code)
            if resp.status_code in (200, 201, 204):
                return True, tried_codes
        except:
            tried_codes.append(0)
        time.sleep(6)

    return False, tried_codes

def cancel_invitation_sync(owner, member, token):
    member_intl = ('20' + member[1:]) if member.startswith('0') else member
    payload = {
        "category": [{"listHierarchyId": "TemplateID", "value": "0"}],
        "createdBy": {"value": "MobileApp"},
        "name": "FlexFamily",
        "parts": {
            "member": [
                {"id": [{"schemeName": "MSISDN", "value": member_intl}], "type": "Member"},
                {"id": [{"schemeName": "MSISDN", "value": owner}], "type": "Owner"}
            ]
        },
        "type": "CancelInvitation"
    }

    device_variants = [
        {"device-id": "53a5c7cdda114b09", "x-agent-operatingsystem": "15", "x-agent-device": "Realme RMX3760", "x-agent-version": "2026.4.1", "x-agent-build": "1139"},
        {"device-id": "b26ba335813fad21", "x-agent-operatingsystem": "13", "x-agent-device": "Xiaomi M2101K7BG", "x-agent-version": "2026.2.1", "x-agent-build": "1200"},
        {"device-id": "b83aab2d8fa633da", "x-agent-operatingsystem": "13", "x-agent-device": "Xiaomi M2102J20SG", "x-agent-version": "2025.11.1", "x-agent-build": "1063"},
        {"device-id": "81bfbfaa09602859", "x-agent-operatingsystem": "16", "x-agent-device": "HONOR DNY-NX9", "x-agent-version": "2025.11.1", "x-agent-build": "1063"},
        {"device-id": "ba4068643748bc78", "x-agent-operatingsystem": "15", "x-agent-device": "HONOR ALI-NX1", "x-agent-version": "2025.11.1.1", "x-agent-build": "1064"},
        {"device-id": "25vt5q5qwg8dk01a", "x-agent-operatingsystem": "15", "x-agent-device": "Samsung SM-A165F", "x-agent-version": "2025.12.2", "x-agent-build": "1080"},
    ]

    base_headers = {
        'User-Agent': "okhttp/4.12.0",
        'Connection': "Keep-Alive",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json; charset=UTF-8",
        'Authorization': f'Bearer {token}',
        'api-version': "v2",
        'clientId': "AnaVodafoneAndroid",
        'msisdn': owner,
        'Accept-Language': "ar"
    }

    tried_codes = []
    for variant in device_variants:
        headers = {**base_headers, **variant}
        try:
            resp = requests.patch(REMOVE_URL, json=payload, headers=headers, timeout=30)
            tried_codes.append(resp.status_code)
            if resp.status_code in (200, 201, 204):
                return True, tried_codes
        except:
            tried_codes.append(0)
        time.sleep(6)

    return False, tried_codes

def normalize_msisdn(msisdn):
    if msisdn.startswith('0'):
        return '+20' + msisdn[1:]
    return msisdn

def accept_invitation_sync(owner, member, token_member):
    retry_waits = [0, 3, 5]
    for attempt, wait in enumerate(retry_waits, start=1):
        if wait:
            time.sleep(wait)
        payload = {
            "category": [{"listHierarchyId": "TemplateID", "value": "47"}],
            "name": "FlexFamily",
            "parts": {
                "member": [
                    {"id": [{"schemeName": "MSISDN", "value": owner}], "type": "Owner"},
                    {"id": [{"schemeName": "MSISDN", "value": member}], "type": "Member"}
                ]
            },
            "type": "AcceptInvitation"
        }
        headers = {
            'User-Agent': "okhttp/4.11.0",
            'Connection': "Keep-Alive",
            'Accept': "application/json",
            'Accept-Encoding': "gzip",
            'Content-Type': "application/json",
            'api_id': "APP",
            'Authorization': f"Bearer {token_member}",
            'api-version': "v2",
            'x-agent-operatingsystem': "13",
            'clientId': "AnaVodafoneAndroid",
            'x-agent-device': "Xiaomi M2101K7BG",
            'x-agent-version': "2026.2.1",
            'x-agent-build': "1200",
            'msisdn': member,
            'Accept-Language': "ar"
        }
        try:
            resp = requests.patch(FAMILY_API_URL_MOBILE, data=json.dumps(payload), headers=headers, timeout=15)
            if resp.status_code in [201, 200]:
                return True
        except:
            pass
    return False

# ====================================================================
# 6.2 دوال الإرسال المحسّنة - مع توزيع الجولات المتغير
# ====================================================================

# تعريف أنماط الجولات - كل جولة تحدد (عدد تطبيق, عدد ويب)
ROUND_PATTERNS = [
    (4, 2),  # الجولة 1: 4 برنامج + 2 ويب
    (2, 4),  # الجولة 2: 2 برنامج + 4 ويب
    (6, 0),  # الجولة 3: 6 برنامج
    (0, 6),  # الجولة 4: 6 ويب
    (3, 3),  # الجولة 5: 3 برنامج + 3 ويب
]

async def send_invitation_async_v3(session, access_token, owner_number, member_number, quota_value, attempt_num, device_type, delay_offset=0):
    """نسخة محسّنة مع random delays و device randomization"""
    
    payload = json.dumps({
      "name": "FlexFamily", 
      "type": "SendInvitation", 
      "category": [
        {"value": "523", "listHierarchyId": "PackageID"}, 
        {"value": "47", "listHierarchyId": "TemplateID"},
        {"value": "523", "listHierarchyId": "TierID"}, 
        {"value": "percentage", "listHierarchyId": "familybehavior"}
      ], 
      "parts": { 
        "member": [
          {"id": [{"value": owner_number, "schemeName": "MSISDN"}], "type": "Owner"},
          {"id": [{"value": member_number, "schemeName": "MSISDN"}], "type": "Member"}
        ], 
        "characteristicsValue": {
          "characteristicsValue": [{"characteristicName": "quotaDist1", "value": str(quota_value), "type": "percentage"}]
        }
      }
    })
    
    if device_type == "app":
        app_variants = [
            {'device-id': 'b26ba335813fad21', 'x-agent-device': 'Xiaomi M2101K7BG', 'x-agent-version': '2026.2.1'},
            {'device-id': '53a5c7cdda114b09', 'x-agent-device': 'Realme RMX3760', 'x-agent-version': '2026.4.1'},
            {'device-id': 'b83aab2d8fa633da', 'x-agent-device': 'Xiaomi M2102J20SG', 'x-agent-version': '2025.11.1'},
            {'device-id': '81bfbfaa09602859', 'x-agent-device': 'HONOR DNY-NX9', 'x-agent-version': '2025.11.1'},
        ]
        device = random.choice(app_variants)
        headers = {
          'User-Agent': 'okhttp/4.12.0', 
          'Accept': "application/json", 
          'Content-Type': "application/json",
          'Authorization': f"Bearer {access_token}", 
          'msisdn': owner_number, 
          'clientId': "AnaVodafoneAndroid",
          'api-version': "v2",
          'device-id': device['device-id'],
          'x-agent-device': device['x-agent-device'],
          'x-agent-version': device['x-agent-version'],
          'Accept-Language': "ar-EG,ar;q=0.9",
          'Accept-Encoding': "gzip, deflate",
          'Connection': 'keep-alive',
        }
        api_url = FAMILY_API_URL_MOBILE
    else:
        web_variants = [
            'Mozilla/5.0 (Linux; Android 10; Samsung SM-G950F)',
            'Mozilla/5.0 (Linux; Android 11; Pixel 5)',
            'Mozilla/5.0 (Linux; Android 12; SM-G960F)',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        ]
        headers = {
          'User-Agent': random.choice(web_variants),
          'Accept': "application/json", 
          'Content-Type': "application/json",
          'Authorization': f"Bearer {access_token}", 
          'msisdn': owner_number, 
          'clientId': "WebsiteConsumer",
          'Origin': "https://web.vodafone.com.eg", 
          'Referer': "https://web.vodafone.com.eg/spa/familySharing",
          'Accept-Language': "ar-EG,ar;q=0.9,en-US;q=0.8",
          'Accept-Encoding': "gzip, deflate, br",
          'Connection': 'keep-alive',
          'Cache-Control': 'no-cache',
        }
        api_url = FAMILY_API_URL_WEB

    await asyncio.sleep(delay_offset + random.uniform(0.1, 0.5))
    
    try:
        async with session.post(api_url, data=payload, headers=headers, timeout=45) as response:
            status_code = response.status
            if status_code == 201:
                return True, status_code, device_type
            else:
                return False, status_code, device_type
    except Exception as e:
        return False, 0, device_type


async def send_round_requests(session, access_token, owner_number, member_number, quota_value, app_count, web_count, round_num):
    """
    إرسال طلبات جولة معينة بناءً على عدد التطبيق وعدد الويب المطلوب
    """
    
    async def send_with_retry(device_type, device_index, retry_count=2):
        for retry in range(retry_count):
            delay = device_index * 0.3 + retry * 0.15 + (round_num * 0.1)
            success, status_code, dtype = await send_invitation_async_v3(
                session, access_token, owner_number, member_number, quota_value, 
                1, device_type, delay_offset=delay
            )
            if success:
                return True, status_code, dtype
            if retry < retry_count - 1:
                await asyncio.sleep(random.uniform(0.3, 1.0))
        return False, 0, device_type
    
    tasks = []
    # إضافة مهام التطبيق
    for i in range(app_count):
        tasks.append(send_with_retry("app", i))
    # إضافة مهام الويب
    for i in range(web_count):
        tasks.append(send_with_retry("web", app_count + i))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = 0
    status_codes = []
    device_types = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            status_codes.append(0)
            device_types.append(f"❌-{i+1}")
        else:
            success, status_code, dtype = result
            status_codes.append(status_code)
            icon = "📱" if dtype == "app" else "🌐"
            device_types.append(f"{icon}{i+1}")
            if success:
                success_count += 1
    
    return success_count, status_codes, device_types


def run_invitation_phase_v3(owner, token, member, quota_percent, chat_id=None, operation_number=None, stop_event=None, owner_pass=None):
    """
    مرحلة الإرسال المحسّنة - جولات متغيرة (4+2, 2+4, 6+0, 0+6, 3+3) وتتكرر
    توقف فوراً لما اتنين أو أكتر ينجحو
    ملحوظة: جلب الحد اليومي بيتم مرة واحدة بس قبل بدء الجولات - مش بيتكرر كل جولة
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_async():
            import time
            start_time = time.time()
            
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
            timeout = aiohttp.ClientTimeout(total=90)

            attempt = 0
            total_success = 0
            consecutive_fail_rounds = 0
            daily_remaining_line = ""
            last_status_line = ""
            round_index = 0
            
            # اقرأ الحد اليومي مرة واحدة بس في الأول
            if owner_pass:
                try:
                    limit_day, remaining_day, _ = get_daily_request_limit(owner, owner_pass)
                    if remaining_day is not None:
                        daily_remaining_line = f"\n📉 **المتبقي اليوم:** {remaining_day}"
                except:
                    pass

            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                while total_success < 2:
                    if stop_event is not None and stop_event.is_set():
                        elapsed_time = int(time.time() - start_time)
                        return "stopped", attempt, total_success, elapsed_time

                    attempt += 1
                    elapsed_time = int(time.time() - start_time)
                    
                    # اختيار نمط الجولة الحالي (يتكرر دورياً)
                    app_count, web_count = ROUND_PATTERNS[round_index % len(ROUND_PATTERNS)]
                    round_index += 1
                    total_requests = app_count + web_count

                    if chat_id and operation_number:
                        time_str = f"{elapsed_time // 60}:{elapsed_time % 60:02d}" if elapsed_time >= 60 else f"{elapsed_time}ث"
                        status_line = f"\n🔎 **آخر رد:** {last_status_line}" if last_status_line else ""
                        update_operation_message(
                            chat_id, operation_number,
                            f"📤 **الجولة {attempt}** ({app_count}📱+{web_count}🌐)\n⏱️ **الوقت:** {time_str}{daily_remaining_line}\n\n⚡ جاري إرسال {total_requests} طلبات...{status_line}\n♥ صلي علي النبي محمد ﷺ",
                            get_stop_button(operation_number)
                        )

                    success_count, status_codes, device_types = await send_round_requests(
                        session, token, owner, member, quota_percent,
                        app_count, web_count, attempt
                    )
                    last_status_line = format_status_codes_line(device_types, status_codes)

                    if success_count == 1:
                        # دعوة يتيمة - نلغيها
                        await asyncio.sleep(10)
                        try:
                            cancelled, tried_codes = await asyncio.to_thread(remove_member_sync, owner, member, token)
                            codes_str = ",".join(str(c) for c in tried_codes)
                            last_status_line += f" | 🗑️ إلغاء: {'✅' if cancelled else '❌'}"
                        except:
                            pass
                        total_success = 0
                        consecutive_fail_rounds += 1
                    elif success_count >= 2:
                        # اتنين أو أكتر - توقف فوراً!
                        total_success = success_count
                        consecutive_fail_rounds = 0
                    else:
                        total_success = 0
                        consecutive_fail_rounds += 1

                    if total_success >= 2:
                        elapsed_time = int(time.time() - start_time)
                        # ملحوظة: مفيش رسالة نجاح هنا عمداً - الرسالة النهائية الموحدة
                        # (نجاح + نتيجة الكشف الحقيقي + الحد اليومي) بتتبعت مرة واحدة بعد الخروج من الدالة دي
                        return True, attempt, total_success, elapsed_time

                    # نوم قابل للمقاطعة
                    for _ in range(16):
                        if stop_event is not None and stop_event.is_set():
                            elapsed_time = int(time.time() - start_time)
                            return "stopped", attempt, total_success, elapsed_time
                        await asyncio.sleep(0.5)

            elapsed_time = int(time.time() - start_time)
            return False, attempt, total_success, elapsed_time

        result, attempts, total_success, elapsed = loop.run_until_complete(run_async())
        loop.close()
        return result, attempts, total_success, elapsed

    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False, 0, 0, 0


async def change_quota_async(session, access_token, owner_number, member_number, new_quota):
    """تغيير النسبة المئوية"""
    payload = json.dumps({
        "category": [{"listHierarchyId": "TemplateID", "value": "47"}],
        "createdBy": {"value": "MobileApp"},
        "parts": {
            "characteristicsValue": {
                "characteristicsValue": [{
                    "characteristicName": "quotaDist1",
                    "type": "percentage",
                    "value": str(new_quota)
                }]
            },
            "member": [
                {"id": [{"schemeName": "MSISDN", "value": owner_number}], "type": "Owner"},
                {"id": [{"schemeName": "MSISDN", "value": member_number}], "type": "Member"}
            ]
        },
        "type": "QuotaRedistribution"
    })

    headers = {
        'User-Agent': "okhttp/4.11.0",
        'Connection': "Keep-Alive",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/json",
        'Authorization': f"Bearer {access_token}",
        'api-version': "v2",
        'x-agent-operatingsystem': "13",
        'clientId': "AnaVodafoneAndroid",
        'x-agent-device': "Xiaomi M2101K7BG",
        'x-agent-version': "2026.2.1",
        'x-agent-build': "1200",
        'msisdn': owner_number,
        'Accept-Language': "ar"
    }

    try:
        async with session.patch(FAMILY_API_URL_MOBILE, data=payload, headers=headers, timeout=15) as response:
            return response.status in [200, 201]
    except:
        return False

def run_flex_operation_v2(message, family_data, operation_id, operation_number):
    """الدورة الكاملة - مع كشف حقيقي للدعوات المعلقة وإعادة محاولة لو العدد مش متطابق"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    owner = family_data['owner_number']
    owner_pass = family_data['owner_password']
    member = family_data['member_number']
    quota_percent = family_data.get('quota_percentage', '10')
    with_accept = family_data.get('with_accept', False)
    member_pass = family_data.get('member_password', None)

    stop_event = threading.Event()
    if user_id not in ACTIVE_OPERATIONS:
        ACTIVE_OPERATIONS[user_id] = {}
    ACTIVE_OPERATIONS[user_id][operation_id] = {
        'stop_event': stop_event,
        'family_data': family_data,
        'start_time': get_egypt_time(),
        'operation_number': operation_number
    }

    markup = get_stop_button(operation_number)
    send_operation_message(
        chat_id, operation_id, operation_number,
        f"🚀 **جاري تنفيذ العملية**\n\n👤 **الأونر:** {owner}\n👥 **الفرد:** {member}\n📊 **النسبة:** {quota_percent}%\n🤖 **نوع:** {'قبول' if with_accept else 'بدون قبول'}\n\n⏳ جاري تسجيل الدخول...\n♥ صلي علي النبي محمد ﷺ",
        markup
    )

    # تسجيل دخول الأونر
    try:
        token_owner, _ = login(owner, owner_pass)
    except Exception as e:
        update_operation_message(chat_id, operation_number, f"❌ **فشل تسجيل دخول الأونر**\n\nالخطأ: {str(e)[:100]}")
        if user_id in ACTIVE_OPERATIONS:
            ACTIVE_OPERATIONS[user_id].pop(operation_id, None)
        return

    MAX_RETRIES = 3
    retry_num = 0
    total_success = 0
    attempts = 0
    pending_invites = []

    while retry_num < MAX_RETRIES:
        if stop_event.is_set():
            if user_id in ACTIVE_OPERATIONS:
                ACTIVE_OPERATIONS[user_id].pop(operation_id, None)
            return

        retry_word = f" (محاولة {retry_num + 1}/{MAX_RETRIES})" if retry_num > 0 else ""
        update_operation_message(
            chat_id, operation_number,
            f"🚀 **جاري تنفيذ العملية**{retry_word}\n\n👤 **الأونر:** {owner}\n👥 **الفرد:** {member}\n📊 **النسبة:** {quota_percent}%\n\n⏳ جاري إرسال الدعوات...\n♥ صلي علي النبي محمد ﷺ",
            markup
        )

        if stop_event.is_set():
            if user_id in ACTIVE_OPERATIONS:
                ACTIVE_OPERATIONS[user_id].pop(operation_id, None)
            return

        # ===== مرحلة الإرسال =====
        invite_success, attempts, total_success, elapsed_sec = run_invitation_phase_v3(
            owner, token_owner, member, quota_percent,
            chat_id=chat_id, operation_number=operation_number,
            stop_event=stop_event, owner_pass=owner_pass
        )

        # ===== المستخدم ضغط إيقاف =====
        if invite_success == "stopped" or stop_event.is_set():
            if user_id in ACTIVE_OPERATIONS:
                ACTIVE_OPERATIONS[user_id].pop(operation_id, None)
            return

        if not invite_success:
            update_operation_message(
                chat_id, operation_number,
                f"❌ **فشل إرسال دعوتين**\n\n📊 **عدد الجولات:** {attempts}\n📤 **عدد الدعوات الناجحة:** {total_success}\n\n⚠️ **لو كل المحاولات بتفشل تأكد من:**\n1️⃣ رصيد الفرد لا يقل عن 14 قرش\n2️⃣ الأونر مبلغش الحد اليومي\n\n🔍 استخدم /dailylimit للتأكد\n\n♥ صلي علي النبي محمد ﷺ"
            )
            update_user_stats(user_id, operation_success=False)
            if user_id in ACTIVE_OPERATIONS:
                ACTIVE_OPERATIONS[user_id].pop(operation_id, None)
            return

        # ===== نجحت الدعوات ظاهرياً - نتأكد بالكشف الحقيقي =====
        update_operation_message(
            chat_id, operation_number,
            f"🔎 **جاري التأكد من الدعوات المعلقة فعلياً...**\n\n♥ صلي علي النبي محمد ﷺ",
            markup
        )

        pending_invites = []
        try:
            family_data_response = get_family_info(token_owner, owner)
            if family_data_response:
                pending_invites = parse_pending_invitations(family_data_response)
        except Exception as e:
            print(f"❌ خطأ في الكشف: {e}")

        pending_count = len(pending_invites)

        if pending_count >= 2:
            # نجاح حقيقي - العدد مطابق فعلاً
            break

        # العدد مش مطابق (0 أو 1) - نحذف اللي موجود ونعيد المحاولة من الأول
        if pending_count == 1:
            try:
                remove_member_sync(owner, pending_invites[0]['number'], token_owner)
            except Exception as e:
                print(f"❌ خطأ في حذف الدعوة اليتيمة قبل الإعادة: {e}")

        retry_num += 1
        if retry_num < MAX_RETRIES:
            update_operation_message(
                chat_id, operation_number,
                f"⚠️ **العدد مش متطابق (لقينا {pending_count} بس)، جاري الحذف وإعادة المحاولة...**\n\n♥ صلي علي النبي محمد ﷺ",
                markup
            )
            time.sleep(3)
    else:
        # خلصت كل المحاولات المسموحة من غير ما نوصل لعدد مطابق
        update_operation_message(
            chat_id, operation_number,
            f"❌ **فشل تأكيد الدعوتين بعد {MAX_RETRIES} محاولات**\n\nحاول تاني بعد شوية أو تأكد يدوياً من التطبيق.\n\n♥ صلي علي النبي محمد ﷺ"
        )
        update_user_stats(user_id, operation_success=False)
        if user_id in ACTIVE_OPERATIONS:
            ACTIVE_OPERATIONS[user_id].pop(operation_id, None)
        return

    # ===== نجحت فعلياً بعدد مطابق (2 أو أكتر) =====
    delete_operation_message(user_id, operation_number)

    pending_count = len(pending_invites)
    detect_line = f"📋 **تم الكشف بنجاح و العثور على {pending_count} دعوة معلقة**"

    # ===== جلب الحد اليومي النهائي مرة واحدة بعد نجاح العملية فعلياً =====
    daily_limit_line = ""
    used_requests = None
    try:
        limit_day, remaining_day, _ = get_daily_request_limit(owner, owner_pass)
        if limit_day is not None and remaining_day is not None:
            limit_int = int(limit_day)
            remaining_int = int(remaining_day)
            used_requests = max(limit_int - remaining_int, 0)
            daily_limit_line = f"\n📊 **الطلبات اليوم:** استهلكت {used_requests} من {limit_int} (متبقي {remaining_int})"
    except Exception as e:
        print(f"❌ خطأ في جلب الحد اليومي النهائي: {e}")

    confirm_msg = (
        f"✅ **تم إرسال {total_success} دعوة بنجاح!**\n\n"
        f"📊 **عدد الجولات:** {attempts}\n\n"
        f"👤 **الأونر:** {owner}\n"
        f"👥 **الفرد:** {member}\n"
        f"📊 **النسبة:** {quota_percent}%\n\n"
        f"{detect_line}"
        f"{daily_limit_line}\n\n"
        f"♥ صلي علي النبي محمد ﷺ"
    )

    main_bot.send_message(chat_id, confirm_msg, parse_mode="Markdown")

    # ===== تنبيه لو عدد الطلبات المستهلكة وصل الحد المحدد =====
    if used_requests is not None and used_requests >= DAILY_LIMIT_WARNING_THRESHOLD:
        main_bot.send_message(
            chat_id,
            f"⚠️ **تنبيه: عدد الطلبات اليومي وصل إلى {used_requests} طلب!**\n\nخد بالك من الوصول للحد الأقصى المسموح به من فودافون.\n\n♥ صلي علي النبي محمد ﷺ",
            parse_mode="Markdown"
        )

    # ===== لو بدون قبول: نعرض عليه إلغاء الدعوة (رسالة الساعة الجاية - زي ما هي) =====
    if not with_accept:
        update_user_stats(user_id, operation_success=True)
        offer_cancel_last_invitation(chat_id, user_id, operation_id, owner, token_owner, member)
        return

    # ===== مع قبول: تشغيل العمليات في الخلفية =====
    Thread(
        target=handle_accept_and_quota_change,
        args=(chat_id, user_id, operation_id, owner, owner_pass, member, member_pass, quota_percent, token_owner, stop_event)
    ).start()

def handle_accept_and_quota_change(chat_id, user_id, operation_id, owner, owner_pass, member, member_pass, quota_percent, token_owner, stop_event=None):
    """معالجة القبول وتغيير النسبة في الخلفية"""
    try:
        if stop_event is not None and stop_event.is_set():
            if user_id in ACTIVE_OPERATIONS:
                ACTIVE_OPERATIONS[user_id].pop(operation_id, None)
            return

        # تسجيل دخول الفرد
        try:
            token_member, _ = login(member, member_pass)
        except Exception as e:
            main_bot.send_message(chat_id, f"❌ **فشل تسجيل دخول الفرد للقبول**\n\nالخطأ: {str(e)[:100]}")
            update_user_stats(user_id, operation_success=False)
            if user_id in ACTIVE_OPERATIONS:
                ACTIVE_OPERATIONS[user_id].pop(operation_id, None)
            return

        if stop_event is not None and stop_event.is_set():
            if user_id in ACTIVE_OPERATIONS:
                ACTIVE_OPERATIONS[user_id].pop(operation_id, None)
            return

        # ===== مرحلة القبول =====
        main_bot.send_message(
            chat_id,
            f"⏳ **جاري قبول الدعوة...**\n\n👤 {owner}\n👥 {member}\n\n♥ صلي علي النبي محمد ﷺ",
            parse_mode="Markdown"
        )

        accept_ok = accept_invitation_sync(owner, member, token_member)

        if not accept_ok:
            main_bot.send_message(
                chat_id,
                f"❌ **فشل قبول الدعوة**\n\nيرجى قبولها يدوياً من التطبيق.\n♥ صلي علي النبي محمد ﷺ"
            )
            update_user_stats(user_id, operation_success=False)
            if user_id in ACTIVE_OPERATIONS and operation_id in ACTIVE_OPERATIONS[user_id]:
                ACTIVE_OPERATIONS[user_id].pop(operation_id, None)
            return

        # ===== تم القبول - اسأل عن تغيير النسبة =====
        main_bot.send_message(
            chat_id,
            f"✅ **تم قبول الدعوة!**\n\n❓ هل تريد تغيير النسبة؟",
            parse_mode="Markdown"
        )

        # إرسال أزرار اختيار النسبة
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(
            types.InlineKeyboardButton("1️⃣3️⃣0️⃣0", callback_data=f"change_quota_1300_{user_id}_{operation_id}"),
            types.InlineKeyboardButton("2️⃣6️⃣0️⃣0", callback_data=f"change_quota_2600_{user_id}_{operation_id}"),
            types.InlineKeyboardButton("5️⃣2️⃣0️⃣0", callback_data=f"change_quota_5200_{user_id}_{operation_id}")
        )
        markup.add(
            types.InlineKeyboardButton("⏭️ تخطي", callback_data=f"skip_quota_{user_id}_{operation_id}")
        )

        sent_msg = main_bot.send_message(
            chat_id,
            f"📊 **اختر النسبة الجديدة:**\n\n• 1300 = 10%\n• 2600 = 20%\n• 5200 = 40%\n\nأم تخطي؟",
            reply_markup=markup,
            parse_mode="Markdown"
        )

        # حفظ بيانات العملية
        if user_id not in ACTIVE_OPERATIONS:
            ACTIVE_OPERATIONS[user_id] = {}
        if operation_id in ACTIVE_OPERATIONS[user_id]:
            ACTIVE_OPERATIONS[user_id][operation_id]['pending_quota_data'] = {
                'sent_msg_id': sent_msg.message_id,
                'token_owner': token_owner,
                'owner_pass': owner_pass,
                'member': member,
                'quota_percent': quota_percent
            }

    except Exception as e:
        print(f"❌ خطأ في معالجة القبول: {e}")
        main_bot.send_message(chat_id, f"❌ حدث خطأ: {str(e)[:100]}")
        update_user_stats(user_id, operation_success=False)
        if user_id in ACTIVE_OPERATIONS and operation_id in ACTIVE_OPERATIONS[user_id]:
            ACTIVE_OPERATIONS[user_id].pop(operation_id, None)

def execute_quota_change(user_id, operation_id, chat_id, new_quota, owner, token_owner, member):
    """تنفيذ تغيير النسبة"""
    percent_value = QUOTA_BUTTON_TO_PERCENT.get(new_quota, new_quota)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_async():
            connector = aiohttp.TCPConnector(limit=10)
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                change_ok = await change_quota_async(session, token_owner, owner, member, percent_value)
                return change_ok

        change_ok = loop.run_until_complete(run_async())
        loop.close()

        if change_ok:
            main_bot.send_message(chat_id, f"✅ **تم تغيير النسبة إلى {new_quota} ({percent_value}%) بنجاح!**\n\n♥ صلي علي النبي محمد ﷺ")
            update_user_stats(user_id, operation_success=True)
        else:
            main_bot.send_message(chat_id, f"⚠️ **فشل تغيير النسبة**\n\nقد تكون هناك مشكلة في الاتصال.\n♥ صلي علي النبي محمد ﷺ")
            update_user_stats(user_id, operation_success=True)

    except Exception as e:
        print(f"❌ خطأ في تنفيذ التغيير: {e}")
        main_bot.send_message(chat_id, f"❌ خطأ: {str(e)[:100]}")
        update_user_stats(user_id, operation_success=True)
    finally:
        offer_cancel_last_invitation(chat_id, user_id, operation_id, owner, token_owner, member)

def offer_cancel_last_invitation(chat_id, user_id, operation_id, owner, token_owner, member):
    """بعد القبول، نسأل المستخدم لو عايز يلغي الدعوة المعلقة"""
    if user_id not in ACTIVE_OPERATIONS or operation_id not in ACTIVE_OPERATIONS[user_id]:
        return

    ACTIVE_OPERATIONS[user_id][operation_id]['pending_cancel_data'] = {
        'owner': owner,
        'token_owner': token_owner,
        'member': member
    }

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🗑️ إلغاء الدعوة المعلقة", callback_data=f"cancel_last_yes_{user_id}_{operation_id}"),
        types.InlineKeyboardButton("✅ لأ، سيبها", callback_data=f"cancel_last_no_{user_id}_{operation_id}")
    )
    main_bot.send_message(
        chat_id,
        "🗑️ **فيه دعوة تانية معلقة (مقبولتش) للفرد ده.**\n\nعايز تلغيها؟ لو قلت أه، هيتم الإلغاء تلقائي بعد ما الساعة الحالية تتجدد + دقيقتين أمان.\n\n♥ صلي علي النبي محمد ﷺ",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def schedule_cancel_last_invitation(user_id, operation_id, chat_id, owner, token_owner, member):
    """الانتظار لحد تجديد الساعة + دقيقتين، ثم الإلغاء"""
    try:
        now = get_egypt_time()
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        wait_seconds = (next_hour - now).total_seconds() + 120
        if wait_seconds > 0:
            time.sleep(wait_seconds)

        if user_id not in ACTIVE_OPERATIONS or operation_id not in ACTIVE_OPERATIONS[user_id]:
            return

        cancel_ok, tried_codes = remove_member_sync(owner, member, token_owner)
        if cancel_ok:
            main_bot.send_message(chat_id, "✅ **تم إلغاء الدعوة المعلقة بنجاح!**\n\n♥ صلي علي النبي محمد ﷺ", parse_mode="Markdown")
        else:
            codes_str = ",".join(str(c) for c in tried_codes)
            main_bot.send_message(chat_id, f"⚠️ **فشل إلغاء الدعوة المعلقة**\n\n🔎 محاولات: {codes_str}\n\nممكن تلغيها يدوياً من التطبيق.\n♥ صلي علي النبي محمد ﷺ", parse_mode="Markdown")
    except Exception as e:
        print(f"❌ خطأ في إلغاء الدعوة الأخيرة: {e}")
    finally:
        if user_id in ACTIVE_OPERATIONS and operation_id in ACTIVE_OPERATIONS[user_id]:
            ACTIVE_OPERATIONS[user_id].pop(operation_id, None)

# ====================================================================
# 7. دالة التحقق من الاشتراك في القنوات
# ====================================================================
def check_subscription(user_id, bot_to_use=main_bot):
    not_subscribed = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot_to_use.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                not_subscribed.append(channel)
        except:
            not_subscribed.append(channel)
    return not_subscribed

def subscription_required(func):
    def wrapper(message):
        user_id = message.from_user.id
        not_subscribed = check_subscription(user_id, main_bot)
        if not_subscribed:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for channel in not_subscribed:
                channel_name = channel.replace('@', '')
                markup.add(types.InlineKeyboardButton(f"اشترك في {channel}", url=f"https://t.me/{channel_name}"))
            markup.add(types.InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_subscription"))
            main_bot.send_message(message.chat.id, "⚠️ يجب الاشتراك في القنوات التالية لاستخدام البوت:\n\n👇 اشترك ثم اضغط تحقق", reply_markup=markup)
            return
        return func(message)
    return wrapper

# ====================================================================
# 8. نظام العمليات والرسائل
# ====================================================================
def create_operation_id(user_id):
    operation_number = get_next_operation_number(user_id)
    operation_id = f"op_{user_id}_{operation_number}"
    return operation_id, operation_number

def update_operation_message(user_id, operation_number, message, reply_markup=None):
    try:
        operation_id = f"op_{user_id}_{operation_number}"
        if user_id in OPERATION_MESSAGES and operation_id in OPERATION_MESSAGES[user_id]:
            msg_id = OPERATION_MESSAGES[user_id][operation_id]
            main_bot.edit_message_text(chat_id=user_id, message_id=msg_id, text=message, parse_mode="Markdown", reply_markup=reply_markup)
    except:
        pass

def send_operation_message(chat_id, operation_id, operation_number, message, reply_markup=None):
    try:
        if chat_id not in OPERATION_MESSAGES:
            OPERATION_MESSAGES[chat_id] = {}
        if operation_id in OPERATION_MESSAGES[chat_id]:
            update_operation_message(chat_id, operation_number, message, reply_markup)
        else:
            sent_msg = main_bot.send_message(chat_id, message, parse_mode="Markdown", reply_markup=reply_markup)
            OPERATION_MESSAGES[chat_id][operation_id] = sent_msg.message_id
    except:
        pass

def delete_operation_message(user_id, operation_number):
    try:
        operation_id = f"op_{user_id}_{operation_number}"
        if user_id in OPERATION_MESSAGES and operation_id in OPERATION_MESSAGES[user_id]:
            msg_id = OPERATION_MESSAGES[user_id][operation_id]
            main_bot.delete_message(user_id, msg_id)
            del OPERATION_MESSAGES[user_id][operation_id]
    except:
        pass

def get_operation_by_number(user_id, operation_number):
    if user_id in ACTIVE_OPERATIONS:
        for op_id, op_data in ACTIVE_OPERATIONS[user_id].items():
            if op_data.get('operation_number') == operation_number:
                return op_id, op_data
    return None, None

def stop_operation(user_id, operation_number):
    op_id, op_data = get_operation_by_number(user_id, operation_number)
    if op_data and 'stop_event' in op_data:
        op_data['stop_event'].set()
        delete_operation_message(user_id, operation_number)
        if user_id in ACTIVE_OPERATIONS:
            ACTIVE_OPERATIONS[user_id].pop(op_id, None)
        main_bot.send_message(user_id, f"⚠️ **تم إيقاف العملية #{operation_number} فوراً.**\n\n♥ صلي علي النبي محمد ﷺ", parse_mode="Markdown")
        return True
    return False

def stop_all_operations(user_id):
    if user_id in ACTIVE_OPERATIONS:
        for op_data in list(ACTIVE_OPERATIONS[user_id].values()):
            if 'stop_event' in op_data:
                op_data['stop_event'].set()
        ACTIVE_OPERATIONS[user_id] = {}
        return True
    return False

def get_stop_button(operation_number):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⏹️ إيقاف العملية", callback_data=f"stop_op_{operation_number}"))
    return markup

def cancel_process(chat_id, user_id):
    if chat_id in USER_STATE:
        del USER_STATE[chat_id]
    if chat_id in PAYMENT_STATE:
        del PAYMENT_STATE[chat_id]
    main_bot.send_message(chat_id, "⚠️ تم إلغاء العملية.", reply_markup=types.ReplyKeyboardRemove())

def get_auto_accept(user_id):
    if str(user_id) not in USERS_STATS:
        return True
    return USERS_STATS[str(user_id)].get('auto_accept', True)

def toggle_auto_accept(user_id):
    user_id_str = str(user_id)
    if user_id_str not in USERS_STATS:
        init_user_stats(user_id)
    current = USERS_STATS[user_id_str].get('auto_accept', True)
    USERS_STATS[user_id_str]['auto_accept'] = not current
    save_all_data()
    return not current

def format_time_remaining(seconds):
    if seconds <= 0:
        return "0 دقيقة"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes > 0:
        return f"{minutes} دقيقة و {secs} ثانية"
    return f"{secs} ثانية"

def check_main_bot_access(user_id):
    if MAIN_BOT_STATUS != "running" and user_id != OWNER_ID:
        return False, "⏸️ البوت متوقف حالياً."
    if is_user_banned(user_id) and user_id != OWNER_ID:
        return False, "⛔ لقد تم حظرك من استخدام البوت."
    not_subscribed = check_subscription(user_id, main_bot)
    if not_subscribed:
        return False, "⚠️ يجب الاشتراك في القنوات الإجبارية أولاً."
    if not has_active_subscription(user_id) and user_id != OWNER_ID:
        return False, f"⚠️ **انتهت صلاحية اشتراكك**\n\nللتواصل مع المطور: {DEV_USERNAME_MD}\n\n📱 **فودافون كاش:** `{VODAFONE_CASH_NUMBER}`"
    return True, ""

def format_status_codes_line(device_types, status_codes):
    """سطر تشخيصي بيوضح رد كل محاولة"""
    parts = []
    for dt, code in zip(device_types, status_codes):
        icon = "✅" if code == 201 else "❌"
        parts.append(f"{dt}:{code}{icon}")
    return " | ".join(parts)

# ====================================================================
# 9. معالجات الأوامر الرئيسية
# ====================================================================
@main_bot.message_handler(commands=['start'])
@subscription_required
def main_start_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    access, msg = check_main_bot_access(user_id)
    if not access:
        if "اشتراكك" in msg:
            show_subscription_menu(chat_id, user_id)
        else:
            main_bot.send_message(chat_id, msg, parse_mode="Markdown")
        return
    init_user_stats(user_id)
    explanation_text = f"""
🌟 **مرحباً بك في بوت التطيير** 🌟
**صلوا على الحبيب محمد ﷺ ❤️**
📱 **فودافون كاش:** `{VODAFONE_CASH_NUMBER}`
📋 **الأوامر المتاحة:**
/run - بدء عملية جديدة
/accept - تشغيل/إيقاف القبول التلقائي
/stop - إيقاف عملية نشطة
/dailylimit - 🔍 كشف عدد الطلبات اليومي المتبقي للأونر
/stats - إحصائياتي الشخصية
/cancel - إلغاء العملية الحالية
    """
    main_bot.send_message(chat_id, explanation_text, parse_mode="Markdown")

@main_bot.message_handler(commands=['run'])
@subscription_required
def main_run_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    access, msg = check_main_bot_access(user_id)
    if not access:
        if "اشتراكك" in msg:
            show_subscription_menu(chat_id, user_id)
        else:
            main_bot.send_message(chat_id, msg, parse_mode="Markdown")
        return

    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    markup.add(
        types.KeyboardButton("📤 تعليق دعوتين فقط (بدون قبول)"),
        types.KeyboardButton("✅ تعليق دعوتين + قبول"),
        types.KeyboardButton("🔍 كشف عدد الطلبات اليومي"),
        types.KeyboardButton("📋 الدعوات المعلقة"),
        types.KeyboardButton("❌ إلغاء العملية")
    )
    main_bot.send_message(
        chat_id,
        "🕌 صلوا على الحبيب محمد ﷺ ❤️\n\n🔘 **اختر نوع العملية:**\n\n• **بدون قبول**: تعليق دعوتين فقط (لا يحتاج باسورد الفرد)\n• **مع قبول**: تعليق دعوتين ثم قبول تلقائي (يحتاج باسورد الفرد)\n• **كشف الحد اليومي**: تعرف عدد الطلبات المتبقية للأونر\n• **الدعوات المعلقة**: عرض الدعوات المعلقة النشطة للأونر",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    if chat_id not in USER_STATE:
        USER_STATE[chat_id] = []
    USER_STATE[chat_id].append({'step': 'choose_type', 'data': {}})
    main_bot.register_next_step_handler(message, handle_operation_type_choice, len(USER_STATE[chat_id]) - 1)

def handle_operation_type_choice(message, state_index):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.text in ("/cancel", "❌ إلغاء العملية"):
        cancel_process(chat_id, user_id)
        return
    if chat_id not in USER_STATE or state_index >= len(USER_STATE[chat_id]):
        main_bot.send_message(chat_id, "❌ انتهت الجلسة، استخدم /run مرة أخرى")
        return

    text = message.text.strip()
    if text == "🔍 كشف عدد الطلبات اليومي":
        if chat_id in USER_STATE and state_index < len(USER_STATE[chat_id]):
            USER_STATE[chat_id].pop(state_index)
            if not USER_STATE[chat_id]:
                del USER_STATE[chat_id]
        main_dailylimit_handler(message)
        return
    if text == "📋 الدعوات المعلقة":
        if chat_id in USER_STATE and state_index < len(USER_STATE[chat_id]):
            USER_STATE[chat_id].pop(state_index)
            if not USER_STATE[chat_id]:
                del USER_STATE[chat_id]
        main_check_pending_invites_handler(message)
        return
    if text == "📤 تعليق دعوتين فقط (بدون قبول)":
        with_accept = False
    elif text == "✅ تعليق دعوتين + قبول":
        with_accept = True
    else:
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        markup.add(
            types.KeyboardButton("📤 تعليق دعوتين فقط (بدون قبول)"),
            types.KeyboardButton("✅ تعليق دعوتين + قبول"),
            types.KeyboardButton("🔍 كشف عدد الطلبات اليومي"),
            types.KeyboardButton("📋 الدعوات المعلقة"),
            types.KeyboardButton("❌ إلغاء العملية")
        )
        main_bot.send_message(chat_id, "❌ اختيار غير صحيح، حاول مرة أخرى.", reply_markup=markup)
        main_bot.register_next_step_handler(message, handle_operation_type_choice, state_index)
        return

    USER_STATE[chat_id][state_index]['data']['with_accept'] = with_accept

    quota_markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True, one_time_keyboard=True)
    quota_markup.add(
        types.KeyboardButton("10"), types.KeyboardButton("20"), types.KeyboardButton("40"),
        types.KeyboardButton("❌ إلغاء العملية")
    )
    main_bot.send_message(chat_id, "📊 اختر نسبة الحصة (10 أو 20 أو 40):", reply_markup=quota_markup)
    USER_STATE[chat_id][state_index]['step'] = 'choose_quota'
    main_bot.register_next_step_handler(message, handle_quota_choice, state_index)

def handle_quota_choice(message, state_index):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.text in ("/cancel", "❌ إلغاء العملية"):
        cancel_process(chat_id, user_id)
        return
    if chat_id not in USER_STATE or state_index >= len(USER_STATE[chat_id]):
        main_bot.send_message(chat_id, "❌ انتهت الجلسة، استخدم /run مرة أخرى")
        return
    if message.text.strip() not in ('10', '20', '40'):
        quota_markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True, one_time_keyboard=True)
        quota_markup.add(types.KeyboardButton("10"), types.KeyboardButton("20"), types.KeyboardButton("40"), types.KeyboardButton("❌ إلغاء العملية"))
        main_bot.send_message(chat_id, "❌ نسبة غير صالحة. اختر 10 أو 20 أو 40.", reply_markup=quota_markup)
        main_bot.register_next_step_handler(message, handle_quota_choice, state_index)
        return

    USER_STATE[chat_id][state_index]['data']['quota_percentage'] = message.text.strip()
    cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel_markup.add(types.KeyboardButton("❌ إلغاء العملية"))
    main_bot.send_message(chat_id, "📱 أدخل رقم الأونر:", reply_markup=cancel_markup)
    USER_STATE[chat_id][state_index]['step'] = 'get_owner'
    main_bot.register_next_step_handler(message, handle_owner_number, state_index)

def handle_owner_number(message, state_index):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.text in ("/cancel", "❌ إلغاء العملية"):
        cancel_process(chat_id, user_id)
        return
    if chat_id not in USER_STATE or state_index >= len(USER_STATE[chat_id]):
        main_bot.send_message(chat_id, "❌ انتهت الجلسة، استخدم /run مرة أخرى")
        return
    USER_STATE[chat_id][state_index]['data']['owner_number'] = message.text.strip()
    cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel_markup.add(types.KeyboardButton("❌ إلغاء العملية"))
    main_bot.send_message(chat_id, "🔒 أدخل باسورد الأونر:", reply_markup=cancel_markup)
    USER_STATE[chat_id][state_index]['step'] = 'get_owner_pass'
    main_bot.register_next_step_handler(message, handle_owner_password, state_index)

def handle_owner_password(message, state_index):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.text in ("/cancel", "❌ إلغاء العملية"):
        cancel_process(chat_id, user_id)
        return
    if chat_id not in USER_STATE or state_index >= len(USER_STATE[chat_id]):
        main_bot.send_message(chat_id, "❌ انتهت الجلسة، استخدم /run مرة أخرى")
        return
    USER_STATE[chat_id][state_index]['data']['owner_password'] = message.text.strip()
    cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel_markup.add(types.KeyboardButton("❌ إلغاء العملية"))
    main_bot.send_message(chat_id, "👤 أدخل رقم الفرد:", reply_markup=cancel_markup)
    USER_STATE[chat_id][state_index]['step'] = 'get_member'
    main_bot.register_next_step_handler(message, handle_member_number, state_index)

def handle_member_number(message, state_index):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.text in ("/cancel", "❌ إلغاء العملية"):
        cancel_process(chat_id, user_id)
        return
    if chat_id not in USER_STATE or state_index >= len(USER_STATE[chat_id]):
        main_bot.send_message(chat_id, "❌ انتهت الجلسة، استخدم /run مرة أخرى")
        return
    USER_STATE[chat_id][state_index]['data']['member_number'] = message.text.strip()

    with_accept = USER_STATE[chat_id][state_index]['data'].get('with_accept', False)

    if with_accept:
        cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        cancel_markup.add(types.KeyboardButton("❌ إلغاء العملية"))
        main_bot.send_message(chat_id, "🔑 أدخل باسورد الفرد:", reply_markup=cancel_markup)
        USER_STATE[chat_id][state_index]['step'] = 'get_member_pass'
        main_bot.register_next_step_handler(message, handle_member_password, state_index)
    else:
        family_data = USER_STATE[chat_id][state_index]['data']
        USER_STATE[chat_id].pop(state_index)
        if not USER_STATE[chat_id]:
            del USER_STATE[chat_id]
        main_bot.send_message(chat_id, "⏳ جاري تنفيذ العملية...", reply_markup=types.ReplyKeyboardRemove())
        operation_id, operation_number = create_operation_id(user_id)
        Thread(target=run_flex_operation_v2, args=(message, family_data, operation_id, operation_number)).start()

def handle_member_password(message, state_index):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.text in ("/cancel", "❌ إلغاء العملية"):
        cancel_process(chat_id, user_id)
        return
    if chat_id not in USER_STATE or state_index >= len(USER_STATE[chat_id]):
        main_bot.send_message(chat_id, "❌ انتهت الجلسة، استخدم /run مرة أخرى")
        return
    USER_STATE[chat_id][state_index]['data']['member_password'] = message.text.strip()
    family_data = USER_STATE[chat_id][state_index]['data']
    USER_STATE[chat_id].pop(state_index)
    if not USER_STATE[chat_id]:
        del USER_STATE[chat_id]
    main_bot.send_message(chat_id, "⏳ جاري تنفيذ العملية...", reply_markup=types.ReplyKeyboardRemove())
    operation_id, operation_number = create_operation_id(user_id)
    Thread(target=run_flex_operation_v2, args=(message, family_data, operation_id, operation_number)).start()

@main_bot.message_handler(commands=['accept'])
@subscription_required
def main_accept_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    access, msg = check_main_bot_access(user_id)
    if not access:
        main_bot.send_message(chat_id, msg, parse_mode="Markdown")
        return
    new_state = toggle_auto_accept(user_id)
    if new_state:
        main_bot.send_message(chat_id, "✅ تم تفعيل القبول التلقائي.")
    else:
        main_bot.send_message(chat_id, "⛔ تم إيقاف القبول التلقائي.")

@main_bot.message_handler(commands=['dailylimit'])
@subscription_required
def main_dailylimit_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    access, msg = check_main_bot_access(user_id)
    if not access:
        main_bot.send_message(chat_id, msg, parse_mode="Markdown")
        return
    cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel_markup.add(types.KeyboardButton("❌ إلغاء العملية"))
    main_bot.send_message(chat_id, "📱 أدخل رقم الأونر اللي عايز تكشف حده اليومي:", reply_markup=cancel_markup)
    main_bot.register_next_step_handler(message, handle_dailylimit_owner_number)

def handle_dailylimit_owner_number(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.text in ("/cancel", "❌ إلغاء العملية"):
        cancel_process(chat_id, user_id)
        return
    owner_number = message.text.strip()
    cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel_markup.add(types.KeyboardButton("❌ إلغاء العملية"))
    main_bot.send_message(chat_id, "🔒 أدخل باسورد الأونر:", reply_markup=cancel_markup)
    main_bot.register_next_step_handler(message, handle_dailylimit_owner_password, owner_number)

def handle_dailylimit_owner_password(message, owner_number):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.text in ("/cancel", "❌ إلغاء العملية"):
        cancel_process(chat_id, user_id)
        return
    owner_password = message.text.strip()
    main_bot.send_message(chat_id, "⏳ جاري كشف الحد اليومي...", reply_markup=types.ReplyKeyboardRemove())
    limit_day, remaining_day, error = get_daily_request_limit(owner_number, owner_password)
    if error and not limit_day and not remaining_day:
        main_bot.send_message(chat_id, f"❌ **لم يتم كشف الحد اليومي**\n\nالخطأ: {error}\n\n♥ صلي علي النبي محمد ﷺ", parse_mode="Markdown")
        return
    main_bot.send_message(chat_id, format_daily_limit_message(owner_number, limit_day, remaining_day), parse_mode="Markdown")

@main_bot.message_handler(commands=['stop'])
@subscription_required
def main_stop_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    access, msg = check_main_bot_access(user_id)
    if not access:
        main_bot.send_message(chat_id, msg, parse_mode="Markdown")
        return
    
    if user_id in ACTIVE_OPERATIONS and ACTIVE_OPERATIONS[user_id]:
        if len(ACTIVE_OPERATIONS[user_id]) == 1:
            op_num = list(ACTIVE_OPERATIONS[user_id].values())[0].get('operation_number', 0)
            stop_operation(user_id, op_num)
        else:
            markup = types.InlineKeyboardMarkup()
            ops_text = "🔄 **العمليات النشطة:**\n\n"
            
            for op_id, op_data in ACTIVE_OPERATIONS[user_id].items():
                phone = op_data.get('family_data', {}).get('member_number', 'غير معروف')
                op_num = op_data.get('operation_number', 0)
                owner = op_data.get('family_data', {}).get('owner_number', 'غير معروف')
                
                ops_text += f"#{op_num} | 👤 {owner} → 👥 {phone}\n"
                
                markup.add(
                    types.InlineKeyboardButton(
                        f"🛑 إيقاف العملية #{op_num}",
                        callback_data=f"stop_op_{op_num}"
                    )
                )
            
            ops_text += "\nاختر العملية التي تريد إيقافها:"
            main_bot.send_message(chat_id, ops_text, reply_markup=markup, parse_mode="Markdown")
    else:
        main_bot.send_message(chat_id, "📭 **لا توجد عمليات نشطة حالياً**", parse_mode="Markdown")

@main_bot.message_handler(commands=['stats'])
@subscription_required
def main_stats_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    access, msg = check_main_bot_access(user_id)
    if not access:
        main_bot.send_message(chat_id, msg, parse_mode="Markdown")
        return
    if str(user_id) not in USERS_STATS:
        init_user_stats(user_id)
    stats = USERS_STATS[str(user_id)]
    success_rate = 0
    if stats['total_operations'] > 0:
        success_rate = (stats['successful_operations'] / stats['total_operations']) * 100
    accept_status = "✅ مفعل" if stats.get('auto_accept', True) else "⛔ معطل"
    sub_info = get_subscription_info(user_id)
    stats_text = f"""
📊 **إحصائياتك الشخصية**
🆔 **ايديك:** {user_id}
📅 **تاريخ الانضمام:** {datetime.fromisoformat(stats['joined_date']).strftime('%Y-%m-%d')}
🔄 **إجمالي العمليات:** {stats['total_operations']}
✅ **العمليات الناجحة:** {stats['successful_operations']}
❌ **العمليات الفاشلة:** {stats['failed_operations']}
📈 **نسبة النجاح:** {success_rate:.1f}%
🤖 **القبول التلقائي:** {accept_status}
💎 **حالة الاشتراك:** {sub_info}
♥ صلي علي النبي محمد ﷺ
    """
    main_bot.send_message(chat_id, stats_text, parse_mode="Markdown")

@main_bot.message_handler(commands=['cancel'])
def main_cancel_handler(message):
    cancel_process(message.chat.id, message.from_user.id)

@main_bot.message_handler(commands=['dev'])
def main_dev_handler(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👨‍💻 التواصل مع المطور", url=f"https://t.me/{DEV_USERNAME.replace('@', '')}"))
    main_bot.send_message(message.chat.id, f"👨‍💻 **معلومات المطور**\n\n👤 **الاسم:** {DEV_NAME}\n📱 **Telegram:** {DEV_USERNAME_MD}\n\n📱 **فودافون كاش:** `{VODAFONE_CASH_NUMBER}`", reply_markup=markup, parse_mode="Markdown")

def main_check_pending_invites_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    access, msg = check_main_bot_access(user_id)
    if not access:
        main_bot.send_message(chat_id, msg, parse_mode="Markdown")
        return
    cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel_markup.add(types.KeyboardButton("❌ إلغاء العملية"))
    main_bot.send_message(chat_id, "📱 أدخل رقم الأونر:", reply_markup=cancel_markup)
    main_bot.register_next_step_handler(message, handle_pending_owner_number)

def handle_pending_owner_number(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.text in ("/cancel", "❌ إلغاء العملية"):
        cancel_process(chat_id, user_id)
        return
    owner_number = message.text.strip()
    cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel_markup.add(types.KeyboardButton("❌ إلغاء العملية"))
    main_bot.send_message(chat_id, "🔒 أدخل باسورد الأونر:", reply_markup=cancel_markup)
    main_bot.register_next_step_handler(message, handle_pending_owner_password, owner_number)

def handle_pending_owner_password(message, owner_number):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.text in ("/cancel", "❌ إلغاء العملية"):
        cancel_process(chat_id, user_id)
        return
    owner_password = message.text.strip()
    main_bot.send_message(chat_id, "⏳ جاري جلب الدعوات المعلقة...", reply_markup=types.ReplyKeyboardRemove())
    try:
        token, _ = login(owner_number, owner_password)
        family_data = get_family_info(token, owner_number)
        pending_invites = parse_pending_invitations(family_data)
        if pending_invites:
            show_pending_invitations_ui(chat_id, owner_number, pending_invites)
        else:
            main_bot.send_message(chat_id, "✅ **لا توجد دعوات معلقة نشطة!**\n\n♥ صلي علي النبي محمد ﷺ", parse_mode="Markdown")
    except Exception as e:
        main_bot.send_message(chat_id, f"❌ **خطأ:** {str(e)[:100]}\n\n♥ صلي علي النبي محمد ﷺ", parse_mode="Markdown")

@main_bot.message_handler(func=lambda message: message.chat.id in PAYMENT_STATE, content_types=['text', 'photo', 'document'])
def handle_payment_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.text in ("/cancel", "❌ إلغاء العملية"):
        cancel_process(chat_id, user_id)
        return
    state = PAYMENT_STATE.get(chat_id)
    if not state:
        return
    step = state.get('step')
    plan_id = state.get('plan_id')
    if step == 'waiting_transfer_number':
        if not message.text:
            main_bot.send_message(chat_id, "❌ من فضلك ابعت رقم التحويل كتابةً (نص)، مش صورة.")
            return
        transfer_number = message.text.strip()
        request_receipt_photo(chat_id, plan_id, transfer_number)
    elif step == 'waiting_receipt':
        transfer_number = state.get('transfer_number')
        file_id = None
        file_type = 'photo'
        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = 'photo'
        elif message.document:
            file_id = message.document.file_id
            file_type = 'document'
        else:
            main_bot.send_message(chat_id, "❌ من فضلك ابعت صورة إيصال التحويل (مش نص).")
            return
        if send_subscription_request_to_admin(user_id, plan_id, transfer_number, file_id, file_type):
            main_bot.send_message(chat_id, "✅ تم إرسال طلبك للمراجعة!\n\nسيتم التواصل معك خلال دقائق.\n🕌 صلي علي النبي محمد ﷺ", reply_markup=types.ReplyKeyboardRemove())
        else:
            main_bot.send_message(chat_id, "❌ فشل إرسال الطلب. تواصل مع @DM_ZO مباشرة.")
        if chat_id in PAYMENT_STATE:
            del PAYMENT_STATE[chat_id]

# ====================================================================
# 10. بوت الأدمن
# ====================================================================
def admin_only(func):
    def wrapper(message):
        if message.from_user.id != OWNER_ID:
            admin_bot.send_message(message.chat.id, "❌ هذه الخاصية للمطور فقط.")
            return
        return func(message)
    return wrapper

@admin_bot.message_handler(commands=['start'])
@admin_only
def admin_start_handler(message):
    chat_id = message.chat.id
    free_status = "🟢 مجاني للكل" if is_free_mode() else "🔴 مدفوع (لازم اشتراك)"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📊 إحصائيات"),
        types.KeyboardButton("👥 عرض المستخدمين"),
        types.KeyboardButton("➕ إضافة مستخدم"),
        types.KeyboardButton("🚫 حظر مستخدم"),
        types.KeyboardButton("✅ إلغاء حظر مستخدم"),
        types.KeyboardButton("⏸️ إيقاف البوت"),
        types.KeyboardButton("▶️ تشغيل البوت"),
        types.KeyboardButton("💾 حفظ البيانات"),
        types.KeyboardButton("📥 تفاصيل الاشتراكات"),
        types.KeyboardButton("💰 تغيير رقم فون كاش"),
        types.KeyboardButton("💵 تغيير سعر الاشتراك"),
        types.KeyboardButton("🕐 فتح مجاني لمدة (ساعات)"),
        types.KeyboardButton("📢 إرسال إشعار"),
        types.KeyboardButton("🔄 استرداد البيانات"),
        types.KeyboardButton("✅ طلبات الموافقة"),
        types.KeyboardButton("🆓 فتح مجاني للكل"),
        types.KeyboardButton("🔒 قفل (لازم اشتراك)")
    )
    admin_bot.send_message(
        chat_id,
        f"🎛️ **لوحة تحكم المطور**\n\n👤 مرحباً {DEV_NAME}\n🆔 ايديك: {OWNER_ID}\n\n💰 **حالة الدفع:** {free_status}\n\n🕌 صلي علي النبي محمد ﷺ",
        reply_markup=markup, parse_mode="Markdown"
    )

@admin_bot.message_handler(func=lambda message: message.text == "📊 إحصائيات")
@admin_only
def admin_stats_handler(message):
    stats = get_admin_stats()
    total_failed = stats['total_operations'] - stats['successful_operations']
    success_rate = 0
    if stats['total_operations'] > 0:
        success_rate = (stats['successful_operations'] / stats['total_operations']) * 100
    plan_stats_text = ""
    for plan_id, count in stats['plan_stats'].items():
        plan_name = SUBSCRIPTION_PLANS.get(plan_id, {}).get('label', plan_id)
        plan_stats_text += f"   • {plan_name}: {count} مستخدم\n"
    free_status = "🆓 مجاني للكل" if stats['free_mode'] else "🔒 مدفوع"
    stats_text = f"""
📊 **إحصائيات عامة**
💰 **وضع الاشتراك:** {free_status}
👥 **المستخدمين:**
   • إجمالي: {stats['total_users']}
   • المشتركين: {stats['subscribed_users']}
   • المحظورين: {stats['banned_users']}
   • النجوم النشطة: {stats['total_stars']}
   • العمليات النشطة: {stats['active_operations']}
   • طلبات انتظار: {stats['pending_requests']}
🔄 **العمليات:**
   • إجمالي: {stats['total_operations']}
   • ناجحة: {stats['successful_operations']}
   • فاشلة: {total_failed}
   • نسبة النجاح: {success_rate:.1f}%
💰 **الاشتراكات النشطة:**
{plan_stats_text}
⚙️ **حالة البوت:** {'🟢 يعمل' if stats['bot_status'] == 'running' else '🔴 متوقف'}
♥ صلي علي النبي محمد ﷺ
    """
    admin_bot.send_message(message.chat.id, stats_text, parse_mode="Markdown")

@admin_bot.message_handler(func=lambda message: message.text == "💵 تغيير سعر الاشتراك")
@admin_only
def admin_change_price_handler(message):
    current_price = SUBSCRIPTION_PLANS["30d"]["price"]
    admin_bot.send_message(
        message.chat.id,
        f"💵 السعر الحالي للاشتراك الشهري: **{current_price} جنيه**\n\nأرسل السعر الجديد (رقم فقط):",
        parse_mode="Markdown"
    )
    admin_bot.register_next_step_handler(message, process_change_price)

def process_change_price(message):
    try:
        new_price = int(message.text.strip())
        if new_price <= 0:
            admin_bot.send_message(message.chat.id, "❌ السعر يجب أن يكون أكبر من صفر.")
            return
        SUBSCRIPTION_PLANS["30d"]["price"] = new_price
        SUBSCRIPTION_PLANS["30d"]["label"] = f"💎 اشتراك شهري - {new_price} جنيه"
        SETTINGS["monthly_price"] = new_price
        save_all_data()
        admin_bot.send_message(
            message.chat.id,
            f"✅ **تم تغيير سعر الاشتراك الشهري إلى {new_price} جنيه**\n\n♥ صلي علي النبي محمد ﷺ",
            parse_mode="Markdown"
        )
    except ValueError:
        admin_bot.send_message(message.chat.id, "❌ سعر غير صالح، أرسل رقم فقط.")

@admin_bot.message_handler(func=lambda message: message.text == "🕐 فتح مجاني لمدة (ساعات)")
@admin_only
def admin_free_hours_handler(message):
    admin_bot.send_message(
        message.chat.id,
        "🕐 كام ساعة عايز تفتح البوت مجاني؟\n\nأرسل رقم الساعات (ممكن تكون كسور زي 0.5):",
        parse_mode="Markdown"
    )
    admin_bot.register_next_step_handler(message, process_free_hours)

def process_free_hours(message):
    try:
        hours = float(message.text.strip())
        if hours <= 0:
            admin_bot.send_message(message.chat.id, "❌ عدد الساعات يجب أن يكون أكبر من صفر.")
            return
    except ValueError:
        admin_bot.send_message(message.chat.id, "❌ عدد غير صالح، أرسل رقم فقط.")
        return

    until = get_egypt_time() + timedelta(hours=hours)
    SETTINGS["free_mode"] = True
    SETTINGS["free_mode_until"] = until.isoformat()
    save_all_data()

    hours_display = int(hours) if hours == int(hours) else hours

    admin_bot.send_message(
        message.chat.id,
        f"✅ **تم فتح البوت مجاناً لمدة {hours_display} ساعة**\n\n⏰ هيتقفل تلقائياً في: {until.strftime('%Y-%m-%d %I:%M %p')}\n\n🕌 صلي علي النبي محمد ﷺ",
        parse_mode="Markdown"
    )

    Thread(target=broadcast_free_mode_notice, args=(hours_display,)).start()

def broadcast_free_mode_notice(hours_display):
    """إشعار كل المستخدمين إن البوت بقى مجاني مؤقتاً"""
    all_users = list(USERS_STATS.keys())
    text = (
        f"🎉 البوت متاح مجاناً الآن لمدة {hours_display} ساعة!\n\n"
        f"استخدموا كل الخدمات من غير اشتراك 🚀\n\n"
        f"🕌 صلوا على النبي محمد ﷺ"
    )
    sent = 0
    failed = 0
    for user_id_str in all_users:
        user_id = int(user_id_str)
        if user_id == OWNER_ID:
            continue
        try:
            main_bot.send_message(user_id, text)
            sent += 1
            time.sleep(0.1)
        except:
            failed += 1
    try:
        admin_bot.send_message(ADMIN_ID, f"📢 إشعار الوضع المجاني اتبعت لـ {sent} مستخدم (فشل: {failed})", parse_mode="Markdown")
    except:
        pass

@admin_bot.message_handler(func=lambda message: message.text == "🆓 فتح مجاني للكل")
@admin_only
def admin_enable_free_mode(message):
    SETTINGS["free_mode"] = True
    SETTINGS["free_mode_until"] = None
    save_all_data()
    admin_bot.send_message(
        message.chat.id,
        "✅ **تم فتح الخدمة مجاناً للجميع!**\n\n🆓 الآن أي مستخدم يقدر يستخدم البوت بدون اشتراك.\n\n🕌 صلي علي النبي محمد ﷺ",
        parse_mode="Markdown"
    )

@admin_bot.message_handler(func=lambda message: message.text == "🔒 قفل (لازم اشتراك)")
@admin_only
def admin_disable_free_mode(message):
    SETTINGS["free_mode"] = False
    SETTINGS["free_mode_until"] = None
    save_all_data()
    admin_bot.send_message(
        message.chat.id,
        "🔒 **تم قفل الخدمة - لازم اشتراك مدفوع!**\n\nالمستخدمين غير المشتركين لن يتمكنوا من الاستخدام.\n\n🕌 صلي علي النبي محمد ﷺ",
        parse_mode="Markdown"
    )

@admin_bot.message_handler(func=lambda message: message.text == "👥 عرض المستخدمين")
@admin_only
def admin_users_handler(message):
    if not USERS_STATS:
        admin_bot.send_message(message.chat.id, "📭 لا يوجد مستخدمون حتى الآن.")
        return
    users_text = "👥 **قائمة المستخدمين:**\n\n"
    for user_id_str, stats in sorted(USERS_STATS.items(), key=lambda x: x[1].get('total_operations', 0), reverse=True)[:20]:
        user_id = int(user_id_str)
        try:
            user_info = admin_bot.get_chat(user_id)
            username = f"@{user_info.username}" if user_info.username else "لا يوجد"
            name = user_info.first_name or "غير معروف"
            sub_status = "✅" if check_subscription_valid(user_id) else "❌"
            users_text += f"👤 **{name}**\n   🆔 `{user_id}`\n   📱 {username}\n   💎 {sub_status}\n   🔄 {stats.get('total_operations', 0)} عملية (✅ {stats.get('successful_operations', 0)})\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        except:
            users_text += f"👤 مستخدم `{user_id_str}` - {stats.get('total_operations', 0)} عملية\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    users_text += f"\n📊 إجمالي: {len(USERS_STATS)}"
    admin_bot.send_message(message.chat.id, users_text, parse_mode="Markdown")

@admin_bot.message_handler(func=lambda message: message.text == "➕ إضافة مستخدم")
@admin_only
def admin_add_user_handler(message):
    admin_bot.send_message(message.chat.id, "🔢 أرسل ايدي المستخدم:", parse_mode="Markdown")
    admin_bot.register_next_step_handler(message, process_add_user_id)

def process_add_user_id(message):
    try:
        user_id = int(message.text.strip())
        admin_bot.send_message(message.chat.id, "📅 كم يوم؟ (أرسل 0 للاشتراك بالنجوم)", parse_mode="Markdown")
        admin_bot.register_next_step_handler(message, process_add_user_days, user_id)
    except ValueError:
        admin_bot.send_message(message.chat.id, "❌ ايدي غير صالح.")

def process_add_user_days(message, user_id):
    try:
        days = int(message.text.strip())
        if days < 0:
            admin_bot.send_message(message.chat.id, "❌ عدد الأيام يجب أن يكون 0 أو أكثر.")
            return
        if days == 0:
            admin_bot.send_message(message.chat.id, "⭐ أرسل عدد النجوم:", parse_mode="Markdown")
            admin_bot.register_next_step_handler(message, process_add_user_stars, user_id)
        else:
            expiry_date = get_egypt_time() + timedelta(days=days)
            SUBSCRIPTIONS[str(user_id)] = {
                'start_date': get_egypt_time().isoformat(), 'expiry_date': expiry_date.isoformat(),
                'days_added': days, 'type': 'normal', 'status': 'active', 'plan': 'manual'
            }
            save_all_data()
            remaining = format_expiry_time(expiry_date)
            admin_bot.send_message(message.chat.id, f"✅ تم إضافة المستخدم `{user_id}` - {days} يوم\nينتهي: {remaining}", parse_mode="Markdown")
            try:
                main_bot.send_message(user_id, f"✅ تم تفعيل اشتراكك!\n📅 المدة: {days} يوم\n⏰ ينتهي: {remaining}\n🕌 صلي علي النبي محمد ﷺ")
            except:
                pass
    except ValueError:
        admin_bot.send_message(message.chat.id, "❌ عدد الأيام غير صالح.")

def process_add_user_stars(message, user_id):
    try:
        stars = int(message.text.strip())
        if stars <= 0:
            admin_bot.send_message(message.chat.id, "❌ عدد النجوم يجب أن يكون أكبر من صفر.")
            return
        SUBSCRIPTIONS[str(user_id)] = {
            'plan': 'stars', 
            'stars': stars, 
            'start_date': get_egypt_time().isoformat(),
            'expiry_date': None, 
            'status': 'active', 
            'transaction_number': 'مدير (نجوم)'
        }
        save_all_data()
        admin_bot.send_message(message.chat.id, f"✅ تم إضافة {stars} نجمة للمستخدم `{user_id}`", parse_mode="Markdown")
        try:
            main_bot.send_message(user_id, f"✅ تم تفعيل اشتراكك بالنجوم!\n⭐ عدد النجوم: {stars}\n🕌 صلي علي النبي محمد ﷺ")
        except:
            pass
    except ValueError:
        admin_bot.send_message(message.chat.id, "❌ عدد النجوم غير صالح.")

@admin_bot.message_handler(func=lambda message: message.text == "🚫 حظر مستخدم")
@admin_only
def admin_ban_user_handler(message):
    admin_bot.send_message(message.chat.id, "🔢 أرسل ايدي المستخدم:")
    admin_bot.register_next_step_handler(message, process_ban_user)

def process_ban_user(message):
    try:
        user_id = int(message.text.strip())
        remove_subscription(user_id)
        ban_user(user_id, "حظر يدوي من الأدمن")
        admin_bot.send_message(message.chat.id, f"✅ تم حظر المستخدم `{user_id}`", parse_mode="Markdown")
        try:
            main_bot.send_message(user_id, f"⛔ تم حظر حسابك. للتواصل: {DEV_USERNAME}")
        except:
            pass
    except ValueError:
        admin_bot.send_message(message.chat.id, "❌ ايدي غير صالح.")

@admin_bot.message_handler(func=lambda message: message.text == "✅ إلغاء حظر مستخدم")
@admin_only
def admin_unban_user_handler(message):
    admin_bot.send_message(message.chat.id, "🔢 أرسل ايدي المستخدم:")
    admin_bot.register_next_step_handler(message, process_unban_user)

def process_unban_user(message):
    try:
        user_id = int(message.text.strip())
        if unban_user(user_id):
            admin_bot.send_message(message.chat.id, f"✅ تم إلغاء حظر المستخدم `{user_id}`", parse_mode="Markdown")
        else:
            admin_bot.send_message(message.chat.id, f"❌ المستخدم `{user_id}` غير موجود في المحظورين.", parse_mode="Markdown")
    except ValueError:
        admin_bot.send_message(message.chat.id, "❌ ايدي غير صالح.")

@admin_bot.message_handler(func=lambda message: message.text == "⏸️ إيقاف البوت")
@admin_only
def admin_stop_bot_handler(message):
    global MAIN_BOT_STATUS
    MAIN_BOT_STATUS = "stopped"
    for user_id in list(ACTIVE_OPERATIONS.keys()):
        stop_all_operations(user_id)
    admin_bot.send_message(message.chat.id, "⏸️ تم إيقاف البوت.\n🕌 صلي علي النبي محمد ﷺ", parse_mode="Markdown")

@admin_bot.message_handler(func=lambda message: message.text == "▶️ تشغيل البوت")
@admin_only
def admin_start_bot_handler(message):
    global MAIN_BOT_STATUS
    MAIN_BOT_STATUS = "running"
    admin_bot.send_message(message.chat.id, "▶️ تم تشغيل البوت بنجاح.\n🕌 صلي علي النبي محمد ﷺ", parse_mode="Markdown")

@admin_bot.message_handler(func=lambda message: message.text == "💾 حفظ البيانات")
@admin_only
def admin_save_data_handler(message):
    try:
        save_all_data()
        admin_bot.send_message(message.chat.id, "✅ تم حفظ جميع البيانات بنجاح", parse_mode="Markdown")
    except Exception as e:
        admin_bot.send_message(message.chat.id, f"❌ خطأ في الحفظ: {e}", parse_mode="Markdown")

@admin_bot.message_handler(func=lambda message: message.text == "📥 تفاصيل الاشتراكات")
@admin_only
def admin_subscriptions_handler(message):
    if not SUBSCRIPTIONS:
        admin_bot.send_message(message.chat.id, "📭 لا يوجد مشتركون.")
        return
    subs_text = "📥 **تفاصيل الاشتراكات:**\n\n"
    for user_id_str, sub_data in SUBSCRIPTIONS.items():
        user_id = int(user_id_str)
        try:
            user_info = admin_bot.get_chat(user_id)
            name = user_info.first_name or "غير معروف"
        except:
            name = "غير معروف"
        subs_text += f"👤 **{name}** `{user_id}`\n"
        if sub_data.get('plan') == 'stars':
            subs_text += f"   ⭐ نجوم: {sub_data.get('stars', 0)}\n"
        else:
            expiry = datetime.fromisoformat(sub_data['expiry_date'])
            subs_text += f"   ⏰ متبقي: {format_expiry_time(expiry)}\n"
        subs_text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    admin_bot.send_message(message.chat.id, subs_text, parse_mode="Markdown")

@admin_bot.message_handler(func=lambda message: message.text == "💰 تغيير رقم فون كاش")
@admin_only
def admin_change_cash_handler(message):
    global VODAFONE_CASH_NUMBER
    admin_bot.send_message(message.chat.id, f"💰 الرقم الحالي: `{VODAFONE_CASH_NUMBER}`\n\nأرسل الرقم الجديد:", parse_mode="Markdown")
    admin_bot.register_next_step_handler(message, process_change_cash)

def process_change_cash(message):
    global VODAFONE_CASH_NUMBER
    new_number = message.text.strip()
    if new_number.isdigit() and len(new_number) == 11:
        VODAFONE_CASH_NUMBER = new_number
        admin_bot.send_message(message.chat.id, f"✅ تم التغيير: `{VODAFONE_CASH_NUMBER}`", parse_mode="Markdown")
    else:
        admin_bot.send_message(message.chat.id, "❌ رقم غير صالح (يجب 11 رقم).", parse_mode="Markdown")

@admin_bot.message_handler(func=lambda message: message.text == "📢 إرسال إشعار")
@admin_only
def admin_broadcast_handler(message):
    admin_bot.send_message(message.chat.id, "📝 أرسل الرسالة التي تريد إرسالها (نص أو صورة بكابشن):")
    admin_bot.register_next_step_handler(message, process_broadcast)

def process_broadcast(message):
    is_photo = bool(message.photo)
    raw_text = (message.caption if is_photo else message.text) or ""
    full_text = f"📢 إشعار من المسؤول:\n\n{raw_text}\n\n🕌 صلي علي النبي محمد ﷺ"

    photo_bytes = None
    if is_photo:
        try:
            file_info = admin_bot.get_file(message.photo[-1].file_id)
            photo_bytes = admin_bot.download_file(file_info.file_path)
        except Exception as e:
            admin_bot.send_message(message.chat.id, f"❌ فشل تحميل الصورة: {e}")
            return

    sent_count = 0
    failed_count = 0
    all_users = list(USERS_STATS.keys())
    admin_bot.send_message(message.chat.id, f"⏳ جاري الإرسال لـ {len(all_users)} مستخدم...")
    for user_id_str in all_users:
        user_id = int(user_id_str)
        if user_id == OWNER_ID:
            continue
        try:
            if is_photo:
                # لازم نبعت البايتس مش الـ file_id، لأنه غير صالح بين بوتين مختلفين
                main_bot.send_photo(user_id, io.BytesIO(photo_bytes), caption=full_text)
            else:
                main_bot.send_message(user_id, full_text)
            sent_count += 1
            time.sleep(0.1)
        except Exception as e:
            print(f"❌ فشل الإرسال لـ {user_id}: {e}")
            failed_count += 1
    admin_bot.send_message(message.chat.id, f"✅ تم الإرسال: {sent_count}\n❌ فشل: {failed_count}", parse_mode="Markdown")

@admin_bot.message_handler(func=lambda message: message.text == "🔄 استرداد البيانات")
@admin_only
def admin_restore_handler(message):
    try:
        load_all_data()
        admin_bot.send_message(message.chat.id, "✅ تم استرداد البيانات بنجاح", parse_mode="Markdown")
    except Exception as e:
        admin_bot.send_message(message.chat.id, f"❌ خطأ: {e}", parse_mode="Markdown")

@admin_bot.message_handler(func=lambda message: message.text == "✅ طلبات الموافقة")
@admin_only
def admin_pending_requests_handler(message):
    if not PENDING_SUBSCRIPTIONS:
        admin_bot.send_message(message.chat.id, "✅ لا توجد طلبات انتظار.")
        return
    for user_id_str, sub_data in PENDING_SUBSCRIPTIONS.items():
        plan_label = SUBSCRIPTION_PLANS[sub_data["plan"]]["label"]
        admin_bot.send_message(
            message.chat.id,
            f"💰 طلب اشتراك:\n🆔 {user_id_str}\n👤 {sub_data['user_name']}\n📦 {plan_label}\n💰 {sub_data['price']} جنيه\n🔢 رقم التحويل: {sub_data['payment_number']}"
        )

# ====================================================================
# 11. معالجات الأزرار (Callbacks)
# ====================================================================
@main_bot.callback_query_handler(func=lambda call: call.data.startswith('change_quota_'))
def handle_quota_change_callback(call):
    rest = call.data[len("change_quota_"):]
    new_quota_str, user_id_str, operation_id = rest.split('_', 2)
    new_quota = int(new_quota_str)
    user_id = int(user_id_str)
    chat_id = call.message.chat.id

    if call.from_user.id != user_id:
        main_bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية", show_alert=True)
        return

    if user_id not in ACTIVE_OPERATIONS or operation_id not in ACTIVE_OPERATIONS[user_id]:
        main_bot.answer_callback_query(call.id, "❌ العملية انتهت", show_alert=True)
        return

    op_data = ACTIVE_OPERATIONS[user_id][operation_id]
    pending_data = op_data.get('pending_quota_data', {})
    
    owner = op_data['family_data']['owner_number']
    member = pending_data.get('member', op_data['family_data']['member_number'])
    token_owner = pending_data.get('token_owner')

    main_bot.answer_callback_query(call.id, "⏳ جاري تنفيذ التغيير...")
    main_bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"⏳ **جاري تغيير النسبة إلى {new_quota}...**\n\n♥ صلي علي النبي محمد ﷺ"
    )

    Thread(
        target=execute_quota_change,
        args=(user_id, operation_id, chat_id, new_quota, owner, token_owner, member)
    ).start()

@main_bot.callback_query_handler(func=lambda call: call.data.startswith('skip_quota_'))
def handle_skip_quota_callback(call):
    rest = call.data[len("skip_quota_"):]
    user_id_str, operation_id = rest.split('_', 1)
    user_id = int(user_id_str)
    chat_id = call.message.chat.id

    if call.from_user.id != user_id:
        main_bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية", show_alert=True)
        return

    if user_id not in ACTIVE_OPERATIONS or operation_id not in ACTIVE_OPERATIONS[user_id]:
        main_bot.answer_callback_query(call.id, "❌ العملية انتهت", show_alert=True)
        return

    main_bot.answer_callback_query(call.id, "✅ تم")
    main_bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"✅ **تم تخطي تغيير النسبة**\n\n♥ صلي علي النبي محمد ﷺ"
    )

    op_data = ACTIVE_OPERATIONS[user_id][operation_id]
    pending_data = op_data.get('pending_quota_data', {})
    owner = op_data['family_data']['owner_number']
    member = pending_data.get('member', op_data['family_data']['member_number'])
    token_owner = pending_data.get('token_owner')

    update_user_stats(user_id, operation_success=True)
    offer_cancel_last_invitation(chat_id, user_id, operation_id, owner, token_owner, member)

@main_bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_last_yes_'))
def handle_cancel_last_yes_callback(call):
    rest = call.data[len("cancel_last_yes_"):]
    user_id_str, operation_id = rest.split('_', 1)
    user_id = int(user_id_str)
    chat_id = call.message.chat.id

    if call.from_user.id != user_id:
        main_bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية", show_alert=True)
        return

    if user_id not in ACTIVE_OPERATIONS or operation_id not in ACTIVE_OPERATIONS[user_id]:
        main_bot.answer_callback_query(call.id, "❌ العملية انتهت", show_alert=True)
        return

    op_data = ACTIVE_OPERATIONS[user_id][operation_id]
    pending_data = op_data.get('pending_cancel_data', {})
    owner = pending_data.get('owner')
    token_owner = pending_data.get('token_owner')
    member = pending_data.get('member')

    main_bot.answer_callback_query(call.id, "⏳ هيتم الإلغاء بعد تجديد الساعة")
    main_bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text="⏳ **تمام، هيتم إلغاء الدعوة المعلقة تلقائياً بعد ما الساعة الحالية تتجدد + دقيقتين أمان.**\n\nهابعتلك تأكيد لما يخلص.\n♥ صلي علي النبي محمد ﷺ"
    )

    Thread(
        target=schedule_cancel_last_invitation,
        args=(user_id, operation_id, chat_id, owner, token_owner, member)
    ).start()

@main_bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_last_no_'))
def handle_cancel_last_no_callback(call):
    rest = call.data[len("cancel_last_no_"):]
    user_id_str, operation_id = rest.split('_', 1)
    user_id = int(user_id_str)
    chat_id = call.message.chat.id

    if call.from_user.id != user_id:
        main_bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية", show_alert=True)
        return

    main_bot.answer_callback_query(call.id, "✅ تم")
    main_bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text="✅ **تمام، هنسيب الدعوة زي ما هي.**\n\n♥ صلي علي النبي محمد ﷺ"
    )

    if user_id in ACTIVE_OPERATIONS and operation_id in ACTIVE_OPERATIONS[user_id]:
        ACTIVE_OPERATIONS[user_id].pop(operation_id, None)

@main_bot.callback_query_handler(func=lambda call: call.data.startswith('accept_pending_'))
def handle_accept_pending_callback(call):
    rest = call.data[len("accept_pending_"):]
    parts = rest.split('_', 1)
    owner = parts[0]
    member = parts[1]
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    # طلب باسورد الفرد
    main_bot.answer_callback_query(call.id, "⏳ جاري طلب بيانات الفرد...")
    main_bot.send_message(
        chat_id,
        f"🔑 **أدخل باسورد الفرد {member} للقبول:**",
        parse_mode="Markdown"
    )
    main_bot.register_next_step_handler(
        call.message,
        handle_pending_accept_member_password,
        owner, member
    )

def handle_pending_accept_member_password(message, owner, member):
    chat_id = message.chat.id
    user_id = message.from_user.id
    member_password = message.text.strip()
    
    main_bot.send_message(chat_id, "⏳ **جاري قبول الدعوة...**", parse_mode="Markdown")
    try:
        token_owner, _ = login(owner, member_password)
    except:
        main_bot.send_message(chat_id, "❌ **فشل تسجيل الدخول للفرد**", parse_mode="Markdown")
        return
    
    accept_ok = accept_invitation_sync(owner, member, token_owner)
    if accept_ok:
        main_bot.send_message(chat_id, f"✅ **تم قبول الدعوة بنجاح!**\n\n👤 {owner}\n👥 {member}\n\n♥ صلي علي النبي محمد ﷺ", parse_mode="Markdown")
    else:
        main_bot.send_message(chat_id, f"❌ **فشل قبول الدعوة**\n\nحاول من التطبيق مباشرة.\n♥ صلي علي النبي محمد ﷺ", parse_mode="Markdown")

@main_bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_pending_'))
def handle_cancel_pending_callback(call):
    rest = call.data[len("cancel_pending_"):]
    parts = rest.split('_', 1)
    owner = parts[0]
    member = parts[1]
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    main_bot.answer_callback_query(call.id, "⏳ جاري طلب البيانات...")
    main_bot.send_message(
        chat_id,
        f"🔒 **أدخل باسورد الأونر {owner} لحذف الدعوة:**",
        parse_mode="Markdown"
    )
    main_bot.register_next_step_handler(
        call.message,
        handle_pending_cancel_owner_password,
        owner, member
    )

def handle_pending_cancel_owner_password(message, owner, member):
    chat_id = message.chat.id
    user_id = message.from_user.id
    owner_password = message.text.strip()
    
    main_bot.send_message(chat_id, "⏳ **جاري حذف الدعوة...**", parse_mode="Markdown")
    try:
        token_owner, _ = login(owner, owner_password)
    except:
        main_bot.send_message(chat_id, "❌ **فشل تسجيل الدخول للأونر**", parse_mode="Markdown")
        return
    
    cancel_ok, tried_codes = remove_member_sync(owner, member, token_owner)
    if cancel_ok:
        main_bot.send_message(chat_id, f"✅ **تم حذف الدعوة بنجاح!**\n\n👤 {owner}\n👥 {member}\n\n♥ صلي علي النبي محمد ﷺ", parse_mode="Markdown")
    else:
        codes_str = ",".join(str(c) for c in tried_codes)
        main_bot.send_message(chat_id, f"❌ **فشل حذف الدعوة**\n\nالمحاولات: {codes_str}\n\nحاول من التطبيق مباشرة.\n♥ صلي علي النبي محمد ﷺ", parse_mode="Markdown")

@main_bot.callback_query_handler(func=lambda call: True)
def main_callback_handler(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    data = call.data
    try:
        if data == "check_subscription":
            not_subscribed = check_subscription(user_id, main_bot)
            if not_subscribed:
                main_bot.answer_callback_query(call.id, "❌ لم تشترك في جميع القنوات بعد!", show_alert=True)
            else:
                main_bot.answer_callback_query(call.id, "✅ شكراً لاشتراكك!", show_alert=True)
                main_bot.delete_message(chat_id, call.message.message_id)
            return
        if data == "check_subscription_status":
            main_bot.delete_message(chat_id, call.message.message_id)
            main_bot.send_message(chat_id, f"📊 حالة اشتراكك:\n\n{get_subscription_info(user_id)}")
            main_bot.answer_callback_query(call.id)
            return
        if data == "cancel_process":
            main_bot.delete_message(chat_id, call.message.message_id)
            cancel_process(chat_id, user_id)
            main_bot.answer_callback_query(call.id, "✅ تم الإلغاء")
            return
        if data == "back_to_subscribe":
            main_bot.delete_message(chat_id, call.message.message_id)
            show_subscription_menu(chat_id, user_id)
            main_bot.answer_callback_query(call.id)
            return
        if data.startswith("subscribe_"):
            plan_id = data.split("_")[1]
            if plan_id in SUBSCRIPTION_PLANS:
                main_bot.delete_message(chat_id, call.message.message_id)
                show_payment_instructions(chat_id, plan_id)
                main_bot.answer_callback_query(call.id)
            return
        if data.startswith("start_payment_"):
            plan_id = data.split("_")[2]
            if plan_id in SUBSCRIPTION_PLANS:
                main_bot.delete_message(chat_id, call.message.message_id)
                start_payment_process(chat_id, plan_id)
                main_bot.answer_callback_query(call.id)
            return
        if data.startswith("stop_op_"):
            operation_number = int(data.split("_")[2])
            if stop_operation(user_id, operation_number):
                main_bot.answer_callback_query(call.id, "✅ تم إلغاء العملية")
            else:
                main_bot.answer_callback_query(call.id, "❌ لم يتم العثور على العملية")
            return
    except Exception as e:
        print(f"❌ خطأ في callback: {e}")
        main_bot.answer_callback_query(call.id, "❌ حدث خطأ")

@admin_bot.callback_query_handler(func=lambda call: True)
def admin_callback_handler(call):
    data = call.data
    try:
        if call.from_user.id != ADMIN_ID:
            admin_bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية.")
            return
        if data.startswith("approve_sub_"):
            target_user_id = int(data.split("_")[2])
            handle_subscription_approval(call, target_user_id)
        elif data.startswith("reject_sub_"):
            target_user_id = int(data.split("_")[2])
            handle_subscription_rejection(call, target_user_id)
    except Exception as e:
        print(f"❌ خطأ في admin callback: {e}")
        admin_bot.answer_callback_query(call.id, "❌ حدث خطأ")

# ====================================================================
# 12. فحص انتهاء الاشتراكات والوضع المجاني المؤقت وتشغيل البوتات
# ====================================================================
def check_expiry_loop():
    while True:
        try:
            now = get_egypt_time()
            for user_id_str, sub in list(SUBSCRIPTIONS.items()):
                if sub.get("status") == "active":
                    if sub.get("plan") == "stars":
                        if sub.get("stars", 0) == 0:
                            sub["status"] = "expired"
                        continue
                    expiry_date_str = sub.get('expiry_date')
                    if not expiry_date_str:
                        continue
                    expiry_date = datetime.fromisoformat(expiry_date_str)
                    if now > expiry_date:
                        sub["status"] = "expired"
                        user_id_int = int(user_id_str)
                        if user_id_int in ACTIVE_OPERATIONS:
                            for op_data in list(ACTIVE_OPERATIONS[user_id_int].values()):
                                if 'stop_event' in op_data:
                                    op_data['stop_event'].set()
                            ACTIVE_OPERATIONS[user_id_int] = {}
            save_all_data()
            time.sleep(3600)
        except Exception as e:
            print(f"❌ خطأ في فحص الاشتراكات: {e}")
            time.sleep(300)

def check_free_mode_loop():
    """يفحص كل دقيقة لو مدة الفتح المجاني المؤقت خلصت، ويقفل الوضع المجاني تلقائياً"""
    while True:
        try:
            if SETTINGS.get("free_mode") and SETTINGS.get("free_mode_until"):
                free_until = datetime.fromisoformat(SETTINGS["free_mode_until"])
                if get_egypt_time() >= free_until:
                    SETTINGS["free_mode"] = False
                    SETTINGS["free_mode_until"] = None
                    save_all_data()
                    try:
                        admin_bot.send_message(
                            ADMIN_ID,
                            "⏰ **انتهت مدة الفتح المجاني - رجع البوت مدفوع تلقائياً.**\n\n🕌 صلي علي النبي محمد ﷺ",
                            parse_mode="Markdown"
                        )
                    except:
                        pass
            time.sleep(60)
        except Exception as e:
            print(f"❌ خطأ في فحص الوضع المجاني: {e}")
            time.sleep(60)

def run_main_bot():
    while True:
        try:
            print("🔄 تشغيل البوت الرئيسي...")
            main_bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ خطأ في البوت الرئيسي: {e}")
            time.sleep(5)

def run_admin_bot():
    while True:
        try:
            print("🔄 تشغيل بوت الأدمن...")
            admin_bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ خطأ في بوت الأدمن: {e}")
            time.sleep(5)

def main():
    print("🚀 جاري تشغيل نظام البوتات...")
    load_all_data()
    print("✅ تم تحميل جميع البيانات")
    threading.Thread(target=check_expiry_loop, daemon=True).start()
    threading.Thread(target=check_free_mode_loop, daemon=True).start()
    main_bot_thread = threading.Thread(target=run_main_bot, daemon=True)
    main_bot_thread.start()
    admin_bot_thread = threading.Thread(target=run_admin_bot, daemon=True)
    admin_bot_thread.start()
    print("✅ تم تشغيل البوتات بنجاح!")
    try:
        while True:
            time.sleep(60)
            active_ops = sum(len(ops) for ops in ACTIVE_OPERATIONS.values())
            print(f"🔄 {get_egypt_time().strftime('%Y-%m-%d %H:%M:%S')} - عمليات نشطة: {active_ops} - وضع مجاني: {is_free_mode()}")
    except KeyboardInterrupt:
        print("\n⏹️ تم الإيقاف")
        save_all_data()
        sys.exit(0)

if __name__ == "__main__":
    main()
