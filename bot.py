from pyrogram import Client, filters
import os
import time
from threading import Thread
from flask import Flask
from pyrogram.types import Message
import asyncio
from pymongo import MongoClient
import re

HANDLER = "."
API_ID = "25321403"
API_HASH = "0024ae3c978ba534b1a9bffa29e9cc9b"
BOT_TOKEN = "7624598210:AAH7GOrCVWiFp8_khJa_Mwh4oEUZxeTHORQ"
MONGO_URI = os.getenv('MONGO_URI', "mongodb+srv://Lakshay3434:Tony123@cluster0.agsna9b.mongodb.net/?retryWrites=true&w=majority")

if not MONGO_URI:
    raise Exception("MONGO_URI environment variable is not set")

print(f"Connected to MongoDB at: {MONGO_URI}")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['grabber_db']
hexa_db_collection = db['hexa_db']
app = Client(
    "word9",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

server = Flask(__name__)

@server.route("/")
def home():
    return "Bot is running"

@app.on_message(filters.chat(-1002136935704) & filters.user(572621020))
async def capture_pokemon_data(client, message):
    try:
        if message.reply_to_message and message.reply_to_message.photo:
            replied_message = message.reply_to_message
            file_unique_id = replied_message.photo.file_unique_id

            if "The pokemon was" in message.text:
                pokemon_name_match = re.search(r"The pokemon was (.*)", message.text)
                if pokemon_name_match:
                    pokemon_name = pokemon_name_match.group(1).strip()
                    pokemon_name = re.sub(r"(\*{2})(.*?)(\*{2})", r"\2", pokemon_name)
                    pokemon_name = re.sub(r"(\*{1})(.*?)(\*{1})", r"\2", pokemon_name)

                    existing_doc = hexa_db_collection.find_one({"file_unique_id": file_unique_id})
                    if existing_doc:
                        await message.reply(f"The file unique ID `{file_unique_id}` already exists in DB!")
                    else:
                        hexa_db_collection.update_one(
                            {"file_unique_id": file_unique_id},
                            {"$set": {"file_unique_id": file_unique_id, "pokemon_name": pokemon_name}},
                            upsert=True
                        )
                        await message.reply(f"Stored `{file_unique_id}` with Pokémon name `{pokemon_name}` Added in DB!")
    except Exception as e:
        await message.reply("An error occurred while processing the request.")
        print(f"Error in capture_pokemon_data: {e}")

@app.on_message(filters.command("getid", HANDLER))
async def get_photo_id(client, message):
    try:
        if message.reply_to_message and message.reply_to_message.photo:
            file_unique_id = message.reply_to_message.photo.file_unique_id
            await message.reply(f"The ID of the photo is: `{file_unique_id}`")
        else:
            await message.reply("reply to a photo to get ID.")
    except Exception as e:
        await message.reply("An error occurred.")
        print(f"Error in get_photo_id: {e}")

@app.on_message(filters.command("ding", HANDLER))
async def ping_pong(client: Client, message: Message):
    start_time = time.time()
    msg = await message.reply_text("Ping...")
    await msg.reply("✮ᑭｴƝGing...✮")
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000, 3)
    
    uptime_seconds = time.time() - bot_start_time
    uptime_str = format_uptime(uptime_seconds)
    
    await msg.reply(f"I Aᴍ Aʟɪᴠᴇ Mᴀꜱᴛᴇʀ\n⋙ 🔔 ᑭｴƝG: `{ping_time}` ms\n⋙ 🕒 Uptime: `{uptime_str}`")
    try:
        await message.delete()
    except Exception as e:
        print(f"Error deleting message: {e}")

def format_uptime(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"
        
def run():
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))  # Ensure to use port 8080

if __name__ == "__main__":
    bot_start_time = time.time()
    t = Thread(target=run)
    t.start()
    app.run()
