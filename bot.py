# full_bot_with_userbot.py
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
import logging

# ---------- CONFIG - fill these ----------
API_ID = 27184163
API_HASH = "4cf380dd354edc4dc4664f2d4f697393"
BOT_TOKEN = "7644463386:AAH4Pp8r17q8OP1hUAYPh3e2u3SwBCHk6uI"

# Put your userbot string session here (YOU'LL FILL)
STRING_SESSION = "BQJgTiUAt3J9ZkBE5Xp3sil0L2Ck-peg3IBOb-xdZhq48bD_Q_pGPYqPKY-Z7W8mE7dTW5SfrTAxdqbxneHOhNOiFZUfMILOOtW1K7LBCKOnYN_7AE7ZugzGaUfQOIkpRIph8AUEnWZ_Qw42_DGmvG0oBG8SyRnvCrT3eJYlot8f-mHkRpEHxdGx0CtabweLCceJEx-A0D_VOY1IAkZOg-fujaZ-YchrIXtPXJE6H1DweVTuVyzNj1r4WR7iGZSGE3oRgzIOArxLYL1lsPJ82bJWXuRz7mzKU9kLQwPeD9NliZcuoa7y14Y9io0aySFBvzzbJEQ6pe22fEpuQt7TWl0Ho-aZzAAAAAGVhmcLAA"

# Put the group/channel id that user MUST join (YOU'LL FILL)
REQUIRED_GROUP = -1003429554283

# Video shown on /start when user uses a code (YOU'LL FILL)
START_VIDEO_LINK = "https://files.catbox.moe/q3smxs.mp4"
# ----------------------------------------

OWNERS_ID = (6600178606, 7893840561, 7530506703, 7240796549, 7169672824)
UPDATE_CHANNEL = -1003245461257
UPDATE_CHANNEL_2 = -1003160341764
UPDATE_CHANNEL_3 = -1002611120947
JOIN_LINK_3 = "https://t.me/+OJs417INvdQyNGI1"
JOIN_LINK_2 = "https://t.me/+sD4RWFdI8ZJiYmU1"
JOIN_LINK = "https://t.me/+n8Of2W18X1Q1Y2Zl"

LOG_GROUP = -1002815905957
backup_channel_id = -1002815905957

MONGO_URI = "mongodb+srv://Anime:Tony123@animedb.veb4qyk.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "anime_stream"
COLLECTION_NAME = "stream_db"

# Initialize bot client and userbot client
app = Client("AnimeBot3", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
# userbot will run as a secondary Pyrogram Client (uses a user account session string)
userbot = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

# Flask server for uptime
server = Flask(__name__)

# Mongo
mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]
channel_episode = db["channel_episode"]
hentai_collection = db["hentai_db"]
hentai_backup = db["hentai_backup"]

CHARACTERS = string.ascii_letters + string.digits

# Logging (optional)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@server.route("/")
def home():
    return "Bot is running"


def run_flask():
    server.run(host="0.0.0.0", port=8894)


async def send_video_with_expiry(client, chat_id, file_id, caption, send_warning=True):
    """
    Send a video and optionally send a warning message that is deleted later.
    """
    video_msg = await client.send_video(chat_id, file_id, caption=caption)

    if send_warning:
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
    else:
        warning_msg = None

    async def delete_later():
        await asyncio.sleep(1000)
        try:
            await video_msg.delete()
            if warning_msg:
                await warning_msg.delete()
        except Exception:
            pass

    asyncio.create_task(delete_later())


def extract_episode_number(caption: str) -> str:
    match = re.search(r"єριѕσ∂є\s*[-:]?\s*(\d+)", caption, re.IGNORECASE)
    return match.group(1).zfill(2) if match else None


# these hold temporary state while owner constructs links
user_video_data = {}
user_batch_flags = {}


