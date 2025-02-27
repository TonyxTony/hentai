import os
from flask import Flask, request, jsonify
from threading import Thread
import imagehash
from PIL import Image
from io import BytesIO
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import Message

HANDLER = "."
API_ID = "25321403"
API_HASH = "0024ae3c978ba534b1a9bffa29e9cc9b"
SESSION = "BQFo9VAAoK91Yrm_Y2wkhW5w39ypH_VsdFfPiiYxsLVPiFfGDAFCCrpQK3SnwjSaPp5l272W422bcEryMiZocGSFleN0HtGv8REcobbU_8eLgY6iDGtjhnKK5M6OTeqJNqvDvabpt6SnEEC3g-uMCoTwfQaLGffKKQMhlhe_c1zN8Ht_JowjtAnZg2B8EXPodo4wmF40ifK6AYHpaOpqw70wUj8NOsMRofNpPI-9LMTjf6HNkfxpt1zmNm3FBJUly0vx8XGOt-BWtlEgaTf-ePwtYl1jUBxKVMoPjel4QNL84Rfmf516Q4PRx8RJIQ5mQmrDpTFAD3_dssiYpWtQHWAr5Lr5IgAAAAGRx5e_AA"
MONGO_URI = os.getenv('MONGO_URI', "mongodb+srv://Lakshay3434:Tony123@cluster0.agsna9b.mongodb.net/?retryWrites=true&w=majority")
hexa_bot = 572621020

mongo_client = MongoClient(MONGO_URI)
db = mongo_client['grabber_db']
hexa_img = db["hexa_img"]

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

def get_hash(image_data):
    image = Image.open(BytesIO(image_data)).convert("L").resize((32, 32))
    return str(imagehash.phash(image))

def add_pokemon(name, image_data):
    img_hash = get_hash(image_data)
    hexa_img.insert_one({"name": name, "hash": img_hash})

def find_pokemon(image_data):
    img_hash = get_hash(image_data)
    match = hexa_img.find_one({"hash": img_hash})
    return match["name"] if match else None

@app.on_message(filters.command("fetch") & filters.me)
async def fetch_images(client, message):
    async for msg in client.get_chat_history("@HexaDB"):
        if msg.photo and msg.caption:
            photo = await client.download_media(msg.photo.file_id)
            with open(photo, "rb") as f:
                add_pokemon(msg.caption.replace("The pokemon was ", ""), f.read())
            os.remove(photo)
    await message.reply("Pokémon images have been stored.")

@app.on_message(filters.photo & filters.group)
async def recognize_pokemon(client, message: Message):
    photo = await message.download()
    with open(photo, "rb") as f:
        pokemon_name = find_pokemon(f.read())
    os.remove(photo)

    if pokemon_name:
        await message.reply(f"The Pokémon is **{pokemon_name}**!")

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
