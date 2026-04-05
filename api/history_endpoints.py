# api/history_endpoints.py
"""
History and Statistics Endpoints for SPECTRA-AI — Supabase edition
"""

from fastapi import HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger("spectra.api.history")


def add_history_endpoints(app, supabase_db, verify_api_key):

    def table(name):
        return supabase_db.client.table(name)

    # ── /history/recent ───────────────────────────────────────
    @app.get("/history/recent")
    async def get_recent_history(
        limit: int = Query(10, ge=1, le=100),
        type: Optional[str] = Query(None)
    ):
        try:
            q = table("analysis_history").select("*").order("timestamp", desc=True).limit(limit)
            if type:
                q = q.eq("type", type)
            res = q.execute()
            results = res.data or []
            return {"status": "success", "count": len(results), "analyses": results}
        except Exception as e:
            logger.error(f"Failed to get recent history: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── /history/stats ────────────────────────────────────────
    @app.get("/history/stats")
    async def get_statistics():
        try:
            from crud import get_statistics
            stats    = await get_statistics(None)
            db_stats = await supabase_db.get_stats()
            return {"status": "success", "analysis_stats": stats, "database_stats": db_stats}
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── /history/by-id/{request_id} ───────────────────────────
    @app.get("/history/by-id/{request_id}")
    async def get_by_request_id(request_id: str):
        try:
            res = table("analysis_history").select("*").eq("request_id", request_id).limit(1).execute()
            if not res.data:
                raise HTTPException(status_code=404, detail="Analysis not found")
            return {"status": "success", "analysis": res.data[0]}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get analysis: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── /history/celebrity/{name} ─────────────────────────────
    @app.get("/history/celebrity/{celebrity_name}")
    async def search_celebrity(
        celebrity_name: str,
        limit: int = Query(20, ge=1, le=100)
    ):
        try:
            res = (
                table("celebrity_verifications")
                .select("*")
                .ilike("celebrity", f"%{celebrity_name}%")
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )
            results = res.data or []
            return {"status": "success", "celebrity": celebrity_name, "count": len(results), "verifications": results}
        except Exception as e:
            logger.error(f"Failed to search celebrity: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── /history/trending ─────────────────────────────────────
    @app.get("/history/trending")
    async def get_trending(
        hours: int = Query(24, ge=1, le=168),
        min_count: int = Query(2, ge=2, le=10)
    ):
        try:
            from crud import get_trending_claims
            trends = await get_trending_claims(None, hours, min_count)
            return {"status": "success", "time_window_hours": hours, "trending_count": len(trends), "trending_claims": trends}
        except Exception as e:
            logger.error(f"Failed to get trending: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── /history/verdicts ─────────────────────────────────────
    @app.get("/history/verdicts")
    async def get_verdict_breakdown():
        try:
            rows = (
                table("analysis_history")
                .select("result")
                .eq("type", "deepfake_image")
                .execute()
                .data or []
            )
            total = len(rows)
            real      = sum(1 for r in rows if (r.get("result") or {}).get("verdict") == "REAL")
            fake      = sum(1 for r in rows if (r.get("result") or {}).get("verdict") == "FAKE")
            uncertain = sum(1 for r in rows if (r.get("result") or {}).get("verdict") == "UNCERTAIN")

            def pct(n): return round(n / total * 100, 2) if total else 0

            return {
                "status": "success",
                "total_deepfake_analyses": total,
                "verdicts": {
                    "REAL":      {"count": real,      "percentage": pct(real)},
                    "FAKE":      {"count": fake,      "percentage": pct(fake)},
                    "UNCERTAIN": {"count": uncertain, "percentage": pct(uncertain)},
                }
            }
        except Exception as e:
            logger.error(f"Failed to get verdict breakdown: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── /history/daily-stats ──────────────────────────────────
    @app.get("/history/daily-stats")
    async def get_daily_stats(days: int = Query(7, ge=1, le=30)):
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            rows = (
                table("analysis_history")
                .select("timestamp, type")
                .gte("timestamp", cutoff)
                .execute()
                .data or []
            )

            # Group by date in Python
            daily: dict = {}
            for row in rows:
                day = row["timestamp"][:10]   # "YYYY-MM-DD"
                if day not in daily:
                    daily[day] = {"date": day, "count": 0, "types": []}
                daily[day]["count"] += 1
                daily[day]["types"].append(row["type"])

            sorted_days = sorted(daily.values(), key=lambda x: x["date"])
            return {"status": "success", "days": days, "daily_stats": sorted_days}
        except Exception as e:
            logger.error(f"Failed to get daily stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    logger.info("✅ History endpoints added")