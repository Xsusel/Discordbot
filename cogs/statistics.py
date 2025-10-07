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

    @commands.command(name='voicelogs', help='Shows voice channel join/leave logs from the last 24 hours.')
    async def voicelogs(self, ctx):
        """Displays the voice channel join/leave logs for the last 24 hours."""
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return

        logs = database.get_voice_logs(ctx.guild.id)

        if not logs:
            await ctx.send("No voice activity recorded in the last 24 hours.")
            return

        embed = discord.Embed(title="Voice Channel Logs (Last 24 Hours)", color=discord.Color.purple())

        description_lines = []
        for log in logs[:20]:  # Limit to 20 most recent entries to keep the embed clean
            try:
                member = await ctx.guild.fetch_member(log['user_id'])
                user_display = member.display_name
            except discord.NotFound:
                user_display = f"Unknown User (ID: {log['user_id']})"

            timestamp_str = log['timestamp'].strftime('%H:%M:%S')
            emoji = '🟢' if log['event_type'] == 'join' else '🔴'
            action = "joined" if log['event_type'] == 'join' else "left"

            description_lines.append(f"`{timestamp_str}` {emoji} **{user_display}** {action} `#{log['channel_name']}`")

        embed.description = "\n".join(description_lines)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Statistics(bot))