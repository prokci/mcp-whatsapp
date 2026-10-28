import asyncio
import logging

from dotenv import load_dotenv

load_dotenv()

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from sqlalchemy import select

from src.mcp_whatsapp.data_base.DBContext import DBContext
from src.mcp_whatsapp.mcp.MessageRecord import MessageRecord
from src.mcp_whatsapp.mcp.RawASGIResponse import RawASGIResponse
from src.mcp_whatsapp.mcp.whatsmeow_events import broadcaster, neonize_context
from src.mcp_whatsapp.tasks.PydollSendMessage import (
    PydollSendFile,
    PydollSendMessage,
)
from src.mcp_whatsapp.utils.funcs import to_jsonable
from src.mcp_whatsapp.web_app.PydollContext import WhatsAppPydollContext
from src.mcp_whatsapp.web_app.WebAppQueue import WebAppQueue

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

db_context = DBContext()

#FASTMCP
mcp = FastMCP("whatsapp-pydoll-mcp")

@mcp.tool()
async def send_whatsapp_message(phone_number: str, message: str, need_user_confirmation: bool = False) -> str:
    """
    Sends a WhatsApp text message to a specific phone number.
    """
    
    task = PydollSendMessage(
        message=message,
        number=phone_number,
        need_user_confirmation=need_user_confirmation
    )
    
    await WebAppQueue().excute_task_no_wait(task)
    answer = f"Make a plan to sent message to {phone_number}."
    log.info(answer)
    return answer


@mcp.tool()
async def send_whatsapp_file(phone_number: str, file_path: str, message: str = "", need_user_confirmation: bool = False) -> str:
    """
    Sends a file (PDF, DOCX, etc.) over WhatsApp.
    """
    target_path = Path(file_path)
    if not target_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist.")

    task = PydollSendFile(
        file_path=target_path,
        number=phone_number,
        message=message,
        need_user_confirmation=need_user_confirmation
    )
    await WebAppQueue().excute_task_no_wait(task)
    answer = f"Make a plan to sent file '{target_path.name}' to {phone_number}."
    log.debug(answer)
    return answer

@mcp.tool()
async def get_chat_history(phone_number: str) -> str:
    """
    Retrieves the chat history for a specific phone number.
    """
    async with db_context.get_session() as session:
        history = await session.execute(
            select(MessageRecord)
            .where(
                MessageRecord.sender == phone_number, 
                MessageRecord.version == db_context.current_db_version
            )
            .order_by(MessageRecord.datetime)
        )
        records = history.scalars().all()
        
    records_json = [
        {str(key): to_jsonable(value) for key, value in record.__dict__.items() if not key.startswith('_')} 
        for record in records
    ]

    answer = json.dumps(records_json, indent=4, ensure_ascii=False)
    log.debug(answer)
    return answer

mcp_sse = SseServerTransport("/messages")


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    context = WhatsAppPydollContext()
    queue = WebAppQueue()
    await db_context.launch()
    await context.lanch()
    queue.start()
                        
    await neonize_context.lanch()

    yield
    
    broadcaster.close_all()
    await neonize_context.cancel()
    await queue.cancel()
    await context.close()
    
#FASTAPI
app = FastAPI(lifespan=app_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/sse")
async def handle_mcp_sse(request: Request):
    """MCP Stream for n8n to connect to Tools."""
    try:
        async with mcp_sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await mcp._mcp_server.run(
                streams[0], streams[1], mcp._mcp_server.create_initialization_options()
            )
    except asyncio.CancelledError:
        log.debug("MCP SSE Client disconnected gracefully.")
        
    return RawASGIResponse()

@app.post("/messages")
async def handle_mcp_messages(request: Request):
    """MCP endpoint for Tool Calls."""
    
    body = await request.body()
    received = False
    async def mock_receive():
        nonlocal received
        if not received:
            received = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    try:
        await mcp_sse.handle_post_message(request.scope, mock_receive, request._send)
    except asyncio.CancelledError:
        log.error("MCP Messages Client disconnected gracefully.")
        
    return RawASGIResponse()

@app.get("/whatsapp-events")
async def whatsapp_events_stream():
    """
    n8n will connect an "SSE Trigger Node" to this endpoint.
    It pushes incoming WhatsApp messages instantly.
    """
    async def event_generator():
        try:
            async with broadcaster.subscribe() as q:
                while True:
                    message_dict = await q.get()
                    if message_dict is None:
                        break
                    
                    json_data = json.dumps(message_dict, ensure_ascii=False)
                    yield f"event: message\ndata: {json_data}\n\n"
                    
        except asyncio.CancelledError:
            log.info("Client disconnected from the WhatsApp event stream.")

    return StreamingResponse(event_generator(), media_type="text/event-stream")