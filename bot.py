from pyrogram import Client, filters
import aiohttp
import asyncio

async def get_download_url(terabox_link):
    # Construct the processing URL
    processing_url = f"https://teraboxdownloader.in/video-downloader?link={terabox_link}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(processing_url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                if response.status == 200:
                    # Placeholder: Adjust this to extract the actual download URL
                    # For now, assuming the processing URL redirects to the download
                    return processing_url
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
        temp_file = f"temp_video_{message.chat.id}.mkv"  # Unique temp file name
        
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as resp:
                if resp.status == 200:
                    # Save the file to disk
                    with open(temp_file, "wb") as f:
                        while True:
                            chunk = await resp.content.read(1024)  # Read in chunks
                            if not chunk:
                                break
                            f.write(chunk)
                    
                    # Check file size (Telegram limit is 50 MB for non-premium bots)
                    file_size = os.path.getsize(temp_file)
                    if file_size > 50 * 1024 * 1024:
                        await message.reply("File size exceeds 50 MB. Please use a premium bot or download manually.")
                        os.remove(temp_file)  # Cleanup
                    else:
                        # Send the video using the file path
                        await client.send_video(
                            chat_id=message.chat.id,
                            video=temp_file,
                            caption="Here’s your video!",
                            progress=progress_callback,  # Optional: Add progress callback
                            progress_args=(message, "Uploading...")
                        )
                        os.remove(temp_file)  # Cleanup after sending
                else:
                    await message.reply("Failed to download the file from the generated link.")
    else:
        await message.reply("Couldn’t extract a valid download link. Please try again or check the TeraBox link.")

# Optional: Progress callback function
async def progress_callback(current, total, message, text):
    if current % 1024 == 0:  # Update every 1 KB
        await message.edit_text(f"{text}\nProgress: {current * 100 / total:.1f}%")

app.run()
