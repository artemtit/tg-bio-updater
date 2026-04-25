import os
import asyncio
import logging
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telethon import TelegramClient, functions

# ========= CONFIG =========
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

UPDATE_HOUR = int(os.getenv("UPDATE_HOUR", "7"))
UPDATE_MINUTE = int(os.getenv("UPDATE_MINUTE", "0"))

QUOTES_FILE = "quotes.txt"
STATE_FILE = "state.json"
LAST_FILE = "last.txt"

MAX_LEN = 70

TZ = ZoneInfo("Europe/Moscow")

# ========= LOGGING =========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# ========= HELPERS =========

def load_quotes():
    if not os.path.exists(QUOTES_FILE):
        raise FileNotFoundError("quotes.txt not found")

    with open(QUOTES_FILE, "r", encoding="utf-8") as f:
        quotes = [q.strip() for q in f.readlines() if q.strip()]

    if not quotes:
        raise ValueError("quotes.txt is empty")

    return quotes


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"index": 0}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def get_next_quote(quotes):
    state = load_state()
    index = state["index"]

    if index >= len(quotes):
        index = 0

    quote = quotes[index]

    state["index"] = index + 1
    save_state(state)

    return quote


def trim_quote(q):
    return q[:MAX_LEN]


def should_update(new_quote):
    if not os.path.exists(LAST_FILE):
        return True

    with open(LAST_FILE, "r") as f:
        last = f.read().strip()

    return last != new_quote


def save_last(quote):
    with open(LAST_FILE, "w") as f:
        f.write(quote)


def seconds_until_target(hour, minute):
    now = datetime.now(TZ)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if target <= now:
        target += timedelta(days=1)

    return (target - now).total_seconds()


# ========= MAIN LOOP =========

async def run(client):
    quotes = load_quotes()

    while True:
        try:
            wait_time = seconds_until_target(UPDATE_HOUR, UPDATE_MINUTE)
            logging.info(f"Sleeping {int(wait_time)} seconds until next update (MSK)")
            await asyncio.sleep(wait_time)

            quote = get_next_quote(quotes)
            quote = trim_quote(quote)

            if not should_update(quote):
                logging.info("Quote is same as last, skipping")
                continue

            await client(functions.account.UpdateProfileRequest(
                about=quote
            ))

            save_last(quote)
            logging.info(f"Bio updated: {quote}")

        except Exception as e:
            logging.error(f"Error: {e}")
            await asyncio.sleep(60)


async def main():
    client = TelegramClient("session", API_ID, API_HASH)

    await client.start()

    me = await client.get_me()
    logging.info(f"Logged in as: {me.username or me.id}")

    await run(client)


if __name__ == "__main__":
    asyncio.run(main())
