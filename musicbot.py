import discord
from discord.ext import commands
import asyncio
import yt_dlp

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='', intents=intents)

# Store queues per guild
music_queues = {}

# ===============================
# Helper Functions
# ===============================
def get_guild_queue(ctx):
    return music_queues.setdefault(ctx.guild.id, [])

def get_ytdlp_source(url_or_search):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch',
        'extract_flat': False,
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url_or_search, download=False)
        if 'entries' in info:
            info = info['entries'][0]
    return {
        'source': info['url'],
        'title': info['title']
    }

async def play_next(ctx):
    queue = get_guild_queue(ctx)
    if not queue:
        await ctx.send("🎶 Queue is empty. Leaving voice channel.")
        await ctx.voice_client.disconnect()
        return

    next_song = queue.pop(0)
    source = discord.FFmpegPCMAudio(next_song['source'], before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
    ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
    await ctx.send(f"🎧 Now playing: **{next_song['title']}**")

# ===============================
# Commands
# ===============================
@bot.command(name='play')
async def play(ctx, *, query: str):
    voice_channel = ctx.author.voice.channel if ctx.author.voice else None
    if not voice_channel:
        await ctx.send("❌ You must be in a voice channel to play music.")
        return

    vc = ctx.voice_client
    if not vc:
        vc = await voice_channel.connect()

    song = get_ytdlp_source(query)
    queue = get_guild_queue(ctx)

    if not vc.is_playing():
        queue.insert(0, song)
        await play_next(ctx)
    else:
        queue.append(song)
        await ctx.send(f"✅ Added to queue: **{song['title']}**")

@bot.command(name='playnow')
async def playnow(ctx, *, query: str):
    if not ctx.voice_client:
        await ctx.send("❌ I'm not connected to a voice channel.")
        return
    song = get_ytdlp_source(query)
    queue = get_guild_queue(ctx)
    queue.insert(0, song)
    ctx.voice_client.stop()
    await ctx.send(f"⚡ Force playing now: **{song['title']}**")

@bot.command(name='skip')
async def skip(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("❌ Nothing is playing right now.")
        return
    ctx.voice_client.stop()
    await ctx.send("⏭️ Song skipped.")

@bot.command(name='fskip')
@commands.has_permissions(administrator=True)
async def fskip(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("❌ Nothing is playing.")
        return
    ctx.voice_client.stop()
    await ctx.send("🚨 Force skipped the song!")

@bot.command(name='pause')
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Music paused.")
    else:
        await ctx.send("❌ Nothing is playing.")

@bot.command(name='unpause')
async def unpause(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Music resumed.")
    else:
        await ctx.send("❌ Music isn't paused.")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ===============================
# Run the Bot
# ===============================
bot.run("MTQyNzMxMDM2ODUxODE4MDg5NA.GLJs6e.nawlDaafPyYTgHTL7LbHCm2jF7hOUK6uVlRk-0")
