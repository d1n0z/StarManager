#!/usr/bin/env python3
import requests
import sys
from datetime import datetime

HEALTH_URL = "http://127.0.0.1:5000/health"

def test_health():
    try:
        resp = requests.get(HEALTH_URL, timeout=5)
        if resp.status_code != 200:
            print(f"❌ HTTP {resp.status_code}")
            return False
        
        data = resp.json()
        
        print(f"Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Overall status
        status = data.get('status', 'unknown')
        print(f"\n📊 Status: {status.upper()}")
        
        # Database
        db = data.get('db', {})
        print("\n💾 Database:")
        print(f"  OK: {db.get('ok', '?')}")
        print(f"  Response time: {db.get('response_time', '?')}s")
        print(f"  Pool: {db.get('pool_used', '?')}/{db.get('pool_size', '?')}")
        
        # Scheduler
        scheduler = data.get('scheduler', {})
        print("\n⏰ Scheduler:")
        print(f"  OK: {scheduler.get('ok', '?')}")
        print(f"  Running: {scheduler.get('running', '?')}")
        print(f"  Message: {scheduler.get('message', '?')}")
        
        jobs = scheduler.get('jobs', {})
        if jobs:
            print("\n  Jobs (seconds since last run):")
            for job_name, seconds_ago in sorted(jobs.items(), key=lambda x: x[1]):
                status_icon = "✅" if seconds_ago < 300 else "⚠️"
                print(f"    {status_icon} {job_name}: {seconds_ago}s ago")
        
        print("\n🔵 VK:")
        print(f"  Active tasks: {data.get('vk_tasks', '?')}")
        print(f"  Dropped events: {data.get('vk_dropped', '?')}")
        
        event_loop = data.get('event_loop', {})
        if event_loop:
            print("\n🔄 Event Loop:")
            print(f"  Blocked count: {event_loop.get('blocked_count', '?')}")
            print(f"  Max block time: {event_loop.get('max_block_time', '?')}s")
        
        system = data.get('system', {})
        print("\n💻 System:")
        print(f"  Memory: {system.get('memory_mb', '?')} MB")
        print(f"  CPU: {system.get('cpu_percent', '?')}%")
        print(f"  Threads: {system.get('threads', '?')}")
        
        print("\n")
        
        return status == 'ok'
        
    except requests.Timeout:
        print("❌ Timeout")
        return False
    except requests.ConnectionError:
        print("❌ Connection refused")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    ok = test_health()
    sys.exit(0 if ok else 1)
