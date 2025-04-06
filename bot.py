from pyrogram import Client, filters
import aiohttp
import asyncio

app = Client("terabox_bot", api_id="25321403", api_hash="0024ae3c978ba534b1a9bffa29e9cc9b", bot_token="7997809826:AAGUMLWI54X7wmdXq6cKqfhNKPsimHAiMfk")

async def get_download_url(terabox_link):
    # Construct the processing URL
    processing_url = f"https://teraboxdownloader.in/video-downloader?link={terabox_link}"
    
    async with aiohttp.ClientSession() as session:
        try:
            # Send request to the processing page
            async with session.get(processing_url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                if response.status == 200:
                    # Assuming the download link is in the HTML or a redirect
                    # This is a simplified approach; you may need to parse the HTML
                    html_content = await response.text()
                    # Look for a download link (e.g., <a> tag with href or redirect URL)
                    # This is a placeholder; adjust based on actual HTML structure
                    download_url = processing_url  # Replace with actual logic to extract URL
                    return download_url
                else:
                    return None
        except Exception as e:
            print(f"Error: {e}")
            return None

@app.on_message(filters.command("download"))
async def download_file(client, message):
    if len(message.command) < 2:
        await message.reply("Please provide a TeraBox link! Usage: /download <terabox_link>")
        return
    
    terabox_link = message.command[1]
    await message.reply("Processing the TeraBox link... Please wait.")
    
    download_url = await get_download_url(terabox_link)
    
    if download_url:
        await message.reply(f"Download link found: {download_url}\nDownloading and sending the file...")
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as resp:
                if resp.status == 200:
                    file_data = await resp.read()
                    # Check file size (Telegram limit is 50 MB for non-premium bots)
                    if len(file_data) > 50 * 1024 * 1024:
                        await message.reply("File size exceeds 50 MB. Please use a premium bot or download manually.")
                    else:
                        await client.send_video(message.chat.id, file_data, caption="Here’s your video!")
                else:
                    await message.reply("Failed to download the file from the generated link.")
    else:
        await message.reply("Couldn’t extract a valid download link. Please try again or check the TeraBox link.")

app.run()
