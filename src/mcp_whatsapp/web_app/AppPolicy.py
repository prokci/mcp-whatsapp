import asyncio
import random


class AppPolicy:
    humanize: bool = True
    need_user_confirmation: bool = True
    task_delay = (0.5, 1.0)
    steps_delay = (0.2, 0.5)
    action_delay = (0.1, 0.2)
    element_timeout = 10
    
    async def delay_between_tasks(self,):
        await asyncio.sleep(random.uniform(*self.task_delay))
        
    async def delay_between_steps(self,):
        await asyncio.sleep(random.uniform(*self.steps_delay))
        
    async def delay_between_actions(self,):
        await asyncio.sleep(random.uniform(*self.action_delay))
        
        