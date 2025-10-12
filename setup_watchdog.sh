#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Setting up StarManager Watchdog..."
echo ""

# Добавляем в crontab
(crontab -l 2>/dev/null | grep -v "watchdog.py"; echo "* * * * * cd $SCRIPT_DIR && venv/bin/python watchdog.py >> logs/watchdog_cron.log 2>&1") | crontab -

echo "✓ Watchdog added to crontab"
echo ""
echo "Watchdog will check service every minute"
echo "Logs: $SCRIPT_DIR/logs/watchdog.log"
echo ""
echo "To remove: crontab -e (delete watchdog.py line)"
