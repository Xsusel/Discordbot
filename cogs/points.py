import discord
from discord.ext import commands, tasks
import database
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_activity_check.start()
        self.monthly_archive_task.start()
        self.last_archive_day = -1

    def cog_unload(self):
        self.voice_activity_check.cancel()
        self.monthly_archive_task.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        database.add_points(message.guild.id, message.author.id, 1)

    @tasks.loop(minutes=10)
    async def voice_activity_check(self):
        logger.info("Running voice activity check...")
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                active_users = [m for m in vc.members if not m.voice.self_mute and not m.voice.self_deaf]
                if len(active_users) > 1:
                    for member in active_users:
                        database.add_points(guild.id, member.id, 25)
                        logger.info(f"Awarded 25 points to {member.display_name} in {guild.name} for voice activity.")

    @voice_activity_check.before_loop
    async def before_voice_activity_check(self):
        await self.bot.wait_until_ready()

    @commands.command(name='leaderboard', help='Shows the monthly points leaderboard.')
    async def leaderboard(self, ctx):
        if not ctx.guild:
            return

        leaderboard_data = database.get_points_leaderboard(ctx.guild.id)

        embed = discord.Embed(title="Monthly Points Leaderboard", color=discord.Color.gold())

        if not leaderboard_data:
            embed.description = "No one has earned any points yet this month."
        else:
            leaderboard_list = []
            for i, row in enumerate(leaderboard_data):
                try:
                    member = await ctx.guild.fetch_member(row['user_id'])
                    display_name = member.display_name
                except discord.NotFound:
                    display_name = f"Unknown User (ID: {row['user_id']})"
                leaderboard_list.append(f"**{i+1}. {display_name}**: {row['points']} points")
            embed.description = "\n".join(leaderboard_list)

        await ctx.send(embed=embed)

    @commands.command(name='archiveleaderboard', help='Manually archives the leaderboard.')
    @commands.has_permissions(administrator=True)
    async def archiveleaderboard(self, ctx):
        if not ctx.guild:
            return

        database.archive_monthly_leaderboard(ctx.guild.id)
        await ctx.send("The monthly leaderboard has been archived and points have been reset.")

    @tasks.loop(hours=24)
    async def monthly_archive_task(self):
        now = datetime.utcnow()
        if now.day == 1 and now.day != self.last_archive_day:
            logger.info(f"It's the first day of the month. Archiving leaderboards...")
            for guild in self.bot.guilds:
                database.archive_monthly_leaderboard(guild.id)
                logger.info(f"Archived leaderboard for {guild.name}.")
            self.last_archive_day = now.day
        elif now.day != 1:
            self.last_archive_day = -1

    @monthly_archive_task.before_loop
    async def before_monthly_archive_task(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Points(bot))
