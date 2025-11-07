@echo off
REM Быстрая проверка здоровья шедулера (Windows)

curl -s http://127.0.0.1:5000/health > %TEMP%\health.json
python -c "import sys, json; data = json.load(open(r'%TEMP%\health.json')); s = data.get('scheduler', {}); print('❌ SCHEDULER PROBLEM:', s.get('message')) if not s.get('ok') or not s.get('running') else print('✅ Scheduler OK'); sys.exit(0 if s.get('ok') and s.get('running') else 1)"
