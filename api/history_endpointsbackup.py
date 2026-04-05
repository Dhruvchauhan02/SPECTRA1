# api/history_endpoints.py
"""
History and Statistics Endpoints for SPECTRA-AI

Endpoints to query MongoDB for analysis history, statistics, and trends.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("spectra.api.history")

# Create router
router = APIRouter(prefix="/history", tags=["History & Statistics"])


def add_history_endpoints(app, mongodb, verify_api_key):
    """
    Add history endpoints to FastAPI app
    
    Args:
        app: FastAPI app instance
        mongodb: MongoDB instance
        verify_api_key: API key verification dependency
    """
    
    @app.get("/history/recent")
    async def get_recent_history(
        limit: int = Query(10, ge=1, le=100),
        type: Optional[str] = Query(None, description="Filter by type: deepfake_image, fake_news_text, celebrity_verification")
    ):
        """
        Get recent analyses
        
        Args:
            limit: Maximum number of results (1-100)
            type: Optional filter by analysis type
        
        Returns:
            List of recent analyses
        """
        try:
            from crud import get_recent_analyses
            
            collection = mongodb.get_collection("analysis_history")
            results = await get_recent_analyses(collection, limit=limit, analysis_type=type)
            
            return {
                "status": "success",
                "count": len(results),
                "analyses": results
            }
        except Exception as e:
            logger.error(f"Failed to get recent history: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.get("/history/stats")
    async def get_statistics():
        """
        Get overall analysis statistics
        
        Returns:
            Statistics about all analyses
        """
        try:
            from crud import get_statistics
            
            collection = mongodb.get_collection("analysis_history")
            stats = await get_statistics(collection)
            
            # Get database stats
            db_stats = await mongodb.get_stats()
            
            return {
                "status": "success",
                "analysis_stats": stats,
                "database_stats": db_stats
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.get("/history/by-id/{request_id}")
    async def get_by_request_id(request_id: str):
        """
        Get analysis by request ID
        
        Args:
            request_id: Request ID from original analysis
        
        Returns:
            Analysis document
        """
        try:
            from crud import get_analysis_by_id
            
            collection = mongodb.get_collection("analysis_history")
            result = await get_analysis_by_id(collection, request_id)
            
            if not result:
                raise HTTPException(status_code=404, detail="Analysis not found")
            
            return {
                "status": "success",
                "analysis": result
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get analysis: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.get("/history/celebrity/{celebrity_name}")
    async def search_celebrity(
        celebrity_name: str,
        limit: int = Query(20, ge=1, le=100)
    ):
        """
        Search verifications by celebrity name
        
        Args:
            celebrity_name: Celebrity name (case-insensitive search)
            limit: Maximum results (1-100)
        
        Returns:
            List of verifications for this celebrity
        """
        try:
            from crud import search_by_celebrity
            
            collection = mongodb.get_collection("analysis_history")
            results = await search_by_celebrity(collection, celebrity_name, limit)
            
            return {
                "status": "success",
                "celebrity": celebrity_name,
                "count": len(results),
                "verifications": results
            }
        except Exception as e:
            logger.error(f"Failed to search celebrity: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.get("/history/trending")
    async def get_trending(
        hours: int = Query(24, ge=1, le=168),
        min_count: int = Query(2, ge=2, le=10)
    ):
        """
        Get trending celebrity claims
        
        Args:
            hours: Time window in hours (1-168)
            min_count: Minimum occurrences to be trending (2-10)
        
        Returns:
            List of trending claims
        """
        try:
            from crud import get_trending_claims
            
            collection = mongodb.get_collection("analysis_history")
            trends = await get_trending_claims(collection, hours, min_count)
            
            return {
                "status": "success",
                "time_window_hours": hours,
                "trending_count": len(trends),
                "trending_claims": trends
            }
        except Exception as e:
            logger.error(f"Failed to get trending: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.get("/history/verdicts")
    async def get_verdict_breakdown():
        """
        Get breakdown of verdicts
        
        Returns:
            Verdict counts and percentages
        """
        try:
            collection = mongodb.get_collection("analysis_history")
            
            # Count by verdict type
            total_deepfake = await collection.count_documents({"type": "deepfake_image"})
            real = await collection.count_documents({
                "type": "deepfake_image",
                "result.verdict": "REAL"
            })
            fake = await collection.count_documents({
                "type": "deepfake_image",
                "result.verdict": "FAKE"
            })
            uncertain = await collection.count_documents({
                "type": "deepfake_image",
                "result.verdict": "UNCERTAIN"
            })
            
            # Calculate percentages
            real_pct = (real / total_deepfake * 100) if total_deepfake > 0 else 0
            fake_pct = (fake / total_deepfake * 100) if total_deepfake > 0 else 0
            uncertain_pct = (uncertain / total_deepfake * 100) if total_deepfake > 0 else 0
            
            return {
                "status": "success",
                "total_deepfake_analyses": total_deepfake,
                "verdicts": {
                    "REAL": {
                        "count": real,
                        "percentage": round(real_pct, 2)
                    },
                    "FAKE": {
                        "count": fake,
                        "percentage": round(fake_pct, 2)
                    },
                    "UNCERTAIN": {
                        "count": uncertain,
                        "percentage": round(uncertain_pct, 2)
                    }
                }
            }
        except Exception as e:
            logger.error(f"Failed to get verdict breakdown: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.get("/history/daily-stats")
    async def get_daily_stats(days: int = Query(7, ge=1, le=30)):
        """
        Get daily analysis statistics
        
        Args:
            days: Number of days to include (1-30)
        
        Returns:
            Daily breakdown of analyses
        """
        try:
            collection = mongodb.get_collection("analysis_history")
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Aggregation pipeline
            pipeline = [
                {"$match": {"timestamp": {"$gte": start_date}}},
                {"$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$timestamp"
                        }
                    },
                    "count": {"$sum": 1},
                    "types": {"$push": "$type"}
                }},
                {"$sort": {"_id": 1}}
            ]
            
            results = await collection.aggregate(pipeline).to_list(length=days)
            
            return {
                "status": "success",
                "days": days,
                "daily_stats": results
            }
        except Exception as e:
            logger.error(f"Failed to get daily stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    logger.info("✅ History endpoints added")
