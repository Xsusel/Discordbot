import discord
from discord.ext import commands
import database

class Statistics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='stats', help='Shows statistics for messages or voice activity.')
    async def stats(self, ctx, stat_type: str, period: str = 'all'):
        """Shows message or voice stats."""
        if stat_type not in ['messages', 'voice'] or period not in ['daily', 'weekly', 'monthly', 'all']:
            await ctx.send("Usage: `$stats <messages|voice> [daily|weekly|monthly|all]`")
            return
        if not ctx.guild:
            return

        embed = discord.Embed(title=f"Top {stat_type.capitalize()} ({period.capitalize()})")

        if stat_type == 'messages':
            embed.color = discord.Color.blue()
            stats_data = database.get_message_stats(ctx.guild.id, period)
            if not stats_data:
                embed.description = "No messages recorded in this period."
            else:
                leaderboard = []
                for i, row in enumerate(stats_data[:10]):
                    try:
                        member = await ctx.guild.fetch_member(row['user_id'])
                        display_name = member.display_name
                    except discord.NotFound:
                        display_name = f"Unknown User (ID: {row['user_id']})"
                    leaderboard.append(f"**{i+1}. {display_name}**: {row['message_count']} messages")
                embed.description = "\n".join(leaderboard)

        elif stat_type == 'voice':
            embed.color = discord.Color.green()
            stats_data = database.get_voice_stats(ctx.guild.id, period)
            if not stats_data:
                embed.description = "No voice activity recorded in this period."
            else:
                leaderboard = []
                for i, row in enumerate(stats_data[:10]):
                    try:
                        member = await ctx.guild.fetch_member(row['user_id'])
                        display_name = member.display_name
                    except discord.NotFound:
                        display_name = f"Unknown User (ID: {row['user_id']})"

                    total_seconds = row['total_seconds'] or 0
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    leaderboard.append(f"**{i+1}. {display_name}**: {int(hours)}h {int(minutes)}m")
                embed.description = "\n".join(leaderboard)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Statistics(bot))