from flask import Flask, request, jsonify, Response, render_template_string
from flask_cors import CORS
import subprocess
import os
import sys
import threading
import queue
import time

app = Flask(__name__)
CORS(app)

# قائمة عشان نخزن فيها اللوجز اللي بتطلع من السكريبتات
log_queue = queue.Queue()
log_history = []

# دالة عشان تشغل السكريبت وتبعت الـ output للـ queue
def run_script(script_name, args):
    global log_history
    try:
        # تأكد إن السكريبت موجود
        if not os.path.exists(script_name):
            log_queue.put(f"❌ الملف {script_name} غير موجود\n")
            return
        
        # تشغيل السكريبت
        process = subprocess.Popen(
            [sys.executable, script_name] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # قراءة الـ output سطر بسطر
        for line in iter(process.stdout.readline, ''):
            if line:
                log_queue.put(line)
                log_history.append(line)
        
        process.stdout.close()
        process.wait()
        log_queue.put("✅ انتهى التنفيذ\n")
        
    except Exception as e:
        log_queue.put(f"❌ خطأ في التشغيل: {str(e)}\n")

# دالة عشان نستخدمها في الـ API
def start_script_in_background(script_name, args):
    thread = threading.Thread(target=run_script, args=(script_name, args))
    thread.daemon = True
    thread.start()
    return thread

# ------------------ APIs ------------------

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'running'}), 200

@app.route('/api/run-split', methods=['POST'])
def api_run_split():
    data = request.json
    owner_phone = data.get('owner_phone')
    owner_pass = data.get('owner_password')
    member_phone = data.get('member_phone')
    member_pass = data.get('member_password')
    gb = data.get('gb')
    minutes = data.get('minutes')
    
    # نمرر البيانات كـ arguments للسكريبت
    args = [owner_phone, owner_pass, member_phone, member_pass, gb, minutes]
    start_script_in_background('split.py', args)
    
    return jsonify({'status': 'started', 'message': 'تم بدء التطير مع التقسيم'})

@app.route('/api/run-nosplit', methods=['POST'])
def api_run_nosplit():
    data = request.json
    owner_phone = data.get('owner_phone')
    owner_pass = data.get('owner_password')
    member_phone = data.get('member_phone')
    member_pass = data.get('member_password')
    gb = data.get('gb')
    minutes = data.get('minutes')
    
    args = [owner_phone, owner_pass, member_phone, member_pass, gb, minutes]
    start_script_in_background('nosplit.py', args)
    
    return jsonify({'status': 'started', 'message': 'تم بدء التطير بدون تقسيم'})

@app.route('/api/run-transfer', methods=['POST'])
def api_run_transfer():
    data = request.json
    owner_phone = data.get('owner_phone')
    owner_pass = data.get('owner_password')
    member_phone = data.get('member_phone')
    member_pass = data.get('member_password')
    
    args = [owner_phone, owner_pass, member_phone, member_pass]
    start_script_in_background('transfer.py', args)
    
    return jsonify({'status': 'started', 'message': 'تم بدء التحويل'})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """دالة عشان الـ Terminal يجيب اللوجز الجديدة"""
    global log_history
    # نرجع اللوجز الجديدة بس
    new_logs = list(log_queue.queue)
    # نفرغ الـ queue
    while not log_queue.empty():
        log_queue.get()
    
    return jsonify({
        'logs': new_logs,
        'history': log_history[-100:]  # آخر 100 سطر
    })

@app.route('/api/clear-logs', methods=['POST'])
def clear_logs():
    global log_history
    log_history = []
    while not log_queue.empty():
        log_queue.get()
    return jsonify({'status': 'cleared'})

# صفحة عشان نشوف اللوجز (ممكن تدمجها في الموقع الأساسي)
@app.route('/terminal')
def terminal_page():
    return render_template_string('''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>Terminal</title>
        <style>
            body { background: #1e1e1e; color: #00ff00; font-family: monospace; padding: 20px; }
            #terminal { background: #000; padding: 20px; border-radius: 10px; min-height: 400px; overflow-y: auto; }
            .log-line { margin: 5px 0; border-bottom: 1px solid #333; padding: 5px; }
        </style>
    </head>
    <body>
        <h1>🖥️ Terminal</h1>
        <div id="terminal"></div>
        <script>
            const BACKEND = 'https://01019092631.pythonanywhere.com';
            const term = document.getElementById('terminal');
            
            async function fetchLogs() {
                try {
                    const res = await fetch(BACKEND + '/api/logs');
                    const data = await res.json();
                    if (data.logs.length > 0) {
                        data.logs.forEach(log => {
                            const div = document.createElement('div');
                            div.className = 'log-line';
                            div.textContent = log;
                            term.appendChild(div);
                        });
                        term.scrollTop = term.scrollHeight;
                    }
                } catch (e) {}
            }
            
            setInterval(fetchLogs, 1000);
        </script>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
