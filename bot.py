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
API_ID = "25560748"
API_HASH = "ebd241a08fddca1c5b686a7a29a2d5d3"
SESSION = "BQGGBqwAAec0L47cMvuiYPzioN1mgJJpqUYpp-dfeK_z0ssxVkzex6j2oNRHmf5waGvClNHjjK376L6YcHeLVa3ZCEwJcNd2w9Y-XlSr0nSl6UKftnBzi4dDZjvfb1oNzZuDpYLBaVyl2uYz0h7-Qq8TSadQZHDtvtHStCkVxIHiot20UQ1nJC9yzYqSjNumYP2_0dEyapdFQZy6X0RiYjlkFHhqLEPkha9mG2o-O4skot_IUWmW2ycGsBHlsAyK5spN9eCTQYim1oAV8tRcNoUbZb3iqdz6Ng6bKJLmiopWhPy3K6xV-SPmRUoWwmG0mc6CZqo5IVx5hYtedF3C2D4rMgOwDAAAAAGsm527AA"
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

auto_reply_enabled = True
auto_response_groups = {}

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
                await message.reply(f"No Pokémon name found for file_unique_id: {file_unique_id}")
        else:
            await message.reply(f"File unique ID not found in DB: {file_unique_id}")

    except Exception as e:
        # Send the error directly as a message
        await message.reply(f"Error handling hexa_bot: {e}")

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

@app.on_message(filters.command("add", HANDLER) & filters.user([7530506703, 6600178606]))
async def add_auto_response_group(client, message):
    global auto_response_groups
    try:
        cmd = message.command
        added_chat_ids = []
        already_added_chat_ids = []
        
        if len(cmd) > 1:
            for chat_id in cmd[1:]:
                try:
                    chat_id = int(chat_id)
                    if chat_id not in auto_response_groups:
                        auto_response_groups[chat_id] = True
                        added_chat_ids.append(chat_id)
                    else:
                        already_added_chat_ids.append(chat_id)
                except ValueError:
                    continue
            if added_chat_ids:
                added_message = f"Added {len(added_chat_ids)} chat(s) to auto-response groups: {', '.join(map(str, added_chat_ids))}"
            else:
                added_message = "No new chat IDs added."
            
            if already_added_chat_ids:
                already_added_message = f"Already in auto-response groups: {', '.join(map(str, already_added_chat_ids))}"
            else:
                already_added_message = ""
            
            response_message = f"{added_message}\n{already_added_message}".strip()
            await message.reply(response_message)
        
        else:
            chat_id = message.chat.id
            if chat_id not in auto_response_groups:
                auto_response_groups[chat_id] = True
                await message.reply("This group has been added to auto-response groups.")
            else:
                await message.reply("This group is already in auto-response groups.")
    except Exception as e:
        print(f"Error adding auto-response group: {e}")

@app.on_message(filters.command("remove", HANDLER) & filters.user([7530506703, 6600178606]))
async def remove_auto_response_group(client, message):
    global auto_response_groups
    try:
        cmd = message.command
        removed_chat_ids = []
        not_found_chat_ids = []
        
        if len(cmd) > 1:
            for chat_id in cmd[1:]:
                try:
                    chat_id = int(chat_id)
                    if chat_id in auto_response_groups:
                        del auto_response_groups[chat_id]
                        removed_chat_ids.append(chat_id)
                    else:
                        not_found_chat_ids.append(chat_id)
                except ValueError:
                    continue
            if removed_chat_ids:
                removed_message = f"Removed {len(removed_chat_ids)} chat(s) from auto-response groups: {', '.join(map(str, removed_chat_ids))}"
            else:
                removed_message = "No chat IDs removed."
            
            if not_found_chat_ids:
                not_found_message = f"Not found in auto-response groups: {', '.join(map(str, not_found_chat_ids))}"
            else:
                not_found_message = ""
            
            response_message = f"{removed_message}\n{not_found_message}".strip()
            await message.reply(response_message)
        
        else:
            chat_id = message.chat.id
            if chat_id in auto_response_groups:
                del auto_response_groups[chat_id]
                await message.reply("This group has been removed from auto-response groups.")
            else:
                await message.reply("This group is not in auto-response groups.")
    except Exception as e:
        print(f"Error removing auto-response group: {e}")

@app.on_message(filters.command("auto", HANDLER) & filters.user([7530506703, 6600178606]) & filters.me)
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

@app.on_message(filters.command("chats", HANDLER) & filters.user([7530506703, 6600178606]))
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

is_sending = False

@app.on_message(filters.command("starthexa", HANDLER) & filters.user([7530506703, 6600178606]))
async def send_guess_command(client, message):
    global is_sending
    if is_sending:
        await message.reply("Hexa is already running Otey!")
        return

    try:
        is_sending = True
        await message.reply("Hexa now started. Guess...!")
        while is_sending:
            for chat_id in auto_response_groups:
                await client.send_message(chat_id, "/guess@HeXamonbot")
                await asyncio.sleep(2)
            await asyncio.sleep(5)
    
    except Exception as e:
        await message.reply("An error occurred while sending the command.")
    
@app.on_message(filters.command("stophexa", HANDLER) & filters.user([7530506703, 6600178606]))
async def stop_send_guess_command(client, message):
    global is_sending
    if not is_sending:
        await message.reply("Hexa is not running Otey!")
        return

    is_sending = False
    await message.reply("Hexa process is stopped Otey!")

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
