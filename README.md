# Discord Bot with Web Dashboard in Docker

This project provides a Discord bot with a web dashboard that can be easily deployed on a VPS using Docker. The bot tracks user activity and server statistics, which are then displayed on a web interface.

## Features

-   **Message Tracking**: Logs every message sent by users.
-   **Voice Activity Tracking**: Records the time users spend in voice channels.
-   **Daily Member Count**: Tracks the server's member count daily.
-   **Web Dashboard**: A web page to visualize server statistics, including a member count graph and a leaderboard of the most active users.
-   **Dockerized**: Runs both the bot and the web server in a single container.

## Prerequisites

-   [Docker](https://docs.docker.com/get-docker/) must be installed on your system.

## Bot Setup and Invitation

Before you can run the project, you need to create a Discord bot application and invite it to your server.

### 1. Create the Bot Application
1.  Go to the [Discord Developer Portal](https://discord.com/developers/applications) and log in.
2.  Click the **"New Application"** button. Give it a name and click **"Create"**.
3.  In the menu on the left, go to the **"Bot"** tab.
4.  Under the "Privileged Gateway Intents" section, enable the following intents:
    -   **SERVER MEMBERS INTENT** (required for member count tracking).
    -   **MESSAGE CONTENT INTENT** (required for reading messages and commands).
5.  Click **"Save Changes"**.

### 2. Get the Bot Token
-   Still on the **"Bot"** tab, click the **"Reset Token"** button (or "View Token" if you've just created it) to reveal your bot's token.
-   **This token is a secret!** Do not share it with anyone. You will need it in the next step.

### 3. Invite the Bot to Your Server
1.  In the menu on the left, go to the **"OAuth2"** tab and then click on **"URL Generator"**.
2.  In the **"SCOPES"** section, check the `bot` box.
3.  A new **"BOT PERMISSIONS"** section will appear below. Check the following permissions:
    -   `Send Messages`
    -   `Read Message History`
    -   `Embed Links`
4.  Scroll down and copy the **generated URL**.
5.  Paste the URL into your browser, select the server you want to add the bot to, and click **"Authorize"**.

## Project Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create the `.env` file:**
    Create a file named `.env` in the root of the project and add your Discord bot token that you obtained in the previous step:
    ```
    DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
    ```

## Running the Bot

You can build and run the bot and web server in a Docker container with the following command. This command also maps port 8080 from the container to your host machine, allowing you to access the web dashboard.

```bash
docker build -t discord-bot . && docker run --env-file .env -d -p 8080:8080 --name my-discord-bot discord-bot
```

### Command Explanation

-   `docker build -t discord-bot .`: Builds the Docker image.
-   `docker run ...`: Runs the container.
    -   `--env-file .env`: Loads the Discord token from your `.env` file.
    -   `-d`: Runs the container in detached mode.
    -   `-p 8080:8080`: Maps port 8080 of the container to port 8080 on your host machine.
    -   `--name my-discord-bot`: Names the container for easy management.

## Bot Commands

-   `$ping`: The bot will reply with `Pong!`.

-   `$stats <type> [period]`: Displays leaderboards for user activity.
    -   **type**: `messages` or `voice`.
    -   **period** (optional): `daily`, `weekly`, `monthly`, or `all` (default).

-   `$dashboard`: The bot will reply with a link to the web dashboard for the current server.

## Web Dashboard

Once the container is running, you can access the web dashboard for any server the bot is in.

1.  Use the `$dashboard` command in your Discord server to get a direct link.
2.  Alternatively, you can manually navigate to `http://<your-vps-ip-or-domain>:8080/dashboard/<your-server-id>`.

The dashboard displays:
-   A graph of the server's member count over time.
-   A leaderboard of the top 10 most active users based on a combined score of messages and voice activity.

## Stopping the Bot

To stop and remove the container, run:

```bash
docker stop my-discord-bot && docker rm my-discord-bot
```