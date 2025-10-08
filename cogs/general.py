import discord
from discord.ext import commands
import os

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping', help='Checks if the bot is responsive.')
    async def ping(self, ctx):
        await ctx.send('Pong!')

    @commands.command(name='dashboard', help='Get a link to the web dashboard.')
    async def dashboard(self, ctx):
        if ctx.guild:
            host_ip = os.getenv('BOT_HOST_IP', 'localhost')
            dashboard_url = f"http://{host_ip}:8080/dashboard/{ctx.guild.id}"

            message = f"You can view the server dashboard here: {dashboard_url}"
            if host_ip == 'localhost':
                message += "\n\n**Note:** The link uses `localhost`. For public access, please set the `BOT_HOST_IP` environment variable in your `bot.env` file."

            await ctx.send(message)
        else:
            await ctx.send("This command can only be used in a server.")

    @commands.command(name='debug', help='Runs diagnostic checks for troubleshooting.')
    async def debug(self, ctx):
        """Runs diagnostic checks."""
        embed = discord.Embed(title="System Debug Report", color=discord.Color.orange())

        # --- YouTube Cookie Check ---
        cookie_path = os.getenv('YOUTUBE_COOKIE_PATH')
        if not cookie_path:
            cookie_status = "⚠️ `YOUTUBE_COOKIE_PATH` environment variable is not set. Music playback may fail."
        else:
            if os.path.exists(cookie_path):
                cookie_status = f"✅ Cookie file found at `{cookie_path}`."
            else:
                cookie_status = (
                    f"❌ Cookie file **NOT FOUND** at `{cookie_path}`.\n"
                    "**Fix:** Make sure you have a `cookies.txt` file in your project directory and that you have **rebuilt the Docker image** after adding it."
                )
        embed.add_field(name="YouTube Cookie Status", value=cookie_status, inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))