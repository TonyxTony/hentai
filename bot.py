from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import pymongo
from random import choice
from flask import Flask
import string
import re
from threading import Thread
import asyncio

API_ID = 27184163
API_HASH = "4cf380dd354edc4dc4664f2d4f697393"
BOT_TOKEN = "7644463386:AAH4Pp8r17q8OP1hUAYPh3e2u3SwBCHk6uI"
OWNERS_ID = (6600178606, 7893840561, 7530506703, 7240796549, 7169672824)
UPDATE_CHANNEL = -1002623332025
UPDATE_CHANNEL_2 = -1002799540890
JOIN_LINK_2 = "https://t.me/+j9jofBdlxjQwY2Vl"
JOIN_LINK = "https://t.me/+PngidWDJgiI2NjU1"
LOG_GROUP = -1002815905957
backup_channel_id = -1002815905957

MONGO_URI = "mongodb+srv://Anime:Tony123@animedb.veb4qyk.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "anime_stream"
COLLECTION_NAME = "stream_db"

app = Client("AnimeBot3", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
server = Flask(__name__)

mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]
channel_episode = db["channel_episode"]
hentai_collection = db["hentai_db"]
hentai_backup = db["hentai_backup"]

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
            "text": "Overflow Season 2 💌",
            "url": "https://t.me/+oPJAKgZ4_1QxYjZl",
            "message": "⚠️ This message will be deleted in 20 minutes. Please save it Somewhere.."
        },
        {
            "text": "More Hentai 🍌",
            "url": "https://t.me/Anime_spectrum_official",
            "message": "⚠️ This message will be deleted in 20 minutes. Please save it Somewhere.\nJoin to watch more hentai 💞"
        }
    ])

    warning_msg = await client.send_message(
        chat_id,
        button_choice["message"],
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(button_choice["text"], url=button_choice["url"])]
        ])
    )

    async def delete_later():
        await asyncio.sleep(1000)
        try:
            await video_msg.delete()
            await warning_msg.delete()
        except:
            pass

    asyncio.create_task(delete_later())

def extract_episode_number(caption: str) -> str:
    match = re.search(r"єριѕσ∂є\s*[-:]?\s*(\d+)", caption, re.IGNORECASE)
    return match.group(1).zfill(2) if match else None
    
user_video_data = {}

@app.on_message(filters.private & filters.command("createlink"))
async def create_link(client: Client, message: Message):
    if message.from_user.id not in OWNERS_ID:
        return
    user_id = message.from_user.id
    user_video_data[user_id] = []
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("Send videos"), KeyboardButton("Close")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.reply_text("Okie, now choose an option:", reply_markup=keyboard)

