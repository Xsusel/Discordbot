#!/bin/bash
# This script is the entrypoint for the Docker container.

# Check for the existence of the bot.env file and source it if it exists.
if [ -f "bot.env" ]; then
    echo "Loading environment variables from bot.env..."
    # The 'export' command ensures that the variables are available to child processes.
    export $(cat bot.env | sed 's/#.*//g' | xargs)
fi

echo "Checking for Discord token..."

# Check if the DISCORD_TOKEN environment variable is set
if [ -z "$DISCORD_TOKEN" ] || [ "$DISCORD_TOKEN" == "your_discord_bot_token_placeholder" ]; then
  echo "ERROR: The DISCORD_TOKEN is not set or is still the placeholder value."
  echo "Please create and configure the bot.env file with your actual token."
  # Exit with a non-zero status to indicate an error
  exit 1
fi

echo "Token found. Starting the application..."
python3 bot.py