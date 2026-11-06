import asyncio
import sys
from pathlib import Path

import pyperclip
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
            inputs = await tab.find(tag_name="input",  find_all=True)
            inputs = [input for input in inputs if await input.is_visible() and input.attributes.get('data_testid') not in ["conversation-compose-box-input", "media-caption-input-container"]]
            if len(inputs) != 1:
                raise RuntimeError("Can't find search box")
            search_box = raise_none(inputs[0])
        
        await search_box.click(humanize=is_humanize)
        
        await tab.keyboard.hotkey(Key.CONTROL, Key.A)
        await tab.keyboard.press(Key.BACKSPACE)
        
        await search_box.type_text(self.number, humanize=True)
        
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
            aria_label=self.lang["close"],
            timeout=policy.element_timeout,
            raise_exc=False
        )
        if close_button:
            await close_button.click(humanize=is_humanize)
            
            discard_button = await tab.query(
                f'//button[.//span[text()="{self.lang["discard"]}"]]', 
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
        
        old_text = pyperclip.paste()
        pyperclip.copy(self.message)
        modifier_key = Key.META if sys.platform == 'darwin' else Key.CONTROL
        await tab.keyboard.hotkey(modifier_key, Key.V)
        pyperclip.copy(old_text)
        
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
            document_btns = await tab.find(text=self.lang["document"], timeout=policy.element_timeout, find_all = True)
            document_btns = [input for input in document_btns if await input.is_visible()]
            if len(document_btns) != 1:
                raise RuntimeError("Can't find document button.")
            document_btn = raise_none(document_btns[0])
            
            await document_btn.click(humanize=is_humanize)
        
        await policy.delay_between_steps()
        await self.send_messge_if_need(policy)
        
        need_user_confirmation = self.need_user_confirmation \
            if self.need_user_confirmation is not None else policy.need_user_confirmation
            
        if not need_user_confirmation:
            await policy.delay_between_steps()
            await tab.keyboard.press(Key.ENTER)
            
    async def send_messge_if_need(self, policy: AppPolicy):
        is_humanize = policy.humanize
        tab = raise_none(self.context.tab)
        
        message_input = await tab.find(data_testid="media-caption-input-container", timeout=policy.element_timeout)
        await message_input.click(humanize=is_humanize)
        await policy.delay_between_steps()
        
        await tab.keyboard.hotkey(Key.CONTROL, Key.A)
        await policy.delay_between_steps()
        await tab.keyboard.press(Key.BACKSPACE)
        
        if self.message:
            old_text = pyperclip.paste()
            pyperclip.copy(self.message)
            modifier_key = Key.META if sys.platform == 'darwin' else Key.CONTROL
            await tab.keyboard.hotkey(modifier_key, Key.V)
            pyperclip.copy(old_text)