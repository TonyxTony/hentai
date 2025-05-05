from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import time
from threading import Thread
from flask import Flask

API_ID = 20321575
API_HASH = "2d4ec904c4e3fa9e3c9ed543a1b852db"
STRING_SESSION = "1BVtsOI0BuzNK9FxskzAP5WRkZeWukmMPAT9NsScus0nMstASvKIldWXkx0QRRETA3U6Mzppsxlcc87BB4XVIlJtHDxF5CJIoCcsvHTD0k3p8BVSxsY7fNuYJsNI6_BmNv-C896Tcg649_yXO5BTCg6CfBu0SSuLdUATPmRvh0nKYYVplxamGh9_kcWdP60flpooqeSga0i8M9qfuhrUQq1Atl3IS652EKcjs1mQVrCnFQMXVNCXX0CGwrGK3nGXuk_501-IGKdR1eEmb6hpZcfbPT4CPv7NUkCcgfG5lbF8CEYWlnGsXyXJ2FELvyo10rpRb7eObdr_UF4maa8MuwwgkuscGl_8="
BOT_USERNAME = "patrickstarsrobot"
BUTTON_TEXT = "✨ Кликер"

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

server = Flask(__name__)

@server.route("/")
def home():
    return "Bot is running"

def run_flask():
    server.run(host="0.0.0.0", port=8080)

async def press_clicker():
    try:
        async for msg in client.iter_messages(BOT_USERNAME, limit=5):
            if msg.buttons:
                for row in msg.buttons:
                    for i, button in enumerate(row):
                        if button.text.strip() == BUTTON_TEXT.strip():
                            await msg.click(i)
                            return True
        return False
    except:
        return False

async def main():
    await client.start()
    while True:
        found = await press_clicker()
        if not found:
            await client.send_message(BOT_USERNAME, "/start")
            await asyncio.sleep(5)
            await press_clicker()
        await asyncio.sleep(605)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    with client:
        client.loop.run_until_complete(main())
