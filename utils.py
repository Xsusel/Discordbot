import requests
import os

def download_file(url, dest_path, progress_callback=None):
    """Downloads a file from a URL to a destination path with an optional progress callback."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024
    downloaded = 0

    with open(dest_path, 'wb') as file:
        for data in response.iter_content(block_size):
            downloaded += len(data)
            file.write(data)
            if progress_callback and total_size > 0:
                progress = (downloaded / total_size) * 100
                progress_callback(progress)

    if total_size != 0 and downloaded != total_size:
        raise Exception("ERROR, something went wrong during download")