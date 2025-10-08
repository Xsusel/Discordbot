import discord
from discord.ext import commands
import os
import database # Import our database module

class AutoResponder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Auto-responder cog loaded.")

    async def check_for_response(self, message):
        """Checks a message and sends an auto-response if it matches the guild's dynamic criteria."""
        if not message.guild:
            return

        # Fetch the auto-responder configuration for this specific guild
        config = database.get_ar_config(message.guild.id)

        # The feature must be enabled and have a target channel set
        if not config or not config['is_enabled'] or not config['target_channel_id']:
            return

        # Avoid replying to messages in the target channel itself
        if message.channel.id == config['target_channel_id']:
            return

        # Fetch keywords for this guild
        keywords_from_db = database.get_ar_keywords(message.guild.id)
        topic_keywords = [row['keyword'] for row in keywords_from_db if row['keyword_type'] == 'topic']
        question_keywords = [row['keyword'] for row in keywords_from_db if row['keyword_type'] == 'question']

        # If no keywords are set, do nothing
        if not topic_keywords or not question_keywords:
            return

        message_content_lower = message.content.lower()

        # Check if the message contains any of the relevant topic keywords
        has_topic_keyword = any(keyword in message_content_lower for keyword in topic_keywords)

        if not has_topic_keyword:
            return

        # Check if the message is likely a question
        is_a_question = False
        if message_content_lower.endswith('?'):
            is_a_question = True
        if not is_a_question and any(q_word in message_content_lower.split() for q_word in question_keywords):
            is_a_question = True

        if is_a_question:
            try:
                # Format the custom reply message from the database
                reply_message = config['reply_message'].format(
                    mention=message.author.mention,
                    channel=f"<#{config['target_channel_id']}>"
                )
                await message.reply(reply_message, mention_author=False)
                print(f"Auto-responded to a settings question from {message.author} in guild {message.guild.id}.")
            except discord.errors.Forbidden:
                print(f"Could not reply to {message.author} in channel {message.channel.id}. Missing permissions.")
            except Exception as e:
                print(f"An error occurred in auto-responder: {e}")

    # --- Management Commands for Auto-Responder ---
    @commands.group(name='ar', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def ar(self, ctx):
        """Manages the auto-responder feature. Use `$ar help` for a list of commands."""
        await ctx.send("Invalid subcommand. Use `$ar list` to see the current configuration or `$ar help` for commands.")

    @ar.command(name='toggle')
    @commands.has_permissions(administrator=True)
    async def ar_toggle(self, ctx):
        """Enables or disables the auto-responder for this server."""
        config = database.get_ar_config(ctx.guild.id)
        new_state = not config['is_enabled']
        database.set_ar_enabled(ctx.guild.id, new_state)
        await ctx.send(f"✅ Auto-responder has been **{'enabled' if new_state else 'disabled'}**.")

    @ar.command(name='channel')
    @commands.has_permissions(administrator=True)
    async def ar_channel(self, ctx, channel: discord.abc.GuildChannel):
        """Sets the channel where users will be redirected."""
        database.set_ar_channel(ctx.guild.id, channel.id)
        await ctx.send(f"✅ Auto-responder will now redirect users to {channel.mention}.")

    @ar.command(name='message')
    @commands.has_permissions(administrator=True)
    async def ar_message(self, ctx, *, message: str):
        """Sets the custom reply message. Use {mention} and {channel}."""
        if '{mention}' not in message or '{channel}' not in message:
            await ctx.send("❌ Error: The message must contain both `{mention}` and `{channel}` placeholders.")
            return
        database.set_ar_message(ctx.guild.id, message)
        await ctx.send("✅ Auto-responder message has been updated.")

    @ar.command(name='add')
    @commands.has_permissions(administrator=True)
    async def ar_add(self, ctx, keyword_type: str, *, keyword: str):
        """Adds a keyword. Type must be 'topic' or 'question'."""
        keyword_type = keyword_type.lower()
        if keyword_type not in ['topic', 'question']:
            await ctx.send("❌ Invalid keyword type. Must be `topic` or `question`.")
            return

        if database.add_ar_keyword(ctx.guild.id, keyword_type, keyword):
            await ctx.send(f"✅ Added `{keyword}` to the `{keyword_type}` keyword list.")
        else:
            await ctx.send(f"⚠️ The keyword `{keyword}` is already in the `{keyword_type}` list.")

    @ar.command(name='remove')
    @commands.has_permissions(administrator=True)
    async def ar_remove(self, ctx, keyword_type: str, *, keyword: str):
        """Removes a keyword. Type must be 'topic' or 'question'."""
        keyword_type = keyword_type.lower()
        if keyword_type not in ['topic', 'question']:
            await ctx.send("❌ Invalid keyword type. Must be `topic` or `question`.")
            return

        if database.remove_ar_keyword(ctx.guild.id, keyword_type, keyword):
            await ctx.send(f"✅ Removed `{keyword}` from the `{keyword_type}` keyword list.")
        else:
            await ctx.send(f"❌ The keyword `{keyword}` was not found in the `{keyword_type}` list.")

    @ar.command(name='list')
    @commands.has_permissions(administrator=True)
    async def ar_list(self, ctx):
        """Lists the current auto-responder configuration."""
        config = database.get_ar_config(ctx.guild.id)
        keywords = database.get_ar_keywords(ctx.guild.id)

        topic_keywords = [f"`{row['keyword']}`" for row in keywords if row['keyword_type'] == 'topic']
        question_keywords = [f"`{row['keyword']}`" for row in keywords if row['keyword_type'] == 'question']

        embed = discord.Embed(title="Auto-Responder Configuration", color=discord.Color.blue(), description=f"**Status:** {'🟢 Enabled' if config['is_enabled'] else '🔴 Disabled'}")

        channel_mention = f"<#{config['target_channel_id']}>" if config['target_channel_id'] else "Not Set"
        embed.add_field(name="Target Channel", value=channel_mention, inline=False)

        embed.add_field(name="Reply Message", value=f"```\n{config['reply_message']}\n```", inline=False)

        embed.add_field(name="Topic Keywords", value=", ".join(topic_keywords) if topic_keywords else "None set", inline=False)
        embed.add_field(name="Question Keywords", value=", ".join(question_keywords) if question_keywords else "None set", inline=False)

        await ctx.send(embed=embed)

    @ar.command(name='seed')
    @commands.has_permissions(administrator=True)
    async def ar_seed(self, ctx):
        """Populates the keyword lists with a default set of values."""
        added_count = database.seed_default_ar_keywords(ctx.guild.id)
        if added_count > 0:
            await ctx.send(f"✅ Successfully seeded the database with {added_count} default keywords.")
        else:
            await ctx.send("⚠️ The database already contains all default keywords. No new keywords were added.")

async def setup(bot):
    await bot.add_cog(AutoResponder(bot))