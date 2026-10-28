from sqlalchemy import (
    select,
)

from src.mcp_whatsapp.mcp.whatsmeow_base import whatsmeow_contacts, whatsmeow_lid_map


async def get_number_push_name_from_lid(session, lid):
    lid = lid if lid.find("@") == -1 else lid[:lid.find("@")]
    lid_query = select(whatsmeow_lid_map).where(whatsmeow_lid_map.c.lid == lid)
    lid_result = await session.execute(lid_query)
    lid_row = lid_result.first()
    number = lid_row.pn if lid_row else lid
    contact_query = select(whatsmeow_contacts).where(whatsmeow_contacts.c.their_jid.like(f"{number}%"))
    contact_result = await session.execute(contact_query)
    contact_row = contact_result.first()
    pushname = contact_row.push_name if contact_row else None
    return number, pushname


def get_text_from_message(message):
    text = ""
    if message.conversation:
        text = message.conversation
    elif message.extendedTextMessage and message.extendedTextMessage.text:
        text = message.extendedTextMessage.text
    elif str(message.templateMessage) != '':
        if message.templateMessage.hydratedTemplate:
            text = message.templateMessage.hydratedTemplate.hydratedContentText
        elif message.templateMessage.hydratedFourRowTemplate:
            text = message.templateMessage.hydratedFourRowTemplate.hydratedContentText
    elif message.interactiveMessage:
        text = message.interactiveMessage.body.text
        
    return text