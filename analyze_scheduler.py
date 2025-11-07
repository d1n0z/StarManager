#!/usr/bin/env python3
import json
from pathlib import Path

DIAGNOSTIC_FILE = Path(__file__).parent / "logs" / "diagnostic.jsonl"

def analyze():
    if not DIAGNOSTIC_FILE.exists():
        print("diagnostic file not found")
        return

    print("scheduler health analysis\n")

    scheduler_issues = []

    with open(DIAGNOSTIC_FILE) as f:
        for line in f:
            try:
                record = json.loads(line)
                reason = record.get('reason', '')
                
                if 'scheduler' in reason.lower():
                    scheduler_issues.append(record)
            except json.JSONDecodeError:
                continue
    
    if not scheduler_issues:
        print("no scheduler health issues")
        return
    
    print(f"scheduler heath issues: {len(scheduler_issues)}\n")
    
    for issue in scheduler_issues[-10:]:
        dt = issue.get('datetime', '?')
        reason = issue.get('reason', '?')
        health = issue.get('health_data', {})
        scheduler = health.get('scheduler', {})
        
        print(f"[{dt}] {reason}")
        print(f"  Scheduler running: {scheduler.get('running', '?')}")
        print(f"  Scheduler message: {scheduler.get('message', '?')}")
        
        jobs = scheduler.get('jobs', {})
        if jobs:
            print("  Jobs (seconds since last run):")
            for job_name, seconds_ago in sorted(jobs.items(), key=lambda x: x[1], reverse=True):
                print(f"    - {job_name}: {seconds_ago}s ago")
        print()

if __name__ == "__main__":
    analyze()
