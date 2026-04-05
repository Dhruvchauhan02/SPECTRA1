# api/analytics_endpoints.py
"""
Analytics Endpoints for SPECTRA-AI — Supabase edition

All mongodb.get_collection() calls removed; analytics.py functions
now pull data directly from Supabase using the global supabase_db client.
"""

from fastapi import HTTPException, Query
from datetime import datetime
import logging

logger = logging.getLogger("spectra.api.analytics")


def add_analytics_endpoints(app, supabase_db, verify_api_key):
    """
    Add analytics endpoints to FastAPI app.

    Args:
        app: FastAPI app instance
        supabase_db: SupabaseDB instance  (kept for API compat; analytics.py uses it internally)
        verify_api_key: API key verification dependency
    """

    @app.get("/analytics/hourly-activity")
    async def get_hourly_activity(
        hours: int = Query(24, ge=1, le=168, description="Hours to analyze (1-168)")
    ):
        """Get analysis activity by hour."""
        try:
            from analytics import get_hourly_activity
            # Pass None — analytics.py fetches data from Supabase directly
            results = await get_hourly_activity(None, hours)
            return {
                "status": "success",
                "time_window_hours": hours,
                "data_points": len(results),
                "hourly_activity": results,
            }
        except Exception as e:
            logger.error(f"Failed to get hourly activity: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/analytics/confidence-distribution")
    async def get_confidence_distribution():
        """Get distribution of confidence scores."""
        try:
            from analytics import get_confidence_distribution
            results = await get_confidence_distribution(None)
            return {"status": "success", **results}
        except Exception as e:
            logger.error(f"Failed to get confidence distribution: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/analytics/performance")
    async def get_performance_stats():
        """Get system performance statistics."""
        try:
            from analytics import get_performance_stats
            stats = await get_performance_stats(None)
            if not stats:
                return {"status": "success", "message": "No data available yet", "stats": {}}
            return {"status": "success", "performance_stats": stats}
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/analytics/anomalies")
    async def detect_anomalies(
        hours: int = Query(24, ge=1, le=168, description="Time window in hours")
    ):
        """Detect anomalies and unusual patterns."""
        try:
            from analytics import detect_anomalies
            results = await detect_anomalies(None, hours)
            return {"status": "success", **results}
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/analytics/top-files")
    async def get_top_filenames(
        limit: int = Query(10, ge=1, le=50, description="Number of results")
    ):
        """Get most frequently analyzed filenames."""
        try:
            from analytics import get_top_filenames
            results = await get_top_filenames(None, limit)
            return {
                "status": "success",
                "top_files_count": len(results),
                "top_files": results,
            }
        except Exception as e:
            logger.error(f"Failed to get top filenames: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/analytics/celebrity-leaderboard")
    async def get_celebrity_leaderboard(
        limit: int = Query(10, ge=1, le=50, description="Number of results")
    ):
        """Get most frequently verified celebrities."""
        try:
            from analytics import get_celebrity_leaderboard
            results = await get_celebrity_leaderboard(None, limit)
            return {
                "status": "success",
                "leaderboard_count": len(results),
                "celebrity_leaderboard": results,
            }
        except Exception as e:
            logger.error(f"Failed to get celebrity leaderboard: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/analytics/time-series")
    async def get_time_series_data(
        days: int = Query(7, ge=1, le=30, description="Number of days")
    ):
        """Get time series data for visualization."""
        try:
            from analytics import get_time_series_data
            results = await get_time_series_data(None, days)
            return {
                "status": "success",
                "days": days,
                "data_points": len(results),
                "time_series": results,
            }
        except Exception as e:
            logger.error(f"Failed to get time series data: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/analytics/summary")
    async def get_analytics_summary():
        """Get comprehensive analytics summary — one-stop endpoint for all key metrics."""
        try:
            from analytics import (
                get_performance_stats,
                detect_anomalies,
                get_confidence_distribution,
            )
            from crud import get_statistics

            basic_stats      = await get_statistics(None)
            performance      = await get_performance_stats(None)
            anomalies        = await detect_anomalies(None, hours=24)
            confidence_dist  = await get_confidence_distribution(None)

            return {
                "status": "success",
                "generated_at": datetime.utcnow().isoformat(),
                "basic_statistics": basic_stats,
                "performance": performance,
                "anomalies": anomalies,
                "confidence_distribution": confidence_dist,
            }
        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    logger.info("✅ Analytics endpoints added")
