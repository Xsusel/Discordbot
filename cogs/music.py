import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

# --- FFMPEG and YTDL Options ---
# These options are crucial for streaming audio from YouTube.
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # Bind to all IP addresses
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

# Check for a cookie file and add it to the options if it exists
cookie_path = os.getenv('YOUTUBE_COOKIE_PATH')
if cookie_path and os.path.exists(cookie_path):
    ytdl_format_options['cookiefile'] = cookie_path
    print(f"Using YouTube cookie file at: {cookie_path}")

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    """A class to represent a YouTube DL source."""
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # Take the first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    """A cog for handling music commands."""
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # A dictionary to hold server-specific queues

    def get_queue(self, ctx):
        """Gets the queue for a specific guild, creating one if it doesn't exist."""
        guild_id = ctx.guild.id
        if guild_id not in self.queues:
            self.queues[guild_id] = asyncio.Queue()
        return self.queues[guild_id]

    async def play_next(self, ctx):
        """Plays the next song in the queue."""
        queue = self.get_queue(ctx)
        if queue.empty():
            # No more songs, consider disconnecting after a timeout
            asyncio.run_coroutine_threadsafe(self.maybe_disconnect(ctx), self.bot.loop)
            return

        source = await queue.get()
        ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
        await ctx.send(f'Now playing: **{source.title}**')

    async def maybe_disconnect(self, ctx):
        """Disconnects from the voice channel if inactive for a period of time."""
        await asyncio.sleep(300) # 5 minutes
        if ctx.voice_client and not ctx.voice_client.is_playing():
            await ctx.voice_client.disconnect()

    @commands.command(name='play', help='Plays a song from YouTube or adds it to the queue.')
    async def play(self, ctx, *, search: str):
        """Plays from a url or search string."""
        if not ctx.voice_client:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                return

        async with ctx.typing():
            try:
                player = await YTDLSource.from_url(search, loop=self.bot.loop, stream=True)
                queue = self.get_queue(ctx)

                if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                    await queue.put(player)
                    await ctx.send(f'Added to queue: **{player.title}**')
                else:
                    await queue.put(player)
                    await self.play_next(ctx)

            except Exception as e:
                await ctx.send(f'An error occurred: {e}')

    @commands.command(name='pause', help='Pauses the current song.')
    async def pause(self, ctx):
        """Pauses the currently playing song."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send('Paused the music.')
        else:
            await ctx.send('Not playing anything right now.')

    @commands.command(name='resume', help='Resumes the paused song.')
    async def resume(self, ctx):
        """Resumes a paused song."""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send('Resumed the music.')
        else:
            await ctx.send('The music is not paused.')

    @commands.command(name='skip', help='Skips the current song.')
    async def skip(self, ctx):
        """Skips the current song."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send('Skipped the song.')
            # The `after` callback in play_next will handle playing the next song
        else:
            await ctx.send('Not playing anything to skip.')

    @commands.command(name='stop', help='Stops the music and clears the queue.')
    async def stop(self, ctx):
        """Stops playing, clears the queue, and leaves the voice channel."""
        guild_id = ctx.guild.id
        if guild_id in self.queues:
            self.queues[guild_id] = asyncio.Queue()  # Clear the queue

        if ctx.voice_client:
            ctx.voice_client.stop()
            await ctx.send('Stopped the music and cleared the queue.')
        else:
            await ctx.send('Not connected to a voice channel.')

    @commands.command(name='queue', help='Shows the current song queue.')
    async def queue(self, ctx):
        """Displays the current song queue."""
        queue = self.get_queue(ctx)
        if queue.empty():
            await ctx.send('The queue is currently empty.')
            return

        embed = discord.Embed(title="Music Queue", color=discord.Color.blue())
        queue_list = list(queue._queue)

        # Show currently playing if possible
        if ctx.voice_client and ctx.voice_client.source:
            embed.add_field(name="Now Playing", value=ctx.voice_client.source.title, inline=False)

        if queue_list:
            song_list = ""
            for i, song in enumerate(queue_list[:10]): # Show up to 10 songs
                song_list += f"{i+1}. {song.title}\n"
            embed.add_field(name="Up Next", value=song_list, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name='leave', help='Disconnects the bot from the voice channel.')
    async def leave(self, ctx):
        """Disconnects the bot and clears the queue."""
        if ctx.voice_client:
            await self.stop(ctx) # stop() already clears queue
            await ctx.voice_client.disconnect()
            await ctx.send('Disconnected from the voice channel.')
        else:
            await ctx.send('Not in a voice channel.')


async def setup(bot):
    """A required function for discord.py to load the cog."""
    await bot.add_cog(Music(bot))