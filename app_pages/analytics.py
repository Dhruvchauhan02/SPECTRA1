# analytics.py
"""
Advanced Analytics for SPECTRA-AI — Supabase (PostgreSQL) edition

All MongoDB aggregation pipelines replaced with Python-side aggregation
over Supabase REST API results (supabase-py).
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from collections import defaultdict
import logging

logger = logging.getLogger("spectra.analytics")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _hours_ago_iso(hours: int) -> str:
    return (_now_utc() - timedelta(hours=hours)).isoformat()

def _days_ago_iso(days: int) -> str:
    return (_now_utc() - timedelta(days=days)).isoformat()

def _supabase_client():
    """Return the live Supabase client."""
    from database import supabase_db
    return supabase_db.client


# ── Hourly Activity ───────────────────────────────────────────────────────────

async def get_hourly_activity(collection, hours: int = 24) -> List[Dict]:
    """
    Get analysis activity by hour.
    `collection` parameter kept for API compat but ignored — uses Supabase directly.
    """
    try:
        cutoff = _hours_ago_iso(hours)
        client = _supabase_client()

        rows = (
            client.table("analysis_history")
            .select("timestamp, type, result")
            .gte("timestamp", cutoff)
            .execute()
            .data or []
        )

        # Group by "YYYY-MM-DD HH:00"
        buckets: Dict[str, Dict] = {}
        for row in rows:
            ts = row.get("timestamp", "")
            hour_key = ts[:13].replace("T", " ") + ":00" if len(ts) >= 13 else "unknown"
            if hour_key not in buckets:
                buckets[hour_key] = {
                    "hour": hour_key,
                    "total_analyses": 0,
                    "fake_detections": 0,
                    "confidences": [],
                    "processing_times": [],
                }
            b = buckets[hour_key]
            b["total_analyses"] += 1
            result = row.get("result") or {}
            if result.get("verdict") == "FAKE":
                b["fake_detections"] += 1
            if result.get("confidence") is not None:
                b["confidences"].append(result["confidence"])
            if result.get("processing_time_ms") is not None:
                b["processing_times"].append(result["processing_time_ms"])

        output = []
        for b in sorted(buckets.values(), key=lambda x: x["hour"]):
            output.append({
                "hour": b["hour"],
                "total_analyses": b["total_analyses"],
                "fake_detections": b["fake_detections"],
                "avg_confidence": round(sum(b["confidences"]) / len(b["confidences"]), 3)
                    if b["confidences"] else 0,
                "avg_processing_time_ms": round(
                    sum(b["processing_times"]) / len(b["processing_times"]), 0
                ) if b["processing_times"] else 0,
            })

        logger.info(f"Retrieved hourly activity for {len(output)} hour buckets")
        return output

    except Exception as e:
        logger.error(f"Failed to get hourly activity: {e}")
        return []


# ── Confidence Distribution ───────────────────────────────────────────────────

async def get_confidence_distribution(collection) -> Dict:
    """Get distribution of confidence scores across fixed ranges."""
    try:
        client = _supabase_client()
        rows = (
            client.table("analysis_history")
            .select("result")
            .eq("type", "deepfake_image")
            .execute()
            .data or []
        )

        ranges = [
            (0.0, 0.3, "0.0-0.3 (Low)"),
            (0.3, 0.5, "0.3-0.5 (Medium-Low)"),
            (0.5, 0.7, "0.5-0.7 (Medium)"),
            (0.7, 0.9, "0.7-0.9 (High)"),
            (0.9, 1.01, "0.9-1.0 (Very High)"),
        ]

        buckets = {label: {"range": label, "count": 0, "verdicts": []} for *_, label in ranges}

        for row in rows:
            result = row.get("result") or {}
            conf = result.get("confidence")
            if conf is None:
                continue
            for lo, hi, label in ranges:
                if lo <= conf < hi:
                    buckets[label]["count"] += 1
                    buckets[label]["verdicts"].append(result.get("verdict", "UNKNOWN"))
                    break

        distribution = [v for v in buckets.values() if v["count"] > 0]
        return {
            "distribution": distribution,
            "total_analyzed": sum(b["count"] for b in distribution),
        }

    except Exception as e:
        logger.error(f"Failed to get confidence distribution: {e}")
        return {}


# ── Performance Stats ─────────────────────────────────────────────────────────

async def get_performance_stats(collection) -> Dict:
    """Get system performance statistics."""
    try:
        client = _supabase_client()
        rows = (
            client.table("analysis_history")
            .select("result")
            .eq("type", "deepfake_image")
            .execute()
            .data or []
        )

        if not rows:
            return {}

        times = []
        confidences = []
        total_faces = 0
        multi_face = 0

        for row in rows:
            result = row.get("result") or {}
            pt = result.get("processing_time_ms")
            if pt is not None:
                times.append(pt)
            c = result.get("confidence")
            if c is not None:
                confidences.append(c)
            fd = result.get("faces_detected", 0) or 0
            total_faces += fd
            if fd > 1:
                multi_face += 1

        return {
            "total_analyses": len(rows),
            "processing_time": {
                "avg_ms": round(sum(times) / len(times), 0) if times else 0,
                "min_ms": round(min(times), 0) if times else 0,
                "max_ms": round(max(times), 0) if times else 0,
            },
            "avg_confidence": round(sum(confidences) / len(confidences), 3) if confidences else 0,
            "total_faces_detected": total_faces,
            "multi_face_images": multi_face,
        }

    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        return {}


# ── Anomaly Detection ─────────────────────────────────────────────────────────

async def detect_anomalies(collection, hours: int = 24) -> Dict:
    """Detect unusual patterns or anomalies."""
    try:
        cutoff = _hours_ago_iso(hours)
        client = _supabase_client()

        rows = (
            client.table("analysis_history")
            .select("timestamp, result")
            .gte("timestamp", cutoff)
            .execute()
            .data or []
        )

        total_recent = len(rows)
        fake_recent = sum(
            1 for r in rows
            if (r.get("result") or {}).get("verdict") == "FAKE"
        )
        slow_threshold = 5000
        slow_count = sum(
            1 for r in rows
            if (r.get("result") or {}).get("processing_time_ms", 0) >= slow_threshold
        )

        fake_rate = (fake_recent / total_recent * 100) if total_recent > 0 else 0

        # Reuse hourly activity for spike detection
        hourly = await get_hourly_activity(None, hours=hours)
        avg_per_hour = (
            sum(h["total_analyses"] for h in hourly) / len(hourly)
            if hourly else 0
        )
        spikes = [h for h in hourly if h["total_analyses"] > avg_per_hour * 2]

        anomalies = []
        if fake_rate > 50:
            anomalies.append({
                "type": "high_fake_rate",
                "severity": "warning",
                "message": f"High fake detection rate: {fake_rate:.1f}%",
                "value": fake_rate,
            })
        if slow_count > 0:
            anomalies.append({
                "type": "slow_processing",
                "severity": "info",
                "message": f"{slow_count} analyses took over {slow_threshold}ms",
                "value": slow_count,
            })
        if spikes:
            anomalies.append({
                "type": "traffic_spike",
                "severity": "info",
                "message": f"Detected {len(spikes)} hour(s) with unusual traffic",
                "hours": [s["hour"] for s in spikes],
            })

        return {
            "time_window_hours": hours,
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies,
            "baseline": {
                "total_analyses": total_recent,
                "fake_rate": round(fake_rate, 2),
                "avg_per_hour": round(avg_per_hour, 2),
            },
        }

    except Exception as e:
        logger.error(f"Failed to detect anomalies: {e}")
        return {}


# ── Top Filenames ─────────────────────────────────────────────────────────────

async def get_top_filenames(collection, limit: int = 10) -> List[Dict]:
    """Get most frequently analyzed filenames."""
    try:
        client = _supabase_client()
        rows = (
            client.table("analysis_history")
            .select("input_data, result, timestamp")
            .execute()
            .data or []
        )

        groups: Dict[str, Dict] = {}
        for row in rows:
            input_data = row.get("input_data") or {}
            filename = input_data.get("filename", "unknown")
            result = row.get("result") or {}
            if filename not in groups:
                groups[filename] = {
                    "filename": filename,
                    "analysis_count": 0,
                    "verdicts": [],
                    "last_analyzed": "",
                }
            g = groups[filename]
            g["analysis_count"] += 1
            g["verdicts"].append(result.get("verdict", "UNKNOWN"))
            ts = row.get("timestamp", "")
            if ts > g["last_analyzed"]:
                g["last_analyzed"] = ts

        sorted_results = sorted(groups.values(), key=lambda x: x["analysis_count"], reverse=True)
        return sorted_results[:limit]

    except Exception as e:
        logger.error(f"Failed to get top filenames: {e}")
        return []


# ── Celebrity Leaderboard ─────────────────────────────────────────────────────

async def get_celebrity_leaderboard(collection, limit: int = 10) -> List[Dict]:
    """Get most frequently verified celebrities."""
    try:
        client = _supabase_client()
        rows = (
            client.table("celebrity_verifications")
            .select("celebrity, verification, timestamp")
            .execute()
            .data or []
        )

        groups: Dict[str, Dict] = {}
        for row in rows:
            name = row.get("celebrity", "Unknown")
            verification = row.get("verification") or {}
            verdict = verification.get("verdict", "UNKNOWN")
            if name not in groups:
                groups[name] = {
                    "celebrity": name,
                    "total_checks": 0,
                    "verdicts": {"disputed": 0, "fake": 0, "verified": 0},
                    "last_checked": "",
                }
            g = groups[name]
            g["total_checks"] += 1
            v_lower = verdict.upper()
            if v_lower == "DISPUTED":
                g["verdicts"]["disputed"] += 1
            elif v_lower == "FAKE":
                g["verdicts"]["fake"] += 1
            elif v_lower == "VERIFIED":
                g["verdicts"]["verified"] += 1
            ts = row.get("timestamp", "")
            if ts > g["last_checked"]:
                g["last_checked"] = ts

        for g in groups.values():
            disputed = g["verdicts"]["disputed"]
            total = g["total_checks"]
            g["disputed_rate"] = round(disputed / total * 100, 1) if total else 0

        sorted_results = sorted(groups.values(), key=lambda x: x["total_checks"], reverse=True)
        return sorted_results[:limit]

    except Exception as e:
        logger.error(f"Failed to get celebrity leaderboard: {e}")
        return []


# ── Time Series ───────────────────────────────────────────────────────────────

async def get_time_series_data(collection, days: int = 7) -> List[Dict]:
    """Get daily time series data for visualization."""
    try:
        cutoff = _days_ago_iso(days)
        client = _supabase_client()

        rows = (
            client.table("analysis_history")
            .select("timestamp, type, result")
            .gte("timestamp", cutoff)
            .execute()
            .data or []
        )

        daily: Dict[str, Dict] = {}
        for row in rows:
            ts = row.get("timestamp", "")
            day = ts[:10]  # "YYYY-MM-DD"
            if not day:
                continue
            if day not in daily:
                daily[day] = {
                    "date": day,
                    "total_analyses": 0,
                    "by_type": {"deepfake": 0, "fake_news": 0, "celebrity": 0},
                    "fake_detected": 0,
                }
            d = daily[day]
            d["total_analyses"] += 1
            t = row.get("type", "")
            if t == "deepfake_image":
                d["by_type"]["deepfake"] += 1
            elif t == "fake_news_text":
                d["by_type"]["fake_news"] += 1
            elif t == "celebrity_verification":
                d["by_type"]["celebrity"] += 1
            result = row.get("result") or {}
            if result.get("verdict") == "FAKE":
                d["fake_detected"] += 1

        return sorted(daily.values(), key=lambda x: x["date"])

    except Exception as e:
        logger.error(f"Failed to get time series data: {e}")
        return []
