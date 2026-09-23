import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv

load_dotenv()

api_id   = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")

async def main():
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start()
    print("\nYOUR SESSION STRING (copy this):")
    print(client.session.save())
    await client.disconnect()

asyncio.run(main())