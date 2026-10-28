import asyncio

from fastapi.concurrency import asynccontextmanager


class MessageBroadcaster:
    def __init__(self):
        self.queues: list[asyncio.Queue] = []

    def broadcast(self, message: dict):
        """Pushes a message to all connected SSE clients."""
        for q in self.queues:
            q.put_nowait(message)
            
    def close_all(self):
        """Sends a kill signal (None) to all connected SSE clients."""
        for q in self.queues:
            q.put_nowait(None)

    @asynccontextmanager
    async def subscribe(self):
        """Creates a queue for a new SSE connection."""
        q = asyncio.Queue()
        self.queues.append(q)
        try:
            yield q
        finally:
            self.queues.remove(q)