# ----------------- Createlink flow (unchanged) -----------------
@app.on_message(filters.private & filters.command("createlink"))
async def create_link(client: Client, message: Message):
    if message.from_user.id not in OWNERS_ID:
        return

    user_id = message.from_user.id
    user_video_data[user_id] = []
    user_batch_flags[user_id] = None

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Normal", callback_data="clink_normal"),
         InlineKeyboardButton("📦 Batch", callback_data="clink_batch")]
    ])
    await message.reply_text("Choose upload mode:", reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^clink_(normal|batch)$"))
async def handle_createlink_mode(client: Client, callback_query):
    user_id = callback_query.from_user.id
    mode = callback_query.data.split("_")[1]

    if mode == "normal":
        user_batch_flags[user_id] = False
        keyboard = ReplyKeyboardMarkup([
            [KeyboardButton("Done"), KeyboardButton("Cancel")]
        ], resize_keyboard=True, one_time_keyboard=True)

        await callback_query.message.reply_text(
            "Send videos with captions Tap **Done** when finished.",
            reply_markup=keyboard
        )

    elif mode == "batch":
        user_batch_flags[user_id] = True
        keyboard = ReplyKeyboardMarkup([
            [KeyboardButton("Done"), KeyboardButton("Cancel")]
        ], resize_keyboard=True, one_time_keyboard=True)

        await callback_query.message.reply_text(
            "Batch mode enabled.\nSend multiple videos (with captions), then tap **Done**.",
            reply_markup=keyboard
        )

    await callback_query.message.delete()


@app.on_message(filters.private & filters.text & filters.regex("^(Done|Cancel)$"))
async def handle_done_or_cancel(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in OWNERS_ID:
        return

    text = message.text

    if text == "Cancel":
        user_video_data.pop(user_id, None)
        user_batch_flags.pop(user_id, None)
        await message.reply_text("❌ Process cancelled.", reply_markup=ReplyKeyboardRemove())
        return

    if text == "Done":
        videos = user_video_data.get(user_id, [])
        is_batch = user_batch_flags.get(user_id, False)

        if not videos:
            await message.reply_text("⚠️ No videos received.", reply_markup=ReplyKeyboardRemove())
            return

        bot_username = (await client.get_me()).username

        if not is_batch:
            # Normal Mode (existing logic)
            for video_data in videos:
                file_unique_id = video_data["file_unique_id"]
                file_id = video_data["file_id"]
                caption = video_data["caption"]
                message_id = video_data["message_id"]

                existing = hentai_collection.find_one({"file_unique_id": file_unique_id})
                if existing:
                    link = f"https://t.me/{bot_username}?start={existing['code']}"
                    await message.reply_text(f"Video already has a link:\n\n{link}", reply_to_message_id=message_id)
                    continue

                while True:
                    code = "".join(choice(CHARACTERS) for _ in range(12))
                    if not hentai_collection.find_one({"code": code}):
                        break

                try:
                    backup_msg = await client.send_video(backup_channel_id, file_id, caption=caption)
                except Exception as e:
                    await message.reply_text(f"❌ Backup failed:\n`{e}`", reply_to_message_id=message_id)
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
                await message.reply_text(f"✅ Link created:\n{link}", reply_to_message_id=message_id)

        else:
            # Batch Mode
            while True:
                code = "".join(choice(CHARACTERS) for _ in range(12))
                if not hentai_collection.find_one({"code": code}):
                    break

            media_array = []

            for video_data in videos:
                file_id = video_data["file_id"]
                caption = video_data["caption"]
                file_unique_id = video_data["file_unique_id"]
                try:
                    backup_msg = await client.send_video(backup_channel_id, file_id, caption=caption)
                except Exception as e:
                    await message.reply_text(f"❌ Backup failed:\n`{e}`", reply_to_message_id=video_data["message_id"])
                    continue

                media_array.append({
                    "file_id": file_id,
                    "file_unique_id": file_unique_id,
                    "caption": caption
                })

            hentai_collection.insert_one({
                "code": code,
                "batch": True,
                "videos": media_array
            })

            link = f"https://t.me/{bot_username}?start={code}"
            await message.reply_text(f"✅ Batch link created:\n{link}")

        user_video_data.pop(user_id, None)
        user_batch_flags.pop(user_id, None)
        await message.reply("✅ All videos processed.", reply_markup=ReplyKeyboardRemove())


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


# ----------------- START COMMAND (modified to use userbot check flow) -----------------
@app.on_message(filters.private & filters.command("start"))
async def start_command(client: Client, message: Message):
    user = message.from_user
    args = message.text.split()

    # If user started with a code (e.g., /start <code>)
    if len(args) > 1:
        code = args[1]
        # Do not force-join here. Show join message + video + verify button.
        item = hentai_collection.find_one({"code": code})

        if item:
            buttons = [
                [
                    InlineKeyboardButton("Join Now", url="https://t.me/invit_link_bot?start=00002ZYtyG"),
                ],
                [
                    InlineKeyboardButton("Verify", callback_data=f"verify_new:{code}")
                ]
            ]

            # If you want to show a video preview when code used:
            try:
                await message.reply_video(
                    video=START_VIDEO_LINK,
                    caption="**Steps: Click the button\n\n🪺 Enter the chat ka option ayega\n🪺 Phir uske bad yek math ka question solve kroge to\n\n🪺 Phir join ka option aa jayegaJoin krne ke bad video aa jayegi Bot me**",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            except Exception:
                # Fallback to photo if the video link fails or is blocked
                await message.reply_text(
                    "**Join my Groups**",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            return

        else:
            exists = hentai_collection.find_one({"code": code}) is not None
            await message.reply_text("**Iɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ.**")
            await client.send_message(
                LOG_GROUP,
                f"Bᴀʙʏ I ғᴏᴜɴᴅ A ʙʀᴏᴋᴇɴ Eᴘɪsᴏᴅᴇ\n"
                f"Cᴏᴅᴇ : `{code}`\n"
                f"Fᴏᴜɴᴅ Iɴ ᴅᴀᴛᴀʙᴀsᴇ : **{exists}**\n\n"
                f"@O0_oo_O0_o0o @baki_lll"
            )
            return

    # When no code provided, show a generic start message (original behavior)
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


# ----------------- VERIFY HANDLER (uses userbot to check membership) -----------------
# Note: userbot does NOT need to be admin to check membership in public/join-by-link groups.
async def is_user_joined(user_id: int, chat_id: int):
    try:
        member = await userbot.get_chat_member(chat_id, user_id)
        if member.status in ("left", "kicked"):
            return False
        return True
    except UserNotParticipant:
        return False
    except Exception:
        # Could be privacy/flood or other error; treat as not joined
        logger.exception("Error checking membership via userbot")
        return False


@app.on_callback_query(filters.regex(r"^verify_new:(.+)"))
async def verify_new(client, callback_query):
    code = callback_query.data.split(":")[1]
    user = callback_query.from_user
    user_id = user.id

    # Check membership using userbot. Replace REQUIRED_GROUP with the group you want to enforce.
    joined = await is_user_joined(user_id, REQUIRED_GROUP)

    if not joined:
        # If user NOT joined, show an alert and do not send the video.
        return await callback_query.answer("❌ Please join the required group first!", show_alert=True)

    item = hentai_collection.find_one({"code": code})

    if item:
        await callback_query.message.edit_text("**Tʜᴀɴᴋs! Sending your video...**")

        # ✅ Handle batch
        if item.get("batch"):
            total = len(item["videos"])
            for idx, video in enumerate(item["videos"]):
                await send_video_with_expiry(
                    client,
                    callback_query.message.chat.id,
                    video["file_id"],
                    video.get("caption", ""),
                    send_warning=(idx == total - 1)
                )
            await client.send_message(
                LOG_GROUP,
                f"📦 Batch of {total} videos sent via verify.\n"
                f"Code: `{code}`\n"
                f"To: [{user.first_name}](tg://user?id={user.id})"
            )
            return

        # ✅ Single video
        await send_video_with_expiry(
            client,
            callback_query.message.chat.id,
            item["file_id"],
            item.get("caption", "")
        )
        await client.send_message(
            LOG_GROUP,
            f"A ɴᴇᴡ Vɪᴅᴇᴏ ɪs ᴘʀᴏᴠɪᴅᴇᴅ Bʏ **hentai**\n"
            f"Cᴏᴅᴇ = `{code}`\n"
            f"Tᴏ : [{user.first_name}](tg://user?id={user.id})"
        )
    else:
        exists = hentai_collection.find_one({"code": code}) is not None
        await callback_query.message.edit_text("**Iɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ.**")
        await client.send_message(
            LOG_GROUP,
            f"Bᴀʙʏ I ғᴏᴜɴᴅ A ʙʀᴏᴋᴇɴ Eᴘɪsᴏᴅᴇ\n"
            f"Cᴏᴅᴇ : `{code}`\n"
            f"Fᴏᴜɴᴅ Iɴ ᴅᴀᴛᴀʙᴀsᴇ : **{exists}**\n\n"
            f"@O0_oo_O0_o0o @baki_lll"
        )


# ----------------- Close message handler (unchanged) -----------------
@app.on_callback_query(filters.regex("close_msg"))
async def close_msg_handler(client: Client, callback_query):
    await callback_query.message.delete()


# ----------------- check command (unchanged) -----------------
@app.on_message(filters.command("check"))
async def check_code(_, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/check <code>`", quote=True)

    code = message.text.split(None, 1)[1].strip()
    data = hentai_collection.find_one({"code": code})  # pymongo, no await

    if not data:
        return await message.reply_text(f"❌ No video found with code: `{code}`", quote=True)

    if data.get("batch"):
        for video in data["videos"]:
            await message.reply_video(
                video=video["file_id"],
                caption=video.get("caption", "")
            )
    else:
        await message.reply_video(
            video=data["file_id"],
            caption=data.get("caption", "")
        )


# ----------------- db stats (unchanged) -----------------
@app.on_message(filters.command("db"))
async def db_stats(_, message: Message):
    count = hentai_collection.count_documents({})
    await message.reply_text(f"📁 Total Episodes videos stored in DB: `{count}`")


# ----------------- backup hentai (unchanged) -----------------
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


# ----------------- run both bot and userbot -----------------
if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("Bot is running...")

    # Start the userbot first (so it can answer membership checks)
    try:
        userbot.start()
        logger.info("Userbot started.")
    except Exception as e:
        logger.exception("Failed to start userbot. Make sure STRING_SESSION is set correctly.")
        # If you want the script to stop when userbot fails, uncomment the next line:
        # raise

    # Start the bot (this will block)
    try:
        app.run()
    finally:
        # Ensure userbot stops cleanly on exit
        try:
            userbot.stop()
            logger.info("Userbot stopped.")
        except Exception:
            pass
