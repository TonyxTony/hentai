from pyrogram import Client, filters
import os
import time
from threading import Thread
from flask import Flask
from pyrogram.types import Message
import asyncio
from pymongo import MongoClient
from PIL import Image
import imagehash
import re

HANDLER = "."
API_ID = "25321403"
API_HASH = "0024ae3c978ba534b1a9bffa29e9cc9b"
SESSION = "BQFo9VAALAHKuEpUHoCealAw8UnYRDLqDtWWGapgMKyDdDNqgra2Gnd2EnVwpwP4PvujFjRM1Lltr8qh1DeTheqRukQF_GPApLhtS2eldLOBWrNYogDqIGr6ifgNnMI1oQAzsMkne0-wkGgrobJyMrKKV3oodj3ast0XVmvtyzh1cutBwm9Ob-BCjS22hK3E5R9A8fL0jKczAM0YgY82TCp2SU9qvCSjPaKASSN2w8HVt8HvWBJWd7tKf0i6VSwIN-5USPrAejxgxpEIwVumBZKTu6wpP2AeWADFN_OCaLTf_hD7klLnBffR6obkodGkIX-ZczkrmX7TstXICIT7jdcxwEutwgAAAAGRx5e_AA"
mongo_uri = os.getenv('MONGO_URI', "mongodb+srv://Lakshay3434:Tony123@cluster0.agsna9b.mongodb.net/?retryWrites=true&w=majority")
waifu_grabber_bot = 6195436879
husbando_grabber_bot = 6546492683
catch_your_husbando_bot = 6763528462
catch_your_waifu_bot = 6883098627
Character_Secure_Bot = 6438576771
hexa_bot = 572621020

if not mongo_uri:
    raise Exception("MONGO_URI environment variable is not set")
    
print(f"Connected to MongoDB at: {mongo_uri}")
mongo_client = MongoClient(mongo_uri)
db = mongo_client['grabber_db']
collection = db['unique_ids']
waifu_grabber_collection = db['waifu_grabber_image_hashes']
guess_bots_collection = db['guess_hashes']
secure_bot_collection = db['secure_ids']
hexa_db_collection = db['hexa_db']

rarity_settingssss = {
    "Animated": True,
    "Christmas": True,
    "Common": True,
    "Emerald": True,
    "Exclusive": True,
    "Halloween": True,
    "Holi": True,
    "Legendary": True,
    "Medium": True,
    "Mythic": True,
    "New Year": True,
    "Rare": True,
    "Shop": True,
    "Special": True,
    "Valentine": True,
    "Winters": True,
    "X-Verse": True
}

rarity_settingsss = {
    "Common": True,
    "Medium": True,
    "Legendary": True,
    "Rare": True,
    "Exclusive": True,
    "Mythical": True,
    "Special": True,
    "Special edition": True,
    "Exotic": True,
    "Marvelous": True
}

rarity_settings = {
    "celestial": True,
    "Limited Edition": True
}

auto_reply_enabled = True
auto_response_groups = {}

async def get_reply_by_image_hash(image_hash):
    doc = waifu_grabber_collection.find_one({"image_hash": image_hash})
    if doc:
        return doc.get("reply"), doc.get("rarity")
    return None, None

async def get_reply_by_image_hashs(image_hash):
    doc = guess_bots_collection.find_one({"image_hash": image_hash})
    if doc:
        return doc.get("reply"), doc.get("rarity")
    return None, None

async def get_reply_by_file_unique_ids(file_unique_id):
    doc = secure_bot_collection.find_one({"file_unique_id": file_unique_id})
    if doc:
        return doc.get("reply"), doc.get("rarity")
    return None, None

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

@app.on_message(filters.user(hexa_bot) & filters.photo)
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

