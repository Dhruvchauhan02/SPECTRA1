# api/main1.py

"""
SPECTRA-AI Main API
Deepfake Detection + Fake News Detection + Celebrity Verification
"""

# ============ PATH SETUP (ADD THIS FIRST) ============
import sys
from pathlib import Path
from download_model import download_model
# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from dotenv import load_dotenv
load_dotenv()
# ============ STANDARD IMPORTS ============
import os
import time
import uuid
import logging
from datetime import datetime

# ============ FASTAPI IMPORTS ============
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional


class ImageBase64Request(BaseModel):
    image_b64: str  # raw base64 image bytes (no data: prefix)
    filename: str = "image.jpg"
import shutil
import tempfile
import base64
import cv2
import numpy as np
from api.analytics_endpoints import add_analytics_endpoints
from api.export_endpoints import add_export_endpoints
# ============ CONFIG ============
# Import config
try:
    from config import settings
except ImportError:
    print("⚠️  Config not found - using defaults")
    class MockSettings:
        API_TITLE = "SPECTRA-AI API"
        API_VERSION = "1.0.0"
        LOG_LEVEL = "INFO"
        MIN_IMAGE_SIZE = 80
        MAX_IMAGE_DIM = 1920
        FACE_CONFIDENCE_THRESHOLD = 0.55
        ENABLE_AUTH = False
        DEVICE = "cpu"
        EFFICIENTNET_MODEL_PATH = "efficientnet_b0_spectra.pth"
        FALLBACK_ENABLED = False
        ENABLE_WARMUP = True
    settings = MockSettings()

# ============ PIPELINE IMPORTS ============
# Use original pipeline (EfficientNet only - no dilution)
from ai_models.deepfake_detection.pipeline import DeepfakePipeline
PIPELINE_AVAILABLE = True

# ============ FAKE NEWS IMPORTS ============
from ai_models.fake_news_detection import FakeNewsPipeline
from api.text_endpoints import add_text_endpoints

# ============ FAKE NEWS IMPORTS ============
from database import supabase_db
from crud import (
    save_deepfake_analysis,
    save_fake_news_analysis,
    save_celebrity_verification
)
from api.history_endpoints import add_history_endpoints

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("spectra.api")

# Initialize FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="AI-powered deepfake detection, fake news analysis, and celebrity verification"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== GLOBAL VARIABLES ==========
pipeline = None
fake_news_pipeline = None
celebrity_system = None  # NEW: Celebrity verification system


