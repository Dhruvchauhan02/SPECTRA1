# api/celebrity_endpoints.py
"""
Celebrity Verification API Endpoints for SPECTRA-AI
Real-time celebrity fake news monitoring and verification
"""

from fastapi import HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import logging  

logger = logging.getLogger("spectra.api.celebrity")


# ========== Request / Response Models ==========

class VerifyClaimRequest(BaseModel):
    """Request model for claim verification"""
    # FIX: min_length was 10, which blocks short but valid claims like
    # "won award" (9 chars) typed via quick-example buttons.
    # Lowered to 3 to match practical minimum meaningful input.
    claim: str = Field(..., min_length=3, max_length=500, description="Claim to verify")
    celebrity: str = Field(..., min_length=2, max_length=100, description="Celebrity name")
    source_url: Optional[str] = Field(None, description="Source URL (optional)")

    class Config:
        schema_extra = {
            "example": {
                "claim": "Elon Musk announced new Tesla factory in India",
                "celebrity": "Elon Musk",
                "source_url": "https://twitter.com/someuser/status/123"
            }
        }


class MonitorCelebrityRequest(BaseModel):
    """Request model for celebrity monitoring"""
    celebrity: str = Field(..., description="Celebrity name to monitor")
    viral_threshold: int = Field(1000, ge=100, le=100000, description="Viral engagement threshold")

    class Config:
        schema_extra = {
            "example": {
                "celebrity": "Taylor Swift",
                "viral_threshold": 5000
            }
        }


class BatchMonitorRequest(BaseModel):
    """Request model for batch monitoring"""
    celebrities: List[str] = Field(..., min_items=1, max_items=10, description="List of celebrities")
    viral_threshold: int = Field(1000, ge=100, le=100000)

    class Config:
        schema_extra = {
            "example": {
                "celebrities": ["Elon Musk", "Taylor Swift", "Kim Kardashian"],
                "viral_threshold": 2000
            }
        }


# ========== Endpoint Implementation ==========

def add_celebrity_endpoints(app, celebrity_system, verify_api_key):
    """
    Add celebrity verification endpoints to FastAPI app.

    Args:
        app: FastAPI application instance
        celebrity_system: CelebrityVerificationSystem instance
        verify_api_key: Authentication dependency
    """

    @app.post("/verify-celebrity-claim")
    async def verify_celebrity_claim(
        request: VerifyClaimRequest,
        authorized: bool = Depends(verify_api_key)
    ):
        """
        Verify a claim about a celebrity.

        Returns:
        - verification.verdict:    VERIFIED | DISPUTED | FAKE | UNVERIFIED | PARTIALLY_VERIFIED
        - verification.confidence: float 0-1
        - explanation:             human-readable reason
        - recommendation:          action advice
        - sources:                 list of news articles used as evidence
        """
        logger.info(f"Verify claim request: celebrity={request.celebrity!r}")

        try:
            result = celebrity_system.verify_celebrity_claim(
                claim=request.claim,
                celebrity_name=request.celebrity,
                source_url=request.source_url,
            )

            verdict    = result.get("verification", {}).get("verdict", "UNVERIFIED")
            confidence = result.get("confidence", 0.0)

            logger.info(f"Verification complete: {verdict} ({confidence:.0%})")

            # FIX: Save verified claims to Supabase (was silently skipped before)
            try:
                from database import supabase_db
                from crud import save_celebrity_verification

                if supabase_db.is_connected:
                    await save_celebrity_verification(
                        collection=None,
                        celebrity=request.celebrity,
                        claim=request.claim,
                        verification={
                            "verdict":    verdict,
                            "confidence": confidence,
                            "explanation": result.get("explanation", ""),
                        },
                        sources=result.get("sources", []),
                        metadata={
                            "source_url":   request.source_url,
                            "request_id":   result.get("request_id", ""),
                        },
                    )
                    logger.debug(f"Saved celebrity verification for {request.celebrity}")
            except Exception as db_err:
                # Don't fail the request if DB save fails
                logger.warning(f"DB save failed (non-critical): {db_err}")

            return result

        except Exception as e:
            logger.error(f"Verification failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Verification failed: {str(e)}"
            )

    @app.post("/monitor-celebrity")
    async def monitor_celebrity(
        request: MonitorCelebrityRequest,
        authorized: bool = Depends(verify_api_key)
    ):
        """Monitor a celebrity for viral fake news."""
        logger.info(f"Monitor request: {request.celebrity}")

        try:
            result = celebrity_system.monitor_celebrity(
                celebrity_name=request.celebrity,
                viral_threshold=request.viral_threshold,
            )
            logger.info(
                f"Monitoring complete: {result['status']} "
                f"({len(result.get('alerts', []))} alerts)"
            )
            return result

        except Exception as e:
            logger.error(f"Monitoring failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Monitoring failed: {str(e)}"
            )

    @app.post("/monitor-celebrities-batch")
    async def monitor_celebrities_batch(
        request: BatchMonitorRequest,
        authorized: bool = Depends(verify_api_key)
    ):
        """Monitor multiple celebrities at once."""
        logger.info(f"Batch monitor: {len(request.celebrities)} celebrities")

        try:
            result = celebrity_system.batch_verify_celebrities(
                celebrities=request.celebrities,
                viral_threshold=request.viral_threshold,
            )
            logger.info(f"Batch complete: {result['total_alerts']} total alerts")
            return result

        except Exception as e:
            logger.error(f"Batch monitoring failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Batch monitoring failed: {str(e)}"
            )

    @app.get("/celebrity-health")
    async def celebrity_health():
        """Health check for celebrity verification module."""
        has_twitter = celebrity_system.social_monitor.twitter_token is not None
        has_news = (
            celebrity_system.news_aggregator.newsapi_key is not None
            or celebrity_system.news_aggregator.gnews_key is not None
        )

        return {
            "status": "healthy" if (has_twitter or has_news) else "degraded",
            "module": "celebrity_verification",
            "components": {
                "twitter_api": "connected" if has_twitter else "not configured",
                "news_api":    "connected" if has_news    else "not configured",
            },
            "message": (
                "Fully operational" if (has_twitter and has_news)
                else "Operating with available APIs"
            ),
        }

    logger.info("✅ Celebrity verification endpoints added")
