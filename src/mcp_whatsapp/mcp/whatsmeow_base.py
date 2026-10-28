from sqlalchemy import (
    Column,
    MetaData,
    Table,
    Text,
)

metadata_obj = MetaData()

whatsmeow_lid_map = Table(
    "whatsmeow_lid_map",
    metadata_obj,
    Column("lid", Text, primary_key=True),
    Column("pn", Text, nullable=False),
)
whatsmeow_contacts = Table(
    "whatsmeow_contacts",
    metadata_obj,
    Column("our_jid", Text, primary_key=True),
    Column("their_jid", Text, primary_key=True),
    Column("first_name", Text),
    Column("full_name", Text),
    Column("push_name", Text),
    Column("business_name", Text),
    Column("redacted_phone", Text),
)