import asyncio
import logging
from typing import ClassVar

from neonize.aioze.client import NewAClient

from src.mcp_whatsapp.data_base.DBContext import DBContext
from src.mcp_whatsapp.utils.Context import Context

log = logging.getLogger(__name__)


class NeonizeContext(Context):
    
    _tasks:ClassVar = set()
    
    def init(self, db: None|str = None):
        self.neonize_client = NewAClient(DBContext.GO_DATABASE_URL if db is None else db)
        self._lock = asyncio.Lock()
        self._is_start = False
        self.idle_task = None
        
        
    async def lanch(self):
        async with self._lock:
            if self._is_start:
                raise RuntimeError("start must be invoke once")
            else:
                self._is_start = True
            
            await self.neonize_client.connect()
            self.idle_task = asyncio.create_task(self.idle())

    async def idle(self):
        try:
            await self.neonize_client.idle()
        except Exception:
            log.exception("Error on idle task")

    async def cancel(self):
        if not self.idle_task is None and not self.idle_task.done():
            self.idle_task.cancel()
            await self.idle_task