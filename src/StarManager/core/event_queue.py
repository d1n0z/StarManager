import asyncio
import pickle
from pathlib import Path

from loguru import logger


class EventQueue:
    def __init__(self, persist_path: Path):
        self.queue = asyncio.Queue()
        self.persist_path = persist_path
        self.persist_path.parent.mkdir(exist_ok=True)

    async def put(self, event):
        await self.queue.put(event)

    async def get(self):
        return await self.queue.get()

    def qsize(self):
        return self.queue.qsize()

    async def save_to_disk(self):
        if self.queue.empty():
            return

        events = []
        while not self.queue.empty():
            try:
                events.append(self.queue.get_nowait())
            except asyncio.QueueEmpty:
                break

        if events:
            try:
                with open(self.persist_path, "wb") as f:
                    pickle.dump(events, f)
                logger.info(f"Saved {len(events)} pending events to disk")
            except Exception as e:
                logger.error(f"Failed to save events: {e}")

    async def load_from_disk(self):
        if not self.persist_path.exists():
            return

        try:
            with open(self.persist_path, "rb") as f:
                events = pickle.load(f)

            for event in events:
                await self.queue.put(event)

            logger.info(f"Restored {len(events)} events from disk")
            self.persist_path.unlink()
        except Exception as e:
            logger.error(f"Failed to load events: {e}")


event_queue = EventQueue(Path(__file__).parent.parent.parent.parent / "vk_events.pkl")
