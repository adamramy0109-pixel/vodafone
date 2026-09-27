import os
import sys
import json
import time
import random
import string
import logging
import queue
import threading
import requests

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

# ==================== إعداد التطبيق ====================
app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== التريمنال اللايف ====================
terminal_queues = {}
terminal_lock = threading.Lock()

def term_log(session_id, message):
    """بعت رسالة للتريمنال اللايف"""
    if not session_id:
        return
    with terminal_lock:
        if session_id in terminal_queues:
            terminal_queues[session_id].put(message)
    logger.info(f"[{session_id}] {message}")

@app.route('/api/terminal/<session_id>', methods=['GET'])
def terminal_stream(session_id):
    """SSE stream للتريمنال"""
    def event_stream():
        q = queue.Queue()
        with terminal_lock:
            terminal_queues[session_id] = q
        try:
            # رسالة ترحيب
            q.put("✅ تم الاتصال بالتريمنال")
            while True:
                try:
                    msg = q.get(timeout=25)
                    yield f"data: {json.dumps({'message': msg}, ensure_ascii=False)}\n\n"
                except queue.Empty:
                    # keep-alive
                    yield f"data: {json.dumps({'message': ''})}\n\n"
        except GeneratorExit:
            pass
        finally:
            with terminal_lock:
                terminal_queues.pop(session_id, None)

    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        }
    )

# ==================== مساعدات ====================
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'running'}), 200

def gen_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# ==================== التخزين المؤقت للأونرز ====================
# ملاحظة: ده مؤقت في الذاكرة، لو السيرفر عمل restart هيتصفّر.
# لو عايز تخزين دائم، هستخدم ملف JSON بعدين.
owners_store = {}  # { "010xxxxxxxx": { "password": "...", "label": "..." } }

# ==================== APIs ====================

@app.route('/api/owners', methods=['GET'])
def get_owners():
    """جلب كل الأونرز المحفوظين"""
    result = []
    for phone, data in owners_store.items():
        result.append({
            'phone': phone,
            'label': data.get('label', phone),
        })
    return jsonify({'status': 'success', 'owners': result})


@app.route('/api/owners', methods=['POST'])
def add_owner():
    """إضافة أونر جديد"""
    data = request.get_json() or {}
    phone = (data.get('phone') or '').strip()
    password = (data.get('password') or '').strip()
    label = (data.get('label') or phone).strip()

    if not phone or not password:
        return jsonify({'status': 'error', 'message': 'رقم وباسورد الأونر مطلوبين'}), 400

    owners_store[phone] = {'password': password, 'label': label}
    return jsonify({'status': 'success', 'message': f'تم إضافة الأونر {phone}'})


@app.route('/api/owners/<phone>', methods=['DELETE'])
def delete_owner(phone):
    """حذف أونر"""
    if phone in owners_store:
        del owners_store[phone]
        return jsonify({'status': 'success', 'message': 'تم الحذف'})
    return jsonify({'status': 'error', 'message': 'الأونر غير موجود'}), 404


