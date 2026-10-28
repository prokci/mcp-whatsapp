import asyncio
import logging

from src.mcp_whatsapp.tasks.Task import Task
from src.mcp_whatsapp.utils.patern_classes import Singleton
from src.mcp_whatsapp.web_app.AppPolicy import AppPolicy

log = logging.getLogger(__name__)

class WebAppQueue(Singleton):
    def init(self):
        self.terminate = False
        self.queue: asyncio.Queue[tuple[Task, asyncio.Future]] = asyncio.Queue() 
        self.policy = AppPolicy()
        self.loop_task = None 
    
    def start(self):
        self.terminate = False 
        async def loop():
            task, future = None, None
            try:
                while not self.terminate:
                    task, future = await self.queue.get()
                    try:
                        result = await task.execute(self.policy)
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)
                        log.exception(f"Task {task.__class__.__name__}({task.__dict__}) failed.")
                    finally:
                        self.queue.task_done()
                        log.debug(f"Task {task.__class__.__name__}({task.__dict__}) executed.")
                        
                    await self.policy.delay_between_tasks()
            except asyncio.CancelledError:
                log.error("WebAppQueue loop canceled.")
                if task and not future.done(): # type: ignore
                    await self.queue.put((task, future)) # type: ignore
                    log.debug(f"Task {task.__class__.__name__}({task.__dict__}) re-enqueued.")
            except Exception as e:
                log.error(e)
                raise
            finally:
                log.info("WebAppQueue loop finished.")
                
        self.loop_task = asyncio.create_task(loop())
            
    async def end(self):
        self.terminate = True
        await self.loop_task # type: ignore
        
    async def cancel(self):
        self.terminate = True
        if self.loop_task and not self.loop_task.done():
            self.loop_task.cancel()
            try:
                await self.loop_task
            except asyncio.CancelledError:
                pass
    
 
            
    async def execute_task(self, task: Task):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        await self.queue.put((task, future))
        return await future
    
    async def excute_task_no_wait(self, task: Task):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        await self.queue.put((task, future))