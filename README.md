# Discord Bot with Web Dashboard in Docker

This project provides a simplified, robust Discord bot with a web dashboard, deployable via Docker. The bot focuses on core features like user activity tracking and a simple economy system, rebuilt from the ground up for stability and ease of use.

## Features

-   **Unified Point System**: Tracks two types of points:
    -   **Activity Points (AP)**: Earned for messaging and voice activity. Used for the activity leaderboard.
    -   **Gambling Points (GP)**: Used as a currency for betting and buying roles in the shop.
-   **Daily Member Count**: Logs the server's member count each day.
-   **Web Dashboard**: A web page to visualize server statistics, including a member count graph and a leaderboard of the most active users.
-   **Simple Economy**: Bet your Gambling Points or spend them in a server-specific role shop.
-   **Dockerized**: Runs both the bot and the web server in a single container for easy deployment.

## Prerequisites

-   [Docker](https://docs.docker.com/get-docker/) must be installed on your system.

## Bot Setup and Invitation

### 1. Create the Bot Application
1.  Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2.  Click **"New Application"**, give it a name, and click **"Create"**.
3.  Navigate to the **"Bot"** tab.
4.  Under "Privileged Gateway Intents", enable:
    -   **SERVER MEMBERS INTENT**
    -   **MESSAGE CONTENT INTENT**
5.  Click **"Save Changes"**.

### 2. Get the Bot Token
-   On the **"Bot"** tab, click **"Reset Token"** to get your bot's token. **Treat this like a password and keep it secret.**

### 3. Invite the Bot to Your Server
1.  Go to the **"OAuth2"** tab and then **"URL Generator"**.
2.  In **"SCOPES"**, check the `bot` box.
3.  In **"BOT PERMISSIONS"**, check the following:
    -   `Send Messages`
    -   `Read Message History`
    -   `Embed Links`
    -   `Connect`
    -   `Speak`
    -   `Manage Roles` (for the role shop)
4.  Copy the generated URL and paste it into your browser to invite the bot to your server.

## Project Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```
2.  **Create and configure the `bot.env` file:**
    Create a file named `bot.env` in the root of the project with the following content:
    ```
    # Your bot's secret token from the Discord Developer Portal
    DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
    ```
    Replace `YOUR_DISCORD_BOT_TOKEN` with your actual token.

## Running the Bot

Build and run the Docker container with this command:

```bash
docker build -t discord-bot . && docker run --env-file bot.env -d -p 8080:8080 --name my-discord-bot discord-bot
```

-   `docker build -t discord-bot .`: Builds the Docker image.
-   `docker run ...`: Runs the container.
    -   `--env-file bot.env`: Loads your secret token.
    -   `-d`: Runs in detached mode.
    -   `-p 8080:8080`: Maps the container's port 8080 to your host's port 8080.
    -   `--name my-discord-bot`: Gives the container a convenient name.

## Bot Commands

### User Commands

-   `$top [monthly]`: Shows the leaderboard for the most active users (Activity Points). Use `monthly` to see this month's leaderboard.
-   `$wallet`: Shows the leaderboard for the richest users (Gambling Points).
-   `$balance [@user]`: Checks your or another user's Gambling Points balance.
-   `$bet <amount>`: Bets a certain amount of your Gambling Points.
-   `$shop`: Displays the roles available for purchase with Gambling Points.
-   `$buy <item_id>`: Buys a role from the shop.
-   `$dashboard`: Provides a link to the web dashboard for the server.

### Admin Commands

-   `$givepoints <@user> <amount>`: Gives a user a specified amount of Gambling Points.
-   `$takepoints <@user> <amount>`: Takes a specified amount of Gambling Points from a user.
-   `$shopadmin add <@role> <price>`: Adds a role to the shop.
-   `$shopadmin remove <item_id>`: Removes a role from the shop by its ID.

## Web Dashboard

Access the web dashboard by using the `$dashboard` command in your server. The dashboard displays:
-   A graph of the server's member count over time.
-   A leaderboard of the top 10 most active users based on their Activity Points.

## Stopping the Bot

To stop and remove the container, run:
```bash
docker stop my-discord-bot && docker rm my-discord-bot
```
