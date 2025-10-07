# Discord Bot with Web Dashboard in Docker

This project provides a Discord bot with a web dashboard that can be easily deployed on a VPS using Docker. The bot tracks user activity and server statistics, which are then displayed on a web interface.

## Features

-   **Message Tracking**: Logs every message sent by users.
-   **Voice Activity Tracking**: Records the time users spend in voice channels.
-   **Daily Member Count**: Tracks the server's member count daily.
-   **Web Dashboard**: A web page to visualize server statistics, including a member count graph and a leaderboard of the most active users.
-   **Music Playback**: Play music from YouTube by providing a URL or search query.
-   **Auto-Responder**: Automatically replies to questions about settings, directing users to a designated channel.
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
-   **This token is a secret!** Do not share it with anyone. You will need it in the "Project Setup" step below.

### 3. Invite the Bot to Your Server
1.  In the menu on the left, go to the **"OAuth2"** tab and then click on **"URL Generator"**.
2.  In the **"SCOPES"** section, check the `bot` box.
3.  A new **"BOT PERMISSIONS"** section will appear below. Check the following permissions, which are required for statistics and music playback:
    -   `Send Messages`
    -   `Read Message History`
    -   `Embed Links`
    -   `Connect` (to join voice channels)
    -   `Speak` (to play audio)
4.  Scroll down and copy the **generated URL**.
5.  Paste the URL into your browser, select the server you want to add the bot to, and click **"Authorize"**.

## Project Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```
2.  **Create and configure the `bot.env` file:**
    Create a file named `bot.env` in the root of the project. This file holds the configuration for your bot.
    You need to add the following variables:
    ```
    # Your bot's secret token from the Discord Developer Portal
    DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN

    # The public IP address of your server (e.g., 123.45.67.89)
    # This is needed for the $dashboard command to generate correct links.
    BOT_HOST_IP=your_server_ip
    ```
    Replace the placeholder values with your actual data.

## Running the Bot

You can build and run the bot and web server in a Docker container with the following command. This command also maps port 8080 from the container to your host machine, allowing you to access the web dashboard.

```bash
docker build -t discord-bot . && docker run --env-file bot.env -d -p 8080:8080 --name my-discord-bot discord-bot
```

### Command Explanation

-   `docker build -t discord-bot .`: Builds the Docker image.
-   `docker run ...`: Runs the container.
    -   `--env-file bot.env`: Loads the Discord token from your `bot.env` file.
    -   `-d`: Runs the container in detached mode.
    -   `-p 8080:8080`: Maps port 8080 of the container to port 8080 on your host machine.
    -   `--name my-discord-bot`: Names the container for easy management.

## Bot Commands

-   `$ping`: The bot will reply with `Pong!`.

-   `$stats <type> [period]`: Displays leaderboards for user activity.
    -   **type**: `messages` or `voice`.
    -   **period** (optional): `daily`, `weekly`, `monthly`, or `all` (default).

-   `$dashboard`: The bot will reply with a link to the web dashboard for the current server.

-   `$voicelogs`: Shows a log of users joining and leaving voice channels in the last 24 hours.

-   `$debug`: Runs and displays a report of diagnostic checks, such as the status of the YouTube cookie file.

## Auto-Responder Commands

The auto-responder feature is fully configurable via commands. These commands are only available to users with **Administrator** permissions. The main command group is `$ar`.

-   `$ar list`: Shows the current configuration for the auto-responder, including its status, target channel, reply message, and all keywords.
-   `$ar toggle`: Enables or disables the auto-responder on the server.
-   `$ar channel <#channel>`: Sets the text channel where users will be redirected.
-   `$ar message <your custom message>`: Sets the reply message. You must include `{mention}` and `{channel}` placeholders, which will be replaced with the user's mention and the target channel link, respectively.
-   `$ar add <type> <keyword>`: Adds a new keyword.
    -   **type**: Must be `topic` or `question`.
    -   **keyword**: The word or phrase to add.
-   `$ar remove <type> <keyword>`: Removes a keyword.
    -   **type**: Must be `topic` or `question`.
    -   **keyword**: The word or phrase to remove.
