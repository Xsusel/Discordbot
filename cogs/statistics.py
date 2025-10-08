import discord
from discord.ext import commands
import database

class Statistics(commands.Cog):
    """Cog for displaying user statistics."""
    def __init__(self, bot):
        self.bot = bot

    async def _create_leaderboard_embed(self, ctx, title: str, data: list, formatter, color: discord.Color):
        """
        A helper function to build a standardized leaderboard embed.

        Args:
            ctx: The command context.
            title: The title of the embed.
            data: The list of data rows from the database.
            formatter: A function that takes a data row and returns a formatted string for the value.
            color: The color of the embed.
        """
        embed = discord.Embed(title=title, color=color)

        if not data:
            embed.description = "No activity recorded in this period."
            return embed

        leaderboard_lines = []
        for i, row in enumerate(data[:10]):  # Display top 10
            try:
                # Try getting member from cache first for efficiency, then fetch as a fallback.
                member = ctx.guild.get_member(row['user_id']) or await ctx.guild.fetch_member(row['user_id'])
                display_name = member.display_name
            except discord.NotFound:
                display_name = f"Unknown User (ID: {row['user_id']})"

            value_str = formatter(row)
            leaderboard_lines.append(f"**{i+1}. {display_name}**: {value_str}")

        embed.description = "\n".join(leaderboard_lines)
        return embed

    def _format_messages(self, row: dict) -> str:
        """Formatter for message count."""
        count = row.get('message_count', 0)
        return f"{count} message(s)"

    def _format_voice(self, row: dict) -> str:
        """Formatter for voice time, converting seconds to hours and minutes."""
        total_seconds = row.get('total_seconds', 0)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{int(hours)}h {int(minutes)}m"

    @commands.command(name='stats', help='Shows statistics for messages or voice activity.')
    async def stats(self, ctx, stat_type: str, period: str = 'all'):
        """
        Shows message or voice stats for a given period.
        Usage: $stats <messages|voice> [daily|weekly|monthly|all]
        """
        stat_type = stat_type.lower()
        period = period.lower()

        if stat_type not in ['messages', 'voice'] or period not in ['daily', 'weekly', 'monthly', 'all']:
            await ctx.send("Usage: `$stats <messages|voice> [daily|weekly|monthly|all]`")
            return
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return

        title = f"Top {stat_type.capitalize()} Activity ({period.capitalize()})"

        if stat_type == 'messages':
            data = database.get_message_stats(ctx.guild.id, period)
            formatter = self._format_messages
            color = discord.Color.blue()
        else:  # 'voice'
            data = database.get_voice_stats(ctx.guild.id, period)
            formatter = self._format_voice
            color = discord.Color.green()

        embed = await self._create_leaderboard_embed(ctx, title, data, formatter, color)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Statistics(bot))