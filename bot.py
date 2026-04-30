import discord
from discord.ext import commands
import yt_dlp
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================== FIX COOKIES (QUAN TRỌNG) ==================
def get_ydl_opts():
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(title)s.%(ext)s',
    }
    
    # Lấy cookies từ Railway Variables
    cookies = os.getenv('COOKIES') or os.getenv('YOUTUBE_COOKIES')
    
    if cookies:
        with open('/tmp/cookies.txt', 'w') as f:
            f.write(cookies)
        ydl_opts['cookiefile'] = '/tmp/cookies.txt'
    elif os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    return ydl_opts

# ================== LỆNH PLAY ==================
@bot.command()
async def play(ctx, *, url):
    if not ctx.author.voice:
        return await ctx.send("Bạn phải vào voice channel trước!")

    voice_channel = ctx.author.voice.channel
    
    if not ctx.voice_client:
        await voice_channel.connect()
    
    try:
        await ctx.send("Đang xử lý...")
        
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['url']
            title = info.get('title', 'Không có tên')
        
        source = discord.FFmpegPCMAudio(url2)
        ctx.voice_client.play(source, after=lambda e: print(f"Đã phát xong: {e}"))
        
        await ctx.send(f"🎵 Đang phát: **{title}**")
        
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

# ================== LỆNH KHÁC ==================
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Đã rời voice channel.")

@bot.event
async def on_ready():
    print(f"Bot đã online: {bot.user}")

# Chạy bot
bot.run(os.getenv("DISCORD_TOKEN"))
