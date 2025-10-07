# Minecraft Launcher

A non-premium Minecraft launcher with CurseForge integration.

## Features

*   Select and launch different Minecraft versions.
*   Search for modpacks on CurseForge.
*   Install and update modpacks.

## Setup

1.  **Install Dependencies:**
    This project requires Python 3 and the `requests` and `tqdm` libraries. You can install them using pip:
    ```bash
    pip install requests tqdm
    ```

2.  **Set API Key:**
    This application requires a CurseForge API key to function. You can apply for one through the [CurseForge for Studios Console](https://console.curseforge.com/).

    Once you have your key, you must set it as an environment variable named `CURSEFORGE_API_KEY`.

    **On Linux/macOS:**
    ```bash
    export CURSEFORGE_API_KEY='your_api_key_here'
    ```

    **On Windows (Command Prompt):**
    ```cmd
    set CURSEFORGE_API_KEY=your_api_key_here
    ```
    **On Windows (PowerShell):**
    ```powershell
    $env:CURSEFORGE_API_KEY='your_api_key_here'
    ```
    *Note: You may need to set this variable permanently depending on your system's configuration.*

## Usage

Run the launcher from your terminal:
```bash
python launcher.py
```