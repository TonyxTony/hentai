from pyrogram import Client, filters
from pyrogram.types import Message
import pymongo
from secrets import choice
import string
from threading import Thread
from flask import Flask

API_ID = 27184163
API_HASH = "4cf380dd354edc4dc4664f2d4f697393"
BOT_TOKEN = "7554171418:AAFW7TW7twbMcKNFr8PFIun0y7AAkh647PU"
OWNER_ID = 6600178606
MONGO_URI = "mongodb+srv://Alisha:Alisha123@cluster0.yqcpftw.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "anime_bot"
COLLECTION_NAME = "video_links"

# MongoDB Setup
mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

# Pyrogram Bot Client
app = Client("AnimeBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Flask App
server = Flask(__name__)

@server.route("/")
def home():
    return "Bot is running"

def run_flask():
    server.run(host="0.0.0.0", port=8893)

# Start Flask in a separate thread
Thread(target=run_flask).start()

# Utility
CHARACTERS = string.ascii_letters + string.digits

def generate_code():
    while True:
        code = "".join(choice(CHARACTERS) for _ in range(12))
        if not collection.find_one({"code": code}):
            return code

last_video = {}

@app.on_message(filters.private & filters.video)
async def handle_video(client: Client, message: Message):
    last_video[message.from_user.id] = {
        "file_unique_id": message.video.file_unique_id,
        "file_id": message.video.file_id
    }
    await message.reply_text("Video received! Use /createlink to generate a link.")

@app.on_message(filters.private & filters.command("createlink"))
async def create_link(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply_text("Only the bot owner can create links!")
        return
    user_id = message.from_user.id
    if user_id not in last_video:
        await message.reply_text("Please send a video first!")
        return
    video = last_video[user_id]
    code = generate_code()
    collection.insert_one({"code": code, "file_unique_id": video["file_unique_id"], "file_id": video["file_id"]})
    bot_info = await client.get_me()
    link = f"https://t.me/{bot_info.username}?start={code}"
    await message.reply_text(f"Link created: {link}")
    del last_video[user_id]

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    args = message.text.split()
    if len(args) > 1:
        code = args[1]
        item = collection.find_one({"code": code})
        if item:
            await message.reply_video(item["file_id"], caption="Enjoy your anime video!")
        else:
            await message.reply_text("Invalid or expired link!")
    else:
        await message.reply_text("Welcome! Use a link with a code to access anime videos.")

# Run the bot
print("Bot is running...")
app.run()
