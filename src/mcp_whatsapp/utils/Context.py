import abc

from src.mcp_whatsapp.utils.patern_classes import Singleton


class Context(Singleton, abc.ABC):
    @abc.abstractmethod
    async def lanch(self):
        pass