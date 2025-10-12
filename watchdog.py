#!/usr/bin/env python3
import time
import requests
import subprocess
import sys
import json
import platform
from pathlib import Path

HEALTH_URL = "http://127.0.0.1:5000/health"
TIMEOUT = 10
MAX_FAILURES = 3
RESTART_COMMAND = "python main.py"
LOG_FILE = Path(__file__).parent / "logs" / "watchdog.log"
STATE_FILE = Path(__file__).parent / "watchdog_state.json"
IS_LINUX = platform.system() == "Linux"

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}\n"
    print(line, end='')
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line)

def check_alive():
    try:
        resp = requests.get(HEALTH_URL, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            log(f"✓ Alive | VK tasks: {data.get('vk_tasks', '?')} | DB pool: {data.get('db', {}).get('pool_used', '?')}/{data.get('db', {}).get('pool_size', '?')}")
            return True
        else:
            log(f"✗ HTTP {resp.status_code}")
            return False
    except requests.Timeout:
        log("✗ Timeout")
        return False
    except requests.ConnectionError:
        log("✗ Connection refused")
        return False
    except Exception as e:
        log(f"✗ Error: {e}")
        return False

def restart_service():
    log("🔄 Restarting service...")
    try:
        if IS_LINUX:
            result = subprocess.run("systemctl restart starmanager", 
                                  shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                log("✅ Service restarted (systemd)")
                return True
            else:
                log(f"❌ Systemd restart failed: {result.stderr}")
                log("Trying pkill...")
                subprocess.run("pkill -f 'python.*main.py'", shell=True)
                time.sleep(2)
                subprocess.Popen(RESTART_COMMAND, shell=True, cwd=Path(__file__).parent)
                log("✅ Service restarted (manual)")
                return True
        else:
            subprocess.run("taskkill /F /IM python.exe /FI \"WINDOWTITLE eq StarManager*\"", 
                          shell=True, capture_output=True)
            time.sleep(2)
            subprocess.Popen(RESTART_COMMAND, shell=True, cwd=Path(__file__).parent)
            log("✅ Service restarted")
            return True
    except Exception as e:
        log(f"❌ Restart failed: {e}")
        return False

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f).get('consecutive_failures', 0)
    except Exception:
        return 0

def save_state(failures):
    STATE_FILE.parent.mkdir(exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump({'consecutive_failures': failures}, f)

if __name__ == "__main__":
    log("=" * 60)
    consecutive_failures = load_state()
    
    if check_alive():
        if consecutive_failures > 0:
            log(f"✅ Service recovered after {consecutive_failures} failures")
        consecutive_failures = 0
        save_state(0)
        sys.exit(0)
    else:
        consecutive_failures += 1
        save_state(consecutive_failures)
        log(f"❌ Service down ({consecutive_failures}/{MAX_FAILURES})")
        
        if consecutive_failures >= MAX_FAILURES:
            log("⚠️ Max failures reached, initiating restart...")
            if restart_service():
                log("Waiting 10s for service to start...")
                time.sleep(10)
                if check_alive():
                    log("✅ Service is back online")
                else:
                    log("⚠️ Service still not responding after restart")
            save_state(0)
        
        sys.exit(1)
