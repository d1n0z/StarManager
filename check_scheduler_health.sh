#!/bin/bash
# Быстрая проверка здоровья шедулера

curl -s http://127.0.0.1:5000/health | python3 -c "
import sys, json
data = json.load(sys.stdin)
s = data.get('scheduler', {})
if not s.get('ok') or not s.get('running'):
    print('❌ SCHEDULER PROBLEM:', s.get('message'))
    sys.exit(1)
jobs = s.get('jobs', {})
for name, age in jobs.items():
    if age > 600:
        print(f'⚠️  {name}: {age}s ago (too old)')
print('✅ Scheduler OK')
"
