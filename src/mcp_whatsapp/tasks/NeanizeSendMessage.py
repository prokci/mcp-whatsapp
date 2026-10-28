from src.mcp_whatsapp.tasks.Task import WhatsappTask
from src.mcp_whatsapp.web_app.NeonizeContext import NeonizeContext
from neonize.utils import build_jid

# class SendMessage(Task):
#     def __init__(self, message: str, supplier: Supplier):
#         self.message = message
#         self.supplier = supplier
        

class NeanizeSendMessage( WhatsappTask):
    def __init__(self, message: str, number: str):
        self.message = message
        self.client = NeonizeContext().neonize_client
        self.jid = build_jid(number)
    
    async def execute(self, policy):
        await policy.delay_between_tasks()
        await self.client.send_message(self.jid, self.message)