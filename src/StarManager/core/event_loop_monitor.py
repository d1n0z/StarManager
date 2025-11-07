import asyncio
import time
from loguru import logger

class EventLoopMonitor:
    def __init__(self, threshold: float = 0.1):
        self.threshold = threshold
        self.last_check = time.time()
        self.blocked_count = 0
        self.max_block_time = 0.0
    
    async def monitor(self):
        while True:
            await asyncio.sleep(1)
            now = time.time()
            elapsed = now - self.last_check
            
            if elapsed > (1 + self.threshold):
                block_time = elapsed - 1
                self.blocked_count += 1
                self.max_block_time = max(self.max_block_time, block_time)
                
                if block_time > 5:
                    logger.warning(f"Event loop blocked for {block_time:.2f}s")
            
            self.last_check = now
    
    def get_stats(self) -> dict:
        return {
            "blocked_count": self.blocked_count,
            "max_block_time": round(self.max_block_time, 2),
        }

event_loop_monitor = EventLoopMonitor()