@app.on_message(filters.user(Character_Secure_Bot) & (filters.photo | filters.video | filters.animation) & filters.regex(r".*/secure"))
async def handle_Character_Secure_Bot(client, message):
    try:
        if auto_reply_enabled and message.chat.id in auto_response_groups:
            if "𝗥𝗲𝗺𝗲𝗺𝗯𝗲𝗿 𝘁𝗼 𝘂𝘀𝗲" in message.caption or message.text:
                print("Ignored message with '𝗥𝗲𝗺𝗲𝗺𝗯𝗲𝗿 𝘁𝗼 𝘂𝘀𝗲'")
                return
            file_unique_id = None
            
            if message.photo:
                file_unique_id = message.photo.file_unique_id
            elif message.video:
                file_unique_id = message.video.file_unique_id
            elif message.animation:
                file_unique_id = message.animation.file_unique_id
            
            if file_unique_id:
                reply_text, rarity = await get_reply_by_file_unique_ids(file_unique_id)
                if reply_text and rarity_settingssss.get(rarity, False):
                    sent_message = await client.send_message(chat_id=message.chat.id, text=reply_text)
                else:
                    print(f"Unique ID not found or rarity not enabled: {file_unique_id}")
            else:
                print("No valid media found in the message.")
    except Exception as e:
        print(f"Error replying to Character_Secure_Bot: {e}")

@app.on_message(filters.user(catch_your_husbando_bot) & filters.photo & filters.regex(r".*/guess"))
async def handle_catch_your_husbando_bot(client, message):
    try:
        if auto_reply_enabled and message.chat.id in auto_response_groups:
            file_path = await message.download()
            image_hash = hash_image(file_path)
            reply_text, rarity = await get_reply_by_image_hashs(image_hash)
            if reply_text and rarity_settingsss.get(rarity, False):
                sent_message = await client.send_message(chat_id=message.chat.id, text=reply_text)
                await asyncio.sleep(60)
                await sent_message.delete()
            else:
                print(f"Image hash not found or rarity not enabled: {image_hash}")
    except Exception as e:
        print(f"Error replying to catch_your_husbando_bot: {e}")

@app.on_message(filters.user(catch_your_waifu_bot) & filters.photo & filters.regex(r".*/guess"))
async def handle_catch_your_waifu_bot(client, message):
    try:
        if auto_reply_enabled and message.chat.id in auto_response_groups:
            file_path = await message.download()
            image_hash = hash_image(file_path)
            reply_text, rarity = await get_reply_by_image_hashs(image_hash)
            if reply_text and rarity_settingsss.get(rarity, False):
                sent_message = await client.send_message(chat_id=message.chat.id, text=reply_text)
                await asyncio.sleep(60)
                await sent_message.delete()
            else:
                print(f"Image hash not found or rarity not enabled: {image_hash}")
    except Exception as e:
        print(f"Error replying to catch_your_waifu_bot: {e}")

@app.on_message(filters.user(waifu_grabber_bot) & filters.photo & filters.regex(r".*/grab"))
async def handle_waifu_grabber_bot(client, message):
    try:
        if auto_reply_enabled and message.chat.id in auto_response_groups:
            file_path = await message.download()
            image_hash = hash_image(file_path)
            reply_text, rarity = await get_reply_by_image_hash(image_hash)
            if reply_text and rarity_settings.get(rarity, False):
                sent_message = await client.send_message(chat_id=message.chat.id, text=reply_text)
                await asyncio.sleep(600)
                await sent_message.delete()
            else:
                print(f"Image hash not found or rarity not enabled: {image_hash}")
    except Exception as e:
        print(f"Error replying to waifu_grabber_bot: {e}")

@app.on_message(filters.user(husbando_grabber_bot) & filters.photo & filters.regex(r".*/grab"))
async def handle_husbando_grabber_bot(client, message):
    try:
        if auto_reply_enabled and message.chat.id in auto_response_groups:
            file_path = await message.download()
            image_hash = hash_image(file_path)
            reply_text, rarity = await get_reply_by_image_hash(image_hash)
            if reply_text and rarity_settings.get(rarity, False):
                sent_message = await client.send_message(chat_id=message.chat.id, text=reply_text)
                await asyncio.sleep(600)
                await sent_message.delete()
            else:
                print(f"Image hash not found or rarity not enabled: {image_hash}")
    except Exception as e:
        print(f"Error replying to husbando_grabber_bot: {e}")

