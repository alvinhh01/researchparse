import re
import asyncio
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

api_id         = int(os.getenv("TG_API_ID"))
api_hash       = os.getenv("TG_API_HASH")
channel        = os.getenv("TARGET_CHANNEL")
session_string = os.getenv("SESSION_STRING")

def get_compensation_amount(text):
    match = re.search(
        r'(?:(?:SGD|S\$|\$)\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:SGD|S\$|\$))',
        text, re.IGNORECASE
    )
    if match:
        return float(match.group(1) or match.group(2))
    return None

async def main():
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.connect()

    @client.on(events.NewMessage(chats=channel))
    async def handler(event):
        text = event.raw_text

        is_online = bool(re.search(
            r'Duration:.*,\s*(?:online|survey|zoom|video|prescreen|call)',
            text, re.IGNORECASE
        ))

        has_sgd = bool(re.search(
            r'(\d+\s*(?:SGD|S\$|\$)|(?:SGD|S\$|\$)\s*\d+|NTUC|PayNow)',
            text, re.IGNORECASE
        ))

        if has_sgd and is_online:
            amount = get_compensation_amount(text)
            if amount and amount >= 100:
                await client.send_message("me", f"🚨 HIGH PAY ALERT (SGD {amount:.0f}+)!\n\n{text}")
            else:
                await client.send_message("me", f"🔔 New paid survey!\n\n{text}")

    print("Watching... Ctrl+C to stop.")
    await client.run_until_disconnected()

asyncio.run(main())