# api/text_endpoints.py
"""
Text Analysis Endpoints for SPECTRA-AI API
Adds fake news detection capability
"""

from fastapi import HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
import time
import uuid
import logging

logger = logging.getLogger("spectra.api.text")


# ========== Request/Response Models ==========

class TextAnalysisRequest(BaseModel):
    """Request model for text analysis"""
    text: str = Field(..., min_length=50, max_length=10000, description="Text to analyze")
    url: Optional[str] = Field(None, description="Source URL (optional)")
    enable_evidence_search: bool = Field(False, description="Search for evidence (slow)")
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Breaking news: Scientists discover shocking truth...",
                "url": "https://example.com/article",
                "enable_evidence_search": False
            }
        }


class TextAnalysisResponse(BaseModel):
    """Response model for text analysis"""
    request_id: str
    processing_time_ms: int
    status: str
    verdict: str
    confidence: float
    spectra_score: int
    signals: dict
    explanation: str
    
    class Config:
        schema_extra = {
            "example": {
                "request_id": "abc123",
                "processing_time_ms": 1234,
                "status": "success",
                "verdict": "LIKELY_FAKE",
                "confidence": 0.85,
                "spectra_score": 78,
                "signals": {},
                "explanation": "Text shows indicators of misinformation..."
            }
        }


# ========== Endpoint Implementation ==========

def add_text_endpoints(app, pipeline, verify_api_key):
    """
    Add text analysis endpoints to FastAPI app
    
    Args:
        app: FastAPI application instance
        pipeline: FakeNewsPipeline instance
        verify_api_key: Authentication dependency
    """
    
    @app.post("/analyze-text", response_model=TextAnalysisResponse)
    async def analyze_text(
        request: TextAnalysisRequest,
        authorized: bool = Depends(verify_api_key)
    ):
        """
        Analyze text for fake news indicators
        
        **Input:**
        - text: Article text or claim (50-10,000 characters)
        - url: Optional source URL for credibility check
        - enable_evidence_search: Whether to search web for evidence (slow)
        
        **Output:**
        - verdict: LIKELY_FAKE, LIKELY_REAL, or UNCERTAIN
        - confidence: Confidence score (0-1)
        - spectra_score: 0-100 scale (higher = more likely fake)
        - signals: Detailed breakdown of analysis
        - explanation: Human-readable explanation
        
        **Status Codes:**
        - 200: Success
        - 400: Invalid input (text too short/long)
        - 401: Missing API key
        - 403: Invalid API key
        - 500: Internal error
        """
        request_id = uuid.uuid4().hex
        start_time = time.time()
        
        logger.info(f"[{request_id}] Text analysis request ({len(request.text)} chars)")
        
        try:
            # Validate text length
            if len(request.text) < 50:
                raise HTTPException(
                    status_code=400,
                    detail="Text too short (minimum 50 characters)"
                )
            
            if len(request.text) > 10000:
                raise HTTPException(
                    status_code=400,
                    detail="Text too long (maximum 10,000 characters)"
                )
            
            # Run analysis
            result = pipeline.analyze(
                text=request.text,
                url=request.url,
                enable_evidence_search=request.enable_evidence_search
            )
            
            # Check for errors
            if result.get("status") != "success":
                logger.error(f"[{request_id}] Analysis failed: {result.get('message')}")
                raise HTTPException(
                    status_code=500,
                    detail=result.get("message", "Analysis failed")
                )
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Build response
            response = TextAnalysisResponse(
                request_id=request_id,
                processing_time_ms=processing_time,
                status="success",
                verdict=result["verdict"],
                confidence=result["confidence"],
                spectra_score=result["spectra_score"],
                signals=result["signals"],
                explanation=result["explanation"]
            )
            
            logger.info(
                f"[{request_id}] ✅ Complete | "
                f"Verdict={result['verdict']} | "
                f"Score={result['spectra_score']} | "
                f"Time={processing_time}ms"
            )
            
            return response
        
        except HTTPException:
            raise
        
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"[{request_id}] ❌ Error: {e}", exc_info=True)
            
            raise HTTPException(
                status_code=500,
                detail=f"Internal error: {str(e)}"
            )
    
    @app.get("/text-health")
    async def text_health():
        """Health check for text analysis module"""
        return {
            "status": "healthy",
            "module": "fake_news_detection",
            "pipeline_loaded": pipeline is not None
        }
    
    logger.info("✅ Text analysis endpoints added")


# ========== Integration Example ==========

def example_integration():
    """
    Example of how to integrate text endpoints into existing API
    """
    
    code = '''
# In your api/main1.py or api/main_improved.py

from api.text_endpoints import add_text_endpoints

# After initializing deepfake pipeline, also initialize fake news pipeline
from ai_models.fake_news_detection import FakeNewsPipeline

fake_news_pipeline = None

@app.on_event("startup")
async def startup_event():
    global pipeline, fake_news_pipeline
    
    # ... existing deepfake pipeline initialization ...
    
    # Initialize fake news pipeline
    logger.info("Initializing fake news detection pipeline...")
    try:
        fake_news_pipeline = FakeNewsPipeline(device="cpu")
        logger.info("✅ Fake news pipeline initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize fake news pipeline: {e}")
    
    # Add text endpoints
    if fake_news_pipeline:
        add_text_endpoints(app, fake_news_pipeline, verify_api_key)
'''
    
    print(code)


if __name__ == "__main__":
    print("=" * 70)
    print("Text Analysis Endpoints - Integration Guide")
    print("=" * 70)
    
    example_integration()
    
    print("\n" + "=" * 70)
    print("✅ Module ready for integration")
    print("=" * 70)
