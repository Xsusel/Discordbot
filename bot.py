import discord
from discord.ext import commands, tasks
import os
import database
from datetime import datetime
import webapp
import threading

# --- Bot Setup ---
# Define the intents required for the bot's functionality
intents = discord.Intents.default()
intents.message_content = True  # For reading message content (commands)
intents.voice_states = True     # For voice channel events (music and stats)
intents.members = True          # For member count (stats)

# Initialize the Bot with a command prefix and the defined intents
bot = commands.Bot(command_prefix='$', intents=intents)

# This dictionary is for tracking voice time for statistics, separate from the music cog
voice_sessions = {}

# --- Background Tasks ---
@tasks.loop(hours=24)
async def daily_member_count_task():
    """A background task that runs daily to log the member count of each guild."""
    print("Running daily member count task...")
    for guild in bot.guilds:
        try:
            member_count = guild.member_count
            database.log_member_count(guild.id, member_count)
            print(f"Logged member count for {guild.name}: {member_count}")
        except Exception as e:
            print(f"Error logging member count for guild {guild.name}: {e}")

@daily_member_count_task.before_loop
async def before_daily_task():
    """Wait until the bot is fully ready before starting the task."""
    await bot.wait_until_ready()

# --- Core Events ---
@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    print(f'Logged in as {bot.user}')
    database.init_db()
    print("Database initialized.")

    # Load all cogs from the 'cogs' directory
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'Loaded cog: {filename}')
            except Exception as e:
                print(f'Failed to load cog {filename}: {e}')

    # Start the web server in a background thread
    webapp.set_bot_client(bot)
    web_thread = threading.Thread(target=webapp.run_webapp)
    web_thread.daemon = True
    web_thread.start()
    print("Web server started.")

    # Start the daily background task
    if not daily_member_count_task.is_running():
        daily_member_count_task.start()

@bot.event
async def on_message(message):
    """Called for every message. Logs messages for stats and processes commands."""
    if message.author.bot:
        return
    if message.guild:
        database.log_message(message.author.id, message.guild.id)
    # This is crucial to ensure that command decorators work
    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    """Tracks voice session durations for statistics."""
    user_id = member.id
    guild_id = member.guild.id
    if after.channel and not before.channel:
        voice_sessions[user_id] = datetime.utcnow()
    elif not after.channel and before.channel:
        if user_id in voice_sessions:
            join_time = voice_sessions.pop(user_id)
            leave_time = datetime.utcnow()
            database.log_voice_session(user_id, guild_id, join_time, leave_time)

# --- General Bot Commands ---
@bot.command(name='ping', help='Checks if the bot is responsive.')
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command(name='dashboard', help='Get a link to the web dashboard.')
async def dashboard(ctx):
    if ctx.guild:
        dashboard_url = f"http://localhost:8080/dashboard/{ctx.guild.id}"
        await ctx.send(f"You can view the server dashboard here: {dashboard_url}")
    else:
        await ctx.send("This command can only be used in a server.")

@bot.command(name='stats', help='Shows statistics for messages or voice activity.')
async def stats(ctx, stat_type: str, period: str = 'all'):
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

# --- Run the Bot ---
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    bot.run(token)