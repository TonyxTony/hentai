from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
import pymongo
from flask import Flask
from secrets import choice
import string
from threading import Thread

API_ID = 27184163
API_HASH = "4cf380dd354edc4dc4664f2d4f697393"
BOT_TOKEN = "8036873523:AAFfjLtsMDIQz0bczvadLapf92a_VQT1wjM"
OWNERS_ID = (6600178606, 7530506703, 7240796549, 7169672824)
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

@server.route("/")
def home():
    return "Bot is running"

def run_flask():
    server.run(host="0.0.0.0", port=8893)

async def is_joined(client: Client, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(UPDATE_CHANNEL, user_id)
        return member.status not in ("left", "kicked")
    except UserNotParticipant:
        return False
    except Exception:
        return False

@app.on_message(filters.private & filters.command("createlink"))
async def create_link(client: Client, message: Message):
    if message.from_user.id not in OWNERS_ID:
        return

    replied = message.reply_to_message
    if not replied or not replied.video or not replied.caption:
        return await message.reply_text("Please reply to a video message *with a caption*.")

    file_unique_id = replied.video.file_unique_id
    file_id = replied.video.file_id
    caption = replied.caption

    existing = collection.find_one({"file_unique_id": file_unique_id})
    if existing:
        bot_username = (await client.get_me()).username
        link = f"https://t.me/{bot_username}?start={existing['code']}"
        return await message.reply_text(f"This video already has a link:\n\n{link}")

    while True:
        code = "".join(choice(CHARACTERS) for _ in range(12))
        if not collection.find_one({"code": code}):
            break

    collection.insert_one({
        "code": code,
        "file_unique_id": file_unique_id,
        "file_id": file_id,
        "caption": caption
    })

    bot_username = (await client.get_me()).username
    link = f"https://t.me/{bot_username}?start={code}"
    await message.reply_text(f"Link created successfully:\n{link}")

@app.on_message(filters.private & filters.command("start"))
async def start_command(client: Client, message: Message):
    user = message.from_user
    args = message.text.split()

    if len(args) > 1:
        code = args[1]
        joined = await is_joined(client, user.id)

        if not joined:
            buttons = [
                [InlineKeyboardButton("Jᴏɪɴ Cʜᴀɴɴᴇʟ", url=JOIN_LINK)],
                [InlineKeyboardButton("✅ Vᴇʀɪғʏ 🕊️", callback_data=f"verify:{code}")]
            ]
            return await message.reply_text(
                f"Hey [{user.first_name}](tg://user?id={user.id})\n\n"
                "**Pʟᴇᴀsᴇ Jᴏɪɴ Aʟʟ Mʏ Uᴘᴅᴀᴛᴇ Cʜᴀɴɴᴇʟs Tᴏ Usᴇ Mᴇ!**",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        item = collection.find_one({"code": code})
        if item:
            await message.reply_video(item["file_id"], caption=item.get("caption", ""))
        else:
            await message.reply_text("**Iɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ.**")
    else:
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Oᴜʀ Cʜᴀɴɴᴇʟ", url=JOIN_LINK),
                InlineKeyboardButton("Sᴜᴘᴘᴏʀᴛ", url="https://t.me/ruxhiiiii")
            ],
            [InlineKeyboardButton("Cʟᴏsᴇ", callback_data="close_msg")]
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
            await callback_query.message.edit_text("**Tʜᴀɴᴋs! Tᴏ Bᴇ ᴘᴀʀᴛ ᴏғ Oᴜʀ Cʜᴀɴɴᴇʟ Sᴇɴᴅɪɴɢ ʏᴏᴜʀ ᴠɪᴅᴇᴏ...**")
            await callback_query.message.reply_video(item["file_id"], caption=item.get("caption", ""))
        else:
            await callback_query.message.edit_text("**Iɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ.**")
    else:
        await callback_query.answer("**Yᴏᴜ'ʀᴇ ɴᴏᴛ Jᴏɪɴᴇᴅ ʏᴇᴛ!**", show_alert=True)

@app.on_callback_query(filters.regex("close_msg"))
async def close_msg_handler(client: Client, callback_query):
    await callback_query.message.delete()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("Bot is running...")
    app.run()