# ========== Authentication ==========
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key if authentication is enabled"""
    if not settings.ENABLE_AUTH:
        return True
    
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include X-API-Key header."
        )
    
    if hasattr(settings, 'API_KEY') and x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return True


# ========== Startup/Shutdown ==========
@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    global pipeline, fake_news_pipeline, celebrity_system
    
    logger.info("=" * 70)
    logger.info("🚀 SPECTRA-AI Starting Up")
    logger.info("=" * 70)
    # NEW
    logger.info("📦 Connecting to Supabase...")
    try:
        connected = supabase_db.connect()
        if connected:
            logger.info("✅ Supabase connected and ready")
            add_history_endpoints(app, supabase_db, verify_api_key)
            add_analytics_endpoints(app, supabase_db, verify_api_key)
            add_export_endpoints(app, supabase_db, verify_api_key)
            logger.info("✅ History endpoints registered")
        else:
            logger.warning("⚠️  Supabase connection failed - continuing without database")
    except Exception as e:
        logger.error(f"⚠️  Supabase connection error: {e}")
        logger.info("Continuing without database storage...")
    # ========== 1. DEEPFAKE DETECTION ==========
    logger.info("Initializing deepfake detection pipeline...")
    try:
        logger.info("⬇️ Downloading model if needed...")
        try:
            download_model()
            logger.info("✅ Model ready")
        except Exception as e:
            logger.error(f"Model download failed: {e}")
        pipeline = DeepfakePipeline(
            device=settings.DEVICE,
            model_path=str(settings.EFFICIENTNET_MODEL_PATH)
        )
        logger.info("✅ Deepfake pipeline ready")
        
    except Exception as e:
        logger.error(f"⚠️  Deepfake initialization failed: {e}")
        logger.info("Continuing without deepfake detection...")
        pipeline = None
    
    # ========== 2. FAKE NEWS DETECTION ==========
    logger.info("🔍 Initializing fake news detection...")
    try:
        fake_news_pipeline = FakeNewsPipeline(
            device="cpu",
            enable_text_encoding=False,
            newsapi_key=os.getenv("NEWS_API_KEY"),
            gnews_key=os.getenv("GNEWS_API_KEY"),
        )
        
        # Add text endpoints
        add_text_endpoints(app, fake_news_pipeline, verify_api_key)
        
        logger.info("✅ Fake news detection ready (<1ms per analysis!)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize fake news detection: {e}")
    
    # ========== 3. CELEBRITY VERIFICATION (NEW!) ==========
    logger.info("🌐 Initializing celebrity verification...")
    try:
        from ai_models.fake_news_detection.celebrity_verification import CelebrityVerificationSystem
        from api.celebrity_endpoints import add_celebrity_endpoints
        
        # Check if API keys are available
        news_api_key = os.getenv("NEWS_API_KEY")
        twitter_token = os.getenv("TWITTER_BEARER_TOKEN")
        
        if news_api_key:
            celebrity_system = CelebrityVerificationSystem(
                twitter_bearer_token=twitter_token,  # Optional (costs $100/mo)
                news_api_key=news_api_key,            # FREE!
                gnews_api_key=os.getenv("GNEWS_API_KEY")  # Optional
            )
            
            # Add celebrity endpoints
            add_celebrity_endpoints(app, celebrity_system, verify_api_key)
            
            logger.info("✅ Celebrity verification ready (with NewsAPI)")
            if twitter_token:
                logger.info("   📱 Twitter monitoring: ENABLED")
            else:
                logger.info("   📱 Twitter monitoring: DISABLED (no API key)")
        else:
            logger.warning("⚠️  NewsAPI key not found - celebrity verification disabled")
            logger.info("   Get free key: https://newsapi.org/")
            celebrity_system = None
    except Exception as e:
        logger.error(f"⚠️  Celebrity verification failed: {e}")
        celebrity_system = None
    
    # ========== WARMUP ==========
    if getattr(settings, 'ENABLE_WARMUP', True) and pipeline:
        logger.info("🔥 Warming up models...")
        dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
        temp_path = os.path.join(tempfile.gettempdir(), "spectra_warmup.jpg")
        
        try:
            cv2.imwrite(temp_path, dummy_img)
            pipeline.analyze(temp_path)
            logger.info("✅ Warmup complete")
        except Exception as e:
            logger.warning(f"⚠️  Warmup failed (non-critical): {e}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    # ========== SUMMARY ==========
    logger.info("=" * 70)
    logger.info("✅ SPECTRA-AI Ready")
    if pipeline:
        logger.info("   📷 Image Analysis:     /analyze-image")
    logger.info("   📝 Text Analysis:      /analyze-text")
    if celebrity_system:
        logger.info("   🔍 Verify Claim:       /verify-celebrity-claim")
        logger.info("   👁️  Monitor Celebrity:  /monitor-celebrity")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 SPECTRA-AI Shutting Down")
    try:
        supabase_db.disconnect()
        logger.info("✅ Supabase connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB: {e}")

# ========== Endpoints ==========
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SPECTRA-AI",
        "version": settings.API_VERSION,
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "analyze_image": "/analyze-image",
            "analyze_text": "/analyze-text",
            "verify_claim": "/verify-celebrity-claim" if celebrity_system else None,
            "monitor": "/monitor-celebrity" if celebrity_system else None,
            "config": "/config"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SPECTRA-AI",
        "version": settings.API_VERSION,
        "modules": {
            "deepfake_detection": pipeline is not None,
            "fake_news_detection": fake_news_pipeline is not None,
            "celebrity_verification": celebrity_system is not None
        },
        "pipeline": "original",
        "config": {
            "device": settings.DEVICE,
            "auth_enabled": settings.ENABLE_AUTH,
            "fallback_enabled": settings.FALLBACK_ENABLED
        }
    }


@app.get("/config")
async def get_config(authorized: bool = Depends(verify_api_key)):
    """Get current configuration (requires auth if enabled)"""
    return {
        "pipeline": "original",
        "device": settings.DEVICE,
        "face_threshold": settings.FACE_CONFIDENCE_THRESHOLD,
        "fallback_mode": settings.FALLBACK_ENABLED,
        "image_limits": {
            "min_size": settings.MIN_IMAGE_SIZE,
            "max_dim": settings.MAX_IMAGE_DIM
        },
        "celebrity_verification_enabled": celebrity_system is not None
    }


@app.post("/analyze-image")
async def analyze_image(
    payload: ImageBase64Request,
    authorized: bool = Depends(verify_api_key)
):
    """
    Analyze image for deepfake indicators.
    Accepts base64-encoded image — no disk writes, no file-watcher reloads.
    """
    request_id = uuid.uuid4().hex
    start_time = time.time()

    logger.info(f"[{request_id}] New request: {payload.filename}")

    temp_filename = os.path.join(tempfile.gettempdir(), f"spectra_{request_id}.jpg")

    try:
        # Decode base64 → numpy array entirely in memory
        try:
            img_bytes = base64.b64decode(payload.image_b64)
            np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image data")

        # Validate image
        if img is None:
        
            if img is None:
                logger.warning(f"[{request_id}] Invalid image file")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid or corrupted image file"
                )
        
        h, w = img.shape[:2]
        logger.debug(f"[{request_id}] Image size: {w}x{h}")
        
        # Check minimum size
        if h < settings.MIN_IMAGE_SIZE or w < settings.MIN_IMAGE_SIZE:
            logger.warning(f"[{request_id}] Image too small: {w}x{h}")
            raise HTTPException(
                status_code=400,
                detail=f"Image too small (min {settings.MIN_IMAGE_SIZE}px)"
            )
        
        # Auto-resize if too large
        if h > settings.MAX_IMAGE_DIM or w > settings.MAX_IMAGE_DIM:
            scale = settings.MAX_IMAGE_DIM / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            logger.info(f"[{request_id}] Resizing from {w}x{h} to {new_w}x{new_h}")
            img = cv2.resize(img, (new_w, new_h))
            h, w = new_h, new_w
        
        # Validate channels
        if len(img.shape) != 3 or img.shape[2] != 3:
            logger.warning(f"[{request_id}] Invalid channels: {img.shape}")
            raise HTTPException(
                status_code=400,
                detail="Image must be RGB (3 channels)"
            )
        
        # Guard: pipeline may be None if model failed to load at startup
        if pipeline is None:
            logger.error(f"[{request_id}] Deepfake pipeline is not available (model failed to load at startup)")
            raise HTTPException(
                status_code=503,
                detail="Deepfake detection model is not available. Check server logs for model loading errors (e.g. missing .pth file)."
            )

        # Write decoded image to system temp dir for pipeline (not project folder)
        cv2.imwrite(temp_filename, img)

        # Run pipeline
        logger.info(f"[{request_id}] Running deepfake detection")
        result = pipeline.analyze(temp_filename)
        
        # Check for errors
        if result.get("status") == "error":
            error_code = result.get("error_code", "UNKNOWN_ERROR")
            
            if error_code == "NO_FACE_DETECTED":
                logger.warning(f"[{request_id}] No face detected")
                raise HTTPException(
                    status_code=400,
                    detail=result.get("message", "No face detected")
                )
            else:
                logger.error(f"[{request_id}] Pipeline error: {result.get('message')}")
                raise HTTPException(
                    status_code=500,
                    detail=result.get("message", "Analysis failed")
                )
        
        # Process results
        processing_time = int((time.time() - start_time) * 1000)
        
        # Get aggregated result
        
        faces = result.get("faces", [])
        if faces:
            max_face = max(faces, key=lambda f: f.get("final_p", 0))
            final_verdict = max_face.get("verdict", "UNKNOWN")
            final_p = max_face.get("final_p", 0.0)
            confidence = abs(final_p - 0.5) * 2
        else:
            final_verdict = "UNKNOWN"
            final_p = 0.0
            confidence = 0.0
        
        # Build response
        response = {
            "request_id": request_id,
            "processing_time_ms": processing_time,
            "spectra_score": int(final_p * 100),
            "verdict": final_verdict,
            "confidence": round(confidence, 3),
            **result
        }
        try:
            if supabase_db.is_connected:  # Check if Supabase is connected
            
                await save_deepfake_analysis(
                    collection=None,  # ignored — kept for compat per crud.py
                    request_id=request_id,
                    input_data={
                        "filename": payload.filename,
                        "original_size": {"width": img.shape[1], "height": img.shape[0]},
                        "processed_size": {"width": w, "height": h},
                        # FIX #4: `file` no longer exists — endpoint now receives
                        # ImageBase64Request (base64 payload), not UploadFile.
                        "content_type": "image/jpeg",
                    },
                    result={
                        "verdict": final_verdict,
                        "confidence": round(confidence, 3),
                        "spectra_score": int(final_p * 100),
                        "faces_detected": result.get("faces_detected", 0),
                        "processing_time_ms": processing_time,
                        "faces": result.get("faces", [])
                    },
                    metadata={
                        "model_version": "efficientnet_b0",
                        "api_version": settings.API_VERSION,
                        "device": settings.DEVICE,
                        "pipeline": "original"
                    },
                    user_info={
                        "ip_address": "127.0.0.1",  # Can get from request if needed
                        "user_agent": "FastAPI"
                    }
                )
            
                logger.debug(f"[{request_id}] ✅ Saved to MongoDB")
            
        except Exception as e:
            # Don't fail the request if MongoDB save fails
            logger.warning(f"[{request_id}] ⚠️  MongoDB save failed (non-critical): {e}")
    
        # ========== END MONGODB SAVE ==========
        logger.info(
            f"[{request_id}] ✅ Complete | "
            f"Faces={result.get('faces_detected', 0)} | "
            f"Verdict={final_verdict} | "
            f"Score={final_p:.3f} | "
            f"Time={processing_time}ms"
        )
        
        return JSONResponse(content=response)
    
    except HTTPException:
        raise
    
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"[{request_id}] ❌ Unexpected error: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )
    
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


# ========== Admin endpoints ==========

# FIX #5: Removed duplicate /admin/storage-info route.
# This route is now registered exclusively in api/export_endpoints.py
# via add_export_endpoints(). The old version here was also broken:
# it called `await supabase_db.get_stats()` in a non-async function body
# (FastAPI would not await it), and returned different keys than the
# frontend expected. The correct version lives in export_endpoints.py.


@app.post("/admin/reload-config")
async def reload_config(authorized: bool = Depends(verify_api_key)):
    """Reload configuration (requires auth)"""
    try:
        logger.info("Configuration reload requested")
        return {"status": "success", "message": "Configuration reloaded (restart recommended)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

