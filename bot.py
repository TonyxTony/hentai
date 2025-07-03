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
hentai_post = db["hentai_post"]

CHARACTERS = string.ascii_letters + string.digits

@server.route("/")
def home():
    return "Bot is running"

def run_flask():
    server.run(host="0.0.0.0", port=8894)

async def is_joined(client: Client, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(UPDATE_CHANNEL, user_id)
        return member.status not in ("left", "kicked")
    except:
        return False
        
async def send_video_with_expiry(client, chat_id, file_id, caption, code=None, send_warning=True):
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
        except:
            pass

        if code:
            bot_username = (await client.get_me()).username
            retrieve_msg = await client.send_message(
                chat_id,
                "📁 **Retrieve Deleted Files**\n⭐This Option is available for **24 hours Only**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔁 Get Again", url=f"https://t.me/{bot_username}?start=retrieve_{code}")]
                ])
            )

            try:
                await asyncio.sleep(40000)
                await retrieve_msg.delete()
            except:
                pass

    asyncio.create_task(delete_later())

def extract_episode_number(caption: str) -> str:
    match = re.search(r"єριѕσ∂є\s*[-:]?\s*(\d+)", caption, re.IGNORECASE)
    return match.group(1).zfill(2) if match else None
    
user_video_data = {}
user_batch_flags = {}
hentai_session = {}

@app.on_message(filters.command("create") & filters.private)
async def start_create(client, message: Message):
    user_id = message.from_user.id
    hentai_session[user_id] = {
        "step": "awaiting_photo",
        "photo": None,
        "caption": None,
        "buttons": [],
        "state": None,
        "add_to_row": None,
        "mode_msg_id": None,
    }
    await message.reply("📸 Please send a photo with or without caption.")


@app.on_message(filters.photo & filters.private)
async def receive_photo(client, message: Message):
    user_id = message.from_user.id
    if user_id not in hentai_session or hentai_session[user_id]["step"] != "awaiting_photo":
        return

    session = hentai_session[user_id]
    session["photo"] = message.photo.file_id
    session["unique_id"] = message.photo.file_unique_id
    session["caption"] = message.caption or None

    if not session["caption"]:
        session["step"] = "awaiting_caption"
        await message.reply("📝 Please send a caption for this photo.")
    else:
        session["step"] = "awaiting_mode"
        await send_preview(client, message.chat.id, user_id)
        reply = await message.reply(
            "Choose button creation mode:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton("Button"), KeyboardButton("Manual")]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        session["mode_msg_id"] = reply.id


@app.on_message(filters.text & filters.private)
async def handle_text(client, message: Message):
    user_id = message.from_user.id
    if user_id not in hentai_session:
        return
    session = hentai_session[user_id]
    text = message.text.strip()

    if session["step"] == "awaiting_caption":
        session["caption"] = text
        session["step"] = "awaiting_mode"
        await send_preview(client, message.chat.id, user_id)
        reply = await message.reply(
            "Choose button creation mode:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton("Button"), KeyboardButton("Manual")]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        session["mode_msg_id"] = reply.id
        return

    if session["step"] == "awaiting_mode":
        try:
            await client.delete_messages(message.chat.id, [message.id, session["mode_msg_id"]])
        except:
            pass

        if text.lower() == "button":
            session["step"] = "adding_buttons"
            await message.reply("✅ Button mode selected. Tap ➕ to begin adding buttons.")
        elif text.lower() == "manual":
            session["step"] = "awaiting_manual_buttons"
            await message.reply("✍️ Send button list like:\n\n`Button 1 : https://link1.com`\n`Button 2 : https://link2.com`\n\nSeparate rows with empty lines.")
        return

    if text.lower() == "done" and session["step"] == "adding_buttons":
        latest_post = hentai_post.find_one(sort=[("post_id", -1)])
        post_id = latest_post["post_id"] + 1 if latest_post else 1

        hentai_post.insert_one({
            "post_id": post_id,
            "file_id": session["photo"],
            "file_unique_id": session["unique_id"],
            "caption": session["caption"],
            "buttons": session["buttons"]
        })

        await client.send_photo(
            chat_id=message.chat.id,
            photo=session["photo"],
            caption=session["caption"],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text=btn["text"], url=btn["url"]) for btn in row]
                for row in session["buttons"]
            ])
        )
        await message.reply(f"✅ Post saved as **#{post_id}**")
        hentai_session.pop(user_id)
        return

    if session["step"] == "awaiting_manual_buttons":
        lines = text.splitlines()
        grouped = []
        temp_row = []

        for line in lines:
            line = line.strip()
            if not line:
                if temp_row:
                    grouped.append(temp_row)
                    temp_row = []
                continue
            match = re.match(r"(.+?)\s*:\s*(https?://\S+)", line)
            if match:
                text_part = match.group(1).strip()
                url_part = match.group(2).strip()
                temp_row.append({"text": text_part, "url": url_part})

        if temp_row:
            grouped.append(temp_row)

        if not grouped:
            await message.reply("❌ No valid buttons found. Try again.")
            return

        latest_post = hentai_post.find_one(sort=[("post_id", -1)])
        post_id = latest_post["post_id"] + 1 if latest_post else 1

        hentai_post.insert_one({
            "post_id": post_id,
            "file_id": session["photo"],
            "file_unique_id": session["unique_id"],
            "caption": session["caption"],
            "buttons": grouped
        })

        await client.send_photo(
            chat_id=message.chat.id,
            photo=session["photo"],
            caption=session["caption"],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text=btn["text"], url=btn["url"]) for btn in row]
                for row in grouped
            ])
        )
        await message.reply(f"✅ Post saved as **#{post_id}**")
        hentai_session.pop(user_id)
        return

    if session.get("state") == "awaiting_button_text":
        session["temp_button"] = {"text": text}
        session["state"] = "awaiting_button_url"
        await message.reply("🔗 Send the URL for this button.")

    elif session.get("state") == "awaiting_button_url":
        if "temp_button" not in session:
            return
        btn = session["temp_button"]
        btn["url"] = text
        row_index = session.get("add_to_row")

        if row_index is not None and row_index < len(session["buttons"]):
            session["buttons"][row_index].append(btn)
        else:
            session["buttons"].append([btn])

        session["temp_button"] = None
        session["state"] = None
        session["add_to_row"] = None
        await send_preview(client, message.chat.id, user_id)