-   `$ar seed`: Populates the keyword lists with a recommended default set of keywords to get you started quickly.

## Music Commands

-   `$play <youtube_url_or_search>`: Plays a song from a YouTube URL or search query. If a song is already playing, it adds the new song to the queue.
-   `$pause`: Pauses the currently playing song.
-   `$resume`: Resumes a paused song.
-   `$skip`: Skips the current song and plays the next one in the queue.
-   `$stop`: Stops the music and clears the queue.
-   `$queue`: Displays the current list of songs in the queue.
-   `$leave`: Disconnects the bot from the voice channel.

## Web Dashboard

Once the container is running, you can access the web dashboard for any server the bot is in.

1.  Use the `$dashboard` command in your Discord server to get a direct link.
2.  Alternatively, you can manually navigate to `http://<your-vps-ip-or-domain>:8080/dashboard/<your-server-id>`.

The dashboard displays:
-   A graph of the server's member count over time.
-   A leaderboard of the top 10 most active users based on a combined score of messages and voice activity.

## Troubleshooting

If you encounter issues, here are some steps to diagnose the problem.

### The Bot is Offline
If the bot is not coming online on Discord, the first step is to check its logs for errors.

1.  **Check the container logs:**
    ```bash
    sudo docker logs my-discord-bot
    ```
2.  Look for any tracebacks or error messages. Common issues include an invalid token (`LoginFailure`) or missing privileged intents. Follow the setup steps carefully to resolve these.

### The Web Dashboard is Not Loading
If the bot is online but you can't access the web dashboard, the issue is likely with the web server or your server's network configuration.

1.  **Check the container logs:**
    Run `sudo docker logs my-discord-bot` again. Look for any errors that occurred after the bot connected successfully. The error log we added will print any problems encountered while trying to render the page.

2.  **Check if the port is exposed:**
    Make sure you included the `-p 8080:8080` flag in your `docker run` command.

3.  **Check your server's firewall:**
    Many cloud providers (like AWS, Google Cloud, Azure) and VPS hosts have a network firewall that blocks all ports by default. You need to create a rule to allow incoming traffic on TCP port `8080`.

    If you are using `ufw` (Uncomplicated Firewall) on your server, you can open the port with this command:
    ```bash
    sudo ufw allow 8080/tcp
    ```
    After running this, you may need to reload `ufw` or your server for the changes to take effect.

### Music Fails with "Sign in to confirm you're not a bot"
This error occurs because YouTube is detecting that the request is coming from a server (your VPS) and is blocking it to prevent abuse. To fix this, you need to provide the bot with your YouTube browser cookies to authenticate the request.

1.  **Install a Cookie Exporter Extension:**
    -   Install a browser extension that can export cookies in the required `Netscape` format. A recommended one is **"Get cookies.txt LOCALLY"**, available for both [Chrome](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelhbbjliilanpilogKdkleogackad) and [Firefox](https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/).

2.  **Export Your YouTube Cookies:**
    -   Go to `https://www.youtube.com` in your browser and make sure you are logged in to your Google account.
    -   Click the cookie exporter extension's icon in your browser's toolbar.
    -   Click the **"Export"** or **"Save"** button to download the cookies file.

3.  **Add the Cookie File to Your Project:**
    -   Rename the downloaded file to exactly `cookies.txt`.
    -   Place this `cookies.txt` file in the root directory of your project (the same directory as the `Dockerfile`).

4.  **Rebuild the Docker Image:**
    -   For the bot to access the new file, you **must** rebuild your Docker image. The existing `docker run` command will not see the new file.
    -   Stop and remove the old container first, then rebuild and run:
        ```bash
        sudo docker stop my-discord-bot && sudo docker rm my-discord-bot
        sudo docker build -t discord-bot . && sudo docker run --env-file bot.env -d -p 8080:8080 --name my-discord-bot discord-bot
        ```
    -   This will copy the `cookies.txt` file into the new image, and the bot will automatically start using it.

## Stopping the Bot

To stop and remove the container, run:

```bash
docker stop my-discord-bot && docker rm my-discord-bot
```