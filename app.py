from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import threading
import time
import uuid
import random

# --- Web App Setup ---
app = Flask(__name__)
CORS(app)
app.secret_key = 'your_super_secret_key_here' # Change this for production

# --- Copied from your original script ---
BANNER = r"""
/$$$$$$$  /$$$$$$$$       /$$$$$$  /$$$$$$$$ /$$$$$$  /$$$$$$$  /$$      /$$ | $$__  $$|__  $$__/      /$$__  $$|__  $$__//$$__  $$| $$__  $$| $$$    /$$$ | $$  \ $$   | $$        | $$  \__/   | $$  | $$  \ $$| $$  \ $$| $$$$  /$$$$ | $$$$$$$    | $$ /$$$$$$|  $$$$$$    | $$  | $$  | $$| $$$$$$$/| $$ $$/$$ $$ | $$__  $$   | $$|______/ \____  $$   | $$  | $$  | $$| $$__  $$| $$  $$$| $$ | $$  \ $$   | $$         /$$  \ $$   | $$  | $$  | $$| $$  \ $$| $$\  $ | $$ | $$$$$$$/   | $$        |  $$$$$$/   | $$  |  $$$$$$/| $$  | $$| $$ \/  | $$ |_______/    |__/         \______/    |__/   \______/ |__/  |__/|__/     |__/
"""
CREDITS = [" Created By DkRuban ", " I Hate This World "]
MOCK_DEVICES = [
    ("AA:BB:CC:DD:EE:01", "Samsung Galaxy S21"), ("AA:BB:CC:DD:EE:02", "iPhone 13 Pro"),
    ("AA:BB:CC:DD:EE:03", "JBL Flip 5"), ("AA:BB:CC:DD:EE:04", "AirPods Pro"),
    ("AA:BB:CC:DD:EE:05", "Sony WH-1000XM4"), ("AA:BB:CC:DD:EE:06", "Bose QuietComfort 35"),
    ("AA:BB:CC:DD:EE:07", "Google Pixel 6"), ("AA:BB:CC:DD:EE:08", "OnePlus 9 Pro"),
]

# --- Global Attack Tracker ---
# This dictionary will hold the state of all active attacks
ATTACK_SESSIONS = {}

# --- Web App Routes ---

@app.route('/')
def index():
    """Displays the main page."""
    return render_template('index.html', banner=BANNER, credits=CREDITS)

@app.route('/scan', methods=['POST'])
def scan():
    """Simulates scanning for devices."""
    print("Web App: Received scan request...")
    time.sleep(2)
    num_devices = random.randint(3, 6)
    found_devices = random.sample(MOCK_DEVICES, num_devices)
    response = {'status': 'success', 'devices': found_devices, 'message': f"Found {len(found_devices)} devices"}
    print(f"Web App: Sending back {len(found_devices)} fake devices.")
    return jsonify(response)

@app.route('/attack', methods=['POST'])
def attack():
    """Starts a simulated attack in a background thread."""
    data = request.get_json()
    attack_type = data.get('type', 'all')
    session_id = str(uuid.uuid4())

    # Initialize this attack's session in our global tracker
    ATTACK_SESSIONS[session_id] = {
        'stop_flag': False,
        'logs': [],
        'status': 'running'
    }

    if attack_type == 'all':
        devices = data.get('devices', [])
        message = f"Starting DoS attack on all {len(devices)} devices..."
        threading.Thread(target=simulate_attack, args=(devices, session_id)).start()
    else: # single
        mac = data.get('mac')
        name = data.get('name')
        message = f"Starting DoS attack on {name} ({mac})..."
        threading.Thread(target=simulate_attack, args=([(mac, name)], session_id)).start()

    return jsonify({'status': 'success', 'message': message, 'session_id': session_id})

@app.route('/stop_attack/<session_id>', methods=['POST'])
def stop_attack(session_id):
    """Sets the stop flag for a running attack."""
    if session_id in ATTACK_SESSIONS:
        ATTACK_SESSIONS[session_id]['stop_flag'] = True
        ATTACK_SESSIONS[session_id]['status'] = 'stopped'
        return jsonify({'status': 'success', 'message': 'Stop signal sent.'})
    return jsonify({'status': 'error', 'message': 'Attack session not found.'}), 404

@app.route('/attack_status/<session_id>', methods=['GET'])
def attack_status(session_id):
    """Checks the status/logs of a simulated attack."""
    if session_id in ATTACK_SESSIONS:
        session_data = ATTACK_SESSIONS[session_id]
        return jsonify({
            'status': 'success',
            'logs': session_data['logs'],
            'is_running': session_data['status'] == 'running'
        })
    return jsonify({'status': 'error', 'message': 'Session not found.'}), 404

# --- Helper Functions for Simulation ---

def simulate_attack(devices, session_id):
    """
    This function runs in the background and pretends to attack devices.
    It now provides real-time logs and can be stopped.
    """
    try:
        for addr, name in devices:
            # Check if stop signal was received
            if ATTACK_SESSIONS[session_id]['stop_flag']:
                log_message = "[!] Attack stopped by user."
                ATTACK_SESSIONS[session_id]['logs'].append(log_message)
                break

            log_message = f"[*] Preparing to attack {name} ({addr})..."
            ATTACK_SESSIONS[session_id]['logs'].append(log_message)
            time.sleep(1)

            log_message = f"[+] Attacking {name} ({addr}) with l2ping flood..."
            ATTACK_SESSIONS[session_id]['logs'].append(log_message)
            time.sleep(1)

            for i in range(10):
                # Check for stop signal before each packet
                if ATTACK_SESSIONS[session_id]['stop_flag']:
                    log_message = f"[!] Attack on {addr} stopped by user."
                    ATTACK_SESSIONS[session_id]['logs'].append(log_message)
                    break
                
                log_message = f"  [>] Sending packet {i+1}/10 to {addr}..."
                ATTACK_SESSIONS[session_id]['logs'].append(log_message)
                time.sleep(0.5)
            else: # This 'else' belongs to the 'for' loop, runs if no break
                log_message = f"[+] Attack on {addr} completed successfully!"
                ATTACK_SESSIONS[session_id]['logs'].append(log_message)
                time.sleep(1)
        
        # Mark as finished if not stopped
        if not ATTACK_SESSIONS[session_id]['stop_flag']:
            ATTACK_SESSIONS[session_id]['status'] = 'finished'
            ATTACK_SESSIONS[session_id]['logs'].append("[*] All attacks completed.")

    except Exception as e:
        ATTACK_SESSIONS[session_id]['logs'].append(f"[!] An error occurred: {e}")
    finally:
        # Clean up the session after a delay to allow final status check
        # This prevents the dictionary from growing indefinitely
        threading.Timer(10.0, lambda: ATTACK_SESSIONS.pop(session_id, None)).start()


# --- Run the App ---
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
