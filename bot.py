from pyrogram import Client, filters
import aiohttp
import asyncio
import os
from urllib.parse import quote

app = Client("terabox_bot", api_id="25321403", api_hash="0024ae3c978ba534b1a9bffa29e9cc9b", bot_token="7997809826:AAGUMLWI54X7wmdXq6cKqfhNKPsimHAiMfk")

async def get_config(session):
    """Fetch the mode from the get_config endpoint."""
    url = "https://teradl-api.dapuntaratya.com/get_config"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                config_data = await response.json()
                print(f"Config response: {config_data}")
                return config_data.get("mode")
            else:
                print(f"Config request failed: Status {response.status}, Text: {await response.text()}")
                return 1  # Default to Mode 1 if config fails
    except Exception as e:
        print(f"Config error: {e}")
        return 1

async def generate_file(session, terabox_link, mode):
    """Generate file data including fs_id or direct link."""
    url = "https://teradl-api.dapuntaratya.com/generate_file"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "url": terabox_link,
        "mode": mode
    }
    try:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                file_data = await response.json()
                print(f"Generate file response: {file_data}")
                return file_data
            else:
                print(f"Generate file request failed: Status {response.status}, Text: {await response.text()}")
                return None
    except Exception as e:
        print(f"Generate file error: {e}")
        return None

async def generate_link(session, terabox_link, mode, file_data):
    """Generate the final download link."""
    url = "https://teradl-api.dapuntaratya.com/generate_link"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if mode == 1:
        # Mode 1: Use fs_id from generate_file
        fs_id = file_data["list"][0]["fs_id"] if file_data and file_data.get("list") else None
        if not fs_id:
            print("No fs_id found in Mode 1 response")
            return None
        payload = {
            "mode": mode,
            "js_token": file_data["js_token"],
            "cookie": file_data["cookie"],
            "sign": file_data["sign"],
            "timestamp": file_data["timestamp"],
            "shareid": file_data["shareid"],
            "uk": file_data["uk"],
            "fs_id": fs_id
        }
    else:  # Mode 2
        # Mode 2: Use link from generate_file
        link = file_data["list"][0]["link"] if file_data and file_data.get("list") else None
        if not link:
            print("No link found in Mode 2 response")
            return None
        payload = {
            "mode": mode,
            "url": link
        }
    try:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                link_data = await response.json()
                print(f"Generate link response: {link_data}")
                download_url = link_data.get("download_link", {}).get("url_1")  # Prefer url_1 as base download
                if download_url:
                    return download_url
                else:
                    return None
            else:
                print(f"Generate link request failed: Status {response.status}, Text: {await response.text()}")
                return None
    except Exception as e:
        print(f"Generate link error: {e}")
        return None

async def get_download_url(terabox_link):
    """Get the download URL using the API workflow."""
    async with aiohttp.ClientSession() as session:
        # Step 1: Get mode
        mode = await get_config(session)
        print(f"Using mode: {mode}")

        # Step 2: Generate file data
        file_data = await generate_file(session, terabox_link, mode)
        if not file_data or file_data.get("status") != "success":
            print("Generate file failed or invalid response")
            return None

        # Step 3: Generate download link
        download_url = await generate_link(session, terabox_link, mode, file_data)
        return download_url

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
