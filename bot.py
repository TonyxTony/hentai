from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = 27184163
API_HASH = "4cf380dd354edc4dc4664f2d4f697393"
BOT_TOKEN = "8185543792:AAH-94mnU2B8gRTr7Nt3X1MH1clLeCa4vvI"

app = Client("inline_post_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Your channel ID and image
CHANNEL_ID = -1002840361612
PHOTO_URL = "https://files.catbox.moe/v630fu.jpg"


CAPTION = (
    "<b>She found out that her husband is cheating on her by fcking her daughter and she can listen to their sx💦👁</b>\n"
    "➠ Episode: 1  20+min\n"
    "➠ Censorship: Censored\n"
    "➠ Rating: 69/10 NTR💋\n\n"
    "<pre>(╭━━━━━━━━━━━━━━━━━━\n"
    "⍟ But her neighbour provokes her by making her wet listening to moans 🥵 and now she wants to fck someone too so now he helps her with the sx🫦💦\n"
    "╰━━━━━━━━━━━━━━━━━━)</pre>"
)

BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("How to Open 💌", url="https://t.me/How_to_open_link5/6"),
        InlineKeyboardButton("Backup 🌚", url="https://t.me/+OIfvzRoudoA2Yjg1")
    ],
    [
        InlineKeyboardButton("🔰 Download 🔰", url="https://adrinolinks.com/2bxE8jJg")
    ]
])

@app.on_message(filters.command("sendnow") & filters.private)
async def send_post_to_channel(client, message):
    try:
        await client.send_photo(
            chat_id=CHANNEL_ID,
            photo=PHOTO_URL,
            caption=CAPTION,
            parse_mode="HTML",  # Real formatting supported on VPS
            reply_markup=BUTTONS
        )
        await message.reply("✅ Post sent to channel.")
    except Exception as e:
        await message.reply(f"❌ Failed to send:\n<code>{e}</code>", parse_mode="HTML")

app.run()
