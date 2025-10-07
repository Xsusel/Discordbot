import discord
from discord.ext import commands, tasks
import database
from datetime import datetime, timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_expired_bans.start()
        print("Moderation cog loaded and unban task started.")

    def cog_unload(self):
        self.check_expired_bans.cancel()

    @tasks.loop(hours=1)
    async def check_expired_bans(self):
        """Periodically checks for and revokes expired bans."""
        expired_bans = database.get_expired_bans()
        if not expired_bans:
            return

        print(f"Found {len(expired_bans)} expired ban(s) to process...")
        for ban in expired_bans:
            guild = self.bot.get_guild(ban['guild_id'])
            if not guild:
                continue

            try:
                user = await self.bot.fetch_user(ban['user_id'])
                await guild.unban(user, reason="Ban duration expired.")
                database.remove_active_ban(guild.id, user.id)
                print(f"Successfully unbanned {user} from {guild.name}.")
            except discord.NotFound:
                # User might not be banned anymore or doesn't exist, so just clean up
                database.remove_active_ban(guild.id, ban['user_id'])
            except discord.Forbidden:
                print(f"Failed to unban user {ban['user_id']} from {guild.name}. Missing permissions.")
            except Exception as e:
                print(f"An unexpected error occurred while unbanning user {ban['user_id']}: {e}")

    @check_expired_bans.before_loop
    async def before_check_expired_bans(self):
        await self.bot.wait_until_ready()

    # --- Warning System Commands ---
    @commands.command(name='warn')
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason provided."):
        """Warns a user and takes action if the warn limit is reached."""
        if member.bot or member == ctx.author:
            await ctx.send("You cannot warn bots or yourself.")
            return

        # Add warning to the database and get the new count
        warn_count = database.add_warning(ctx.guild.id, member.id, ctx.author.id, reason)

        # Get the guild's warning settings
        settings = database.get_warn_settings(ctx.guild.id)
        warn_limit = settings['warn_limit']

        await ctx.send(f"**{member.display_name}** has been warned. They now have **{warn_count}/{warn_limit}** warnings.")

        # Check if the user has reached the warning limit
        if warn_count >= warn_limit:
            action = settings['action']
            action_reason = f"Reached warning limit of {warn_limit}."

            try:
                await member.send(f"You have been **{action}ed** from **{ctx.guild.name}** for the following reason: {action_reason}")
            except discord.Forbidden:
                pass # User may have DMs disabled

            if action == 'kick':
                await member.kick(reason=action_reason)
                await ctx.send(f"👢 **{member.display_name}** has been kicked for reaching the warning limit.")
            elif action == 'ban':
                duration_days = settings['ban_duration_days']
                unban_timestamp = datetime.utcnow() + timedelta(days=duration_days)
                await member.ban(reason=action_reason, delete_message_days=0)
                # Log the timed ban in the database
                database.add_active_ban(ctx.guild.id, member.id, unban_timestamp)
                await ctx.send(f"🔨 **{member.display_name}** has been banned for **{duration_days} days** for reaching the warning limit.")

    @commands.command(name='warnings')
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, member: discord.Member = None):
        """Shows warnings for a specific user or a server-wide summary."""
        if member:
            # Show detailed warnings for a specific user
            user_warnings = database.get_user_warnings(ctx.guild.id, member.id)
            if not user_warnings:
                await ctx.send(f"**{member.display_name}** has no warnings.")
                return

            embed = discord.Embed(title=f"Warnings for {member.display_name}", color=discord.Color.orange())
            for warn in user_warnings:
                mod = self.bot.get_user(warn['moderator_id']) or f"ID: {warn['moderator_id']}"
                embed.add_field(
                    name=f"Warn ID: {warn['warn_id']} | By: {mod}",
                    value=f"**Reason:** {warn['reason']}\n**Date:** {warn['timestamp'].strftime('%Y-%m-%d %H:%M')}",
                    inline=False
                )
            await ctx.send(embed=embed)
        else:
            # Show a summary for the whole server
            all_warnings = database.get_all_warnings_summary(ctx.guild.id)
            if not all_warnings:
                await ctx.send("No users have any warnings on this server.")
                return

            embed = discord.Embed(title="Server Warning Summary", color=discord.Color.orange())
            description = []
            for row in all_warnings:
                user = self.bot.get_user(row['user_id']) or f"User ID: {row['user_id']}"
                description.append(f"**{user}**: {row['warn_count']} warning(s)")
            embed.description = "\n".join(description)
            await ctx.send(embed=embed)

    @commands.command(name='unwarn')
    @commands.has_permissions(kick_members=True)
    async def unwarn(self, ctx, warn_id: int):
        """Removes a specific warning by its ID."""
        if database.remove_warning(warn_id, ctx.guild.id):
            await ctx.send(f"✅ Warning ID `{warn_id}` has been removed.")
        else:
            await ctx.send(f"❌ Could not find a warning with ID `{warn_id}` on this server.")

    # --- Configuration Commands for Warning System ---
    @commands.group(name='warnconfig')
    @commands.has_permissions(administrator=True)
    async def warnconfig(self, ctx):
        """Manages the warning system configuration."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand. Use `$warnconfig view` to see settings.")

    @warnconfig.command(name='view')
    @commands.has_permissions(administrator=True)
    async def warnconfig_view(self, ctx):
        """Displays the current warning system settings."""
        settings = database.get_warn_settings(ctx.guild.id)
        embed = discord.Embed(title="Warning System Configuration", color=discord.Color.blue())
        embed.add_field(name="Warning Limit", value=f"`{settings['warn_limit']}` warnings", inline=False)
        embed.add_field(name="Action on Limit", value=f"`{settings['action'].capitalize()}`", inline=False)
        if settings['action'] == 'ban':
            embed.add_field(name="Ban Duration", value=f"`{settings['ban_duration_days']}` days", inline=False)
        await ctx.send(embed=embed)

    @warnconfig.command(name='limit')
    @commands.has_permissions(administrator=True)
    async def warnconfig_limit(self, ctx, limit: int):
        """Sets the number of warnings before an action is taken."""
        if limit < 1:
            await ctx.send("❌ Limit must be at least 1.")
            return
        database.set_warn_limit(ctx.guild.id, limit)
        await ctx.send(f"✅ Warning limit set to `{limit}`.")

    @warnconfig.command(name='action')
    @commands.has_permissions(administrator=True)
    async def warnconfig_action(self, ctx, action: str):
        """Sets the action to take on reaching the limit (kick or ban)."""
        action = action.lower()
        if action not in ['kick', 'ban']:
            await ctx.send("❌ Invalid action. Must be `kick` or `ban`.")
            return
        database.set_warn_action(ctx.guild.id, action)
        await ctx.send(f"✅ Action on limit set to `{action}`.")

    @warnconfig.command(name='banduration')
    @commands.has_permissions(administrator=True)
    async def warnconfig_banduration(self, ctx, days: int):
        """Sets the duration of the ban in days."""
        if days < 1:
            await ctx.send("❌ Ban duration must be at least 1 day.")
            return
        database.set_ban_duration(ctx.guild.id, days)
        await ctx.send(f"✅ Ban duration set to `{days}` days.")

async def setup(bot):
    await bot.add_cog(Moderation(bot))