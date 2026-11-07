import abc

from src.mcp_whatsapp.web_app.AppPolicy import AppPolicy


class Task(abc.ABC):
    description: str
    
    @abc.abstractmethod
    async def execute(self, policy):...
        
class WhatsappTask(Task):
    description: str
    
    @abc.abstractmethod
    async def execute(self, policy: AppPolicy):...
    
    
class UpdateSupplierForWhatsapp(WhatsappTask):...

