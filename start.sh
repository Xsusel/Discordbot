#!/bin/bash
# This script is the entrypoint for the Docker container.

echo "Checking for Discord token..."

# Check if the DISCORD_TOKEN environment variable is set
if [ -z "$DISCORD_TOKEN" ]; then
  echo "ERROR: The DISCORD_TOKEN environment variable is not set."
  echo "Please create a bot.env file with your token and use the --env-file flag in your Docker run command."
  # Exit with a non-zero status to indicate an error
  exit 1
fi

echo "Token found. Starting the application..."
python3 bot.py