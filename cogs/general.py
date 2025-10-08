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

async def setup(bot):
    await bot.add_cog(General(bot))