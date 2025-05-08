from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import pymongo
from secrets import choice
import string
from threading import Thread
from flask import Flask

API_ID = 27184163
API_HASH = "4cf380dd354edc4dc4664f2d4f697393"
BOT_TOKEN = "7554171418:AAFW7TW7twbMcKNFr8PFIun0y7AAkh647PU"
OWNER_ID = 6600178606
UPDATE_CHANNEL = -1002030424154
JOIN_LINK = "https://t.me/+LgU79CrQZdY2ZGE1"

MONGO_URI = "mongodb+srv://Alisha:Alisha123@cluster0.yqcpftw.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "anime_bot"
COLLECTION_NAME = "video_links"

mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

app = Client("AnimeBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Flask App
server = Flask(__name__)
@server.route("/")
def home():
    return "Bot is running"
def run_flask():
    server.run(host="0.0.0.0", port=8893)
Thread(target=run_flask).start()

# Utils
CHARACTERS = string.ascii_letters + string.digits
def generate_code():
    while True:
        code = "".join(choice(CHARACTERS) for _ in range(12))
        if not collection.find_one({"code": code}):
            return code

last_video = {}

async def is_joined(client: Client, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(UPDATE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

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
        return await message.reply_text("Only the bot owner can create links!")
    user_id = message.from_user.id
    if user_id not in last_video:
        return await message.reply_text("Please send a video first!")
    video = last_video[user_id]
    code = generate_code()
    collection.insert_one({
        "code": code,
        "file_unique_id": video["file_unique_id"],
        "file_id": video["file_id"]
    })
    bot_info = await client.get_me()
    link = f"https://t.me/{bot_info.username}?start={code}"
    await message.reply_text(f"Link created: {link}")
    del last_video[user_id]

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) > 1:
        code = args[1]
        if not await is_joined(client, user_id):
            name = message.from_user.first_name
            await message.reply_text(
                f"Hey [{name}](tg://user?id={user_id})\n\n"
                "Please Join All My Update Channels To Use Me!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Join", url=JOIN_LINK)],
                    [InlineKeyboardButton("Verify 🕊️", callback_data=f"verify_{code}")]
                ]),
                disable_web_page_preview=True
            )
            return

        item = collection.find_one({"code": code})
        if item:
            await message.reply_video(item["file_id"], caption="Enjoy your anime video!")
        else:
            await message.reply_text("Invalid or expired link!")
    else:
        await message.reply_text("Welcome! Use a link with a code to access anime videos.")

@app.on_callback_query(filters.regex(r"^verify_(.+)"))
async def verify_callback(client: Client, query: CallbackQuery):
    code = query.data.split("_", 1)[1]
    user_id = query.from_user.id
    if await is_joined(client, user_id):
        item = collection.find_one({"code": code})
        if item:
            await query.message.delete()
            await query.message.reply_video(item["file_id"], caption="Enjoy your anime video!")
        else:
            await query.answer("Invalid or expired code!", show_alert=True)
    else:
        await query.answer("You're not joined yet!", show_alert=True)

# Run bot
print("Bot is running...")
app.run()
