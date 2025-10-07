import discord
import os

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$ping'):
        await message.channel.send('Pong!')

# It's recommended to run the bot using a token stored in an environment variable.
# I will create a .env file later for this.
# For now, this structure is good.
# The Dockerfile will handle getting the token from the environment.
client.run(os.getenv('DISCORD_TOKEN'))