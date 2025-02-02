import asyncio
import time
import random
import os
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from PIL import Image
import imagehash
import json

# Constants and Setup
HANDLER = "."
API_ID = "25321403"
API_HASH = "0024ae3c978ba534b1a9bffa29e9cc9b"
SESSION = "BQFo9VAALAHKuEpUHoCealAw8UnYRDLqDtWWGapgMKyDdDNqgra2Gnd2EnVwpwP4PvujFjRM1Lltr8qh1DeTheqRukQF_GPApLhtS2eldLOBWrNYogDqIGr6ifgNnMI1oQAzsMkne0-wkGgrobJyMrKKV3oodj3ast0XVmvtyzh1cutBwm9Ob-BCjS22hK3E5R9A8fL0jKczAM0YgY82TCp2SU9qvCSjPaKASSN2w8HVt8HvWBJWd7tKf0i6VSwIN-5USPrAejxgxpEIwVumBZKTu6wpP2AeWADFN_OCaLTf_hD7klLnBffR6obkodGkIX-ZczkrmX7TstXICIT7jdcxwEutwgAAAAGRx5e_AA"
MONGO_URI = os.getenv('MONGO_URI', "mongodb+srv://Lakshay3434:Tony123@cluster0.agsna9b.mongodb.net/?retryWrites=true&w=majority")
hexa_bot = 572621020
ALLOWED_CHAT_IDS = [-1002136935704, -1002244785813, -1002200182279, -1002232771623]

if not MONGO_URI:
    raise Exception("MONGO_URI environment variable is not set")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client['grabber_db']
hexa_status = db['hexa_hashes']
hexaimg = db["hexa_img"]

# Load Pokémon data once into memory for fast lookup
pokemon_data_cache = {}

def load_pokemon_data():
    global pokemon_data_cache
    if not pokemon_data_cache:
        try:
            with open("pokemon_data.json", "r") as file:
                pokemon_data = json.load(file)
                pokemon_data_cache = {entry["image_hash"]: entry["pokemon_name"] for entry in pokemon_data}
        except Exception as e:
            print(f"Error loading pokemon data: {e}")
    return pokemon_data_cache

# Client setup
app = Client("pokemon_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)

# Hashing function for images
def hash_image(image_path):
    try:
        with Image.open(image_path) as img:
            hash_value = imagehash.phash(img)
            return str(hash_value)
    except Exception as e:
        return None

# Main handler for Pokémon images
async def process_pokemon_image(file_path):
    pokemon_data = load_pokemon_data()
    image_hash_value = hash_image(file_path)

    # Collect all matching Pokémon names from the hash
    matching_pokemon = [pokemon_name for hash_value, pokemon_name in pokemon_data.items() if hash_value == image_hash_value]

    if matching_pokemon:
        return random.sample(matching_pokemon, random.randint(1, len(matching_pokemon)))  # Return random selection
    else:
        return []

# Handle image received from Hexa bot
@app.on_message(filters.user(hexa_bot) & filters.photo)
async def handle_hexa_bot(client, message):
    try:
        # Download the image from the message
        file_path = await message.download()

        # Process the image asynchronously to get Pokémon names
        pokemon_names = await process_pokemon_image(file_path)

        # If no names are found
        if not pokemon_names:
            await message.reply("No matching Pokémon found for the image.")
        else:
            # Randomly select a number of Pokémon names to send as a reply
            selected_pokemon = random.sample(pokemon_names, random.randint(1, len(pokemon_names)))
            await message.reply(f"Found Pokémon: {', '.join(selected_pokemon)}")

        # Optionally remove the image after processing
        os.remove(file_path)

    except Exception as e:
        await message.reply(f"Error processing the image: {str(e)}")

# Capture Pokémon images and send them to Hexa bot
@app.on_message(filters.chat(ALLOWED_CHAT_IDS) & filters.user(hexa_bot) & filters.regex(r"pokemon was"))
async def capture_pokemon(client, message):
    try:
        # Clean the message text
        cleaned_text = re.sub(r'(\*{1,2})(.*?)\1', r'\2', message.text.strip())
        if "pokemon was" not in cleaned_text:
            return

        # Check if the message contains a photo
        if message.reply_to_message and message.reply_to_message.photo:
            replied_message = message.reply_to_message
            file_id = replied_message.photo.file_id

            file_path = await client.download_media(replied_message.photo)
            full_text = message.text.strip()

            try:
                # Send the image to Hexa_DB channel
                sent_photo_message = await client.send_photo('@Hexa_DB', file_path, caption=full_text)
                os.remove(file_path)  # Clean up the file after sending

            except Exception as send_error:
                await message.reply(f"Error sending photo to @Hexa_DB: {send_error}")

    except Exception as e:
        await message.reply(f"Error capturing Pokémon: {str(e)}")

# Handle ping command for bot health check
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
        await message.reply(f"Error in the ping process: {str(e)}")

# Format uptime to hours, minutes, and seconds
def format_uptime(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

# Run the bot and server
def run():
    app.run()

if __name__ == "__main__":
    bot_start_time = time.time()
    run()
