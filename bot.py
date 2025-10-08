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
    """Called for every message. Logs messages, checks for auto-responses, and processes commands."""
    if message.author.bot:
        return

    # First, log the message for statistics
    if message.guild:
        database.log_message(message.author.id, message.guild.id)

    # Then, check if the auto-responder cog should handle this message
    auto_responder_cog = bot.get_cog('AutoResponder')
    if auto_responder_cog:
        await auto_responder_cog.check_for_response(message)

    # Finally, process any potential commands in the message
    await bot.process_commands(message)

# The on_voice_state_update event is now handled by the AuditLog cog
# to provide detailed logging and to track session times for statistics.

# --- Global Error Handler ---
@bot.event
async def on_command_error(ctx, error):
    """A global error handler for all commands."""
    if isinstance(error, commands.CommandNotFound):
        # Silently ignore commands that don't exist
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        # Provide helpful feedback for missing arguments
        await ctx.send(f"❌ You are missing a required argument: `{error.param.name}`.\n"
                       f"Use `{ctx.prefix}help {ctx.command}` for more info.")
    elif isinstance(error, commands.ChannelNotFound):
        await ctx.send(f"❌ I could not find the channel `{error.argument}`. Please make sure it exists and I can see it.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Invalid argument provided. Please check the command's usage with `{ctx.prefix}help {ctx.command}`.")
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("This command cannot be used in private messages.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f"🚫 You do not have the required permissions to run this command: `{'`, `'.join(error.missing_permissions)}`")
    else:
        # For any other errors, log them to the console
        print(f"Ignoring exception in command {ctx.command}:")
        import traceback
        traceback.print_exception(type(error), error, error.__traceback__)

# --- General Bot Commands ---
# All commands have been moved to their respective cogs in the 'cogs/' directory.
# This main file is now responsible only for loading cogs and handling core events.


# --- Run the Bot ---
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    bot.run(token)