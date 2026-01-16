import requests
import os

BASE_URL = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights"
CDN_URL = "https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js"

MODELS_DIR = "src/web/static/models"
JS_DIR = "src/web/static/js"

files_to_download = [
    "tiny_face_detector_model-weights_manifest.json",
    "tiny_face_detector_model-shard1"
]

def download_file(url, dest_path):
    print(f"Downloading {url}...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        print(f"Saved to {dest_path}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

if __name__ == "__main__":
    # Download models
    for file in files_to_download:
        url = f"{BASE_URL}/{file}"
        dest = os.path.join(MODELS_DIR, file)
        download_file(url, dest)

    # Download face-api.js
    download_file(CDN_URL, os.path.join(JS_DIR, "face-api.min.js"))
