import asyncio
from typing import List, Callable, Any

class QueueManager:
    def __init__(self, max_concurrency: int = 4):
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def _worker(self, item, processor, results):
        async with self.semaphore:
            return await processor(item)

    async def process_parallel(self, items: List[Any], processor: Callable):
        tasks = [asyncio.create_task(self._worker(item, processor, None)) for item in items]
        await asyncio.gather(*tasks)
