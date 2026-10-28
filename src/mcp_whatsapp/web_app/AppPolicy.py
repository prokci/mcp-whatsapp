import asyncio
import random


class AppPolicy:
    humanize: bool = True
    need_user_confirmation: bool = True
    task_delay = (5, 10)
    steps_delay = (1, 5)
    action_delay = (0.1, 1)
    element_timeout = 5
    
    async def delay_between_tasks(self,):
        await asyncio.sleep(random.uniform(*self.task_delay))
        
    async def delay_between_steps(self,):
        await asyncio.sleep(random.uniform(*self.steps_delay))
        
    async def delay_between_actions(self,):
        await asyncio.sleep(random.uniform(*self.action_delay))
        
        