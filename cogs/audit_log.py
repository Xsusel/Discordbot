import discord
from discord.ext import commands, tasks
import database
from datetime import datetime

class AuditLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # The self.voice_sessions dictionary is removed in favor of a persistent database solution.
        print("Audit Log cog loaded.")

    async def _send_log_message(self, guild_id, embed):
        """A helper function to send embeds to the configured log channel."""
        settings = database.get_guild_settings(guild_id)
        if not settings or not settings['audit_log_channel_id']:
            return

        log_channel = self.bot.get_channel(settings['audit_log_channel_id'])
        if log_channel:
            try:
                await log_channel.send(embed=embed)
            except discord.Forbidden:
                print(f"Failed to send to audit log channel in guild {guild_id}. Missing permissions.")
            except Exception as e:
                print(f"An error occurred while sending to audit log channel: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Synchronizes voice states when the bot starts up."""
        print("Audit Log cog is ready. Synchronizing voice states.")
        # Clear any potentially stale sessions from a previous crash
        database.clear_all_active_voice_sessions()
        # Go through all guilds and find users currently in voice channels
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                for member in channel.members:
                    if not member.bot:
                        # Start a new session for anyone found in a channel on startup
                        database.start_voice_session(guild.id, member.id)
                        print(f"Synchronized active user: {member.name} in {guild.name}")
        print("Voice state synchronization complete.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Logs when a member joins the server."""
        embed = discord.Embed(
            description=f"**{member.mention} has joined the server.**",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"{member.name} ({member.id})", icon_url=member.display_avatar.url)
        embed.set_footer(text="User Joined")
        await self._send_log_message(member.guild.id, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Logs when a member leaves the server."""
        embed = discord.Embed(
            description=f"**{member.mention} has left the server.**",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"{member.name} ({member.id})", icon_url=member.display_avatar.url)
        embed.set_footer(text="User Left")
        await self._send_log_message(member.guild.id, embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Logs when a message is deleted."""
        if message.author.bot:
            return

        embed = discord.Embed(
            description=f"**Message sent by {message.author.mention} deleted in {message.channel.mention}**\n{message.content}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"{message.author.name} ({message.author.id})", icon_url=message.author.display_avatar.url)
        embed.set_footer(text="Message Deleted")
        await self._send_log_message(message.guild.id, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Logs when a member's roles are changed."""
        if before.roles != after.roles:
            added_roles = [r for r in after.roles if r not in before.roles]
            removed_roles = [r for r in before.roles if r not in after.roles]

            if added_roles:
                embed = discord.Embed(
                    description=f"**{after.mention} was given the `{added_roles[0].name}` role.**",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed.set_author(name=f"{after.name} ({after.id})", icon_url=after.display_avatar.url)
                embed.set_footer(text="Roles Updated")
                await self._send_log_message(after.guild.id, embed)

            if removed_roles:
                embed = discord.Embed(
                    description=f"**`{removed_roles[0].name}` role was removed from {after.mention}.**",
                    color=discord.Color.dark_blue(),
                    timestamp=datetime.utcnow()
                )
                embed.set_author(name=f"{after.name} ({after.id})", icon_url=after.display_avatar.url)
                embed.set_footer(text="Roles Updated")
                await self._send_log_message(after.guild.id, embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Logs voice channel events and tracks session duration for statistics using the database."""
        if member.bot:
            return

        user_id = member.id
        guild_id = member.guild.id

        # User joins a voice channel (from no channel)
        if not before.channel and after.channel:
            database.start_voice_session(guild_id, user_id)
            embed = discord.Embed(description=f"**{member.mention} joined voice channel `{after.channel.name}`**", color=0x7289DA, timestamp=datetime.utcnow())
            embed.set_author(name=f"{member.name} ({member.id})", icon_url=member.display_avatar.url)
            await self._send_log_message(guild_id, embed)

        # User leaves a voice channel (to no channel)
        elif before.channel and not after.channel:
            # The end_voice_session function now handles finding the start time,
            # logging the full session, and cleaning up the active session record.
            database.end_voice_session(guild_id, user_id)
            embed = discord.Embed(description=f"**{member.mention} left voice channel `{before.channel.name}`**", color=0x99AAB5, timestamp=datetime.utcnow())
            embed.set_author(name=f"{member.name} ({member.id})", icon_url=member.display_avatar.url)
            await self._send_log_message(guild_id, embed)

        # User moves between voice channels
        elif before.channel and after.channel and before.channel != after.channel:
            # When a user moves, we don't need to do anything with the database,
            # as their session is continuous. We just log the move itself.
            embed = discord.Embed(description=f"**{member.mention} moved from `{before.channel.name}` to `{after.channel.name}`**", color=0x99AAB5, timestamp=datetime.utcnow())
            embed.set_author(name=f"{member.name} ({member.id})", icon_url=member.display_avatar.url)
            await self._send_log_message(guild_id, embed)

    @commands.command(name='setlogchannel')
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        """Sets the channel where audit logs will be sent."""
        database.set_audit_log_channel(ctx.guild.id, channel.id)
        await ctx.send(f"✅ Audit log channel has been set to {channel.mention}.")

async def setup(bot):
    await bot.add_cog(AuditLog(bot))