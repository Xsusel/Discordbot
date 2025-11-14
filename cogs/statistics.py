import discord
from discord.ext import commands
import database

class Statistics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='stats', help='Shows statistics for messages, voice activity, or points.')
    async def stats(self, ctx, stat_type: str, period: str = 'all'):
        """Shows message, voice, or points stats."""
        if stat_type not in ['messages', 'voice', 'points'] or period not in ['daily', 'weekly', 'monthly', 'all']:
            await ctx.send("Usage: `$stats <messages|voice|points> [daily|weekly|monthly|all]`")
            return
        if not ctx.guild:
            return

        # Points stats do not have a period, so we adjust the title accordingly.
        title = f"Top {stat_type.capitalize()}"
        if stat_type != 'points':
            title += f" ({period.capitalize()})"

        embed = discord.Embed(title=title)

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

        elif stat_type == 'points':
            embed.color = discord.Color.gold()
            leaderboard_data = database.get_points_leaderboard(ctx.guild.id)

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

    @commands.command(name='clearstats', help='Clears statistics for the server.')
    @commands.has_permissions(administrator=True)
    async def clearstats(self, ctx, stat_type: str):
        """Clears server statistics. Only for administrators."""
        if stat_type not in ['messages', 'voice', 'points', 'all']:
            await ctx.send("Usage: `$clearstats <messages|voice|points|all>`")
            return
        if not ctx.guild:
            return

        if stat_type == 'messages':
            database.clear_message_stats(ctx.guild.id)
            await ctx.send("All message statistics have been cleared.")
        elif stat_type == 'voice':
            database.clear_voice_stats(ctx.guild.id)
            await ctx.send("All voice statistics have been cleared.")
        elif stat_type == 'points':
            database.reset_all_points(ctx.guild.id)
            await ctx.send("All points have been cleared.")
        elif stat_type == 'all':
            database.clear_message_stats(ctx.guild.id)
            database.clear_voice_stats(ctx.guild.id)
            database.reset_all_points(ctx.guild.id)
            await ctx.send("All statistics (messages, voice, and points) have been cleared.")

async def setup(bot):
    await bot.add_cog(Statistics(bot))