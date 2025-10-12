#!/usr/bin/env python3
import json
from pathlib import Path

DIAGNOSTIC_FILE = Path(__file__).parent / "logs" / "diagnostic.jsonl"

def analyze():
    if not DIAGNOSTIC_FILE.exists():
        print("No diagnostic data")
        return
    
    records = []
    with open(DIAGNOSTIC_FILE) as f:
        for line in f:
            records.append(json.loads(line))
    
    if not records:
        print("No records")
        return
    
    print(f"\n=== Analysing {len(records)} problems ===\n")
    
    by_reason = {}
    for r in records:
        reason = r['reason']
        by_reason.setdefault(reason, []).append(r)
    
    for reason, items in sorted(by_reason.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"• {reason}: {len(items)} times")
        last = items[-1]
        if last['health_data']:
            data = last['health_data']
            print(f"  VK tasks: {data.get('vk_tasks', '?')}")
            if 'db' in data:
                db = data['db']
                print(f"  DB pool: {db.get('pool_used', '?')}/{db.get('pool_size', '?')}")
                print(f"  DB time: {db.get('response_time', '?')}s")
            if 'system' in data:
                sys = data['system']
                print(f"  Memory: {sys.get('memory_mb', '?')} MB")
                print(f"  Threads: {sys.get('threads', '?')}")
        print()

if __name__ == "__main__":
    analyze()
