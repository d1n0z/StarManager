#!/usr/bin/env python3
import time
import requests
import json
import sys
from pathlib import Path

HEALTH_URL = "http://127.0.0.1:5000/health"
TIMEOUT = 5
MAX_VK_TASKS = 100
LOG_FILE = Path(__file__).parent / "logs" / "monitor.log"
DIAGNOSTIC_FILE = Path(__file__).parent / "logs" / "diagnostic.jsonl"

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}\n"
    print(line, end='')
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line)

def save_diagnostic(data, reason):
    DIAGNOSTIC_FILE.parent.mkdir(exist_ok=True)
    record = {
        "timestamp": time.time(),
        "datetime": time.strftime('%Y-%m-%d %H:%M:%S'),
        "reason": reason,
        "health_data": data
    }
    with open(DIAGNOSTIC_FILE, 'a') as f:
        f.write(json.dumps(record) + '\n')
    log(f"Diagnostic saved: {reason}")

def check_health():
    try:
        resp = requests.get(HEALTH_URL, timeout=TIMEOUT)
        if resp.status_code != 200:
            return False, "HTTP error", None
        
        data = resp.json()
        
        if data.get("vk_tasks", 0) > MAX_VK_TASKS:
            return False, f"Too many VK tasks: {data['vk_tasks']}", data
        
        if not data.get("db_ok"):
            return False, "DB not responding", data
        
        if data.get("db_response_time", 0) > 2:
            return False, f"DB slow: {data['db_response_time']}s", data
        
        return True, "OK", data
    except requests.Timeout:
        return False, "Timeout", None
    except Exception as e:
        return False, str(e), None

if __name__ == "__main__":
    ok, msg, data = check_health()
    
    if ok and data:
        log(f"✓ Health: {msg} | VK tasks: {data.get('vk_tasks', '?')} | DB: {data.get('db_response_time', '?')}s")
    else:
        log(f"✗ Health: {msg}")
        if data:
            save_diagnostic(data, msg)
    
    sys.exit(0 if ok else 1)
