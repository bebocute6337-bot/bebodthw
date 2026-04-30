import asyncio
import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import yt_dlp

load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Sync error: {e}")

@bot.tree.command(name="play", description="Phát nhạc")
@app_commands.describe(query="Link YouTube hoặc tên bài")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    
    if not interaction.user.voice:
        return await interaction.followup.send("❌ Bạn cần vào kênh thoại trước!")
    
    vc = interaction.guild.voice_client
    if not vc:
        vc = await interaction.user.voice.channel.connect()
    
    try:
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
            info = ydl.extract_info(query, download=False)
            url = info['url'] if 'url' in info else info['entries'][0]['url']
        
        vc.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
        await interaction.followup.send(f"🎵 Đang phát: **{info.get('title', query)}**")
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi: {str(e)[:100]}")

@bot.tree.command(name="skip", description="Bỏ qua bài")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("⏭️ Đã bỏ qua!")
    else:
        await interaction.response.send_message("❌ Không có bài nào đang phát")

@bot.tree.command(name="stop", description="Dừng nhạc")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        vc.stop()
        await vc.disconnect()
    await interaction.response.send_message("⏹️ Đã dừng!")

bot.run(BOT_TOKEN)
