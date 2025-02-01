from pyrogram import Client, filters
import os
import time
from threading import Thread
from flask import Flask
from pyrogram.types import Message
import asyncio
from pymongo import MongoClient
import re
from PIL import Image
import imagehash

HANDLER = "."
API_ID = "25321403"
API_HASH = "0024ae3c978ba534b1a9bffa29e9cc9b"
BOT_TOKEN = os.getenv('BOT_TOKEN', '7373345228:AAFzQdntjOGtHaEpsHbVYUsL8xQMacfd8G4')
MONGO_URI = os.getenv('MONGO_URI', "mongodb+srv://Lakshay3434:Tony123@cluster0.agsna9b.mongodb.net/?retryWrites=true&w=majority")
hexa_bot = 572621020

if not MONGO_URI:
    raise Exception("MONGO_URI environment variable is not set")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client['grabber_db']
hexa_status = db['hexa_hashes']

app = Client(
    "word9",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

server = Flask(__name__)

@server.route("/")
def home():
    return "Bot is running"

ALLOWED_CHAT_IDS = [
    -1002136935704, -1002244785813, -1002200182279, -1002232771623,
    -1002241545267, -1002180680112, -1002152913531, -1002244523802,
    -1002159180828, -1002186623520, -1002220460503
]

def hash_image(image_path):
    with Image.open(image_path) as img:
        hash_value = imagehash.phash(img)
        return str(hash_value)

@app.on_message(filters.user(hexa_bot) & filters.photo)
async def handle_hexa_bot(client, message):
    try:
        file_path = await message.download()
        image_hash_value = hash_image(file_path)
        existing_doc = hexa_status.find_one({"image_hash": image_hash_value})

        if existing_doc:
            pokemon_name = existing_doc.get("pokemon_name")
            if pokemon_name:
                await message.reply(f"{pokemon_name}")
            else:
                print(f"No Pokémon name found for image hash: {image_hash_value}")
        else:
            print(f"Image hash not found in DB: {image_hash_value}") 
    except Exception as e:
        print(f"Error handling hexa_bot: {e}")

@app.on_message(filters.photo)
async def capture_pokemon_data(client, message):
    try:
        if message.photo and message.caption:
            pokemon_name_match = re.search(r"The pokemon was (\w+)", message.caption)
            
            if pokemon_name_match:
                pokemon_name = pokemon_name_match.group(1).strip()
                file_path = await client.download_media(message.photo)
                image_hash_value = hash_image(file_path)

                existing_doc = hexa_status.find_one({"image_hash": image_hash_value})
                if existing_doc:
                    await message.reply(f"The image `{image_hash_value}` already exists in DB!")
                else:
                    hexa_status.update_one(
                        {"image_hash": image_hash_value},
                        {"$set": {"image_hash": image_hash_value, "pokemon_name": pokemon_name}},
                        upsert=True
                    )
                    await message.reply(f"Stored image `{image_hash_value}` with Pokémon name `{pokemon_name}` Added in DB!")
            else:
                await message.reply("No valid Pokémon name found in the message caption.")
        else:
            await message.reply("No valid photo or caption found.")
    except Exception as e:
        await message.reply(f"An error occurred while processing the request: {str(e)}")
        
@app.on_message(filters.command("total_pokemon", HANDLER))
async def total_pokemon(client: Client, message: Message):
    try:
        total_pokemon_count = hexa_status.count_documents({})
        await message.reply(f"Pokémon in the database `{total_pokemon_count}` Otey!")
    except Exception as e:
        await message.reply(f"An error occurred while fetching the total Pokémon count: {str(e)}")

@app.on_message(filters.command("ding", HANDLER))
async def ping_pong(client: Client, message: Message):
    try:
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
    except Exception as e:
        await message.reply(f"An error occurred in the ping-pong process: {str(e)}")

def format_uptime(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

def run():
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    bot_start_time = time.time()
    t = Thread(target=run)
    t.start()
    app.run()
