# crud.py
"""
CRUD Operations for SPECTRA-AI — Supabase (PostgreSQL)

Drop-in replacement for the MongoDB/motor CRUD layer.
All functions keep the same signatures as the originals so
the rest of the codebase needs zero changes.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import logging

logger = logging.getLogger("spectra.crud")

# ── Helpers ───────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    """UTC timestamp as ISO-8601 string (Supabase / PostgreSQL compatible)."""
    return datetime.now(timezone.utc).isoformat()

def _hours_ago_iso(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

def _days_ago_iso(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


# ── Save operations ───────────────────────────────────────────────────────────

async def save_deepfake_analysis(
    collection,          # Supabase table reference (ignored — kept for compat)
    request_id: str,
    input_data: Dict,
    result: Dict,
    metadata: Dict,
    user_info: Optional[Dict] = None,
) -> str:
    """Save deepfake image analysis to Supabase analysis_history table."""
    from database import get_analysis_table

    row = {
        "request_id":  request_id,
        "type":        "deepfake_image",
        "timestamp":   _now_iso(),
        "input_data":  input_data,      # stored as JSONB
        "result":      result,           # stored as JSONB
        "metadata":    metadata,         # stored as JSONB
        "user_info":   user_info or {},
    }

    try:
        res = get_analysis_table().insert(row).execute()
        inserted_id = res.data[0]["id"]
        logger.debug(f"Saved deepfake analysis: {request_id}")
        return str(inserted_id)
    except Exception as e:
        logger.error(f"Failed to save deepfake analysis: {e}")
        raise


async def save_fake_news_analysis(
    collection,
    text: str,
    verdict: str,
    confidence: float,
    patterns: List[str],
    metadata: Optional[Dict] = None,
) -> str:
    """Save fake news text analysis to Supabase fake_news_analyses table."""
    from database import get_fakenews_table

    row = {
        "timestamp":         _now_iso(),
        "text_snippet":      text[:500],
        "text_length":       len(text),
        "verdict":           verdict,
        "confidence":        confidence,
        "patterns_detected": patterns,   # JSONB array
        "metadata":          metadata or {},
    }

    try:
        res = get_fakenews_table().insert(row).execute()
        inserted_id = res.data[0]["id"]
        logger.debug("Saved fake news analysis")
        return str(inserted_id)
    except Exception as e:
        logger.error(f"Failed to save fake news analysis: {e}")
        raise


async def save_celebrity_verification(
    collection,
    celebrity: str,
    claim: str,
    verification: Dict,
    sources: List[Dict],
    metadata: Optional[Dict] = None,
) -> str:
    """Save celebrity claim verification to Supabase celebrity_verifications table."""
    from database import get_celebrity_table

    row = {
        "timestamp":    _now_iso(),
        "celebrity":    celebrity,
        "claim":        claim,
        "verification": verification,   # JSONB
        "sources":      sources,         # JSONB array
        "metadata":     metadata or {},
    }

    try:
        res = get_celebrity_table().insert(row).execute()
        inserted_id = res.data[0]["id"]
        logger.debug(f"Saved celebrity verification: {celebrity}")
        return str(inserted_id)
    except Exception as e:
        logger.error(f"Failed to save celebrity verification: {e}")
        raise


# ── Read operations ───────────────────────────────────────────────────────────

async def get_recent_analyses(
    collection,
    limit: int = 10,
    analysis_type: Optional[str] = None,
) -> List[Dict]:
    """Get recent analyses from analysis_history, newest first."""
    from database import get_analysis_table

    try:
        query = get_analysis_table().select("*").order("timestamp", desc=True).limit(limit)
        if analysis_type:
            query = query.eq("type", analysis_type)
        res = query.execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Failed to get recent analyses: {e}")
        return []


async def get_analysis_by_id(
    collection,
    request_id: str,
) -> Optional[Dict]:
    """Get a single analysis by request_id."""
    from database import get_analysis_table

    try:
        res = get_analysis_table().select("*").eq("request_id", request_id).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"Failed to get analysis: {e}")
        return None


async def get_statistics(collection) -> Dict:
    """Return aggregated statistics (mirrors the MongoDB version)."""
    from database import get_analysis_table, get_fakenews_table, get_celebrity_table

    try:
        def count_where(**filters):
            q = get_analysis_table().select("id", count="exact")
            for col, val in filters.items():
                q = q.eq(col, val)
            return q.execute().count or 0

        total      = get_analysis_table().select("id", count="exact").execute().count or 0
        deepfake   = count_where(type="deepfake_image")
        fakenews   = (get_fakenews_table().select("id", count="exact").execute().count or 0)
        celebrity  = (get_celebrity_table().select("id", count="exact").execute().count or 0)

        # Deepfake verdicts — relies on result->>'verdict' stored in JSONB
        # We fetch and count in Python (small dataset) for simplicity
        df_rows = (
            get_analysis_table()
            .select("result")
            .eq("type", "deepfake_image")
            .execute()
            .data or []
        )
        real_count = sum(1 for r in df_rows if (r.get("result") or {}).get("verdict") == "REAL")
        fake_count = sum(1 for r in df_rows if (r.get("result") or {}).get("verdict") == "FAKE")

        # Last 24 h
        cutoff = _hours_ago_iso(24)
        recent = (
            get_analysis_table()
            .select("id", count="exact")
            .gte("timestamp", cutoff)
            .execute()
            .count or 0
        )

        return {
            "total_analyses": total,
            "by_type": {
                "deepfake_image":        deepfake,
                "fake_news_text":        fakenews,
                "celebrity_verification": celebrity,
            },
            "deepfake_verdicts": {"real": real_count, "fake": fake_count},
            "last_24h": recent,
        }
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        return {}


async def search_by_celebrity(
    collection,
    celebrity_name: str,
    limit: int = 20,
) -> List[Dict]:
    """Case-insensitive celebrity name search using Supabase ilike."""
    from database import get_celebrity_table

    try:
        res = (
            get_celebrity_table()
            .select("*")
            .ilike("celebrity", f"%{celebrity_name}%")
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception as e:
        logger.error(f"Failed to search celebrity: {e}")
        return []


async def get_trending_claims(
    collection,
    hours: int = 24,
    min_count: int = 2,
) -> List[Dict]:
    """
    Get celebrities with multiple recent verifications (trending).

    Supabase doesn't support GROUP BY via the REST API directly, so we
    aggregate in Python. For large datasets, use a Supabase RPC / SQL view.
    """
    from database import get_celebrity_table

    try:
        cutoff = _hours_ago_iso(hours)
        res = (
            get_celebrity_table()
            .select("celebrity, claim, verification")
            .gte("timestamp", cutoff)
            .execute()
        )
        rows = res.data or []

        # Group by celebrity name
        groups: Dict[str, Dict] = {}
        for row in rows:
            name = row["celebrity"]
            if name not in groups:
                groups[name] = {"_id": name, "count": 0, "claims": [], "verdicts": []}
            groups[name]["count"] += 1
            groups[name]["claims"].append(row.get("claim", ""))
            groups[name]["verdicts"].append(
                (row.get("verification") or {}).get("verdict", "UNKNOWN")
            )

        trending = [g for g in groups.values() if g["count"] >= min_count]
        trending.sort(key=lambda x: x["count"], reverse=True)
        return trending[:10]
    except Exception as e:
        logger.error(f"Failed to get trending claims: {e}")
        return []


async def delete_old_analyses(
    collection,
    days: int = 30,
) -> int:
    """Delete analyses older than `days` days."""
    from database import get_analysis_table

    try:
        cutoff = _days_ago_iso(days)
        res = get_analysis_table().delete().lt("timestamp", cutoff).execute()
        deleted = len(res.data or [])
        logger.info(f"Deleted {deleted} old analyses")
        return deleted
    except Exception as e:
        logger.error(f"Failed to delete old analyses: {e}")
        return 0