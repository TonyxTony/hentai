from pyrogram import Client, filters
import os
import time
from threading import Thread
from flask import Flask
import asyncio
from pymongo import MongoClient
import re

HANDLER = "."
API_ID = "25321403"
API_HASH = "0024ae3c978ba534b1a9bffa29e9cc9b"
SESSION = "BQFo9VAALAHKuEpUHoCealAw8UnYRDLqDtWWGapgMKyDdDNqgra2Gnd2EnVwpwP4PvujFjRM1Lltr8qh1DeTheqRukQF_GPApLhtS2eldLOBWrNYogDqIGr6ifgNnMI1oQAzsMkne0-wkGgrobJyMrKKV3oodj3ast0XVmvtyzh1cutBwm9Ob-BCjS22hK3E5R9A8fL0jKczAM0YgY82TCp2SU9qvCSjPaKASSN2w8HVt8HvWBJWd7tKf0i6VSwIN-5USPrAejxgxpEIwVumBZKTu6wpP2AeWADFN_OCaLTf_hD7klLnBffR6obkodGkIX-ZczkrmX7TstXICIT7jdcxwEutwgAAAAGRx5e_AA"
mongo_uri = os.getenv('MONGO_URI', "mongodb+srv://Lakshay3434:Tony123@cluster0.agsna9b.mongodb.net/?retryWrites=true&w=majority")
hexa_bot = 572621020

if not mongo_uri:
    raise Exception("MONGO_URI environment variable is not set")
    
print(f"Connected to MongoDB at: {mongo_uri}")
mongo_client = MongoClient(mongo_uri)
db = mongo_client['grabber_db']
hexa_db_collection = db['hexa_db']

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

# List of allowed chats
allowed_chats = [
    -1002220303971, -1002220460503, -1002244785813, -1002200182279, -1002241545267, 
    -1002180680112, -1002152913531, -1002232771623, -1002244523802, -1002159180828
]

@app.on_message(filters.user(hexa_bot) & filters.photo & filters.chat(allowed_chats))
async def handle_hexa_bot(client, message):
    try:
        file_unique_id = message.photo.file_unique_id
        existing_doc = hexa_db_collection.find_one({"file_unique_id": file_unique_id})
        
        if existing_doc:
            pokemon_name = existing_doc.get("pokemon_name")
            
            if pokemon_name:
                await message.reply(f"{pokemon_name}")
            else:
                print(f"No Pokémon name found for file_unique_id: {file_unique_id}")
        else:
            print(f"File unique ID not found in DB: {file_unique_id}")
    
    except Exception as e:
        print(f"Error handling hexa_bot: {e}")
        # Gracefully handle any issues with the peer ID or other errors
        try:
            await message.reply("An error occurred while processing the image.")
        except Exception as msg_error:
            print(f"Error replying to the message: {msg_error}")

@app.on_message(filters.chat(allowed_chats))
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
                        await message.reply(f"Stored `{file_unique_id}` with Pokémon name `{pokemon_name}` in DB!")
    except Exception as e:
        print(f"Error in capture_pokemon_data: {e}")
        try:
            await message.reply("An error occurred while processing the Pokémon data.")
        except Exception as msg_error:
            print(f"Error replying to the message: {msg_error}")

# Function to send guess command to allowed chats
@app.on_message(filters.command("starthexa", HANDLER) & filters.chat(allowed_chats) & filters.user([7530506703, 6600178606]))
async def send_guess_command(client, message):
    global is_sending
    if is_sending:
        await message.reply("Hexa is already running Otey!")
        return

    try:
        is_sending = True
        await message.reply("Hexa now started. Guess...!")
        while is_sending:
            for chat_id in allowed_chats:
                try:
                    await client.send_message(chat_id, "/guess@HeXamonbot")
                    await asyncio.sleep(3)
                except Exception as e:
                    print(f"Error sending message to {chat_id}: {e}")
            await asyncio.sleep(5)
    
    except Exception as e:
        await message.reply("An error occurred while sending the command.")

# Function to stop sending guess command to allowed chats
@app.on_message(filters.command("stophexa", HANDLER) & filters.chat(allowed_chats) & filters.user([7530506703, 6600178606]))
async def stop_send_guess_command(client, message):
    global is_sending
    if not is_sending:
        await message.reply("Hexa is not running Otey!")
        return

    is_sending = False
    await message.reply("Hexa process is stopped Otey!")

@app.on_message(filters.command("ding", HANDLER) & filters.me)
async def ping_pong(client, message):
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
