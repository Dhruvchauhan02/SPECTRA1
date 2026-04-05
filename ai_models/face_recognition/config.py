# config.py
"""
Centralized Configuration Management for SPECTRA-AI
All tunable parameters in one place
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    SPECTRA-AI Configuration
    
    All settings can be overridden via environment variables
    Example: export FACE_CONFIDENCE_THRESHOLD=0.6
    """
    
    # ========== API Configuration ==========
    API_TITLE: str = Field(
        default="SPECTRA-AI API",
        description="API title"
    )
    
    API_VERSION: str = Field(
        default="1.0.0",
        description="API version"
    )
    
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    # ========== Image Validation ==========
    MIN_IMAGE_SIZE: int = Field(
        default=80,
        description="Minimum image dimension in pixels",
        ge=1
    )
    
    MAX_IMAGE_DIM: int = Field(
        default=1920,
        description="Maximum image dimension (will auto-resize)",
        ge=100
    )
    
    REQUIRED_CHANNELS: int = Field(
        default=3,
        description="Required number of image channels (RGB=3)"
    )
    
    # ========== Face Detection ==========
    FACE_CONFIDENCE_THRESHOLD: float = Field(
        default=0.55,
        description="Minimum confidence for face detection",
        ge=0.0,
        le=1.0
    )
    
    FACE_DETECTION_SIZE: tuple = Field(
        default=(640, 640),
        description="Detection resolution (width, height)"
    )
    
    MIN_FACE_SIZE: int = Field(
        default=96,
        description="Minimum face size for fallback mode",
        ge=1
    )
    
    # Fallback mode heuristics
    FALLBACK_ENABLED: bool = Field(
        default=False,
        description="Enable fallback mode for cropped faces (NOT RECOMMENDED)"
    )
    
    FALLBACK_ASPECT_RATIO_MIN: float = Field(
        default=0.6,
        description="Min aspect ratio for fallback face detection"
    )
    
    FALLBACK_ASPECT_RATIO_MAX: float = Field(
        default=1.6,
        description="Max aspect ratio for fallback face detection"
    )
    
    FALLBACK_VARIANCE_THRESHOLD: float = Field(
        default=120.0,
        description="Minimum image variance for fallback"
    )
    
    # ========== Deepfake Detection ==========
    DEVICE: str = Field(
        default="cpu",
        description="Computation device (cpu or cuda)"
    )
    
    EFFICIENTNET_MODEL_PATH: str = Field(
        default="efficientnet_b0_spectra.pth",
        description="Path to EfficientNet weights"
    )
    
    CLIP_MODEL_NAME: str = Field(
        default="openai/clip-vit-base-patch32",
        description="HuggingFace CLIP model name"
    )
    
    # ========== Score Fusion ==========
    # Detector weights (must sum to 1.0)
    WEIGHT_VISUAL: float = Field(
        default=0.50,
        description="Weight for EfficientNet detector",
        ge=0.0,
        le=1.0
    )
    
    WEIGHT_CLIP: float = Field(
        default=0.35,
        description="Weight for CLIP detector",
        ge=0.0,
        le=1.0
    )
    
    WEIGHT_FREQUENCY: float = Field(
        default=0.15,
        description="Weight for frequency detector",
        ge=0.0,
        le=1.0
    )
    
    # Verdict thresholds
    FAKE_THRESHOLD_HIGH: float = Field(
        default=0.70,
        description="Probability threshold for high-confidence FAKE",
        ge=0.0,
        le=1.0
    )
    
    FAKE_THRESHOLD_LOW: float = Field(
        default=0.30,
        description="Probability threshold for high-confidence REAL",
        ge=0.0,
        le=1.0
    )
    
    # Calibration (temperature scaling)
    USE_CALIBRATION: bool = Field(
        default=False,
        description="Enable probability calibration"
    )
    
    TEMP_VISUAL: float = Field(
        default=1.0,
        description="Temperature for EfficientNet calibration",
        gt=0.0
    )
    
    TEMP_CLIP: float = Field(
        default=1.0,
        description="Temperature for CLIP calibration",
        gt=0.0
    )
    
    TEMP_FREQUENCY: float = Field(
        default=1.0,
        description="Temperature for frequency calibration",
        gt=0.0
    )
    
    # ========== Fake News Detection (Future) ==========
    FAKENEWS_ENABLED: bool = Field(
        default=False,
        description="Enable fake news detection module"
    )
    
    TEXT_ENCODER_MODEL: str = Field(
        default="microsoft/deberta-v3-large",
        description="Model for text encoding"
    )
    
    MAX_TEXT_LENGTH: int = Field(
        default=10000,
        description="Maximum text length in characters",
        ge=1
    )
    
    MIN_TEXT_LENGTH: int = Field(
        default=50,
        description="Minimum text length in characters",
        ge=1
    )
    
    SEARCH_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for web search (Bing, Google, etc.)"
    )
    
    MAX_EVIDENCE_SOURCES: int = Field(
        default=5,
        description="Maximum number of evidence sources to retrieve",
        ge=1
    )
    
    # ========== Performance ==========
    ENABLE_WARMUP: bool = Field(
        default=True,
        description="Warm up models on startup"
    )
    
    CACHE_ENABLED: bool = Field(
        default=False,
        description="Enable result caching"
    )
    
    CACHE_TTL_SECONDS: int = Field(
        default=3600,
        description="Cache time-to-live in seconds",
        ge=0
    )
    
    # ========== Security ==========
    ENABLE_AUTH: bool = Field(
        default=False,
        description="Enable API key authentication"
    )
    
    API_KEY: Optional[str] = Field(
        default=None,
        description="API key for authentication"
    )
    
    RATE_LIMIT_ENABLED: bool = Field(
        default=False,
        description="Enable rate limiting"
    )
    
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="Maximum requests per minute per IP",
        ge=1
    )
    
    # ========== Database (Future) ==========
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Database connection URL"
    )
    
    SAVE_REQUESTS: bool = Field(
        default=False,
        description="Save all requests to database"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def validate_weights(self):
        """Ensure fusion weights sum to 1.0"""
        total = self.WEIGHT_VISUAL + self.WEIGHT_CLIP + self.WEIGHT_FREQUENCY
        if not (0.99 <= total <= 1.01):  # Allow small floating point error
            raise ValueError(
                f"Fusion weights must sum to 1.0, got {total}. "
                f"Current: visual={self.WEIGHT_VISUAL}, "
                f"clip={self.WEIGHT_CLIP}, freq={self.WEIGHT_FREQUENCY}"
            )
    
    def validate_thresholds(self):
        """Ensure thresholds are logically consistent"""
        if self.FAKE_THRESHOLD_LOW >= self.FAKE_THRESHOLD_HIGH:
            raise ValueError(
                f"FAKE_THRESHOLD_LOW ({self.FAKE_THRESHOLD_LOW}) must be "
                f"less than FAKE_THRESHOLD_HIGH ({self.FAKE_THRESHOLD_HIGH})"
            )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate_weights()
        self.validate_thresholds()


# Global settings instance
settings = Settings()


# ========== Example .env file content ==========
"""
# SPECTRA-AI Configuration
# Copy this to .env and customize

# API Configuration
API_TITLE=SPECTRA-AI Production
API_VERSION=1.0.0
LOG_LEVEL=INFO

# Image Validation
MIN_IMAGE_SIZE=80
MAX_IMAGE_DIM=1920

# Face Detection
FACE_CONFIDENCE_THRESHOLD=0.55
FALLBACK_ENABLED=false

# Deepfake Detection
DEVICE=cuda  # or cpu
EFFICIENTNET_MODEL_PATH=efficientnet_b0_spectra.pth

# Score Fusion
WEIGHT_VISUAL=0.50
WEIGHT_CLIP=0.35
WEIGHT_FREQUENCY=0.15
FAKE_THRESHOLD_HIGH=0.70
FAKE_THRESHOLD_LOW=0.30

# Calibration
USE_CALIBRATION=true
TEMP_VISUAL=1.2
TEMP_CLIP=0.8
TEMP_FREQUENCY=1.0

# Security
ENABLE_AUTH=true
API_KEY=your-secret-api-key-here
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100

# Performance
ENABLE_WARMUP=true
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600

# Fake News (when implemented)
FAKENEWS_ENABLED=false
SEARCH_API_KEY=your-bing-api-key-here
"""


# ========== Usage Examples ==========
if __name__ == "__main__":
    print("=" * 60)
    print("SPECTRA-AI Configuration")
    print("=" * 60)
    
    # Load settings
    config = Settings()
    
    print("\n📋 Current Configuration:")
    print(f"  API Title: {config.API_TITLE}")
    print(f"  Device: {config.DEVICE}")
    print(f"  Face Confidence Threshold: {config.FACE_CONFIDENCE_THRESHOLD}")
    print(f"  Fallback Enabled: {config.FALLBACK_ENABLED}")
    
    print("\n🔧 Fusion Weights:")
    print(f"  Visual: {config.WEIGHT_VISUAL}")
    print(f"  CLIP: {config.WEIGHT_CLIP}")
    print(f"  Frequency: {config.WEIGHT_FREQUENCY}")
    print(f"  Total: {config.WEIGHT_VISUAL + config.WEIGHT_CLIP + config.WEIGHT_FREQUENCY}")
    
    print("\n📊 Thresholds:")
    print(f"  High (FAKE): {config.FAKE_THRESHOLD_HIGH}")
    print(f"  Low (REAL): {config.FAKE_THRESHOLD_LOW}")
    print(f"  Uncertainty Zone: {config.FAKE_THRESHOLD_LOW:.2f} - {config.FAKE_THRESHOLD_HIGH:.2f}")
    
    print("\n🔐 Security:")
    print(f"  Authentication: {config.ENABLE_AUTH}")
    print(f"  Rate Limiting: {config.RATE_LIMIT_ENABLED}")
    if config.RATE_LIMIT_ENABLED:
        print(f"  Rate Limit: {config.RATE_LIMIT_PER_MINUTE} req/min")
    
    print("\n" + "=" * 60)
    print("✅ Configuration loaded successfully")
    print("=" * 60)
    
    print("\n💡 Tips:")
    print("  - Create a .env file to customize settings")
    print("  - Environment variables override defaults")
    print("  - All settings are validated on load")
    print("  - Use config.validate_weights() to check fusion weights")
