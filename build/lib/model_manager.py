import os
import sys
import zipfile
import urllib.request
import shutil
from pathlib import Path
from tqdm import tqdm

class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

def download_url(url, output_path):
    with DownloadProgressBar(unit='B', unit_scale=True,
                             miniters=1, desc=url.split('/')[-1]) as t:
        urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)

def setup_vosk_model(model_path_str):
    """
    Checks if the Vosk model exists. If not, downloads and extracts it.
    Returns the path to the model.
    """
    model_path = Path(model_path_str)
    
    # If model exists, we're good
    if model_path.exists():
        return True

    print(f"⚠️  Vosk model not found at: {model_path}")
    print("   This is required for offline voice recognition.")
    
    # Define model URL (using the lgraph model we chose)
    MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip"
    ZIP_NAME = "vosk-model-en-us-0.22-lgraph.zip"
    
    # Ask user permission
    print(f"   Do you want to download it now? (~128MB)")
    response = input("   [Y/n]: ").strip().lower()
    
    if response in ['n', 'no']:
        print("❌ Model download cancelled. The assistant cannot run without it.")
        return False

    # Download
    print(f"⬇️  Downloading {ZIP_NAME}...")
    try:
        download_url(MODEL_URL, ZIP_NAME)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

    # Extract
    print("📦 Extracting model...")
    try:
        with zipfile.ZipFile(ZIP_NAME, 'r') as zip_ref:
            zip_ref.extractall(model_path.parent)
        
        # Cleanup zip
        os.remove(ZIP_NAME)
        print("✅ Model setup complete!")
        return True
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False

if __name__ == "__main__":
    # Test run
    setup_vosk_model("vosk-model-en-us-0.22-lgraph")
