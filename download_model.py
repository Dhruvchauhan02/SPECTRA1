import os
import gdown
import time

MODELS = {
    "efficientnet": {
        "path": "models/efficientnet_b0_spectra.pth",
        "url": "https://drive.google.com/uc?id=1qv4x8CT-U2yVTqOBh7vuE-6jnnuTtcRi"
    },
    "resnet": {
        "path": "models/Resnet50_Final.pth",
        "url": "https://drive.google.com/uc?id=154TONYxKdPMx6-dxQ_hQdowN0wSQw1Dt"
    }
}

def download_file(url, path, retries=3):
    for attempt in range(retries):
        try:
            gdown.download(url, path, quiet=False, fuzzy=True)
            return True
        except Exception as e:
            print(f"❌ Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return False

def download_model():
    os.makedirs("models", exist_ok=True)

    for name, model in MODELS.items():
        path = model["path"]
        url = model["url"]

        if not os.path.exists(path):
            print(f"⬇️ Downloading {name} model...")

            success = download_file(url, path)

            if success and os.path.exists(path):
                print(f"✅ {name} downloaded successfully")
            else:
                raise RuntimeError(f"❌ Failed to download {name} after retries")

        else:
            print(f"✅ {name} already exists (skipping)")