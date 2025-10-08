import discord
from discord.ext import commands
import os
import database
import shutil

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='debug')
    @commands.is_owner()
    async def debug(self, ctx):
        """Runs a comprehensive diagnostic check."""
        embed = discord.Embed(title="System Diagnostics", color=discord.Color.blue())

        # 1. Bot Latency
        latency_ms = round(self.bot.latency * 1000)
        embed.add_field(name="🌐 Bot Latency", value=f"{latency_ms}ms", inline=False)

        # 2. Cog Status
        loaded_cogs = list(self.bot.cogs.keys())
        embed.add_field(name="⚙️ Loaded Cogs", value=f"```\n{', '.join(loaded_cogs)}\n```", inline=False)

        # 3. Database Connection
        try:
            database.get_db_connection().execute("SELECT 1")
            db_status = "✅ Connected"
        except Exception as e:
            db_status = f"❌ Disconnected\n`{e}`"
        embed.add_field(name="🗃️ Database Status", value=db_status, inline=False)

        # 4. FFMPEG Check
        ffmpeg_path = shutil.which("ffmpeg")
        ffmpeg_status = f"✅ Found at `{ffmpeg_path}`" if ffmpeg_path else "❌ Not found in PATH"
        embed.add_field(name="🎵 FFMPEG Check", value=ffmpeg_status, inline=False)

        # 5. Cookies file check
        cookies_file = "cookies.txt"
        cookies_status = "✅ Found" if os.path.exists(cookies_file) else "❌ Not found"
        embed.add_field(name="🍪 Cookies File Check", value=f"`{cookies_file}`: {cookies_status}", inline=False)

        # 6. Channel Permissions Check
        perms = ctx.channel.permissions_for(ctx.guild.me)
        perm_list = {
            "Send Messages": perms.send_messages,
            "Embed Links": perms.embed_links,
            "Attach Files": perms.attach_files,
            "Connect": perms.connect,
            "Speak": perms.speak,
        }
        perm_str = "\n".join([f"{'✅' if v else '❌'} {k}" for k, v in perm_list.items()])
        embed.add_field(name=f"📜 Permissions in #{ctx.channel.name}", value=perm_str, inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))