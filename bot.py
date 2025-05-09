from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
import pymongo
from flask import Flask
from secrets import choice
import string
from threading import Thread
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from random import choice

API_ID = 27184163
API_HASH = "4cf380dd354edc4dc4664f2d4f697393"
BOT_TOKEN = "7554171418:AAFW7TW7twbMcKNFr8PFIun0y7AAkh647PU"
OWNER_ID = 6600178606
UPDATE_CHANNEL = -1002030424154
JOIN_LINK = "https://t.me/+LgU79CrQZdY2ZGE1"
MONGO_URI = "mongodb+srv://Alisha:Alisha123@cluster0.yqcpftw.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "anime_bot"
COLLECTION_NAME = "video_links"

app = Client("AnimeBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
server = Flask(__name__)

mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

CHARACTERS = string.ascii_letters + string.digits
last_video = {}

BOT_USERNAMES = {
    "480p": "Anime_spectrum420_bot",
    "720p": "Anime_spectrum720_bot",
    "1080p": "Anime_spectrum1080_bot"
}

@server.route("/")
def home():
    return "Bot is running"

def run_flask():
    server.run(host="0.0.0.0", port=8893)

def generate_code():
    while True:
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        if not collection.find_one({"code": code}):
            return code

async def is_joined(client: Client, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(UPDATE_CHANNEL, user_id)
        return member.status not in ("left", "kicked")
    except UserNotParticipant:
        return False
    except Exception:
        return False

@app.on_message(filters.private & filters.video)
async def handle_video(client: Client, message: Message):
    if not message.caption:
        return await message.reply_text("Please send a video **with a caption** to create a link.")
    
    last_video[message.from_user.id] = {
        "file_id": message.video.file_id,
        "file_unique_id": message.video.file_unique_id,
        "caption": message.caption
    }
    await message.reply_text("Video received with caption! Now use /createlink to generate a link.")

@app.on_message(filters.private & filters.command("createlink"))
async def create_link(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("Only the bot owner can create links.")
    
    if message.from_user.id not in last_video:
        return await message.reply_text("Please send a video with caption first.")

    buttons = [
        [
            InlineKeyboardButton("480p", callback_data="quality:480p"),
            InlineKeyboardButton("720p", callback_data="quality:720p"),
            InlineKeyboardButton("1080p", callback_data="quality:1080p")
        ]
    ]
    await message.reply_text("Choose the video quality to generate a link:", reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^quality:(.+)"))
async def handle_quality_selection(client: Client, callback_query: CallbackQuery):
    quality = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id

    if user_id not in last_video:
        return await callback_query.message.edit_text("Video info missing. Please send a video again.")

    video = last_video[user_id]
    existing = collection.find_one({"file_unique_id": video["file_unique_id"], "quality": quality})

    if existing:
        bot_username = BOT_USERNAMES[quality]
        link = f"https://t.me/{bot_username}?start={existing['code']}"
        return await callback_query.message.edit_text(f"Link already exists:\n{link}")

    for _ in range(10):
        code = "".join(choice(CHARACTERS) for _ in range(12))
        if not collection.find_one({"code": code}):
            break
    else:
        return await callback_query.message.edit_text("Failed to generate a unique code. Try again.")

    collection.insert_one({
        "code": code,
        "file_id": video["file_id"],
        "file_unique_id": video["file_unique_id"],
        "caption": video["caption"],
        "quality": quality
    })

    bot_username = BOT_USERNAMES[quality]
    link = f"https://t.me/{bot_username}?start={code}"
    await callback_query.message.edit_text(f"Link created:\n{link}")

    del last_video[user_id]

@app.on_message(filters.private & filters.command("start"))
async def start_command(client: Client, message: Message):
    user = message.from_user
    args = message.text.split()

    if len(args) > 1:
        code = args[1]
        joined = await is_joined(client, user.id)

        if not joined:
            buttons = [
                [InlineKeyboardButton("Join Channel", url=JOIN_LINK)],
                [InlineKeyboardButton("✅ Verify 🕊️", callback_data=f"verify:{code}")]
            ]
            return await message.reply_text(
                f"Hey [{user.first_name}](tg://user?id={user.id})\n\n"
                "**Please Join All My Update Channels To Use Me!**",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        item = collection.find_one({"code": code})
        if item:
            await message.reply_video(item["file_id"], caption=item.get("caption", ""))
        else:
            await message.reply_text("Invalid or expired link.")
    else:
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Our Channel", url=JOIN_LINK),
                InlineKeyboardButton("Support", url="https://t.me/ruxhiiiii")
            ],
            [InlineKeyboardButton("Close", callback_data="close_msg")]
        ])

        await message.reply_photo(
            photo="https://i.ibb.co/67WkkKrj/photo-2025-05-08-14-46-55-7502086450427461668.jpg",
            caption=(
                f"**Hey !** [{user.first_name}](tg://user?id={user.id})\n\n"
                "**Welcome To our Bot!**\n"
                "Please Start the bot With link Provided in Channel\n"
                "and Enjoy your Anime Journey With US."
            ),
            reply_markup=buttons
        )

@app.on_callback_query(filters.regex(r"^verify:(.+)"))
async def verify_join(client: Client, callback_query):
    code = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id

    if await is_joined(client, user_id):
        item = collection.find_one({"code": code})
        if item:
            await callback_query.message.edit_text("Thanks! To Be part of Our Channel Sending your video...")
            await callback_query.message.reply_video(item["file_id"], caption=item.get("caption", ""))
        else:
            await callback_query.message.edit_text("Invalid or expired link.")
    else:
        await callback_query.answer("You're not joined yet!", show_alert=True)

@app.on_callback_query(filters.regex("close_msg"))
async def close_msg_handler(client: Client, callback_query):
    await callback_query.message.delete()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("Bot is running...")
    app.run()
