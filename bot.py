from pyrogram import Client, filters
import aiohttp
import asyncio
import os
from urllib.parse import quote

app = Client("terabox_bot", api_id="25321403", api_hash="0024ae3c978ba534b1a9bffa29e9cc9b", bot_token="7997809826:AAGUMLWI54X7wmdXq6cKqfhNKPsimHAiMfk")

async def get_download_url(terabox_link):
    encoded_link = quote(terabox_link, safe='')
    
    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: Get config to retrieve mode
            config_url = "https://teradl-api.dapuntaratya.com/get_config"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json",
            }
            async with session.get(config_url, headers=headers) as response:
                if response.status == 200:
                    config_data = await response.json()
                    mode = config_data.get("mode")
                    if not mode:
                        print(f"Config response: {config_data}")
                        return None
                else:
                    print(f"Config request failed: Status {response.status}, Text: {await response.text()}")
                    return None

            # Step 2: Generate download link using mode2
            generate_link_url = "https://teradl-api.dapuntaratya.com/generate_link"
            payload = {
                "mode": mode,
                "url": terabox_link
            }
            async with session.post(generate_link_url, headers=headers, json=payload) as response:
                if response.status == 200:
                    link_data = await response.json()
                    print(f"Generate link response: {link_data}")
                    download_url = link_data.get("download_link")
                    if download_url:
                        return download_url
                    else:
                        return None
                else:
                    print(f"Generate link request failed: Status {response.status}, Text: {await response.text()}")
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
    await message.reply("Processing the TeraBox link via API... Please wait.")
    
    download_url = await get_download_url(terabox_link)
    
    if download_url:
        await message.reply(f"Download link found: {download_url}\nDownloading and sending the file...")
        temp_file = f"temp_video_{message.chat.id}.mkv"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as resp:
                if resp.status == 200:
                    with open(temp_file, "wb") as f:
                        while True:
                            chunk = await resp.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
                    
                    file_size = os.path.getsize(temp_file)
                    if file_size > 50 * 1024 * 1024:
                        await message.reply("File size exceeds 50 MB. Please use a premium bot or download manually.")
                        os.remove(temp_file)
                    else:
                        await client.send_video(
                            chat_id=message.chat.id,
                            video=temp_file,
                            caption="Here’s your video!"
                        )
                        os.remove(temp_file)
                else:
                    await message.reply(f"Failed to download the file. Status: {resp.status}")
    else:
        await message.reply("Couldn’t extract a valid download link. Please check the TeraBox link or try again later.")

app.run()
