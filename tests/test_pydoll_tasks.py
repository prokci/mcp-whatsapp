import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from pydoll import Key

from src.mcp_whatsapp.tasks.PydollSendMessage import (
    PydollSendFile,
    PydollSendMessage,
    PydollWalkToChat,
)
from src.mcp_whatsapp.utils.funcs import is_in_container, raise_none
from src.mcp_whatsapp.web_app.AppPolicy import AppPolicy
from src.mcp_whatsapp.web_app.PydollContext import WhatsAppPydollContext

assert load_dotenv(
    override=True,
    dotenv_path=Path(".env") if not is_in_container() else Path(".env.docker"),
)

TEST_PHONE_NUMBER = os.environ["TEST_PHONE_NUMBER"]





@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@asynccontextmanager
async def pydoll_context_maker(policy):
    try:
        context = WhatsAppPydollContext()
        await context.lanch()
        assert context.tab is not None
        yield context
    finally:
        await context.close()

@pytest_asyncio.fixture(scope="module")
async def policy():
    return AppPolicy()

@pytest_asyncio.fixture()
async def temp_file(tmp_path: Path,):
    dummy_file = tmp_path / "attachment_test.txt"
    dummy_file.write_text("Binary/raw text content for automated test.", encoding="utf-8")
    assert dummy_file.exists()
    yield dummy_file
    dummy_file.unlink()
    

async def check_pydoll_walk_to_chat(tab, test_message):
    compose_box = await tab.find(
        data_testid="conversation-compose-box-input",
        timeout=policy.element_timeout,
    )
    assert compose_box is not None

    inserted_text = await compose_box.text()
    assert inserted_text.strip() == test_message

@pytest.mark.asyncio
async def test_pydoll_walk_to_chat(policy: FastTestPolicy):
    async with pydoll_context_maker(policy) as pydoll_context:
        walk_task = PydollWalkToChat(TEST_PHONE_NUMBER)
        await walk_task.execute(policy)

        tab = raise_none(pydoll_context.tab)
        compose_box = await tab.find(
            data_testid="conversation-compose-box-input",
            timeout=policy.element_timeout,
        )
        assert compose_box is not None
        
        
async def pydoll_send_message_cheak(tab, test_message, policy):
    compose_box = await tab.find(
        data_testid="conversation-compose-box-input",
        timeout=policy.element_timeout,
    )
    assert compose_box is not None

    inserted_text = await compose_box.text()
    assert inserted_text.strip() == test_message


@pytest.mark.asyncio
async def test_pydoll_send_message_confirmation_and_cleanup(
    policy: FastTestPolicy,
):
    async with pydoll_context_maker(policy) as pydoll_context:
        tab = raise_none(pydoll_context.tab)
        test_message = "Test message for confirmation pipeline verification."

        send_task = PydollSendMessage(
            message=test_message,
            number=TEST_PHONE_NUMBER,
            need_user_confirmation=True,
        )
        await send_task.execute(policy)
        
        await pydoll_send_message_cheak(tab, test_message, policy)
        
        await tab.keyboard.hotkey(Key.CONTROL, Key.A)
        await policy.delay_between_steps()
        await tab.keyboard.press(Key.BACKSPACE)


async def check_pydoll_file_text(tab, caption_text, policy):
    
    caption_input = await tab.find(
        data_testid="media-caption-input-container",
        timeout=policy.element_timeout,
    )
    assert caption_input is not None

    inserted_caption = await caption_input.text()
    assert inserted_caption.strip() == caption_text

@pytest.mark.asyncio
async def test_pydoll_send_file(
    policy: FastTestPolicy,
    temp_file:Path
):
    async with pydoll_context_maker(policy) as pydoll_context:
        tab = raise_none(pydoll_context.tab)

        caption_text = "Verification caption attached."
        file_task = PydollSendFile(
            file_path=temp_file,
            number=TEST_PHONE_NUMBER,
            message=caption_text,
            need_user_confirmation=True,
        )
        
        await file_task.execute(policy)
        
        await check_pydoll_file_text(tab, caption_text, policy)
        
        await tab.keyboard.hotkey(Key.CONTROL, Key.A)
        await policy.delay_between_steps()
        await tab.keyboard.press(Key.BACKSPACE)
        

@pytest.mark.asyncio
async def test_pydoll_sendfile_and_send_message(
    policy: FastTestPolicy,
    temp_file:Path
):
    async with pydoll_context_maker(policy) as pydoll_context:
        tab = raise_none(pydoll_context.tab)
    
        caption_text = "Verification caption attached."
        file_task = PydollSendFile(
            file_path=temp_file,
            number=TEST_PHONE_NUMBER,
            message=caption_text,
            need_user_confirmation=True,
        )
        await file_task.execute(policy)
        
        await check_pydoll_file_text(tab, caption_text, policy)
        
        tab = raise_none(pydoll_context.tab)
        test_message = "Test message for confirmation pipeline verification."
    
        send_task = PydollSendMessage(
            message=test_message,
            number=TEST_PHONE_NUMBER,
            need_user_confirmation=True,
        )
        await send_task.execute(policy)
        
        await pydoll_send_message_cheak(tab, test_message, policy)
        
        await tab.keyboard.hotkey(Key.CONTROL, Key.A)
        await policy.delay_between_steps()
        await tab.keyboard.press(Key.BACKSPACE)