@app.on_message(filters.private & filters.text & filters.regex("^(Send videos|Done|Cancel|Close)$"))
async def handle_buttons(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in OWNERS_ID:
        return
    text = message.text
    if text == "Close" or text == "Cancel":
        user_video_data.pop(user_id, None)
        await message.reply_text("Cancellation Successful", reply_markup=ReplyKeyboardRemove())
        return
    if text == "Send videos":
        keyboard = ReplyKeyboardMarkup(
            [
                [KeyboardButton("Done"), KeyboardButton("Cancel")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.reply_text(
            'Okie, send videos with captions, then tap "Done" when finished.',
            reply_markup=keyboard
        )
        return
    if text == "Done":
        if user_id not in user_video_data or not user_video_data[user_id]:
            await message.reply_text(
                "No videos were sent. Process cancelled.",
                reply_markup=ReplyKeyboardRemove()
            )
            user_video_data.pop(user_id, None)
            return

        bot_username = (await client.get_me()).username
        episode_links = []

        for video_data in user_video_data[user_id]:
            file_unique_id = video_data["file_unique_id"]
            file_id = video_data["file_id"]
            caption = video_data["caption"]
            message_id = video_data["message_id"]

            existing = hentai_collection.find_one({"file_unique_id": file_unique_id})
            if existing:
                link = f"https://t.me/{bot_username}?start={existing['code']}"
                episode_number = extract_episode_number(caption)
                episode_links.append(f"Episode {episode_number}: {link}" if episode_number else f"{link}")
                await message.reply_text(
                    f"Video already has a link:\n\n{link}",
                    reply_to_message_id=message_id
                )
                continue

            while True:
                code = "".join(choice(CHARACTERS) for _ in range(12))
                if not collection.find_one({"code": code}):
                    break

            try:
                backup_msg = await client.send_video(
                    chat_id=backup_channel_id,
                    video=file_id,
                    caption=caption
                )
            except Exception as e:
                await message.reply_text(
                    f"❌ Failed to send to backup channel:\n`{e}`",
                    reply_to_message_id=message_id
                )
                continue

            hentai_collection.insert_one({
                "code": code,
                "file_unique_id": file_unique_id,
                "file_id": file_id,
                "caption": caption
            })
            hentai_backup.insert_one({
                "code": code,
                "file_unique_id": file_unique_id,
                "file_id": file_id,
                "caption": caption,
                "channel_id": backup_channel_id,
                "message_id": backup_msg.id
            })

            link = f"https://t.me/{bot_username}?start={code}"
            episode_number = extract_episode_number(caption)
            episode_links.append(f"Episode {episode_number}: {link}" if episode_number else f"{link}")

            await message.reply_text(
                f"✅ Link created successfully:\n{link}",
                reply_to_message_id=message_id
            )

        user_video_data.pop(user_id, None)

        if episode_links:
            result = "\n".join(episode_links)
            await message.reply_text(f"{result}", reply_markup=ReplyKeyboardRemove())
        else:
            await message.reply_text("All videos processed but no links generated.", reply_markup=ReplyKeyboardRemove())
            
@app.on_message(filters.private & filters.video)
async def collect_videos(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in OWNERS_ID or user_id not in user_video_data:
        return
    if not message.caption:
        await message.reply_text("Please include a caption with the video.")
        return
    user_video_data[user_id].append({
        "file_unique_id": message.video.file_unique_id,
        "file_id": message.video.file_id,
        "caption": message.caption,
        "message_id": message.id
    })

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

        item = hentai_collection.find_one({"code": code})
        if item:
            await send_video_with_expiry(client, message.chat.id, item["file_id"], item.get("caption", ""))
            await client.send_message(
                LOG_GROUP,
                f"A ɴᴇᴡ Vɪᴅᴇᴏ ɪs ᴘʀᴏᴠɪᴅᴇᴅ Bʏ **hentai**\nCᴏᴅᴇ = `{code}`\nTᴏ : [{user.first_name}](tg://user?id={user.id})"
            )
        else:
            exists = hentai_collection.find_one({"code": code}) is not None
            await message.reply_text("**Iɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ.**")
            await client.send_message(
                LOG_GROUP,
                f"Bᴀʙʏ I ғᴏᴜɴᴅ A ʙʀᴏᴋᴇɴ Eᴘɪsᴏᴅᴇ\nCᴏᴅᴇ : `{code}`\nFᴏᴜɴᴅ Iɴ ᴅᴀᴛᴀʙᴀsᴇ : **{exists}**\n\n@O0_oo_O0_o0o @baki_lll**"
            )
    else:
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Oᴜʀ Cʜᴀɴɴᴇʟ", url=JOIN_LINK),
                InlineKeyboardButton("Sᴜᴘᴘᴏʀᴛ", url="https://t.me/+STCT2ywFAA0yYjM1")
            ],
            [InlineKeyboardButton("Cʟᴏsᴇ", callback_data="close_msg")]
        ])

        await message.reply_photo(
            photo="https://i.ibb.co/67WkkKrj/photo-2025-05-08-14-46-55-7502086450427461668.jpg",
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
    user = callback_query.from_user

    if await is_joined(client, user.id):
        item = collection.find_one({"code": code})
        if item:
            await callback_query.message.edit_text("**Tʜᴀɴᴋs! Tᴏ Bᴇ ᴘᴀʀᴛ ᴏғ Oᴜʀ Cʜᴀɴɴᴇʟ Sᴇɴᴅɪɴɢ ʏᴏᴜʀ ᴠɪᴅᴇᴏ...**")
            await send_video_with_expiry(client, callback_query.message.chat.id, item["file_id"], item.get("caption", ""))
            await client.send_message(
                LOG_GROUP,
                f"A ɴᴇᴡ Vɪᴅᴇᴏ ɪs ᴘʀᴏᴠɪᴅᴇᴅ Bʏ **hentai**\nCᴏᴅᴇ = `{code}`\nTᴏ : [{user.first_name}](tg://user?id={user.id})"
            )
        else:
            exists = hentai_collection.find_one({"code": code}) is not None
            await callback_query.message.edit_text("**Iɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ.**")
            await client.send_message(
                LOG_GROUP,
                f"Bᴀʙʏ I ғᴏᴜɴᴅ A ʙʀᴏᴋᴇɴ Eᴘɪsᴏᴅᴇ\nCᴏᴅᴇ : `{code}`\nFᴏᴜɴᴅ Iɴ ᴅᴀᴛᴀʙᴀsᴇ : **{exists}**\n\n@O0_oo_O0_o0o @baki_lll**"
            )
    else:
        await callback_query.answer("Yᴏᴜ'ʀᴇ ɴᴏᴛ Jᴏɪɴᴇᴅ ʏᴇᴛ!", show_alert=True)

@app.on_callback_query(filters.regex("close_msg"))
async def close_msg_handler(client: Client, callback_query):
    await callback_query.message.delete()

@app.on_message(filters.command("check"))
async def check_code(_, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/check <code>`", quote=True)

    code = message.text.split(None, 1)[1].strip()
    data = hentai_collection.find_one({"code": code})  # <- no await for pymongo

    if not data:
        return await message.reply_text(f"❌ No video found with code: `{code}`", quote=True)

    file_id = data.get("file_id")
    caption = data.get("caption", "")

    await message.reply_video(video=file_id, caption=caption)

@app.on_message(filters.command("db"))
async def db_stats(_, message: Message):
    count = hentai_collection.count_documents({})
    await message.reply_text(f"📁 Total Episodes videos stored in DB: `{count}`")

@app.on_message(filters.command("backuphentai"))
async def backup_to_channel(client, message):
    backup_channel_id = -1002815905957  # replace with your channel ID
    all_docs = list(hentai_collection.find())
    total = len(all_docs)

    if total == 0:
        return await message.reply("❌ No documents found in the collection.")

    success = 0
    failed = 0
    checked = 0
    last_msg_id = None

    status = await message.reply(
        f"📦 Total: `{total}`\n"
        f"🔍 Checked: `{checked}`\n"
        f"✅ Success: `{success}`\n"
        f"❌ Failed: `{failed}`\n"
        f"🆔 Last Msg ID: `...`"
    )

    for doc in all_docs:
        code = doc.get("code")
        checked += 1

        if not code:
            failed += 1
            await status.edit(
                f"📦 Total: `{total}`\n"
                f"🔍 Checked: `{checked}`\n"
                f"✅ Success: `{success}`\n"
                f"❌ Failed: `{failed}`\n"
                f"🆔 Last Msg ID: `{last_msg_id}`"
            )
            continue

        data = hentai_collection.find_one({"code": code})
        if not data:
            failed += 1
            await status.edit(
                f"📦 Total: `{total}`\n"
                f"🔍 Checked: `{checked}`\n"
                f"✅ Success: `{success}`\n"
                f"❌ Failed: `{failed}`\n"
                f"🆔 Last Msg ID: `{last_msg_id}`"
            )
            continue

        file_id = data.get("file_id")
        caption = data.get("caption", "")
        file_unique_id = data.get("file_unique_id")

        try:
            sent = await client.send_video(
                chat_id=backup_channel_id,
                video=file_id,
                caption=caption
            )
            last_msg_id = sent.id

            insert_data = {
                "code": code,
                "file_id": file_id,
                "file_unique_id": file_unique_id,
                "caption": caption,
                "channel_id": str(backup_channel_id),
                "message_id": sent.id
            }

            hentai_backup.insert_one(insert_data)
            success += 1

        except Exception as e:
            print(f"❌ Failed on code {code}: {e}")
            failed += 1

        await status.edit(
            f"📦 Total: `{total}`\n"
            f"🔍 Checked: `{checked}`\n"
            f"✅ Success: `{success}`\n"
            f"❌ Failed: `{failed}`\n"
            f"🆔 Last Msg ID: `{last_msg_id}`"
        )

        await asyncio.sleep(6)

    await status.edit(
        f"✅ **Backup Completed**\n\n"
        f"📦 Total: `{total}`\n"
        f"🔍 Checked: `{checked}`\n"
        f"✅ Success: `{success}`\n"
        f"❌ Failed: `{failed}`\n"
        f"🆔 Last Msg ID: `{last_msg_id}`"
    )
    
if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("Bot is running...")
    app.run()
