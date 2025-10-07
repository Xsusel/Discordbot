import discord
import os
import database
from datetime import datetime

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # Required for tracking voice activity

client = discord.Client(intents=intents)

# A dictionary to keep track of active voice sessions {user_id: join_time}
voice_sessions = {}

# --- Events ---

@client.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    print(f'We have logged in as {client.user}')
    # Initialize the database
    database.init_db()
    print("Database initialized.")

@client.event
async def on_message(message):
    """Called when a message is sent in a channel the bot can see."""
    # Ignore messages from the bot itself and other bots
    if message.author.bot:
        return

    # Log the message for statistics
    if message.guild:
        database.log_message(message.author.id, message.guild.id)

    # --- Command Handling ---
    if message.content.startswith('$ping'):
        await message.channel.send('Pong!')

    elif message.content.startswith('$stats'):
        args = message.content.split()
        # Provide usage instructions if the command is malformed
        if len(args) < 2 or args[1] not in ['messages', 'voice']:
            await message.channel.send("Usage: `$stats <messages|voice> [daily|weekly|monthly|all]`")
            return

        stat_type = args[1]
        period = 'all'
        if len(args) > 2 and args[2] in ['daily', 'weekly', 'monthly', 'all']:
            period = args[2]

        guild = message.guild
        if not guild:
            return

        embed = discord.Embed(color=discord.Color.gold())

        if stat_type == 'messages':
            stats = database.get_message_stats(guild.id, period)
            title = f"Top Message Senders ({period.capitalize()})"
            embed.title = title
            embed.color = discord.Color.blue()
            if not stats:
                embed.description = "No messages recorded in this period."
            else:
                leaderboard = []
                for i, row in enumerate(stats[:10]):  # Limit to top 10
                    try:
                        member = await guild.fetch_member(row['user_id'])
                        display_name = member.display_name
                    except discord.NotFound:
                        display_name = f"Unknown User (ID: {row['user_id']})"
                    leaderboard.append(f"**{i+1}. {display_name}**: {row['message_count']} messages")
                embed.description = "\n".join(leaderboard)

        elif stat_type == 'voice':
            stats = database.get_voice_stats(guild.id, period)
            title = f"Top Voice Channel Users ({period.capitalize()})"
            embed.title = title
            embed.color = discord.Color.green()
            if not stats:
                embed.description = "No voice activity recorded in this period."
            else:
                leaderboard = []
                for i, row in enumerate(stats[:10]): # Limit to top 10
                    try:
                        member = await guild.fetch_member(row['user_id'])
                        display_name = member.display_name
                    except discord.NotFound:
                        display_name = f"Unknown User (ID: {row['user_id']})"

                    total_seconds = row['total_seconds'] or 0
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    leaderboard.append(f"**{i+1}. {display_name}**: {int(hours)}h {int(minutes)}m")
                embed.description = "\n".join(leaderboard)

        await message.channel.send(embed=embed)

@client.event
async def on_voice_state_update(member, before, after):
    """Called when a member's voice state changes."""
    user_id = member.id
    guild_id = member.guild.id

    # User joined a voice channel or moved from another
    if after.channel and not before.channel:
        voice_sessions[user_id] = datetime.utcnow()
        print(f"User {member.display_name} joined voice channel {after.channel.name}.")

    # User left a voice channel
    elif not after.channel and before.channel:
        if user_id in voice_sessions:
            join_time = voice_sessions.pop(user_id)
            leave_time = datetime.utcnow()
            # Log the session to the database
            database.log_voice_session(user_id, guild_id, join_time, leave_time)
            duration = (leave_time - join_time).total_seconds()
            print(f"User {member.display_name} left voice channel. Session duration: {duration:.2f} seconds.")

# --- Run the Bot ---
# The token is loaded from an environment variable for security.
token = os.getenv('DISCORD_TOKEN')
if not token:
    print("Error: DISCORD_TOKEN environment variable not set.")
else:
    client.run(token)