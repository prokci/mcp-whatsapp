import asyncio
import logging

from src.mcp_whatsapp.data_base.DBContext import DBContext, SQLModel
from src.mcp_whatsapp.mcp.whatsmeow_events import neonize_context

db_context = DBContext()

async def init_db():
    await db_context.launch()
    async with db_context.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


logging.basicConfig(level=logging.DEBUG)

DOWLAND_TIMEOUT = 120

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

async def main():
    
    await init_db()
    
    await neonize_context.lanch()
    await neonize_context.idle_task # type: ignore

if __name__ == "__main__":
    asyncio.run(main())