import discord
from discord.ext import commands, tasks
import os
import database
import logging
from dotenv import load_dotenv

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv('bot.env')

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='$', intents=intents)

    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        logging.info(f'Logged in as {self.user}')
        database.init_db()
        logging.info("Database initialized.")

        # Load the new core cog
        try:
            await self.load_extension('cogs.core')
            logging.info('Loaded cog: core.py')
        except Exception as e:
            logging.error(f'Failed to load cog core.py: {e}')

        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logging.info(f"Synced {len(synced)} slash commands.")
        except Exception as e:
            logging.error(f"Failed to sync slash commands: {e}")

        # Register the error handler for the command tree
        self.tree.on_error = self.on_tree_error

        # Start the daily background task
        if not daily_member_count_task.is_running():
            daily_member_count_task.start()

    async def on_tree_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Global error handler for app commands (slash commands)."""
        if isinstance(error, discord.app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Nie masz uprawnień do użycia tej komendy.", ephemeral=True
            )
        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            await interaction.response.send_message(
                "❌ Bot nie ma wystarczających uprawnień, aby wykonać tę akcję.", ephemeral=True
            )
        elif isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏳ Komenda jest na odnowieniu. Spróbuj ponownie za {error.retry_after:.2f}s.", ephemeral=True
            )
        else:
            logging.error(f"An error occurred in command '{interaction.command.name}': {error}")
            await interaction.response.send_message(
                "❌ Wystąpił błąd podczas wykonywania komendy.", ephemeral=True
            )

bot = MyBot()

# --- Background Tasks ---
@tasks.loop(hours=24)
async def daily_member_count_task():
    """A background task that runs daily to log the member count of each guild."""
    logging.info("Running daily member count task...")
    for guild in bot.guilds:
        try:
            member_count = guild.member_count
            database.log_member_count(guild.id, member_count)
            logging.info(f"Logged member count for {guild.name}: {member_count}")
        except Exception as e:
            logging.error(f"Error logging member count for guild {guild.name}: {e}")

@daily_member_count_task.before_loop
async def before_daily_task():
    await bot.wait_until_ready()

# --- Run the Bot ---
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logging.error("DISCORD_TOKEN not found in bot.env file.")
    else:
        bot.run(token)
