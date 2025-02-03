import os
import time
import asyncio
import json
import logging
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from PIL import Image
import imagehash
import re
from flask import Flask

# Configuration
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

# Initialize MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['grabber_db']
hexa_status = db['hexa_hashes']
hexaimg = db["hexa_img"]

# Initialize Flask server
server = Flask(__name__)

# Global cache for Pokémon data
pokemon_data_cache = {}

# Load Pokémon data into memory (cached lookup)
def load_pokemon_data():
    global pokemon_data_cache
    try:
        with open("pokemon_data.json", "r") as file:
            data = json.load(file)
        
        # Create a dictionary for fast lookup by image_hash
        pokemon_data_cache = {entry["image_hash"]: entry["pokemon_name"] for entry in data}
        print(f"Loaded {len(pokemon_data_cache)} Pokémon names into cache.")
    except Exception as e:
        logging.error(f"Error loading pokemon data: {e}")
        print(f"Error loading pokemon data: {e}")

# Load Pokémon data when bot starts
load_pokemon_data()

# Initialize Pyrogram client
app = Client(
    "word9",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION
)

# Set up Flask error handler to catch and log errors globally
@app.errorhandler(Exception)
def handle_error(error):
    logging.error(f"Flask Error: {str(error)}")
    return f"Internal server error: {str(error)}", 500

# Set up logging to redirect all errors to the server log
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Flask home route
@server.route("/")
def home():
    return "Bot is running"

# Handle image sent by hexa_bot and reply with Pokémon name
@app.on_message(filters.user(hexa_bot) & filters.photo)
async def handle_hexa_bot(client, message):
    try:
        # Collect all the image download tasks
        download_tasks = []

        # Check if the message has a photo
        if message.photo:
            download_tasks.append(download_image(client, message.photo))

        # Wait for all download tasks to finish concurrently
        downloaded_images = await asyncio.gather(*download_tasks)

        # Process each downloaded image concurrently
        processing_tasks = []
        for file_path in downloaded_images:
            processing_tasks.append(process_image(file_path))

        # Wait for all processing tasks to finish
        await asyncio.gather(*processing_tasks)

    except Exception as e:
        logging.error(f"Error in handle_hexa_bot: {str(e)}")
        print(f"Error in handle_hexa_bot: {str(e)}")

# Function to download the image
async def download_image(client, photo):
    try:
        # Download the photo and return the file path
        file_path = await client.download_media(photo)
        return file_path
    except Exception as e:
        logging.error(f"Error downloading image: {e}")
        print(f"Error downloading image: {e}")
        return None

# Function to process downloaded image and look up Pokémon name
async def process_image(file_path):
    if not file_path:
        return

    try:
        # Generate the image hash
        image_hash_value = hash_image(file_path)

        # Check the image hash against the cached Pokémon data
        if image_hash_value in pokemon_data_cache:
            pokemon_name = pokemon_data_cache[image_hash_value]
            print(f"Found Pokémon: {pokemon_name}")
        else:
            print(f"No Pokémon found for image hash: {image_hash_value}")

        # Optionally delete the file after processing
        os.remove(file_path)

    except Exception as e:
        logging.error(f"Error processing image {file_path}: {str(e)}")
        print(f"Error processing image {file_path}: {str(e)}")

# Function to generate image hash using perceptual hash
def hash_image(image_path):
    try:
        with Image.open(image_path) as img:
            hash_value = imagehash.phash(img)
            return str(hash_value)
    except Exception as e:
        logging.error(f"Error generating hash for image {image_path}: {str(e)}")
        print(f"Error generating hash for image {image_path}: {str(e)}")
        return str(e)

# Handle command ping to check bot's response time
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
            logging.error(f"Error deleting message: {e}")
            print(f"Error deleting message: {e}")
    except Exception as e:
        logging.error(f"An error occurred in the ping-pong process: {str(e)}")
        await message.reply(f"An error occurred in the ping-pong process: {str(e)}")

# Format uptime to a human-readable string
def format_uptime(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

# Flask server to keep the bot alive
def run():
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))

# Main entry point
if __name__ == "__main__":
    bot_start_time = time.time()
    t = Thread(target=run)
    t.start()
    app.run()
