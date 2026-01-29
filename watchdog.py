#!/usr/bin/env python3
import atexit
import json
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path

import requests

HEALTH_URL = "http://127.0.0.1:5000/health"
TIMEOUT = 10
MAX_FAILURES = 3
MAX_TASKS_TIMEDOUT = 100
RESTART_COMMAND = "python main.py"
LOG_FILE = Path(__file__).parent / "logs" / "watchdog.log"
STATE_FILE = Path(__file__).parent / "watchdog_state.json"
LOCK_FILE = Path(__file__).parent / "watchdog.lock"
IS_LINUX = platform.system() == "Linux"


def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    print(line, end="")
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def _is_pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    else:
        return True


def acquire_lock():
    try:
        if LOCK_FILE.exists():
            try:
                content = LOCK_FILE.read_text().strip()
                pid = int(content) if content else None
            except Exception:
                pid = None

            if pid:
                if _is_pid_running(pid):
                    log(f"🔒 Another watchdog is running (pid {pid}). Exiting.")
                    return False
                else:
                    log(
                        f"🕸️ Found stale lock file (pid {pid}). Removing and continuing."
                    )
                    try:
                        LOCK_FILE.unlink()
                    except Exception as e:
                        log(f"⚠️ Failed to remove stale lock: {e}")
                        return False
            else:
                try:
                    LOCK_FILE.unlink()
                except Exception:
                    pass

        with open(LOCK_FILE, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        if LOCK_FILE.exists():
            log(f"🔒 Acquired lock (pid {os.getpid()})")
            return True
        else:
            log("⚠️ Failed to create lock file.")
            return False
    except Exception as e:
        log(f"⚠️ Lock acquisition error: {e}")
        return False


def release_lock():
    try:
        if LOCK_FILE.exists():
            content = LOCK_FILE.read_text().strip()
            try:
                pid = int(content) if content else None
            except Exception:
                pid = None
            if pid == os.getpid() or pid is None:
                LOCK_FILE.unlink()
                log("🔓 Lock released")
            else:
                log(f"🔒 Lock file owned by pid {pid}, not removing.")
    except Exception as e:
        log(f"⚠️ Failed to release lock: {e}")


atexit.register(release_lock)
for sig in (
    signal.SIGINT,
    signal.SIGTERM,
):
    try:
        signal.signal(sig, lambda signum, frame: sys.exit(0))
    except Exception:
        pass


def check_alive():
    try:
        resp = requests.get(HEALTH_URL, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            scheduler_data = data.get("scheduler", {})
            scheduler_ok = scheduler_data.get("ok", False)
            scheduler_running = scheduler_data.get("running", False)

            log(
                f"✓ Alive | VK tasks: {data.get('vk_tasks', '?')} | Queued: {data.get('vk_queued', 0)} | DB pool: {data.get('db', {}).get('pool_used', '?')}/{data.get('db', {}).get('pool_size', '?')} | Scheduler: {scheduler_ok}/{scheduler_running}"
            )

            if not scheduler_ok or not scheduler_running:
                log(f"⚠️ Scheduler issue: {scheduler_data.get('message', 'unknown')}")
                return False

            if data.get("_vk_tasks_timeouts", 0) > MAX_TASKS_TIMEDOUT:
                log(f"⚠️ Scheduler issue: {scheduler_data.get('message', 'unknown')}")
                return False

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
            script_dir = Path(__file__).parent
            log("Killing tmux session 'bot'...")
            subprocess.run("tmux kill-session -t bot", shell=True, capture_output=True)
            time.sleep(2)

            log("Starting new tmux session...")
            subprocess.run("tmux new -s bot -d", shell=True)
            subprocess.run(f"tmux send-keys -t bot 'cd {script_dir}' ENTER", shell=True)

            venv_path = script_dir / "venv" / "bin" / "activate"
            if venv_path.exists():
                subprocess.run(
                    f"tmux send-keys -t bot '. {venv_path}' ENTER", shell=True
                )
                time.sleep(1)

            subprocess.run("tmux send-keys -t bot 'python main.py' ENTER", shell=True)
            log("✅ Service restarted (tmux)")
            return True
        else:
            subprocess.run(
                'taskkill /F /IM python.exe /FI "WINDOWTITLE eq StarManager*"',
                shell=True,
                capture_output=True,
            )
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
            return json.load(f).get("consecutive_failures", 0)
    except Exception:
        return 0


def save_state(failures):
    STATE_FILE.parent.mkdir(exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"consecutive_failures": failures}, f)


if __name__ == "__main__":
    if not acquire_lock():
        sys.exit(0)

    consecutive_failures = load_state()

    try:
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
                    log("Waiting 500s for service to start...")
                    time.sleep(500)
                    if check_alive():
                        log("✅ Service is back online")
                    else:
                        log("⚠️ Service still not responding after restart")
                save_state(0)

            sys.exit(1)
    finally:
        release_lock()
