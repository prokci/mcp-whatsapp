import asyncio
from pathlib import Path

from pydoll.constants import Key

from src.mcp_whatsapp.tasks.Task import WhatsappTask
from src.mcp_whatsapp.utils.funcs import raise_none
from src.mcp_whatsapp.web_app.AppPolicy import AppPolicy
from src.mcp_whatsapp.web_app.PydollContext import WhatsAppPydollContext
from src.mcp_whatsapp.web_app.whatsapp_dictinary import Language


class PydollWalkToChat(WhatsappTask):
    def __init__(self, number: str):
        self.number = number
        self.context = WhatsAppPydollContext()
        self.lang = Language()
        
    async def execute(self, policy: AppPolicy):
        is_humanize = policy.humanize
        tab = raise_none(self.context.tab)
        
        search_box = await tab.find(
            tag_name="input", 
            placeholder=self.lang["placeholder_search"], 
            raise_exc=False
        )
        if not search_box:
            search_box = await tab.query(
                '/html/body/div[1]/div/div/div/div/div[3]/div/div[3]/div/div[1]/div[1]/div/div/div/div/div/div[2]/input'
            )
        
        await search_box.click(humanize=is_humanize)
        
        await tab.keyboard.hotkey(Key.CONTROL, Key.A)
        await tab.keyboard.press(Key.BACKSPACE)
        
        await search_box.type_text(self.number, humanize=False)
        
        await asyncio.sleep(2) 
        
        first_result = await tab.find(data_testid="list-item-1", timeout=5)
        await first_result.click(humanize=is_humanize)
        
        await self.close_if_need_file_send(policy)
        
    async def close_if_need_file_send(self, policy: AppPolicy):
        is_humanize = policy.humanize
        tab = raise_none(self.context.tab)
        
        close_button = await tab.find(
            tag_name="div",
            role="button",
            tabindex="0",
            aria_label="Close",
            timeout=policy.element_timeout,
            raise_exc=False
        )
        if close_button:
            await close_button.click(humanize=is_humanize)
            
            discard_button = await tab.query(
                '//button[.//span[text()="Discard"]]', 
            )
            
            await policy.delay_between_actions()
            await discard_button.click(humanize=is_humanize)
        
        
        

class PydollSendMessage(WhatsappTask):
    def __init__(self, message: str, number: str, need_user_confirmation: bool|None = None):
        self.to_chat = PydollWalkToChat(number)
        self.message = message
        self.context = WhatsAppPydollContext()
        self.need_user_confirmation = need_user_confirmation
    
    async def execute(self, policy: AppPolicy):
        is_humanize = policy.humanize
        tab = raise_none(self.context.tab)
        
        await self.to_chat.execute(policy)
        await policy.delay_between_steps()
        
        compose_box = await tab.find(
            data_testid="conversation-compose-box-input", 
            timeout=policy.element_timeout
        )
        await compose_box.click(humanize=is_humanize)
        
        await tab.keyboard.hotkey(Key.CONTROL, Key.A)
        await tab.keyboard.press(Key.BACKSPACE)
        
        
        await compose_box.type_text(self.message, humanize=is_humanize)
        
        need_user_confirmation = self.need_user_confirmation \
            if self.need_user_confirmation is not None else policy.need_user_confirmation
            
        if not need_user_confirmation:
            
            await tab.keyboard.press(Key.ENTER)
    
class PydollSendFile(WhatsappTask):
    def __init__(self, file_path: Path, number: str, message: str="", need_user_confirmation: bool|None = None):
        self.to_chat = PydollWalkToChat(number)
        self.file_path = file_path
        assert self.file_path.exists(), f"File doesn't exist: {self.file_path}"
        self.context = WhatsAppPydollContext()
        self.need_user_confirmation = need_user_confirmation
        self.message = message
        self.lang = Language()
        
    async def execute(self, policy: AppPolicy):
        is_humanize = policy.humanize
        tab = raise_none(self.context.tab)
        
        await self.to_chat.execute(policy)
        await policy.delay_between_steps()
        
        attach_btn = await tab.find(aria_label=self.lang["attach"], timeout=policy.element_timeout)
        await attach_btn.click(humanize=is_humanize)
        
        async with tab.expect_file_chooser(files=self.file_path):
            document_btn = await tab.find(text=self.lang["document"], timeout=policy.element_timeout)
            await document_btn.click(humanize=is_humanize)
        
        await policy.delay_between_steps()
        await self.send_messge_if_need(policy)
        
        need_user_confirmation = self.need_user_confirmation \
            if self.need_user_confirmation is not None else policy.need_user_confirmation
            
        if not need_user_confirmation:
            await policy.delay_between_steps()
            send_btn = await tab.find(data_testid="wds-ic-send-filled", timeout=policy.element_timeout)
            await send_btn.click(humanize=is_humanize)
            
    async def send_messge_if_need(self, policy: AppPolicy):
        is_humanize = policy.humanize
        tab = raise_none(self.context.tab)
        
        message_input = await tab.find(data_testid="media-caption-input-container", timeout=policy.element_timeout)
        await message_input.click(humanize=is_humanize)
        await policy.delay_between_actions()
        
        await tab.keyboard.hotkey(Key.CONTROL, Key.A)
        await policy.delay_between_actions()
        await tab.keyboard.press(Key.BACKSPACE)
        
        if self.message:
            await message_input.type_text(self.message, humanize=is_humanize)