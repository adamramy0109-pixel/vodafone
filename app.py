from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import random
import string

# إعداد اللوجز
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# تفعيل CORS بشكل كامل عشان GitHub Pages يقدر يكلم السيرفر
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# ------------------ APIs ------------------

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'running'}), 200

@app.route('/api/split-transfer', methods=['POST'])
def split_transfer():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        phone = data.get('phone')
        gb = data.get('gb')
        minutes = data.get('minutes')
        logger.info(f"Split transfer: {phone}, {gb}GB, {minutes}min")
        return jsonify({'status': 'success', 'message': f'OK: {gb}GB transferred'})
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/nosplit-transfer', methods=['POST'])
def nosplit_transfer():
    try:
        data = request.get_json()
        phone = data.get('phone')
        gb = data.get('gb')
        logger.info(f"No split transfer: {phone}, {gb}GB")
        return jsonify({'status': 'success', 'message': f'OK: {gb}GB transferred'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/check-daily-limit', methods=['POST'])
def check_daily_limit():
    try:
        data = request.get_json()
        owner_phone = data.get('owner_phone')
        logger.info(f"Check daily limit: {owner_phone}")
        return jsonify({'status': 'success', 'daily_limit': 50, 'message': 'Limit: 50GB'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/transfer-number', methods=['POST'])
def transfer_number():
    try:
        data = request.get_json()
        from_number = data.get('from_number')
        to_number = data.get('to_number')
        logger.info(f"Transfer: {from_number} to {to_number}")
        return jsonify({'status': 'success', 'message': 'Transfer OK'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/unlock-device', methods=['POST'])
def unlock_device():
    try:
        data = request.get_json()
        owner_phone = data.get('owner_phone')
        user_phone = data.get('user_phone')
        logger.info(f"Unlock: {user_phone}")
        return jsonify({'status': 'success', 'message': 'Unlocked'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/block-ip', methods=['POST'])
def block_ip():
    try:
        data = request.get_json()
        ip = data.get('ip')
        logger.info(f"Block IP: {ip}")
        return jsonify({'status': 'success', 'message': 'Blocked'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/generate-code', methods=['POST'])
def generate_code():
    try:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        logger.info(f"Generated code: {code}")
        return jsonify({'status': 'success', 'code': code})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
