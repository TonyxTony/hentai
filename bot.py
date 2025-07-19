from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton
)
import re
from flask import Flask
from threading import Thread
import asyncio
import threading
from pyrogram.types import KeyboardButton, ReplyKeyboardMarkup

API_ID = 27184163
API_HASH = "4cf380dd354edc4dc4664f2d4f697393"
BOT_TOKEN = "8185543792:AAH-94mnU2B8gRTr7Nt3X1MH1clLeCa4vvI"

app = Client("create_button_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
server = Flask(__name__)

@server.route("/")
def home():
    return "Bot is running"

def run_flask():
    server.run(host="0.0.0.0", port=8897)

user_sessions = {}
saved_posts = {}
post_counter_lock = threading.Lock()
post_counter = 2

@app.on_message(filters.command("create") & filters.private)
async def start_create(client, message: Message):
    user_id = message.from_user.id
    user_sessions[user_id] = {
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
    if user_id not in user_sessions or user_sessions[user_id]["step"] != "awaiting_photo":
        return

    session = user_sessions[user_id]
    session["photo"] = message.photo.file_id
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
    global post_counter
    user_id = message.from_user.id
    if user_id not in user_sessions:
        return

    session = user_sessions[user_id]
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
        except Exception as e:
            print(f"Error deleting messages: {e}")

        if text.lower() == "button":
            session["step"] = "adding_buttons"
            await message.reply("✅ Button mode selected. Tap ➕ to begin adding buttons.")
        elif text.lower() == "manual":
            session["step"] = "awaiting_manual_buttons"
            await message.reply(
                "✍️ Send button list like:\n\n`Button 1 : https://link1.com`\n`Button 2 : https://link2.com`\n\nSeparate rows with empty lines."
            )
        return

    if text.lower() == "done" and session["step"] == "adding_buttons":
        saved_posts[post_counter] = {
            "photo": session["photo"],
            "caption": session["caption"],
            "buttons": session["buttons"]
        }
        await client.send_photo(
            chat_id=message.chat.id,
            photo=session["photo"],
            caption=session["caption"],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text=btn["text"], url=btn["url"]) for btn in row]
                for row in session["buttons"]
            ])
        )
        await message.reply(f"✅ Post saved as **#{post_counter}**")
        post_counter += 1
        user_sessions.pop(user_id)
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

        saved_posts[post_counter] = {
            "photo": session["photo"],
            "caption": session["caption"],
            "buttons": grouped
        }
        await client.send_photo(
            chat_id=message.chat.id,
            photo=session["photo"],
            caption=session["caption"],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text=btn["text"], url=btn["url"]) for btn in row]
                for row in grouped
            ])
        )
        await message.reply(f"✅ Post saved as **#{post_counter}**")
        post_counter += 1
        user_sessions.pop(user_id)
        return

    if session.get("state") == "awaiting_button_text":
        session["temp_button"] = {"text": text}
        session["state"] = "awaiting_button_url"
        await message.reply("🔗 Send the URL for this button.")

    elif session.get("state") == "awaiting_button_url":
        if "temp_button" not in session:
            return
        btn = session["temp_button"]
        if not re.match(r"https?://\S+", text):
            await message.reply("❌ Invalid URL. Please send a valid URL (e.g., https://example.com).")
            return
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
    if user_id not in user_sessions:
        return await query.answer("Session expired. Use /create again.", show_alert=True)

    row_index = int(query.data.split(":")[1])
    user_sessions[user_id]["state"] = "awaiting_button_text"
    user_sessions[user_id]["add_to_row"] = row_index
    await query.message.reply("✏️ Send the **button text**.")
    await query.answer()

def build_keyboard(buttons):
    keyboard = []
    for i, row in enumerate(buttons):
        new_row = [InlineKeyboardButton(text=btn["text"], url=btn["url"]) for btn in row]
        if len(new_row) < 3:
            new_row.append(InlineKeyboardButton("➕", callback_data=f"add_button:{i}"))
        keyboard.append(new_row)
    if len(buttons) < 8:
        keyboard.append([InlineKeyboardButton("➕", callback_data=f"add_button:{len(buttons)}")])
    return InlineKeyboardMarkup(keyboard)

async def send_preview(client, chat_id, user_id):
    session = user_sessions[user_id]
    await client.send_photo(
        chat_id,
        photo=session["photo"],
        caption=session["caption"] or "",
        reply_markup=build_keyboard(session["buttons"])
    )

@app.on_message(filters.command("send") & (filters.group | filters.channel | filters.private))
async def send_post_to_chat(client, message: Message):
    try:
        if message.reply_to_message and message.reply_to_message.text:
            match = re.search(r"#(\d+)", message.reply_to_message.text)
            if not match:
                return await message.reply("❌ No post number found in the replied message.", quote=True)
            post_number = int(match.group(1))
        elif len(message.command) >= 2 and message.command[1].isdigit():
            post_number = int(message.command[1])
        else:
            return await message.reply("❗ Usage: `/send 1` or reply to a saved post.", quote=True)

        if post_number not in saved_posts:
            return await message.reply(f"❌ Post #{post_number} not found.", quote=True)

        post = saved_posts[post_number]
        if not post.get("photo") or not post.get("buttons"):
            return await message.reply(f"❌ Post #{post_number} is invalid or missing data.", quote=True)

        await client.send_photo(
            chat_id=message.chat.id,
            photo=post["photo"],
            caption=post["caption"],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text=btn["text"], url=btn["url"]) for btn in row]
                for row in post["buttons"]
            ])
        )
    except Exception as e:
        await message.reply(f"❌ Error sending post: {str(e)}", quote=True)

@app.on_message(filters.command("setrange"))
async def send_post_range(client, message: Message):
    if len(message.command) != 3:
        return await message.reply("❗ Usage: `/setrange <start> <end>`", quote=True)

    try:
        start = int(message.command[1])
        end = int(message.command[2])
        if start > end:
            return await message.reply("❌ Start number must be less than or equal to end number.", quote=True)

        for post_number in range(start, end + 1):
            if post_number not in saved_posts:
                continue
            post = saved_posts[post_number]
            if not post.get("photo") or not post.get("buttons"):
                continue

            try:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=post["photo"],
                    caption=post["caption"],
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(text=btn["text"], url=btn["url"]) for btn in row]
                        for row in post["buttons"]
                    ])
                )
                await asyncio.sleep(4)  # 4-second gap between posts
            except Exception as e:
                await message.reply(f"⚠️ Failed to send post #{post_number}: {str(e)}", quote=True)

    except ValueError:
        await message.reply("❌ Invalid range. Please use numbers.", quote=True)
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}", quote=True)

@app.on_message(filters.forwarded & filters.photo & filters.chat(-1002815905957))
async def save_forwarded_post(client, message: Message):
    global post_counter

    if not message.caption or not message.reply_markup or not isinstance(message.reply_markup, InlineKeyboardMarkup):
        return await message.reply("❌ Forwarded post must have a caption and inline buttons.")

    buttons = []
    for row in message.reply_markup.inline_keyboard:
        button_row = []
        for btn in row:
            if btn.url:
                button_row.append({"text": btn.text, "url": btn.url})
        if button_row:
            buttons.append(button_row)

    if not buttons:
        return await message.reply("❌ No valid buttons found in the forwarded post.")

    with post_counter_lock:
        current_post_number = post_counter
        post_counter += 1

    saved_posts[current_post_number] = {
        "photo": message.photo.file_id,
        "caption": message.caption,
        "buttons": buttons
    }

    await message.reply(f"✅ Forwarded post saved as **#{current_post_number}**")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("Bot is running...")
    app.run()
