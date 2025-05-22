from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
import pymongo
from random import choice
from flask import Flask
from secrets import choice
import string
from threading import Thread
import asyncio

API_ID = 27184163
API_HASH = "4cf380dd354edc4dc4664f2d4f697393"
BOT_TOKEN = "7503376749:AAGAwgA7knAYww46-aUoYq2sOm14Q0X9pb0"
OWNERS_ID = (6600178606, 7893840561, 7530506703, 7240796549, 7169672824)
UPDATE_CHANNEL = -1002030424154
UPDATE_CHANNEL_2 = -1002512623846
JOIN_LINK_2 = "https://t.me/+ki5H61TI9YQzMDFl"
JOIN_LINK = "https://t.me/+LgU79CrQZdY2ZGE1"
MONGO_URI = "mongodb+srv://Anime:Tony123@animedb.veb4qyk.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "anime_stream"
COLLECTION_NAME = "stream_db"

app = Client("AnimeBot3", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
server = Flask(__name__)

mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

CHARACTERS = string.ascii_letters + string.digits

@server.route("/")
def home():
    return "Bot is running"

def run_flask():
    server.run(host="0.0.0.0", port=8894)

async def is_joined(client: Client, user_id: int) -> bool:
    async def check(channel_id):
        try:
            member = await client.get_chat_member(channel_id, user_id)
            return member.status not in ("left", "kicked")
        except:
            return False
    return await check(UPDATE_CHANNEL) and await check(UPDATE_CHANNEL_2)

async def send_video_with_expiry(client, chat_id, file_id, caption):
    video_msg = await client.send_video(chat_id, file_id, caption=caption)

    button_choice = choice([
        {
            "text": "Request Group 💌",
            "url": "https://t.me/+STCT2ywFAA0yYjM1",
            "message": "⚠️ This message will be deleted in 20 minutes. Please save it Somewhere.\nWant any anime? Just request it in the Request Group."
        },
        {
            "text": "More Anime 🍌",
            "url": "https://t.me/addlist/KFp8zZlXXVZiYmI1",
            "message": "⚠️ This message will be deleted in 20 minutes. Please save it Somewhere.\nJoin to watch more anime 👀💞"
        }
    ])

    warning_msg = await client.send_message(
        chat_id,
        button_choice["message"],
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(button_choice["text"], url=button_choice["url"])]
        ])
    )

    await asyncio.sleep(1200)
    try:
        await video_msg.delete()
        await warning_msg.delete()
    except Exception:
        pass

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
                [
                    InlineKeyboardButton("Jᴏɪɴ Cʜᴀɴɴᴇʟ", url=JOIN_LINK),
                    InlineKeyboardButton("Jᴏɪɴ Nᴏᴡ", url=JOIN_LINK_2)
                ],
                [InlineKeyboardButton("✅ Vᴇʀɪғʏ 🕊️", callback_data=f"verify:{code}")]
            ]
            return await message.reply_text(
                f"Hey [{user.first_name}](tg://user?id={user.id})\n\n"
                "**Pʟᴇᴀsᴇ Jᴏɪɴ Aʟʟ Mʏ Uᴘᴅᴀᴛᴇ Cʜᴀɴɴᴇʟs Tᴏ Usᴇ Mᴇ!**",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        item = collection.find_one({"code": code})
        if item:
            await send_video_with_expiry(client, message.chat.id, item["file_id"], item.get("caption", ""))
        else:
            await message.reply_text("**Iɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ.**")
    else:
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Oᴜʀ Cʜᴀɴɴᴇʟ", url=JOIN_LINK),
                InlineKeyboardButton("Sᴜᴘᴘᴏʀᴛ", url="https://t.me/+STCT2ywFAA0yYjM1")
            ],
            [InlineKeyboardButton("Cʟᴏsᴇ", callback_data="close_msg")]
        ])

        await message.reply_photo(
            photo="https://i.ibb.co/67WkkKr/photo-2025-05-08-14-46-55-7502086450427461668.jpg",
            caption=(
                f"**Hᴇʏ !** [{user.first_name}](tg://user?id={user.id})\n\n"
                "**Wᴇʟᴄᴏᴍᴇ Tᴏ ᴏᴜʀ Sᴛʀᴇᴀᴍɪɴɢ Bᴏᴛ!**\n"
                "Pʟᴇᴀsᴇ Sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ Wɪᴛʜ ʟɪɴᴋ Pʀᴏᴠɪᴅᴇᴅ ɪɴ Cʜᴀɴɴᴇʟ\n"
                "ᴀɴᴅ EɴJᴏʏ ʏᴏᴜʀ Aɴɪᴍᴇ Jᴏᴜʀɴᴇʏ Wɪᴛʜ US."
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
            await send_video_with_expiry(client, callback_query.message.chat.id, item["file_id"], item.get("caption", ""))
        else:
            await callback_query.message.edit_text("**Iɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ.**")
    else:
        await callback_query.answer("Yᴏᴜ'ʀᴇ ɴᴏᴛ Jᴏɪɴᴇᴅ ʏᴇᴛ!", show_alert=True)

@app.on_callback_query(filters.regex("close_msg"))
async def close_msg_handler(client: Client, callback_query):
    await callback_query.message.delete()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("Bot is running...")
    app.run()
