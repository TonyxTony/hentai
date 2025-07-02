from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
import traceback

API_ID = 27184163
API_HASH = "4cf380dd354edc4dc4664f2d4f697393"
BOT_TOKEN = "8185543792:AAH-94mnU2B8gRTr7Nt3X1MH1clLeCa4vvI"

app = Client("inline_post_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Your channel ID and image
CHANNEL_ID = -1002840361612
PHOTO_URL = "https://files.catbox.moe/najxt7.jpg"

# Caption with <blockquote>
CAPTION = (
    "<b>Its raining today and his shop keeper can't come so now he's alone so he starts watching p@rn in his computer but...🌚\n"
    "➪ Episode: 01 [ 20+min ]\n"
    "➪ Censorship: Censored/n"
    "➪ Rating: 69/10 [ Fck bro she's damn hottttt🔥 ]\n"
    "<blockquote>Highly #recommended\n"
    "The prnstar comes in the shop and asks him to if she\n"
    "can work in the shop for today</blockquote>"
)

BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("How to Open 💌", url="https://t.me/How_to_open_link5/7"),
        InlineKeyboardButton("Backup 🌚", url="https://t.me/+OIfvzRoudoA2Yjg1")
    ],
    [
        InlineKeyboardButton("🔰 Download 🔰", url="https://reel2earn.com/Ck0A2")
    ]
])

@app.on_message(filters.command("sendnow") & filters.private)
async def send_post_to_channel(client, message):
    try:
        await app.send_photo(
            chat_id=CHANNEL_ID,
            photo=PHOTO_URL,
            caption=CAPTION,
            parse_mode=ParseMode.HTML,  # Use enum
            reply_markup=BUTTONS
        )
        await message.reply("✅ Post sent to channel.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply(
            f"❌ Failed to send:\n<code>{e}\n{traceback.format_exc()}</code>",
            parse_mode=ParseMode.HTML
        )

app.run()
