import time
from collections import defaultdict
from threading import Lock

class SchedulerMonitor:
    def __init__(self):
        self._last_run = defaultdict(lambda: 0.0)
        self._timeouts = {}
        self._lock = Lock()
    
    def mark_run(self, job_name: str):
        with self._lock:
            self._last_run[job_name] = time.time()
    
    def register_job(self, job_name: str, timeout: int):
        with self._lock:
            self._timeouts[job_name] = timeout
    
    def get_last_run(self, job_name: str) -> float:
        with self._lock:
            return self._last_run.get(job_name, 0.0)
    
    def get_all_jobs(self) -> dict[str, float]:
        with self._lock:
            return dict(self._last_run)
    
    def is_healthy(self, max_delay: int = 300) -> tuple[bool, str]:
        now = time.time()
        with self._lock:
            if not self._last_run:
                return False, "No jobs executed yet"
            
            for job_name, last_run in self._last_run.items():
                job_timeout = self._timeouts.get(job_name)
                if job_timeout is not None and now - last_run > job_timeout + 60:
                    return False, f"Job '{job_name}' not running (last: {int(now - last_run)}s ago)"
            
            return True, "OK"

scheduler_monitor = SchedulerMonitor()
