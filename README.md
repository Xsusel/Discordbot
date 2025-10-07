# Discord Bot in Docker

This project provides a simple Discord bot that can be easily deployed on a VPS using Docker with a single command.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) must be installed on your system.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create the `.env` file:**
    Create a file named `.env` in the root of the project and add your Discord bot token:
    ```
    DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
    ```
    Replace `YOUR_DISCORD_BOT_TOKEN` with your actual bot token from the [Discord Developer Portal](https://discord.com/developers/applications).

## Running the Bot

You can build and run the bot in a Docker container with the following command:

```bash
docker build -t discord-bot . && docker run --env-file .env -d --name my-discord-bot discord-bot
```

### Command Explanation

-   `docker build -t discord-bot .`: Builds the Docker image from the `Dockerfile` in the current directory and tags it as `discord-bot`.
-   `docker run --env-file .env -d --name my-discord-bot discord-bot`: Runs the `discord-bot` image in detached mode (`-d`), names the container `my-discord-bot`, and loads environment variables from the `.env` file.

## Usage

Once the bot is running and has been invited to your Discord server, you can use the following command:

-   `$ping`: The bot will reply with `Pong!`.

## Stopping the Bot

To stop and remove the container, run:

```bash
docker stop my-discord-bot && docker rm my-discord-bot
```