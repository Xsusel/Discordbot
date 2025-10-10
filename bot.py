import discord
from discord.ext import commands, tasks
import os
import database
from datetime import datetime
import webapp
import threading
from dotenv import load_dotenv

load_dotenv('bot.env')

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
    """Called for every message. Logs messages, checks for AI, auto-responses, and processes commands."""
    if message.author.bot:
        return

    # Log the message for statistics
    if message.guild:
        database.log_message(message.author.id, message.guild.id)

    # Check if the bot was mentioned for an AI response
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        ai_cog = bot.get_cog('AI')
        if ai_cog and ai_cog.model:
            # Clean the message content of the bot's mention
            question = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
            if question:
                async with message.channel.typing():
                    response = await ai_cog.get_ai_response(question)
                    if response:
                        await message.reply(response)
                return # Stop further processing to avoid command conflicts

    # Check if the auto-responder cog should handle this message
    auto_responder_cog = bot.get_cog('AutoResponder')
    if auto_responder_cog:
        await auto_responder_cog.check_for_response(message)

    # Process any potential commands in the message
    await bot.process_commands(message)

# The on_voice_state_update event is now handled by the AuditLog cog
# to provide detailed logging and to track session times for statistics.

# --- General Bot Commands ---
# All commands have been moved to their respective cogs in the 'cogs/' directory.
# This main file is now responsible only for loading cogs and handling core events.


# --- Run the Bot ---
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    bot.run(token)