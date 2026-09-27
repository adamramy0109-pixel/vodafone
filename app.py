from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@app.route('/api/split-transfer', methods=['POST'])
def split_transfer():
    data = request.json
    phone = data.get('phone')
    gb = data.get('gb')
    minutes = data.get('minutes')
    logger.info(f"Split transfer: {phone}, {gb}GB, {minutes}min")
    return jsonify({'status': 'success', 'message': f'OK: {gb}GB transferred'})

@app.route('/api/nosplit-transfer', methods=['POST'])
def nosplit_transfer():
    data = request.json
    phone = data.get('phone')
    gb = data.get('gb')
    logger.info(f"No split transfer: {phone}, {gb}GB")
    return jsonify({'status': 'success', 'message': f'OK: {gb}GB transferred'})

@app.route('/api/check-daily-limit', methods=['POST'])
def check_daily_limit():
    data = request.json
    owner_phone = data.get('owner_phone')
    logger.info(f"Check daily limit: {owner_phone}")
    return jsonify({'status': 'success', 'daily_limit': 50, 'message': 'Limit: 50GB'})

@app.route('/api/transfer-number', methods=['POST'])
def transfer_number():
    data = request.json
    from_number = data.get('from_number')
    to_number = data.get('to_number')
    logger.info(f"Transfer: {from_number} to {to_number}")
    return jsonify({'status': 'success', 'message': 'Transfer OK'})

@app.route('/api/unlock-device', methods=['POST'])
def unlock_device():
    data = request.json
    owner_phone = data.get('owner_phone')
    user_phone = data.get('user_phone')
    logger.info(f"Unlock: {user_phone}")
    return jsonify({'status': 'success', 'message': 'Unlocked'})

@app.route('/api/block-ip', methods=['POST'])
def block_ip():
    data = request.json
    ip = data.get('ip')
    logger.info(f"Block IP: {ip}")
    return jsonify({'status': 'success', 'message': 'Blocked'})

@app.route('/api/generate-code', methods=['POST'])
def generate_code():
    import random, string
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"Generated code: {code}")
    return jsonify({'status': 'success', 'code': code})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'running'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
