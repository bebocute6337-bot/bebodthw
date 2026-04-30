import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================== FIX COOKIES ==================
def get_ydl_opts():
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extractaudio': True,
        'audioformat': 'mp3',
    }
    
    cookies = os.getenv('COOKIES') or os.getenv('YOUTUBE_COOKIES')
    if cookies:
        with open('/tmp/cookies.txt', 'w') as f:
            f.write(cookies)
        ydl_opts['cookiefile'] = '/tmp/cookies.txt'
    elif os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    return ydl_opts

# ================== SLASH COMMAND PLAY ==================
@bot.tree.command(name="play", description="Phát nhạc từ YouTube")
@app_commands.describe(url="Link YouTube")
async def play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    
    if not interaction.user.voice:
        return await interaction.followup.send("❌ Bạn phải vào voice channel trước!")
    
    voice_channel = interaction.user.voice.channel
    
    if not interaction.guild.voice_client:
        await voice_channel.connect()
    
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            title = info.get('title', 'Không có tên')
        
        source = discord.FFmpegPCMAudio(audio_url)
        interaction.guild.voice_client.play(source)
        
        await interaction.followup.send(f"🎵 Đang phát: **{title}**")
        
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi: {str(e)}")

@bot.tree.command(name="leave", description="Rời voice channel")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("✅ Đã rời voice channel.")
    else:
        await interaction.response.send_message("❌ Bot không ở trong voice channel.")

@bot.event
async def on_ready():
    print(f"✅ Bot đã online: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Đã sync {len(synced)} lệnh slash")
    except Exception as e:
        print(f"Lỗi sync: {e}")

bot.run(os.getenv("DISCORD_TOKEN"))
