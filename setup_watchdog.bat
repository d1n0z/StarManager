@echo off
echo Setting up watchdog task...

schtasks /create /tn "StarManager Watchdog" /tr "python %~dp0watchdog.py" /sc minute /mo 1 /f

echo.
echo Watchdog task created!
echo It will check service every minute and restart after 3 failures.
echo.
echo To remove: schtasks /delete /tn "StarManager Watchdog" /f
pause
