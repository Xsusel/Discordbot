import requests
import os

API_KEY = os.getenv("CURSEFORGE_API_KEY")
BASE_URL = "https://api.curseforge.com"

class CurseForgeAPI:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("CurseForge API key not found. Please set the CURSEFORGE_API_KEY environment variable.")
        self.api_key = api_key
        self.headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }

    def get_minecraft_versions(self):
        """Fetches all available Minecraft versions."""
        response = requests.get(f"{BASE_URL}/v1/minecraft/version", headers=self.headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()['data']

    def search_modpacks(self, search_filter, game_version=''):
        """Searches for modpacks on CurseForge."""
        params = {
            'gameId': 432,  # 432 is the game ID for Minecraft
            'classId': 4471,  # 4471 is for Modpacks
            'searchFilter': search_filter,
            'sortField': 2, # Sort by popularity
        }
        if game_version:
            params['gameVersion'] = game_version

        response = requests.get(f"{BASE_URL}/v1/mods/search", headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()['data']

    def get_mod_files(self, mod_id):
        """Gets all files for a given mod."""
        response = requests.get(f"{BASE_URL}/v1/mods/{mod_id}/files", headers=self.headers)
        response.raise_for_status()
        return response.json()['data']

    def get_mod_file_download_url(self, mod_id, file_id):
        """Gets the download URL for a specific file."""
        response = requests.get(f"{BASE_URL}/v1/mods/{mod_id}/files/{file_id}/download-url", headers=self.headers)
        response.raise_for_status()
        # The download URL is in the 'data' field of the response
        return response.json()['data']

if __name__ == '__main__':
    # Example usage:
    cf_api = CurseForgeAPI(API_KEY)
    try:
        versions = cf_api.get_minecraft_versions()
        for version in versions:
            print(version['versionString'])
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")