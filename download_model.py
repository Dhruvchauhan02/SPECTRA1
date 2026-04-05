import os
import gdown

# ===== MODEL CONFIG =====
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

def download_model():
    os.makedirs("models", exist_ok=True)

    for name, model in MODELS.items():
        path = model["path"]
        url = model["url"]

        if not os.path.exists(path):
            print(f"⬇️ Downloading {name} model...")
            try:
                gdown.download(url, path, quiet=False)
                print(f"✅ {name} downloaded successfully")
            except Exception as e:
                print(f"❌ Failed to download {name}: {e}")
        else:
            print(f"✅ {name} already exists (skipping)")