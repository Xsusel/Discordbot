# This file will manage downloading, installing, and launching Minecraft.
import os
import json
import subprocess
import zipfile
import uuid
import requests
import minecraft_launcher_lib
from utils import download_file

MINECRAFT_PATH = minecraft_launcher_lib.utils.get_minecraft_directory().replace('minecraft', 'minecraft-launcher')

class MinecraftManager:
    def __init__(self, curseforge_api):
        self.cf_api = curseforge_api

    def install_version(self, version_string):
        """Installs the specified Minecraft version using minecraft-launcher-lib."""
        print(f"Installing Minecraft version {version_string} using the library...")
        try:
            minecraft_launcher_lib.install.install_minecraft_version(version_string, MINECRAFT_PATH)
            print(f"Minecraft {version_string} installed successfully.")
            return True
        except Exception as e:
            print(f"Failed to install Minecraft {version_string}: {e}")
            return False

    def launch_game(self, username, version_string):
        """Prepares and launches the specified Minecraft version using minecraft-launcher-lib."""
        version_path = os.path.join(MINECRAFT_PATH, 'versions', version_string)
        if not os.path.isdir(version_path):
            print(f"Version {version_string} is not installed. Installing now...")
            if not self.install_version(version_string):
                print(f"Failed to install version {version_string}. Cannot launch.")
                return

        # Generate a consistent UUID for the username for offline play
        offline_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, username))

        options = {
            "username": username,
            "uuid": offline_uuid,
            "token": "0"  # Not required for offline play
        }

        try:
            command = minecraft_launcher_lib.command.get_minecraft_command(version_string, MINECRAFT_PATH, options)
            print("Launching Minecraft...")
            print(f"Command: {' '.join(command)}")
            subprocess.Popen(command, cwd=MINECRAFT_PATH)
        except FileNotFoundError:
            print("Error: 'java' command not found. Please make sure Java is installed and in your PATH.")
        except Exception as e:
            print(f"An error occurred while launching Minecraft: {e}")

    def install_modpack(self, modpack_data, progress_callback=None, status_callback=None):
        """Downloads and fully installs a modpack, with callbacks for GUI updates."""
        print(f"Starting full installation of modpack: {modpack_data['name']}")
        try:
            mod_id = modpack_data['id']
            if status_callback: status_callback("Fetching modpack file list...")
            files = self.cf_api.get_mod_files(mod_id)
            modpack_file = next((f for f in sorted(files, key=lambda x: x['fileDate'], reverse=True) if f['fileName'].endswith('.zip')), None)

            if not modpack_file:
                raise Exception("No suitable zip file found for this modpack.")

            file_id = modpack_file['id']
            download_url = self.cf_api.get_mod_file_download_url(mod_id, file_id)

            temp_dir = os.path.join(MINECRAFT_PATH, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            zip_path = os.path.join(temp_dir, modpack_file['fileName'])

            if status_callback: status_callback(f"Downloading {modpack_file['fileName']}...")
            download_file(download_url, zip_path, progress_callback)

            if status_callback: status_callback("Extracting modpack...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                overrides_path = 'overrides/'
                for member in zip_ref.infolist():
                    if member.filename.startswith(overrides_path) and not member.is_dir():
                        target_path = os.path.join(MINECRAFT_PATH, member.filename[len(overrides_path):])
                        if not os.path.realpath(target_path).startswith(os.path.realpath(MINECRAFT_PATH)):
                             raise Exception(f"Attempted path traversal in zip file: {member.filename}")
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with zip_ref.open(member) as source, open(target_path, "wb") as target:
                            target.write(source.read())

                manifest = json.loads(zip_ref.read('manifest.json'))
                minecraft_version = manifest['minecraft']['version']
                modloader_data = next((loader for loader in manifest['minecraft']['modLoaders'] if loader['primary']), None)

                launch_version = minecraft_version
                if modloader_data:
                    full_modloader_version = f"{minecraft_version}-{modloader_data['id']}"
                    if status_callback: status_callback(f"Installing modloader: {full_modloader_version}...")
                    minecraft_launcher_lib.forge.install_forge_version(full_modloader_version, MINECRAFT_PATH)
                    launch_version = full_modloader_version

                mods_path = os.path.join(MINECRAFT_PATH, 'mods')
                os.makedirs(mods_path, exist_ok=True)
                total_mods = len(manifest['files'])
                if status_callback: status_callback(f"Downloading {total_mods} mods...")

                for i, mod_file in enumerate(manifest['files']):
                    mod_info_files = self.cf_api.get_mod_files(mod_file['projectID'])
                    file_info = next((f for f in mod_info_files if f['id'] == mod_file['fileID']), None)
                    file_name = file_info['fileName'] if file_info else f"{mod_file['projectID']}-{mod_file['fileID']}.jar"

                    if status_callback: status_callback(f"Downloading mod {i+1}/{total_mods}: {file_name}...")

                    mod_download_url = self.cf_api.get_mod_file_download_url(mod_file['projectID'], mod_file['fileID'])
                    if mod_download_url:
                        mod_path = os.path.join(mods_path, file_name)
                        download_file(mod_download_url, mod_path, progress_callback)
                    else:
                        print(f"Could not get download URL for mod {file_name}")

            os.remove(zip_path)

            with open(os.path.join(MINECRAFT_PATH, 'installed_modpack.json'), 'w') as f:
                json.dump({'mod_id': mod_id, 'file_id': file_id, 'name': modpack_data['name'], 'launch_version': launch_version}, f)

            if status_callback: status_callback(f"Modpack '{modpack_data['name']}' installed successfully.")

        except Exception as e:
            if status_callback: status_callback(f"Error: {e}")
            print(f"Failed to install modpack: {e}")

    def check_for_updates(self):
        """Checks if there is an update for the installed modpack."""
        modpack_info_path = os.path.join(MINECRAFT_PATH, 'installed_modpack.json')
        if not os.path.exists(modpack_info_path):
            return None, "No modpack is currently installed.", None

        with open(modpack_info_path, 'r') as f:
            installed_data = json.load(f)

        try:
            print(f"Checking for updates for {installed_data['name']}...")
            files = self.cf_api.get_mod_files(installed_data['mod_id'])
            latest_file = sorted(files, key=lambda x: x['fileDate'], reverse=True)[0]

            if latest_file['id'] != installed_data['file_id']:
                modpack_data_for_install = {'id': installed_data['mod_id'], 'name': installed_data['name']}
                return True, f"An update is available for {installed_data['name']}!", modpack_data_for_install
            else:
                return False, "You have the latest version of the modpack.", None
        except Exception as e:
            return None, f"An error occurred while checking for updates: {e}", None