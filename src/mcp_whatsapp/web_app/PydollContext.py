import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import ClassVar
from zoneinfo import ZoneInfo

import psutil
import pydoll
import pydoll.exceptions as exc
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.browser.tab import Tab
from pydoll.decorators import retry

from src.mcp_whatsapp.utils.Context import Context
from src.mcp_whatsapp.utils.funcs import is_in_container, raise_none
from src.mcp_whatsapp.web_app.WebAppQueue import WebAppQueue
from src.mcp_whatsapp.web_app.whatsapp_dictinary import Language

log = logging.getLogger(__name__)


class WhatsAppPydollContext(Context):
    
    config:ClassVar[dict] = {
        "lang": "en-US",
        "accept_lang": "en-US,en;q=0.9",
        "timezone": "America/New_York",
    }
    
        
    def init(self, ping_interval_seconds: int = 5, timeout_seconds: int = 5):
        self.ping_interval = ping_interval_seconds
        self.timeout = timeout_seconds
        self.browser: Chrome | None = None
        self.tab: Tab | None = None
        self.lock = asyncio.Lock()
        self._watchdog_task: asyncio.Task | None = None
        self._quque = WebAppQueue()
        self.lang = None
        self._chrome_options = None
        
    async def lanch(self, is_lock = True):
        async def lanch_func():
            self._chrome_options = await self.make_chrome_options()
            self.browser = Chrome(options = self._chrome_options)
            self.tab = await self.browser.start()
            self.tab = await self.get_new_whatsapp_tab(self.tab)
            is_find = False
            while not is_find:
                for lang, key_word in Language.get_all_languages("load_whatsapp_key_word"):
                    res = await self.tab.find(text=key_word, raise_exc = False, timeout=5)
                    if res:
                        is_find = True
                        self.lang = Language(lang = lang)
                        log.info(f"WhatsApp Web readyState is complete in {lang} mode.")
                        break
            
            
            self._watchdog_task = asyncio.create_task(self._watchdog_loop())
            
        if is_lock:
            async with self.lock:
                await lanch_func()
        else:
            await lanch_func()
            
    async def is_lanch(self):
        return self._watchdog_task and not self._watchdog_task.done()
            
    async def close(self):
        if self._watchdog_task:
            self._watchdog_task.cancel()
        
        await self._quque.cancel()
        
        if self.browser:
            await self.browser.close()
            try:await self.browser.stop()
            except exc.BrowserNotRunning:pass
            await self.kill_browser()
        self.browser = None
        self.tab = None
        
        

       
                
    @classmethod
    async def make_chrome_options(cls):
        def get_offset(timezone_id: str):
            target_tz = ZoneInfo(timezone_id)
            now_in_target_tz = datetime.now(target_tz)
            return int(raise_none(now_in_target_tz.utcoffset()).total_seconds() / 60)
    
        cls.config["tz_offset"] =  get_offset(cls.config["timezone"]) 

        options = ChromiumOptions()
        USER_CHROME_DIR = os.environ["USER_CHROME_DIR"]
        CHROME_PROFILE = os.environ["CHROME_PROFILE"]
        
        user_chrome_path = Path(USER_CHROME_DIR).absolute()
        
        if not user_chrome_path.exists():
            raise FileNotFoundError(f"USER_CHROME_DIR: {USER_CHROME_DIR} not found")
        
        options.add_argument(f"--user-data-dir={user_chrome_path!s}")
        options.add_argument(f"--profile-directory={CHROME_PROFILE}")
        # options.add_argument(f"--proxy-server={PSIPHON_PROXIES['socks5']}")
        
         # Prevent Background & Timer Throttling
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-background-media-suspend")

        # Prevent CDP / IPC Freezing
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-gpu-watchdog")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-hang-monitor")
        
        if is_in_container():
            options.add_argument('--no-sandbox')
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

        disabled_features = [
            "CalculateNativeWinOcclusion",
            "WebContentsDiscard",
            "TrimOnMemoryPressure",
            "BackForwardCache",
            "IntensiveWakeUpThrottling",
            "BatterySaverModeAlignWakeUps"
        ]
        options.add_argument(f"--disable-features={','.join(disabled_features)}")

        # options.add_argument(f"--lang={cls.config['lang']}")
        # options.add_argument(f"--tz={cls.config['timezone']}")
        # options.set_accept_languages(cls.config['accept_lang'])

        options.browser_preferences = {
            'profile': {
                'default_content_setting_values': {
                    'cookies': 1,
                    'images': 1,
                    'javascript': 1,
                    'notifications': 1, 
                }
            }
        }

        return options
    
    
    async def get_new_whatsapp_tab(self, tab:Tab|None = None):
        if not tab:
            tab = await self.browser.new_tab() # type: ignore
        await tab._connection_handler.execute_command({
            'method': 'Emulation.setTimezoneOverride',
            'params': {
                'timezoneId': self.config['timezone']
            }
        })
        
        await tab._connection_handler.execute_command({
            'method': 'Emulation.setLocaleOverride',
            'params': {
                'locale': self.config['lang']
            }
        })
        @retry(max_retries=5, delay=5, exceptions = pydoll.exceptions.NavigationError) # type: ignore
        async def retry_func():
            await tab.go_to("https://web.whatsapp.com/")
            
        await retry_func()
        return tab
    
    async def _watchdog_loop(self):
        try:
            while True:
                await asyncio.sleep(self.ping_interval)
                is_alive = await self.assert_alive()
                if not is_alive:
                    await self.close()
                    await self.lanch()
                    self._quque.start()
                    return
        except asyncio.CancelledError:
            log.info("Watchdog loop canceled.")

    async def assert_alive(self):
        if not self.tab:
            raise RuntimeError("Browser tab is None.")
        
        try:
            is_alive = await asyncio.wait_for(
                self.tab.execute_script("return document.readyState === 'complete';"),
                timeout=self.timeout
            )
            if not is_alive:
                raise RuntimeError("WhatsApp Web readyState is not complete.")
            return True
        except TimeoutError:
            log.error("Browser frozen: CDP command timed out during heartbeat.")
            return False
            
    async def kill_browser(self):
        pid = self.browser._browser_process_manager._process.pid # type: ignore
        try:
            parent = psutil.Process(pid)
        except psutil.NoSuchProcess:
            return
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
        log.info(f"Forcefully killed frozen Chrome instance (PID: {pid})")
        