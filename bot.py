import re
import asyncio
from telethon import TelegramClient, events
from dotenv import load_dotenv
import os

load_dotenv()

api_id   = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")
channel  = os.getenv("TARGET_CHANNEL")

client = TelegramClient("session", api_id, api_hash)

# --- Parsing ---

NO_COMP = {"none", "nil", "no reward stated", "no reward", "n/a", ""}

def parse_duration_line(line):
    value = re.sub(r'^Duration:\s*', '', line, flags=re.IGNORECASE).strip()
    parts = value.split(',', 1)
    study_type_raw = parts[1].strip() if len(parts) > 1 else ""
    lower = study_type_raw.lower()
    if "online survey" in lower:
        study_type = "Online Survey"
    elif "online interview" in lower:
        study_type = "Online Interview"
    else:
        study_type = "Other"
    return {"duration_raw": parts[0].strip(), "study_type": study_type}

def parse_compensation_line(line):
    raw = re.sub(r'^Compensation:\s*', '', line, flags=re.IGNORECASE).strip()
    if raw.lower() in NO_COMP:
        return {"has_compensation": False, "amount": None, "numeric_amount": None}
    match = re.search(r'(?:SGD|S\$|\$)\s*(\d+(?:\.\d+)?)', raw, re.IGNORECASE)
    numeric = float(match.group(1)) if match else None
    return {"has_compensation": True, "amount": raw, "numeric_amount": numeric}

def parse_post(raw):
    lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
    result = {
        "title": None, "institution": None,
        "duration_raw": None, "study_type": None,
        "has_compensation": None, "amount": None,
        "numeric_amount": None, "deadline": None,
    }
    for line in lines:
        if result["title"] is None and not line.lower().startswith("by "):
            result["title"] = line
        elif line.lower().startswith("by "):
            result["institution"] = line[3:].strip()
        elif re.match(r'^Duration:', line, re.IGNORECASE):
            result.update(parse_duration_line(line))
        elif re.match(r'^Compensation:', line, re.IGNORECASE):
            result.update(parse_compensation_line(line))
        elif "#Open till" in line:
            result["deadline"] = line.replace("#Open till", "").strip()
    return result if result["title"] else None

def is_relevant(post):
    return (
        post.get("study_type") == "Online Survey"
        and post.get("has_compensation") is True
        and post.get("numeric_amount") is not None
    )

def format_message(post):
    return (
        f"🔔 New Paid Online Survey!\n\n"
        f"📌 {post['title']}\n"
        f"🏫 {post['institution']}\n"
        f"⏱ Duration: {post['duration_raw']}\n"
        f"💰 Compensation: {post['amount']}\n"
        f"📅 Open till: {post['deadline']}"
    )

# --- Live listener ---

async def main():
    async with client:
        @client.on(events.NewMessage(chats=channel))
        async def handler(event):
            post = parse_post(event.raw_text)
            if post and is_relevant(post):
                await client.send_message("me", format_message(post))
                print(f"[SENT] {post['title']}")
            else:
                print(f"[SKIPPED]")

        print(f"Watching {channel}... Ctrl+C to stop.")
        await client.run_until_disconnected()

asyncio.run(main())