def hash_image(image_path):
    with Image.open(image_path) as img:
        hash_value = imagehash.phash(img)
        return str(hash_value)

@app.on_message(filters.chat())
async def capture_pokemon_data(client, message):
    try:
        if auto_reply_enabled and message.chat.id in auto_response_groups:
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
        await message.reply("An error occurred while processing the request.")
        print(f"Error in capture_pokemon_data: {e}")
        
@app.on_message(filters.command("add", HANDLER))
async def add_auto_response_group(client, message):
    global auto_response_groups
    try:
        cmd = message.command
        if len(cmd) == 2:
            chat_id = int(cmd[1])
            if chat_id not in auto_response_groups:
                auto_response_groups[chat_id] = True
                await message.reply(f"Group with chat ID `{chat_id}` added to auto-response groups.")
            else:
                await message.reply(f"Group with chat ID `{chat_id}` is already in auto-response groups.")
        else:
            chat_id = message.chat.id
            if chat_id not in auto_response_groups:
                auto_response_groups[chat_id] = True
                await message.reply("This group has been added to auto-response groups.")
            else:
                await message.reply("This group is already in auto-response groups.")
    except Exception as e:
        print(f"Error adding auto-response group: {e}")

@app.on_message(filters.command("remove", HANDLER))
async def remove_auto_response_group(client, message):
    global auto_response_groups
    try:
        cmd = message.command
        if len(cmd) == 2:
            chat_id = int(cmd[1])
            if chat_id in auto_response_groups:
                del auto_response_groups[chat_id]
                await message.reply(f"Group with chat ID `{chat_id}` removed from auto-response groups.")
            else:
                await message.reply(f"Group with chat ID `{chat_id}` is not in auto-response groups.")
        else:
            chat_id = message.chat.id
            if chat_id in auto_response_groups:
                del auto_response_groups[chat_id]
                await message.reply("This group has been removed from auto-response groups.")
            else:
                await message.reply("This group is not in auto-response groups.")
    except Exception as e:
        print(f"Error removing auto-response group: {e}")

@app.on_message(filters.command("auto", HANDLER))
async def toggle_auto_reply(client, message):
    global auto_reply_enabled
    try:
        cmd = message.command
        if len(cmd) == 2 and cmd[1].lower() in ['on', 'off']:
            if cmd[1].lower() == 'on':
                if not auto_reply_enabled:
                    auto_reply_enabled = True
                    await message.reply("Auto-reply enabled.")
                else:
                    await message.reply("Auto-reply is already enabled.")
            elif cmd[1].lower() == 'off':
                if auto_reply_enabled:
                    auto_reply_enabled = False
                    await message.reply("Auto-reply disabled.")
                else:
                    await message.reply("Auto-reply is already disabled.")
        else:
            await message.edit("Use like this: .auto [on/off]")
    except Exception as e:
        print(f"Error toggling auto-reply: {e}")

@app.on_message(filters.command("chats", HANDLER))
async def list_auto_response_groups(client, message):
    try:
        if auto_response_groups:
            response_text = f"Auto-response enabled for {len(auto_response_groups)} group(s):\n"
            for chat_id in auto_response_groups:
                chat_info = await client.get_chat(chat_id)
                response_text += f"• {chat_info.title} (Chat ID: `{chat_id}`)\n"
            await message.reply(response_text)
        else:
            await message.reply("No groups have been added to auto-response.")
    except Exception as e:
        print(f"Error listing auto-response groups: {e}")

@app.on_message(filters.command("ding", HANDLER) & filters.me)
async def ping_pong(client: Client, message: Message):
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