@app.on_callback_query(filters.regex(r"^add_button:(\d+)$"))
async def add_button(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in hentai_session:
        return await query.answer("Session expired. Use /create again.", show_alert=True)

    row_index = int(query.data.split(":")[1])
    hentai_session[user_id]["state"] = "awaiting_button_text"
    hentai_session[user_id]["add_to_row"] = row_index
    await query.message.reply("✏️ Send the **button text**.")
    await query.answer()


def build_keyboard(buttons):
    keyboard = []

    for i, row in enumerate(buttons):
        new_row = [InlineKeyboardButton(text=btn["text"], url=btn["url"]) for btn in row]
        if len(new_row) < 3:
            new_row.append(InlineKeyboardButton("➕", callback_data=f"add_button:{i}"))
        keyboard.append(new_row)

    keyboard.append([InlineKeyboardButton("➕", callback_data=f"add_button:{len(buttons)}")])
    return InlineKeyboardMarkup(keyboard)


async def send_preview(client, chat_id, user_id):
    session = hentai_session[user_id]
    await client.send_photo(
        chat_id,
        photo=session["photo"],
        caption=session["caption"] or "",
        reply_markup=build_keyboard(session["buttons"])
    )


@app.on_message(filters.command("send") & (filters.group | filters.channel | filters.private))
async def send_post_to_chat(client, message: Message):
    if len(message.command) < 2 or not message.command[1].isdigit():
        return await message.reply("❗ Usage: `/send 1`", quote=True)

    post_number = int(message.command[1])
    post = hentai_post.find_one({"post_id": post_number})

    if not post:
        return await message.reply("❌ Post not found.", quote=True)

    await client.send_photo(
        chat_id=message.chat.id,
        photo=post["file_id"],
        caption=post["caption"],
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text=btn["text"], url=btn["url"]) for btn in row]
            for row in post["buttons"]
        ])
    )

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

@app.on_message(filters.private & filters.command("start"))
async def start_command(client: Client, message: Message):
    user = message.from_user
    args = message.text.split()
    is_retrieve = False

    if len(args) > 1:
        code = args[1]
        if code.startswith("retrieve_"):
            is_retrieve = True
            code = code.replace("retrieve_", "")

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
            if item.get("batch"):
                total = len(item["videos"])
                for idx, video in enumerate(item["videos"]):
                    await send_video_with_expiry(
                        client,
                        message.chat.id,
                        video["file_id"],
                        video.get("caption", ""),
                        code=code,
                        send_warning=(idx == total - 1)
                    )
            else:
                await send_video_with_expiry(
                    client,
                    message.chat.id,
                    item["file_id"],
                    item.get("caption", ""),
                    code=code
                )

            if is_retrieve:
                await client.send_message(
                    LOG_GROUP,
                    f"🔁 Retrieved via Button\n"
                    f"Code = `{code}`\n"
                    f"User: [{user.first_name}](tg://user?id={user.id})"
                )

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
        item = hentai_collection.find_one({"code": code})
        if item:
            await callback_query.message.edit_text("**Tʜᴀɴᴋs! Tᴏ Bᴇ ᴘᴀʀᴛ ᴏғ Oᴜʀ Cʜᴀɴɴᴇʟ Sᴇɴᴅɪɴɢ ʏᴏᴜʀ ᴠɪᴅᴇᴏ...**")
            if item.get("batch"):
                total = len(item["videos"])
                for idx, video in enumerate(item["videos"]):
                    await send_video_with_expiry(
                        client,
                        callback_query.message.chat.id,
                        video["file_id"],
                        video.get("caption", ""),
                        code=code,
                        send_warning=(idx == total - 1)
                    )
            else:
                await send_video_with_expiry(
                    client,
                    callback_query.message.chat.id,
                    item["file_id"],
                    item.get("caption", ""),
                    code=code
                )

            await client.send_message(
                LOG_GROUP,
                f"📁 File sent via Verify Button\n"
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
    data = hentai_collection.find_one({"code": code})

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

@app.on_message(filters.command("db"))
async def db_stats(_, message: Message):
    count = hentai_collection.count_documents({})
    await message.reply_text(f"📁 Total Episodes videos stored in DB: `{count}`")
    
if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("Bot is running...")
    app.run()
