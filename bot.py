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
SESSION = "BQFo9VAALAHKuEpUHoCealAw8UnYRDLqDtWWGapgMKyDdDNqgra2Gnd2EnVwpwP4PvujFjRM1Lltr8qh1DeTheqRukQF_GPApLhtS2eldLOBWrNYogDqIGr6ifgNnMI1oQAzsMkne0-wkGgrobJyMrKKV3oodj3ast0XVmvtyzh1cutBwm9Ob-BCjS22hK3E5R9A8fL0jKczAM0YgY82TCp2SU9qvCSjPaKASSN2w8HVt8HvWBJWd7tKf0i6VSwIN-5USPrAejxgxpEIwVumBZKTu6wpP2AeWADFN_OCaLTf_hD7klLnBffR6obkodGkIX-ZczkrmX7TstXICIT7jdcxwEutwgAAAAGRx5e_AA"
MONGO_URI = os.getenv('MONGO_URI', "mongodb+srv://Lakshay3434:Tony123@cluster0.agsna9b.mongodb.net/?retryWrites=true&w=majority")
hexa_bot = 572621020

ALLOWED_CHAT_IDS = [
    -1002136935704, -1002244785813, -1002200182279, -1002232771623,
    -1002241545267, -1002180680112, -1002152913531, -1002244523802,
    -1002159180828, -1002186623520, -1002220460503
]

if not MONGO_URI:
    raise Exception("MONGO_URI environment variable is not set")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client['grabber_db']
hexacollection = db['hexa_hash']

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
    
import os
import re

@app.on_message(filters.chat(ALLOWED_CHAT_IDS))
async def capture_pokemon(client, message):
    try:
        # Check if the message is a reply with a photo
        if message.reply_to_message and message.reply_to_message.photo:
            replied_message = message.reply_to_message
            file_path = await client.download_media(replied_message.photo)

            # Remove markdown formatting (e.g., bold, italic) from the text
            cleaned_text = re.sub(r'(\*{1,2})(.*?)\1', r'\2', message.text.strip())

            # Check if the word "Pokemon" is in the cleaned text
            if "Pokemon" in cleaned_text:
                # Extract the full text of the message
                full_text = message.text.strip()

                # Attempt to send the photo to @Hexa_DB channel
                try:
                    sent_photo = await client.send_photo('@Hexa_DB', file_path)
                    # After sending the photo, edit the message to include the full text
                    await client.edit_message_caption(
                        chat_id='@Hexa_DB',
                        message_id=sent_photo.message_id,
                        caption=full_text
                    )

                    # Delete the local photo file after sending it
                    os.remove(file_path)

                except Exception as send_error:
                    # Send error message to user about sending the photo
                    await message.reply(f"Error sending photo to @Hexa_DB: {send_error}")
                    return

            else:
                # If the text does not contain "Pokemon"
                await message.reply("The message does not contain 'Pokemon'.")
                return

        else:
            # If there is no photo in the replied message
            await message.reply("No photo found in the replied message.")

    except Exception as e:
        # Send error message to user about any other issues
        await message.reply(f"An error occurred: {str(e)}")

def hash_image(image_path):
    try:
        with Image.open(image_path) as img:
            hash_value = imagehash.phash(img)
            return str(hash_value)
    except Exception as e:
        return str(e)

@app.on_message(filters.user(hexa_bot) & filters.photo)
async def handle_hexa_bot(client, message):
    try:
        file_path = await message.download()
        image_hash_value = hash_image(file_path)
        existing_doc = hexacollection.find_one({"image_hash": image_hash_value})

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

@app.on_message(filters.chat(ALLOWED_CHAT_IDS))
async def capture_pokemon_data(client, message):
    try:
        if message.reply_to_message and message.reply_to_message.photo:
            replied_message = message.reply_to_message
            file_path = await client.download_media(replied_message.photo)

            image_hash_value = hash_image(file_path)
            if 'Error' in image_hash_value:  # Check if there was an error generating the hash
                await message.reply(f"Error generating hash: {image_hash_value}")
                return

            if "The pokemon was" in message.text:
                pokemon_name_match = re.search(r"The pokemon was (.*)", message.text)
                if pokemon_name_match:
                    pokemon_name = pokemon_name_match.group(1).strip()
                    pokemon_name = re.sub(r"(\*{2})(.*?)(\*{2})", r"\2", pokemon_name)
                    pokemon_name = re.sub(r"(\*{1})(.*?)(\*{1})", r"\2", pokemon_name)

                    existing_doc = hexacollection.find_one({"image_hash": image_hash_value})
                    if existing_doc:
                        await message.reply(f"The image `{image_hash_value}` already exists in DB!")
                    else:
                        hexacollection.update_one(
                            {"image_hash": image_hash_value},
                            {"$set": {"image_hash": image_hash_value, "pokemon_name": pokemon_name}},
                            upsert=True
                        )
                        await message.reply(f"Stored image `{image_hash_value}` with Pokémon name `{pokemon_name}` Added in DB!")
    except Exception as e:
        await message.reply(f"An error occurred while processing the request: {str(e)}")

@app.on_message(filters.command("total_pokemon", HANDLER) & filters.me)
async def total_pokemon(client: Client, message: Message):
    try:
        total_pokemon_count = hexacollection.count_documents({})
        await message.reply(f"Pokémon in the database `{total_pokemon_count}` Otey!")
    except Exception as e:
        await message.reply(f"An error occurred while fetching the total Pokémon count: {str(e)}")

@app.on_message(filters.command("ding", HANDLER) & filters.me)
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
