# config.py

import os
from pathlib import Path

class Settings:
    """SPECTRA-AI Complete Configuration"""
    
    # ========== PROJECT INFO ==========
    PROJECT_ROOT = Path(__file__).parent
    PROJECT_NAME = "SPECTRA-AI"
    API_TITLE = "SPECTRA-AI API"
    API_VERSION = "2.0.0"
    API_DESCRIPTION = "Multimodal Misinformation Detection: Deepfake + Fake News"
    
    # ========== SERVER SETTINGS ==========
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    RELOAD = os.getenv("RELOAD", "false").lower() == "true"
    
    # ========== DEVICE ==========
    DEVICE = os.getenv("DEVICE", "cpu")
    
    # ========== LOGGING ==========
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = PROJECT_ROOT / "logs" / "spectra.log"
    
    # ========== SECURITY ==========
    API_KEY = os.getenv("API_KEY", "spectra-ai-secret-key-change-in-production")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    ENABLE_AUTH = False
    
    # ========== CORS ==========
    ALLOWED_ORIGINS = ["*"]
    ALLOW_CREDENTIALS = True
    ALLOW_METHODS = ["*"]
    ALLOW_HEADERS = ["*"]
    
    # ========== IMAGE PROCESSING ==========
    MIN_IMAGE_SIZE = 80                    # Minimum image dimension (pixels)
    MAX_IMAGE_DIM = 1920                   # Maximum dimension (auto-resize)
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
    MAX_FILE_SIZE = 10 * 1024 * 1024      # 10MB
    
    # ========== DEEPFAKE DETECTION ==========
    FACE_CONFIDENCE_THRESHOLD = 0.55       # Face detection threshold
    CONFIDENCE_THRESHOLD = 0.5             # Deepfake confidence threshold
    ENABLE_FREQUENCY_ANALYSIS = True
    ENABLE_CLIP_ANALYSIS = True
    
    # ========== MODEL PATHS ==========
    MODELS_DIR = PROJECT_ROOT / "models"
    EFFICIENTNET_MODEL_PATH = PROJECT_ROOT / "efficientnet_b0_spectra.pth"
    CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"
    
    # ========== PIPELINE SETTINGS ==========
    ENABLE_WARMUP = True
    FALLBACK_ENABLED = True
    PIPELINE_AVAILABLE = True
    
    # ========== FAKE NEWS DETECTION ==========
    ENABLE_TEXT_ENCODING = False           # Disabled for speed
    FAKE_NEWS_THRESHOLD_FAKE = 0.70
    FAKE_NEWS_THRESHOLD_REAL = 0.30
    
    # ========== CELEBRITY VERIFICATION ==========
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
    
    # ========== FILE STORAGE ==========
    UPLOAD_DIR = PROJECT_ROOT / "uploads"
    
    # ========== DATABASE (optional) ==========
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./spectra.db")
    
    # ========== RATE LIMITING (optional) ==========
    RATE_LIMIT_ENABLED = False
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 60  # seconds

settings = Settings()

# Create directories if they don't exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
if settings.LOG_FILE:
    settings.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)