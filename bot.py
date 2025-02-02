from pyrogram import Client, filters
import os
import time
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram.types import Message
from PIL import Image
import imagehash
from flask import Flask
from threading import Thread
from pyrogram.types import Message
from pymongo import MongoClient
import re

API_ID = "25321403"
API_HASH = "0024ae3c978ba534b1a9bffa29e9cc9b"
SESSION = "BQFo9VAALAHKuEpUHoCealAw8UnYRDLqDtWWGapgMKyDdDNqgra2Gnd2EnVwpwP4PvujFjRM1Lltr8qh1DeTheqRukQF_GPApLhtS2eldLOBWrNYogDqIGr6ifgNnMI1oQAzsMkne0-wkGgrobJyMrKKV3oodj3ast0XVmvtyzh1cutBwm9Ob-BCjS22hK3E5R9A8fL0jKczAM0YgY82TCp2SU9qvCSjPaKASSN2w8HVt8HvWBJWd7tKf0i6VSwIN-5USPrAejxgxpEIwVumBZKTu6wpP2AeWADFN_OCaLTf_hD7klLnBffR6obkodGkIX-ZczkrmX7TstXICIT7jdcxwEutwgAAAAGRx5e_AA"
MONGO_URI = os.getenv('MONGO_URI', "mongodb+srv://Lakshay3434:Tony123@cluster0.agsna9b.mongodb.net/?retryWrites=true&w=majority")
hexa_bot = 572621020
ALLOWED_CHAT_IDS = [
    -1002136935704, -1002244785813, -1002200182279, -1002232771623,
    -1002241545267, -1002180680112, -1002152913531, -1002244523802,
    -1002159180828, -1002186623520, -1002220460503
]

mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client['grabber_db']
hexa_status = db['hexa_hashes']

app = Client(
    "word9",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION
)

server = Flask(__name__)

@server.route("/")
def home():
    return "Bot is running"

async def process_image_and_query_db_async(image_path):
    try:
        with Image.open(image_path) as img:
            image_hash_value = imagehash.phash(img)

        existing_doc = await hexa_status.find_one({"image_hash": str(image_hash_value)})

        if existing_doc:
            pokemon_name = existing_doc.get("pokemon_name")
            return pokemon_name
        else:
            return None
    except Exception as e:
        return None

@app.on_message(filters.chat(ALLOWED_CHAT_IDS) & filters.user(hexa_bot) & filters.regex(r"pokemon was"))
async def capture_pokemon(client, message):
    try:
        cleaned_text = re.sub(r'(\*{1,2})(.*?)\1', r'\2', message.text.strip())
        if "pokemon was" not in cleaned_text:
            return

        if message.reply_to_message and message.reply_to_message.photo:
            replied_message = message.reply_to_message
            file_id = replied_message.photo.file_id

            file_path = await client.download_media(replied_message.photo)
            full_text = message.text.strip()

            try:
                sent_photo_message = await client.send_photo(
                    '@Hexa_DB', 
                    file_path, 
                    caption=full_text
                )

                os.remove(file_path)

            except Exception as send_error:
                await message.reply(f"Error sending photo to @Hexa_DB: {send_error}")
                return

    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")

@app.on_message(filters.command("generate", HANDLER) & filters.me)
async def generate_file_ids(client: Client, message: Message):
    try:
        # Fetch all records from the hexa_status collection
        records = hexa_status.find({})

        # Initialize a counter for the successful operations
        processed_count = 0
        
        for record in records:
            image_hash = record.get("image_hash")
            pokemon_name = record.get("pokemon_name")

            if image_hash and pokemon_name:
                # Generate a unique file ID based on the image hash and Pokémon name
                unique_file_id = f"{image_hash}_{pokemon_name}"
                
                # Insert only the unique file ID and Pokémon name into the hexaimg collection
                hexaimg.insert_one({
                    "file_id": unique_file_id,
                    "pokemon_name": pokemon_name
                })

                # Increment the counter for each successful insertion
                processed_count += 1
        
        # After processing all records, send the success message
        await message.reply(f"Successfully processed {processed_count} records and generated unique file IDs.")
    
    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")

@app.on_message(filters.user(hexa_bot) & filters.photo)
async def handle_hexa_bot(client, message):
    try:
        file_path = await message.download()

        pokemon_name = await process_image_and_query_db_async(file_path)

        if pokemon_name:
            await message.reply(f"Pokemon Name: {pokemon_name}")
        else:
            await message.reply("Pokemon name not found in the database.")

        os.remove(file_path)

    except Exception as e:
        await message.reply("An error occurred while processing the image.")

@app.on_message(filters.command("ding", ".") & filters.me)
async def ping_pong(client: Client, message: Message):
    try:
        start_time = time.time()
        msg = await message.reply_text("Ping...")
        await msg.edit("✮ᑭｴƝGing...✮")
        end_time = time.time()
        ping_time = round((end_time - start_time) * 1000, 3)
        
        uptime_seconds = time.time() - bot_start_time
        uptime_str = format_uptime(uptime_seconds)
        
        await msg.edit(f"I Aᴍ Aʟɪᴠᴇ Mᴀꜱᴛᴇʀ\n⋙ 🔔 ᑭｴƝG: `{ping_time}` ms\n⋙ 🕒 Uptime: `{uptime_str}`")
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
