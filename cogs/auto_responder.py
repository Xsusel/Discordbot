import discord
from discord.ext import commands
import database

class AutoResponder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Auto-responder cog loaded.")

    def _is_eligible_for_response(self, message, config):
        """Checks if a message is in a context where an auto-response is appropriate."""
        if not message.guild:
            return False
        if not config or not config.get('is_enabled') or not config.get('target_channel_id'):
            return False
        if message.channel.id == config['target_channel_id']:
            return False
        return True

    def _is_question_about_topic(self, content, topic_keywords, question_keywords):
        """Determines if the message content is a question about a specific topic."""
        content_lower = content.lower()

        # Check for topic keywords
        if not any(keyword in content_lower for keyword in topic_keywords):
            return False

        # Check if it's a question (ends with '?' or contains a question word)
        if content_lower.endswith('?') or any(q_word in content_lower.split() for q_word in question_keywords):
            return True

        return False

    async def check_for_response(self, message):
        """Checks a message and sends an auto-response if it matches the guild's dynamic criteria."""
        config = database.get_ar_config(message.guild.id)

        if not self._is_eligible_for_response(message, config):
            return

        keywords = database.get_ar_keywords(message.guild.id)
        topic_keywords = [row['keyword'] for row in keywords if row['keyword_type'] == 'topic']
        question_keywords = [row['keyword'] for row in keywords if row['keyword_type'] == 'question']

        if not topic_keywords or not question_keywords:
            return

        if self._is_question_about_topic(message.content, topic_keywords, question_keywords):
            try:
                reply_message = config['reply_message'].format(
                    mention=message.author.mention,
                    channel=f"<#{config['target_channel_id']}>"
                )
                await message.reply(reply_message, mention_author=False)
                print(f"Auto-responded to {message.author} in guild {message.guild.id}.")
            except discord.errors.Forbidden:
                print(f"Could not reply to {message.author} in {message.channel.id}. Missing permissions.")
            except Exception as e:
                print(f"An error occurred in auto-responder: {e}")

    @commands.group(name='ar', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def ar(self, ctx):
        """Manages the auto-responder. Use `$ar help` for commands."""
        await ctx.send("Invalid subcommand. Use `$ar list` for config or `$ar help` for commands.")

    @ar.command(name='toggle')
    @commands.has_permissions(administrator=True)
    async def ar_toggle(self, ctx):
        """Enables or disables the auto-responder."""
        config = database.get_ar_config(ctx.guild.id)
        new_state = not config.get('is_enabled', False)
        database.set_ar_enabled(ctx.guild.id, new_state)
        await ctx.send(f"✅ Auto-responder has been **{'enabled' if new_state else 'disabled'}**.")

    @ar.command(name='channel')
    @commands.has_permissions(administrator=True)
    async def ar_channel(self, ctx, channel_str: str):
        """Sets the channel where users will be redirected. Accepts channel ID or mention."""
        try:
            # Clean the input string to extract the channel ID
            if channel_str.startswith('<#') and channel_str.endswith('>'):
                channel_id = int(channel_str[2:-1])
            else:
                channel_id = int(channel_str)

            # Fetch the channel object from the bot's cache
            channel = self.bot.get_channel(channel_id)

            # Verify the channel is a text channel in the correct guild
            if not channel or not isinstance(channel, discord.TextChannel) or channel.guild.id != ctx.guild.id:
                raise commands.ChannelNotFound(channel_str)

            database.set_ar_channel(ctx.guild.id, channel.id)
            await ctx.send(f"✅ Auto-responder will now redirect users to {channel.mention}.")

        except (ValueError, commands.ChannelNotFound):
            await ctx.send(f"❌ Could not find a text channel with the input `{channel_str}`. Please provide a valid channel mention or ID.")

    @ar.command(name='message')
    @commands.has_permissions(administrator=True)
    async def ar_message(self, ctx, *, message: str):
        """Sets the reply message. Use {mention} and {channel}."""
        if '{mention}' not in message or '{channel}' not in message:
            await ctx.send("❌ The message must contain `{mention}` and `{channel}` placeholders.")
            return
        database.set_ar_message(ctx.guild.id, message)
        await ctx.send("✅ Auto-responder message updated.")

    @ar.command(name='add')
    @commands.has_permissions(administrator=True)
    async def ar_add(self, ctx, keyword_type: str, *, keyword: str):
        """Adds a keyword. Type: 'topic' or 'question'."""
        keyword_type = keyword_type.lower()
        if keyword_type not in ['topic', 'question']:
            await ctx.send("❌ Invalid type. Must be `topic` or `question`.")
            return

        if database.add_ar_keyword(ctx.guild.id, keyword_type, keyword):
            await ctx.send(f"✅ Added `{keyword}` to the `{keyword_type}` list.")
        else:
            await ctx.send(f"⚠️ `{keyword}` is already in the `{keyword_type}` list.")

    @ar.command(name='remove')
    @commands.has_permissions(administrator=True)
    async def ar_remove(self, ctx, keyword_type: str, *, keyword: str):
        """Removes a keyword. Type: 'topic' or 'question'."""
        keyword_type = keyword_type.lower()
        if keyword_type not in ['topic', 'question']:
            await ctx.send("❌ Invalid type. Must be `topic` or `question`.")
            return

        if database.remove_ar_keyword(ctx.guild.id, keyword_type, keyword):
            await ctx.send(f"✅ Removed `{keyword}` from the `{keyword_type}` list.")
        else:
            await ctx.send(f"❌ `{keyword}` not found in the `{keyword_type}` list.")

    @ar.command(name='list')
    @commands.has_permissions(administrator=True)
    async def ar_list(self, ctx):
        """Lists the current auto-responder configuration."""
        config = database.get_ar_config(ctx.guild.id)
        keywords = database.get_ar_keywords(ctx.guild.id)

        topic_keywords = [f"`{r['keyword']}`" for r in keywords if r['keyword_type'] == 'topic']
        question_keywords = [f"`{r['keyword']}`" for r in keywords if r['keyword_type'] == 'question']

        status = '🟢 Enabled' if config.get('is_enabled') else '🔴 Disabled'
        embed = discord.Embed(title="Auto-Responder Configuration", description=f"**Status:** {status}", color=discord.Color.blue())

        channel_mention = f"<#{config['target_channel_id']}>" if config.get('target_channel_id') else "Not Set"
        embed.add_field(name="Target Channel", value=channel_mention, inline=False)

        reply_msg = config.get('reply_message', 'Not set.')
        embed.add_field(name="Reply Message", value=f"```\n{reply_msg}\n```", inline=False)

        embed.add_field(name="Topic Keywords", value=", ".join(topic_keywords) or "None", inline=False)
        embed.add_field(name="Question Keywords", value=", ".join(question_keywords) or "None", inline=False)

        await ctx.send(embed=embed)

    @ar.command(name='seed')
    @commands.has_permissions(administrator=True)
    async def ar_seed(self, ctx):
        """Populates the keyword lists with default values."""
        added_count = database.seed_default_ar_keywords(ctx.guild.id)
        if added_count > 0:
            await ctx.send(f"✅ Seeded the database with {added_count} default keywords.")
        else:
            await ctx.send("⚠️ Database already contains all default keywords.")

async def setup(bot):
    await bot.add_cog(AutoResponder(bot))