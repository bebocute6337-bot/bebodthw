import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os
from collections import deque

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Queue cho mỗi server
queues = {}

def get_ydl_opts():
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    cookies = os.getenv('COOKIES') or os.getenv('YOUTUBE_COOKIES')
    if cookies:
        with open('/tmp/cookies.txt', 'w') as f:
            f.write(cookies)
        ydl_opts['cookiefile'] = '/tmp/cookies.txt'
    elif os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    return ydl_opts

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
            
            # Gửi thông báo
            channel = guild.system_channel or guild.text_channels[0]
            await channel.send(f"🎵 Đang phát: **{title}**")
        except Exception as e:
            print(f"Lỗi play_next: {e}")

@bot.tree.command(name="play", description="Phát nhạc từ YouTube (có hàng đợi)")
@app_commands.describe(url="Link YouTube")
async def play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    
    if not interaction.user.voice:
        return await interaction.followup.send("❌ Bạn phải vào voice channel!")
    
    voice_channel = interaction.user.voice.channel
    guild = interaction.guild
    
    if not guild.voice_client:
        await voice_channel.connect()
    
    # Nếu đang phát → thêm vào queue
    if guild.voice_client and guild.voice_client.is_playing():
        if guild.id not in queues:
            queues[guild.id] = deque()
        queues[guild.id].append(url)
        await interaction.followup.send("✅ Đã thêm vào hàng đợi!")
    else:
        # Phát ngay
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

@bot.tree.command(name="skip", description="Bỏ qua bài hiện tại")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("⏭️ Đã bỏ qua bài!")
    else:
        await interaction.response.send_message("❌ Không có bài nào đang phát.")

@bot.tree.command(name="queue", description="Xem hàng đợi")
async def queue_cmd(interaction: discord.Interaction):
    if interaction.guild.id in queues and queues[interaction.guild.id]:
        msg = "\n".join([f"{i+1}. {url}" for i, url in enumerate(queues[interaction.guild.id])])
        await interaction.response.send_message(f"📋 Hàng đợi:\n{msg}")
    else:
        await interaction.response.send_message("📭 Hàng đợi trống.")

@bot.tree.command(name="leave", description="Rời voice channel")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("✅ Đã rời voice channel.")
    else:
        await interaction.response.send_message("❌ Bot không ở trong voice channel.")

@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user}")
    await bot.tree.sync()

bot.run(os.getenv("DISCORD_TOKEN"))
