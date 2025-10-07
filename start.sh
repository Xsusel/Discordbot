#!/bin/bash
# This script is the entrypoint for the Docker container.

echo "Checking for Discord token..."

# Check if the DISCORD_TOKEN environment variable is set
if [ -z "$DISCORD_TOKEN" ]; then
  echo "ERROR: The DISCORD_TOKEN environment variable is not set."
  echo "Please create a .env file with your token or provide it in the Docker run command."
  # Exit with a non-zero status to indicate an error
  exit 1
fi

echo "Token found. Starting the application..."
# Use python3 as the command, which is standard in many base images
python3 bot.py