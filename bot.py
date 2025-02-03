import asyncio
import os
import json
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from threading import Thread
from flask import Flask
from PIL import Image
import imagehash
from pymongo import MongoClient

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

max_concurrent_tasks = 4
concurrent_tasks = []
pokemon_data = []

def load_pokemon_data():
    global pokemon_data
    if not pokemon_data:
        try:
            with open("pokemon_data.json", "r") as file:
                pokemon_data = json.load(file)
        except Exception as e:
            print(f"Error loading pokemon data: {e}")
    return pokemon_data

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

def hash_image(image_path):
    try:
        with Image.open(image_path) as img:
            img = img.resize((32, 32), Image.ANTIALIAS)
            hash_value = imagehash.phash(img)
            return str(hash_value)
    except Exception as e:
        return str(e)

async def process_image_task(file_path, image_hash_value, message):
    try:
        pokemon_data = load_pokemon_data()
        found_pokemon = None
        for entry in pokemon_data:
            if entry.get("image_hash") == image_hash_value:
                found_pokemon = entry
                break

        if found_pokemon:
            pokemon_name = found_pokemon.get("pokemon_name")
            if pokemon_name:
                await message.reply(f"{pokemon_name}")
            else:
                print(f"No Pokémon name found for image hash: {image_hash_value}")
        else:
            print(f"Image hash not found in JSON data: {image_hash_value}")
    except Exception as e:
        print(f"Error processing image task: {e}")

async def handle_hexa_bot(client, message):
    try:
        if len(concurrent_tasks) >= max_concurrent_tasks:
            await message.reply("Already full")
            return

        file_path = await message.download()
        image_hash_value = hash_image(file_path)

        task = asyncio.create_task(process_image_task(file_path, image_hash_value, message))
        concurrent_tasks.append(task)

        task.add_done_callback(lambda t: concurrent_tasks.remove(t))

    except Exception as e:
        print(f"Error handling hexa_bot: {e}")

@app.on_message(filters.user(hexa_bot) & filters.photo)
async def handle_hexa_bot_trigger(client, message):
    await handle_hexa_bot(client, message)

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
