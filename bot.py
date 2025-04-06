from pyrogram import Client, filters
import requests
from bs4 import BeautifulSoup
import asyncio
import os
import aiohttp
from urllib.parse import quote

app = Client("terabox_bot", api_id="25321403", api_hash="0024ae3c978ba534b1a9bffa29e9cc9b", bot_token="7997809826:AAGUMLWI54X7wmdXq6cKqfhNKPsimHAiMfk")

async def get_download_link(terabox_link):
    """Extract the download link from teraboxfast.com player page."""
    encoded_link = quote(terabox_link, safe='')
    player_url = f"https://www.teraboxfast.com/p/video-player.html?q={encoded_link}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        response = requests.get(player_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the download link near file size (MB or GB) or video file name
        download_link = None
        size_elements = soup.find_all(text=lambda text: isinstance(text, str) and ("MB" in text or "GB" in text))
        for element in size_elements:
            parent = element.find_parent('a')
            if parent and 'href' in parent.attrs:
                download_link = parent['href']
                break
        
        if not download_link:
            # Fallback: Check for any downloadable link (e.g., video file)
            video_links = soup.find_all('a', href=lambda href: href and any(ext in href for ext in ['.mp4', '.mkv', '.zip']))
            if video_links:
                download_link = video_links[0]['href']
        
        if download_link and not download_link.startswith('http'):
            download_link = f"https://www.teraboxfast.com{download_link}"
        
        return download_link if download_link else None
    
    except requests.RequestException as e:
        print(f"Error fetching player page: {e}")
        return None
    except Exception as e:
        print(f"Error parsing page: {e}")
        return None

async def download_file_from_url(download_url, temp_file):
    """Download the file (video or zip) from the URL."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as resp:
                if resp.status == 200:
                    with open(temp_file, "wb") as f:
                        while True:
                            chunk = await resp.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
                    return temp_file
                else:
                    raise Exception(f"Failed to download: Status {resp.status}")
    except Exception as e:
        print(f"Download error: {e}")
        return None

async def extract_if_zip(file_path):
    """Extract video from .zip if applicable, otherwise return the file."""
    if file_path.lower().endswith('.zip'):
        extracted_dir = file_path.replace('.zip', '_extracted')
        os.makedirs(extracted_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extracted_dir)
            for file in os.listdir(extracted_dir):
                if file.lower().endswith(('.mp4', '.mkv', '.avi')):
                    return os.path.join(extracted_dir, file)
            raise Exception("No video file found in .zip")
        except Exception as e:
            print(f"Extraction error: {e}")
            return None
    return file_path

@app.on_message(filters.command("download"))
async def download_file(client, message):
    if len(message.command) < 2:
        await message.reply("Please provide a TeraBox link! Usage: /download <terabox_link>")
        return
    
    terabox_link = message.command[1]
    await message.reply("Processing the TeraBox link via teraboxfast.com... Please wait.")
    
    download_link = await get_download_link(terabox_link)
    
    if download_link:
        await message.reply(f"Download link found: {download_link}\nDownloading the file...")
        # Use a generic temp file name based on extension or .tmp
        temp_file = f"temp_file_{message.chat.id}.{download_link.split('.')[-1] if '.' in download_link.split('/')[-1] else 'tmp'}"
        
        downloaded_file = await download_file_from_url(download_link, temp_file)
        if downloaded_file:
            video_file = await extract_if_zip(downloaded_file)
            if video_file and os.path.exists(video_file):
                file_size = os.path.getsize(video_file)
                if file_size > 50 * 1024 * 1024:
                    await message.reply("File size exceeds 50 MB. Please download manually or use a premium bot.")
                    os.remove(video_file)
                    if os.path.exists(os.path.dirname(video_file)):
                        for f in os.listdir(os.path.dirname(video_file)):
                            os.remove(os.path.join(os.path.dirname(video_file), f))
                        os.rmdir(os.path.dirname(video_file))
                else:
                    await client.send_video(
                        chat_id=message.chat.id,
                        video=video_file,
                        caption=f"Here’s your video: {os.path.basename(video_file)}"
                    )
                    os.remove(video_file)
                    if os.path.exists(os.path.dirname(video_file)):
                        for f in os.listdir(os.path.dirname(video_file)):
                            os.remove(os.path.join(os.path.dirname(video_file), f))
                        os.rmdir(os.path.dirname(video_file))
            else:
                await message.reply("Failed to process the file as a video.")
                os.remove(downloaded_file)
        else:
            await message.reply("Failed to download the file.")
    else:
        await message.reply("Couldn’t extract a valid download link. Please check the TeraBox link or try again later.")

app.run()
