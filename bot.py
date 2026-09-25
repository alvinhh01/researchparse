import re
import asyncio
import os
import sys
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import AuthKeyUnregisteredError
from dotenv import load_dotenv

load_dotenv()

api_id         = int(os.getenv("TG_API_ID"))
api_hash       = os.getenv("TG_API_HASH")
channel        = os.getenv("TARGET_CHANNEL")
session_string = os.getenv("SESSION_STRING", "").strip()

def get_compensation_amount(text):
    comp_line = re.search(r'Compensation:(.+)', text, re.IGNORECASE)
    if not comp_line:
        return None
    match = re.search(r'(\d+(?:\.\d+)?)', comp_line.group(1))
    return float(match.group(1)) if match else None

async def main():
    print(f"Session length: {len(session_string)}")
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    try:
        await client.connect()
        print("Connected successfully.")

        @client.on(events.NewMessage(chats=channel))
        async def handler(event):
            text = event.raw_text

            has_sgd = bool(re.search(
                r'(\d+\s*(?:SGD|S\$|\$)|(?:SGD|S\$|\$)\s*\d+|NTUC|PayNow)',
                text, re.IGNORECASE
            ))

            # Exit early if no compensation mentioned at all
            if not has_sgd:
                return

            is_online = bool(re.search(
                r'Duration:.*(?:online|survey|zoom|video|prescreen|call)',
                text, re.IGNORECASE
            ))

            amount = get_compensation_amount(text)

            # High pay alert fires regardless of online/in-person
            if amount and amount >= 100:
                await client.send_message(
                    "me",
                    f"🚨 HIGH PAY ALERT (SGD {amount:.0f}+)!\n\n{text}"
                )
            # Low pay only notified if it's an online/remote format
            elif is_online:
                await client.send_message(
                    "me",
                    f"🔔 New paid survey!\n\n{text}"
                )

        print(f"Watching {channel}... Ctrl+C to stop.")
        await client.run_until_disconnected()

    except AuthKeyUnregisteredError:
        print("Session expired. Regenerate SESSION_STRING.")
        sys.exit(0)
    finally:
        await client.disconnect()

asyncio.run(main())