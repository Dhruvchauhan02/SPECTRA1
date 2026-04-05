import os
import gdown

MODEL_PATH = "ai_models/Resnet50_Final.pth"

def download_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading model...")
        os.makedirs("ai_models", exist_ok=True)
        
        url = "https://drive.google.com/uc?id=154TONYxKdPMx6-dxQ_hQdowN0wSQw1Dt"
        gdown.download(url, MODEL_PATH, quiet=False)
        
        print("Download complete!")
    else:
        print("Model already exists.")