import os
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base

# from sqlmodel import SQLModel
from src.mcp_whatsapp.utils.funcs import raise_none
from src.mcp_whatsapp.utils.patern_classes import Singleton

SQLModel = declarative_base()


class DBContext(Singleton):
    load_dotenv()
    DATABASE_URL = raise_none(os.getenv("DATABASE_URL"))
    GO_DATABASE_URL = raise_none(os.getenv("GO_DATABASE_URL"))
    timezone = ZoneInfo("Europe/Minsk")
    
    engine:AsyncEngine
    
    def init(self):
        self.engine = create_async_engine(self.DATABASE_URL)
        self.current_db_version = 1
        
    async def launch(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        await self.set_current_db_version()
                
    @asynccontextmanager
    async def get_session(self):
        async with AsyncSession(self.engine) as session:
            yield session
    
    async def set_current_db_version(self):
        from src.mcp_whatsapp.mcp.MessageRecord import MessageRecord
        async with self.get_session() as session:
            result = await session.execute(select(func.max(MessageRecord.version)))
            max_v = result.scalar()
            if max_v is not None:
                self.current_db_version = max_v