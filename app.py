from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import threading
import time
import uuid
import random

# --- Web App Setup ---
app = Flask(__name__)
CORS(app)  # Allows the web page to talk to the server
app.secret_key = 'your_super_secret_key_here' # Change this to a random string

# --- Copied from your original script ---
# Banner
BANNER = r"""
/$$$$$$$  /$$$$$$$$       /$$$$$$  /$$$$$$$$ /$$$$$$  /$$$$$$$  /$$      /$$ | $$__  $$|__  $$__/      /$$__  $$|__  $$__//$$__  $$| $$__  $$| $$$    /$$$ | $$  \ $$   | $$        | $$  \__/   | $$  | $$  \ $$| $$  \ $$| $$$$  /$$$$ | $$$$$$$    | $$ /$$$$$$|  $$$$$$    | $$  | $$  | $$| $$$$$$$/| $$ $$/$$ $$ | $$__  $$   | $$|______/ \____  $$   | $$  | $$  | $$| $$__  $$| $$  $$$| $$ | $$  \ $$   | $$         /$$  \ $$   | $$  | $$  | $$| $$  \ $$| $$\  $ | $$ | $$$$$$$/   | $$        |  $$$$$$/   | $$  |  $$$$$$/| $$  | $$| $$ \/  | $$ |_______/    |__/         \______/    |__/   \______/ |__/  |__/|__/     |__/
"""

# Credits
CREDITS = [
    " Created By DkRuban ",
    " I Hate This World "
]

# --- Simulation Data (because we can't use real Bluetooth) ---
MOCK_DEVICES = [
    ("AA:BB:CC:DD:EE:01", "Samsung Galaxy S21"),
    ("AA:BB:CC:DD:EE:02", "iPhone 13 Pro"),
    ("AA:BB:CC:DD:EE:03", "JBL Flip 5"),
    ("AA:BB:CC:DD:EE:04", "AirPods Pro"),
    ("AA:BB:CC:DD:EE:05", "Sony WH-1000XM4"),
    ("AA:BB:CC:DD:EE:06", "Bose QuietComfort 35"),
    ("AA:BB:CC:DD:EE:07", "Google Pixel 6"),
    ("AA:BB:CC:DD:EE:08", "OnePlus 9 Pro"),
]

# --- Web App Routes ---

@app.route('/')
def index():
    """Displays the main page."""
    return render_template('index.html', banner=BANNER, credits=CREDITS)

@app.route('/scan', methods=['POST'])
def scan():
    """Simulates scanning for devices."""
    print("Web App: Received scan request...")
    time.sleep(2) # Simulate the time it takes to scan
    
    # Pick a few random devices to "find"
    num_devices = random.randint(3, 6)
    found_devices = random.sample(MOCK_DEVICES, num_devices)
    
    response = {
        'status': 'success',
        'devices': found_devices,
        'message': f"Found {len(found_devices)} devices"
    }
    print(f"Web App: Sending back {len(found_devices)} fake devices.")
    return jsonify(response)

@app.route('/attack', methods=['POST'])
def attack():
    """Starts a simulated attack in a background thread."""
    data = request.get_json()
    attack_type = data.get('type', 'all')
    session_id = str(uuid.uuid4()) # Unique ID for this attack
    
    # Store initial status in session
    if 'attack_logs' not in session:
        session['attack_logs'] = {}
    session['attack_logs'][session_id] = []

    if attack_type == 'all':
        devices = data.get('devices', [])
        message = f"Starting DoS attack on all {len(devices)} devices..."
        # Start a background thread to simulate the attack
        threading.Thread(target=simulate_attack, args=(devices, session_id)).start()
    else: # single
        mac = data.get('mac')
        name = data.get('name')
        message = f"Starting DoS attack on {name} ({mac})..."
        threading.Thread(target=simulate_attack, args=([(mac, name)], session_id)).start()

    return jsonify({
        'status': 'success',
        'message': message,
        'session_id': session_id
    })

@app.route('/attack_status/<session_id>', methods=['GET'])
def attack_status(session_id):
    """Checks the status/logs of a simulated attack."""
    logs = session.get('attack_logs', {}).get(session_id, [])
    return jsonify({'status': 'success', 'logs': logs})

# --- Helper Functions for Simulation ---

def simulate_attack(devices, session_id):
    """This function runs in the background and pretends to attack devices."""
    for addr, name in devices:
        log_message = f"[+] Attacking {name} ({addr}) with l2ping flood..."
        session['attack_logs'][session_id].append(log_message)
        time.sleep(1)

        for i in range(10):
            log_message = f"[+] Sending packet {i+1}/10 to {addr}..."
            session['attack_logs'][session_id].append(log_message)
            time.sleep(0.5)
        
        log_message = f"[+] Attack on {addr} completed successfully!"
        session['attack_logs'][session_id].append(log_message)
        time.sleep(1)

# --- Run the App ---
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
