import asyncio
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path

import anyio
import neonize
from neonize.aioze.client import NewAClient
from neonize.aioze.events import HistorySyncEv, MessageEv

from src.mcp_whatsapp.data_base.DBContext import DBContext
from src.mcp_whatsapp.mcp.MessageBroadcaster import MessageBroadcaster
from src.mcp_whatsapp.mcp.MessageRecord import MessageRecord
from src.mcp_whatsapp.mcp.whatsmeow_funcs import (
    get_number_push_name_from_lid,
    get_text_from_message,
)
from src.mcp_whatsapp.web_app.NeonizeContext import NeonizeContext

neonize_context = NeonizeContext()

BASE_DIR = Path(os.path.join(".", ".data", "dowland"))
BASE_DIR.mkdir(parents=True, exist_ok=True)

db_context = DBContext()

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

broadcaster = MessageBroadcaster()

@neonize_context.neonize_client.event(MessageEv)
async def on_message(client: NewAClient, event: MessageEv):
    async with db_context.get_session() as session:
        number, pushname = await get_number_push_name_from_lid(session, event.Info.MessageSource.Chat.User)
        data = {
            "pushname": pushname,
            "sender": number,
            "is_from_me": event.Info.MessageSource.IsFromMe,
            "text": get_text_from_message(event.Message),
            "chat_user": event.Info.MessageSource.Chat.User
        }
        
        file_bytes = None
        try:
            file_bytes = await client.download_any(event.Message)
        
            filename = "unknown"
            if event.Message.documentMessage and event.Message.documentMessage.fileName:
                filename = event.Message.documentMessage.fileName
                log.debug(f"Downloading document: {filename}...")
            elif event.Message.imageMessage and event.Message.imageMessage.URL:
                caption = event.Message.imageMessage.caption
                log.debug(f"Downloading image: '{caption}'")
                filename = f"image_{event.Info.ID}.jpg"
            elif event.Message.audioMessage and event.Message.audioMessage.URL:
                is_voice_note = event.Message.audioMessage.PTT 
                log.debug(f"Downloading {'Voice Note' if is_voice_note else 'Audio File'}...")
                filename = f"audio_{event.Info.ID}.ogg"
                    
            i = 0
            while True:
                if i > 0:
                    path = BASE_DIR / f"{filename[:filename.rfind('.')]}({i}){filename[filename.rfind('.'):]}"
                else:
                    path = BASE_DIR / filename
                i += 1
                if not path.exists():
                    break
            
            
            async with await anyio.open_file(path, 'wb') as f:
                await f.write(file_bytes)
                
            log.debug(f"Downloaded on {path}")
            data["file_path"] = str(path.absolute())
        except neonize.exc.DownloadError as e: # type: ignore
            log.debug(f'message dont have file {e}')
        
        new_msg = MessageRecord(
            message_id=event.Info.ID,
            pushname=data["pushname"],
            sender=data["sender"],
            is_from_me=data["is_from_me"],
            text=data["text"],
            chat_user=data["chat_user"],
            file_path=data.get("file_path"),
            version=db_context.current_db_version,
            datetime=datetime.fromtimestamp(event.Info.Timestamp / 1000, tz=UTC)
        )
        session.add(new_msg)
        await session.commit()
        
    broadcaster.broadcast(data)
    log.debug(f"Broadcasted new message {json.dumps(data, indent=4, ensure_ascii=False)}")

is_database_updated = False
database_updated_lock = asyncio.Lock()

@neonize_context.neonize_client.event(HistorySyncEv)
async def on_history_sync(client: NewAClient, event: HistorySyncEv):
    global is_database_updated
    sync_type_str = str(event.Data.syncType)
    log.debug(f"WhatsApp is currently syncing history... Type: {sync_type_str}")

    async with database_updated_lock:
        if event.Data.syncType in [3] and len(event.Data.conversations) > 0:
            if not is_database_updated:
                db_context.current_db_version += 1
                is_database_updated = True
                log.info(f"Mapping {len(event.Data.conversations)} conversations. DB Version is now: {db_context.current_db_version}")
            else:
                log.info(f"Add new {len(event.Data.conversations)} conversations.")

            async with db_context.get_session() as session:
                for conv in event.Data.conversations:
                    chat_user = conv.ID
                    for history_msg in conv.messages:
                        msg_info = history_msg.message
                        timestamp = datetime.fromtimestamp(msg_info.messageTimestamp, tz=UTC)
                        if msg_info.messageTimestamp == 0:
                            raise ValueError("Message timestamp is 0. This is not expected.")
                        key = msg_info.key
                        
                        message_id = key.ID
                        is_from_me = key.fromMe
                        
                        sender = key.remoteJID
                        
                        number, pushname = await get_number_push_name_from_lid(session, sender)
                        text = get_text_from_message(msg_info.message)
                        
                        new_msg = MessageRecord(
                            message_id=message_id,
                            pushname=pushname,
                            sender=number,
                            is_from_me=is_from_me,
                            text=text,
                            chat_user=chat_user[:chat_user.find('@')],
                            file_path=None,
                            version=db_context.current_db_version,
                            datetime=datetime.fromtimestamp(msg_info.userReceipt[0].receiptTimestamp, tz=UTC) if msg_info.userReceipt and msg_info.userReceipt[0].receiptTimestamp != 0 else timestamp
                        )
                        session.add(new_msg)
                
                await session.commit()
                print("Successfully saved all history messages to database.")