@app.route('/api/check-daily-limit', methods=['POST'])
def check_daily_limit():
    """
    كشف الحد اليومي للدعوات - بيرجع من سيرفر فودافون
    """
    data = request.get_json() or {}
    owner_phone = (data.get('owner_phone') or '').strip()
    owner_password = (data.get('owner_password') or '').strip()
    session_id = data.get('session_id', 'default')

    if not owner_phone or not owner_password:
        return jsonify({'status': 'error', 'message': 'رقم وباسورد الأونر مطلوبين'}), 400

    term_log(session_id, f"📊 بدء كشف الحد اليومي للرقم: {owner_phone}")

    try:
        # تسجيل الدخول
        term_log(session_id, "🔐 جاري تسجيل الدخول...")
        token = vf_login(owner_phone, owner_password, session_id)
        if not token:
            term_log(session_id, "❌ فشل تسجيل الدخول")
            return jsonify({'status': 'error', 'message': 'فشل تسجيل الدخول - تأكد من البيانات'}), 401

        term_log(session_id, "✅ تم تسجيل الدخول")

        # عمل request بسيط عشان نقرأ الـ headers
        term_log(session_id, "📡 جاري قراءة بيانات الحد...")
        headers = build_headers(owner_phone, token)
        url = "https://mobile.vodafone.com.eg/services/dxl/cg/customerGroupAPI/customerGroup"

        # request بسيط (OPTIONS أو GET) عشان ناخد الهيدرز
        try:
            resp = requests.get(
                "https://mobile.vodafone.com.eg/services/dxl/usage/usageConsumptionReport",
                headers=headers,
                params={
                    'bucket.product.publicIdentifier': owner_phone,
                    '@type': 'aggregated'
                },
                timeout=20
            )
        except Exception as e:
            term_log(session_id, f"⚠️ خطأ في الاتصال: {e}")
            resp = None

        if resp is not None:
            rem = int(resp.headers.get('x-ratelimit-remaining-day', -1))
            lim = int(resp.headers.get('x-ratelimit-limit-day', 100))
            if rem < 0:
                # لو مش موجودين، نجرب من الهيدرز التانية
                rem = int(resp.headers.get('X-RateLimit-Remaining-Day', -1))
                lim = int(resp.headers.get('X-RateLimit-Limit-Day', 100))
        else:
            rem, lim = -1, 100

        if rem < 0:
            term_log(session_id, "⚠️ السيرفر مرجعش بيانات الحد، هعرض قيمة افتراضية")
            rem = 0

        term_log(session_id, f"📊 الحد اليومي المتبقي: {rem} / {lim}")

        return jsonify({
            'status': 'success',
            'daily_limit': rem,
            'limit_max': lim,
            'message': f'الحد المتبقي: {rem} من {lim}'
        })

    except Exception as e:
        logger.exception("check_daily_limit error")
        term_log(session_id, f"❌ خطأ: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/split-transfer', methods=['POST'])
def split_transfer():
    """
    تطير مع تقسيم
    ملاحظة: ده placeholder مؤقت، هيتوصل بملف gegat2.py بعدين
    """
    data = request.get_json() or {}
    phone = (data.get('phone') or '').strip()
    gb = data.get('gb')
    minutes = data.get('minutes')
    owner_phone = (data.get('owner_phone') or '').strip()
    owner_password = (data.get('owner_password') or '').strip()
    session_id = data.get('session_id', 'default')

    if not all([phone, gb, minutes, owner_phone, owner_password]):
        return jsonify({'status': 'error', 'message': 'كل الحقول مطلوبة'}), 400

    term_log(session_id, f"🚀 بدء تطير مع تقسيم للرقم: {phone}")
    term_log(session_id, f"📦 الباقة: {gb} GB + {minutes} دقيقة")
    term_log(session_id, f"👤 الأونر: {owner_phone}")

    try:
        # تسجيل دخول الأونر
        term_log(session_id, "🔐 جاري تسجيل دخول الأونر...")
        owner_token = vf_login(owner_phone, owner_password, session_id)
        if not owner_token:
            term_log(session_id, "❌ فشل تسجيل دخول الأونر")
            return jsonify({'status': 'error', 'message': 'فشل تسجيل دخول الأونر'}), 401
        term_log(session_id, "✅ تم تسجيل دخول الأونر")

        # ⚠️ هنا هنستدعي دالة الـ split الفعلية بعدين
        term_log(session_id, "⏳ (مؤقتاً) محاكاة تنفيذ العملية...")
        time.sleep(2)

        term_log(session_id, "✅ (مؤقتاً) تم التنفيذ بنجاح")
        return jsonify({
            'status': 'success',
            'message': f'OK: {gb}GB transferred',
            'note': 'placeholder - هيتم استبداله بعدين'
        })

    except Exception as e:
        logger.exception("split_transfer error")
        term_log(session_id, f"❌ خطأ: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/nosplit-transfer', methods=['POST'])
def nosplit_transfer():
    """
    تطير بدون تقسيم
    ملاحظة: placeholder مؤقت
    """
    data = request.get_json() or {}
    phone = (data.get('phone') or '').strip()
    gb = data.get('gb')
    minutes = data.get('minutes')
    owner_phone = (data.get('owner_phone') or '').strip()
    owner_password = (data.get('owner_password') or '').strip()
    session_id = data.get('session_id', 'default')

    if not all([phone, gb, minutes, owner_phone, owner_password]):
        return jsonify({'status': 'error', 'message': 'كل الحقول مطلوبة'}), 400

    term_log(session_id, f"✈️ بدء تطير بدون تقسيم للرقم: {phone}")
    term_log(session_id, f"📦 الباقة: {gb} GB + {minutes} دقيقة")
    term_log(session_id, f"👤 الأونر: {owner_phone}")

    try:
        term_log(session_id, "🔐 جاري تسجيل دخول الأونر...")
        owner_token = vf_login(owner_phone, owner_password, session_id)
        if not owner_token:
            term_log(session_id, "❌ فشل تسجيل دخول الأونر")
            return jsonify({'status': 'error', 'message': 'فشل تسجيل دخول الأونر'}), 401
        term_log(session_id, "✅ تم تسجيل دخول الأونر")

        term_log(session_id, "⏳ (مؤقتاً) محاكاة تنفيذ العملية...")
        time.sleep(2)

        term_log(session_id, "✅ (مؤقتاً) تم التنفيذ بنجاح")
        return jsonify({
            'status': 'success',
            'message': f'OK: {gb}GB transferred',
            'note': 'placeholder - هيتم استبداله بعدين'
        })

    except Exception as e:
        logger.exception("nosplit_transfer error")
        term_log(session_id, f"❌ خطأ: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/transfer-number', methods=['POST'])
def transfer_number():
    """
    تحويل الأرقام
    ملاحظة: placeholder مؤقت
    """
    data = request.get_json() or {}
    phone = (data.get('phone') or '').strip()
    password = (data.get('password') or '').strip()
    percentage = data.get('percentage')
    from_number = (data.get('from_number') or '').strip()
    to_number = (data.get('to_number') or '').strip()
    session_id = data.get('session_id', 'default')

    term_log(session_id, f"🔄 بدء تحويل الأرقام")
    term_log(session_id, f"📱 من: {from_number or phone}")
    term_log(session_id, f"📱 إلى: {to_number or 'N/A'}")
    term_log(session_id, f"📊 النسبة: {percentage or 'N/A'}")

    try:
        term_log(session_id, "⏳ (مؤقتاً) محاكاة تنفيذ العملية...")
        time.sleep(2)

        term_log(session_id, "✅ (مؤقتاً) تم التحويل بنجاح")
        return jsonify({
            'status': 'success',
            'message': 'Transfer OK',
            'note': 'placeholder - هيتم استبداله بعدين'
        })

    except Exception as e:
        logger.exception("transfer_number error")
        term_log(session_id, f"❌ خطأ: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/unlock-device', methods=['POST'])
def unlock_device():
    """فك اليمت - placeholder"""
    data = request.get_json() or {}
    owner_phone = (data.get('owner_phone') or '').strip()
    user_phone = (data.get('user_phone') or '').strip()
    session_id = data.get('session_id', 'default')

    term_log(session_id, f"🔓 بدء فك اليمت للرقم: {user_phone}")
    time.sleep(1)
    term_log(session_id, "✅ تم فك اليمت")

    return jsonify({'status': 'success', 'message': 'Unlocked'})


@app.route('/api/block-ip', methods=['POST'])
def block_ip():
    """حظر IP - placeholder"""
    data = request.get_json() or {}
    ip = (data.get('ip') or '').strip()
    session_id = data.get('session_id', 'default')

    term_log(session_id, f"🚫 بدء حظر IP: {ip}")
    time.sleep(1)
    term_log(session_id, "✅ تم الحظر")

    return jsonify({'status': 'success', 'message': 'Blocked'})


@app.route('/api/generate-code', methods=['POST'])
def generate_code():
    """توليد كود"""
    code = gen_code(6)
    return jsonify({'status': 'success', 'code': code})


# ==================== دوال Vodafone المساعدة ====================
CLIENT_SECRET = "dca0pbLUWXVhXR266Gw1iT5rqwvvJQoN"
CLIENT_ID = "AnaVF"
AUTH_URL = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"

DEVICE_NAMES = [
    "Realme RMX3760", "OPPO CPH2701", "Samsung SM-A155F", "Samsung SM-S911B",
    "Xiaomi Redmi Note 13", "Xiaomi 14T", "Infinix Hot 40", "Tecno Spark 20",
    "Honor X8b", "Honor X9b", "Vivo Y28", "Vivo Y36", "Nokia G42",
    "Motorola Moto G84", "Motorola Edge 40", "Realme 11 Pro", "Realme C55",
    "POCO X6 Pro", "OnePlus Nord CE 3", "Huawei Nova 12i",
]
ANDROID_VERSIONS = ["12", "13", "14", "15", "16"]
APP_VERSIONS = ["2026.8.3.1", "2026.7.4", "2026.6.3", "2026.6.9", "2026.7.1",
                "2026.5.2", "2026.5.8", "2026.6.1", "2026.8.1", "2026.7.9"]
BUILDS = ["1105", "1108", "1112", "1130", "1140", "1145", "1148",
          "1160", "1172", "1178", "1190", "1200", "1207", "1215"]


def gen_device():
    import uuid
    return {
        "device_id": uuid.uuid4().hex[:16],
        "digital_id": uuid.uuid4().hex[:13].upper(),
        "device_name": random.choice(DEVICE_NAMES),
        "android_ver": random.choice(ANDROID_VERSIONS),
        "app_ver": random.choice(APP_VERSIONS),
        "build": random.choice(BUILDS),
        "user_agent": "okhttp/4.12.0",
    }


def build_headers(phone, token, device=None):
    if device is None:
        device = gen_device()
    return {
        'User-Agent': "okhttp/4.12.0",
        'Connection': "Keep-Alive",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'Authorization': f"Bearer {token}",
        'api-version': "v2",
        'device-id': device["device_id"],
        'x-agent-operatingsystem': device["android_ver"],
        'clientId': "AnaVodafoneAndroid",
        'x-agent-device': device["device_name"],
        'x-agent-version': device["app_ver"],
        'x-agent-build': device["build"],
        'msisdn': phone,
        'Accept-Language': "ar",
        'Content-Type': "application/json; charset=UTF-8"
    }


def vf_login(phone, password, session_id=None, max_retries=2):
    """تسجيل الدخول لفودافون"""
    device = gen_device()
    payload = {
        'grant_type': "password",
        'username': phone,
        'password': password,
        'client_secret': CLIENT_SECRET,
        'client_id': CLIENT_ID
    }
    headers = {
        'Accept': "application/json, text/plain, */*",
        'Connection': "keep-alive",
        'silentLogin': "true",
        'msisdn': phone,
        'x-agent-operatingsystem': device["android_ver"],
        'clientId': "AnaVodafoneAndroid",
        'Accept-Language': "ar",
        'x-agent-device': device["device_name"],
        'x-agent-version': device["app_ver"],
        'x-agent-build': device["build"],
        'digitalId': device["digital_id"],
        'device-id': device["device_id"],
        'Content-Type': "application/x-www-form-urlencoded",
        'Host': "mobile.vodafone.com.eg",
        'Accept-Encoding': "gzip",
        'User-Agent': "okhttp/4.12.0"
    }

    for attempt in range(max_retries):
        try:
            term_log(session_id, f"🔐 محاولة تسجيل دخول {attempt+1}/{max_retries}...")
            resp = requests.post(AUTH_URL, data=payload, headers=headers, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                if 'access_token' in data:
                    return data['access_token']
            term_log(session_id, f"⚠️ HTTP {resp.status_code}: {resp.text[:150]}")
        except Exception as e:
            term_log(session_id, f"⚠️ محاولة {attempt+1} فشلت: {e}")

        if attempt < max_retries - 1:
            time.sleep(5)

    return None


# ==================== تشغيل ====================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
