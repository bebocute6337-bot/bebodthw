import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os
from collections import deque
import base64

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
queues = {}

def get_ydl_opts():
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extractaudio': True,
        'audioformat': 'mp3',
    }
    
    # === CÁCH 1: Dùng biến môi trường COOKIES (khuyến nghị) ===
    cookies_b64 = os.getenv('COOKIES') or os.getenv('YOUTUBE_COOKIES')
    
    if cookies_b64:
        try:
            cookies_content = base64.b64decode(cookies_b64).decode('utf-8')
            with open('/tmp/cookies.txt', 'w') as f:
                f.write(cookies_content)
            ydl_opts['cookiefile'] = '/tmp/cookies.txt'
            print("✅ Đã load cookies từ biến môi trường")
        except Exception as e:
            print(f"❌ Lỗi decode cookies: {e}")
    
    # === CÁCH 2: Dùng file cookies.txt (nếu có) ===
    elif os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
        print("✅ Đã load cookies từ file cookies.txt")
    
    return ydl_opts

# ================== CÁC LỆNH ==================
@bot.tree.command(name="play", description="Phát nhạc YouTube (có hàng đợi)")
@app_commands.describe(url="Link YouTube")
async def play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    
    if not interaction.user.voice:
        return await interaction.followup.send("❌ Vào voice channel trước!")
    
    guild = interaction.guild
    if not guild.voice_client:
        await interaction.user.voice.channel.connect()
    
    if guild.voice_client.is_playing():
        if guild.id not in queues:
            queues[guild.id] = deque()
        queues[guild.id].append(url)
        await interaction.followup.send("✅ Đã thêm vào hàng đợi!")
    else:
        try:
            with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info['url']
                title = info.get('title', 'Không có tên')
            
            source = discord.FFmpegPCMAudio(audio_url)
            guild.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(guild)))
            await interaction.followup.send(f"🎵 Đang phát: **{title}**")
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi: {str(e)}")

async def play_next(guild):
    if guild.id in queues and queues[guild.id]:
        url = queues[guild.id].popleft()
        try:
            with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info['url']
                title = info.get('title', 'Không có tên')
            
            source = discord.FFmpegPCMAudio(audio_url)
            guild.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(guild)))
            
            channel = guild.system_channel or guild.text_channels[0]
            await channel.send(f"🎵 Đang phát: **{title}**")
        except Exception as e:
            print(f"Lỗi play_next: {e}")

@bot.tree.command(name="skip", description="Bỏ qua bài")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("⏭️ Đã bỏ qua!")
    else:
        await interaction.response.send_message("❌ Không có bài đang phát.")

@bot.tree.command(name="leave", description="Rời voice")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("✅ Đã rời voice channel.")

@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user}")
    await bot.tree.sync()
    print("✅ Đã sync slash commands")

bot.run(os.getenv("DISCORD_TOKEN"))
