# analytics.py
"""
Advanced Analytics for SPECTRA-AI MongoDB

Provides complex aggregation queries, trending detection, and insights.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger("spectra.analytics")


async def get_hourly_activity(collection, hours: int = 24) -> List[Dict]:
    """
    Get analysis activity by hour
    
    Args:
        collection: MongoDB collection
        hours: Number of hours to analyze
    
    Returns:
        List of hourly statistics
    """
    try:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        pipeline = [
            # Filter recent
            {"$match": {"timestamp": {"$gte": time_threshold}}},
            
            # Group by hour
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d %H:00",
                        "date": "$timestamp"
                    }
                },
                "count": {"$sum": 1},
                "fake_count": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$result.verdict", "FAKE"]},
                            1,
                            0
                        ]
                    }
                },
                "avg_confidence": {"$avg": "$result.confidence"},
                "avg_processing_time": {"$avg": "$result.processing_time_ms"}
            }},
            
            # Sort by hour
            {"$sort": {"_id": 1}},
            
            # Format output
            {"$project": {
                "_id": 0,
                "hour": "$_id",
                "total_analyses": "$count",
                "fake_detections": "$fake_count",
                "avg_confidence": {"$round": ["$avg_confidence", 3]},
                "avg_processing_time_ms": {"$round": ["$avg_processing_time", 0]}
            }}
        ]
        
        results = await collection.aggregate(pipeline).to_list(length=hours)
        logger.info(f"Retrieved hourly activity for {len(results)} hours")
        return results
        
    except Exception as e:
        logger.error(f"Failed to get hourly activity: {e}")
        return []


async def get_confidence_distribution(collection) -> Dict:
    """
    Get distribution of confidence scores
    
    Returns:
        Confidence ranges with counts
    """
    try:
        pipeline = [
            {"$match": {"type": "deepfake_image"}},
            
            # Bucket by confidence ranges
            {"$bucket": {
                "groupBy": "$result.confidence",
                "boundaries": [0, 0.3, 0.5, 0.7, 0.9, 1.0],
                "default": "other",
                "output": {
                    "count": {"$sum": 1},
                    "verdicts": {"$push": "$result.verdict"}
                }
            }},
            
            # Format output
            {"$project": {
                "_id": 0,
                "range": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$_id", 0]}, "then": "0.0-0.3 (Low)"},
                            {"case": {"$eq": ["$_id", 0.3]}, "then": "0.3-0.5 (Medium-Low)"},
                            {"case": {"$eq": ["$_id", 0.5]}, "then": "0.5-0.7 (Medium)"},
                            {"case": {"$eq": ["$_id", 0.7]}, "then": "0.7-0.9 (High)"},
                            {"case": {"$eq": ["$_id", 0.9]}, "then": "0.9-1.0 (Very High)"}
                        ],
                        "default": "Other"
                    }
                },
                "count": 1,
                "verdicts": 1
            }}
        ]
        
        results = await collection.aggregate(pipeline).to_list(length=10)
        
        return {
            "distribution": results,
            "total_analyzed": sum(r["count"] for r in results)
        }
        
    except Exception as e:
        logger.error(f"Failed to get confidence distribution: {e}")
        return {}


async def get_performance_stats(collection) -> Dict:
    """
    Get system performance statistics
    
    Returns:
        Performance metrics
    """
    try:
        pipeline = [
            {"$match": {"type": "deepfake_image"}},
            
            # Calculate stats
            {"$group": {
                "_id": None,
                "total_analyses": {"$sum": 1},
                "avg_processing_time": {"$avg": "$result.processing_time_ms"},
                "min_processing_time": {"$min": "$result.processing_time_ms"},
                "max_processing_time": {"$max": "$result.processing_time_ms"},
                "avg_confidence": {"$avg": "$result.confidence"},
                "faces_detected_total": {"$sum": "$result.faces_detected"},
                "multi_face_count": {
                    "$sum": {
                        "$cond": [
                            {"$gt": ["$result.faces_detected", 1]},
                            1,
                            0
                        ]
                    }
                }
            }},
            
            # Format
            {"$project": {
                "_id": 0,
                "total_analyses": 1,
                "processing_time": {
                    "avg_ms": {"$round": ["$avg_processing_time", 0]},
                    "min_ms": {"$round": ["$min_processing_time", 0]},
                    "max_ms": {"$round": ["$max_processing_time", 0]}
                },
                "avg_confidence": {"$round": ["$avg_confidence", 3]},
                "total_faces_detected": "$faces_detected_total",
                "multi_face_images": "$multi_face_count"
            }}
        ]
        
        results = await collection.aggregate(pipeline).to_list(length=1)
        return results[0] if results else {}
        
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        return {}


async def detect_anomalies(collection, hours: int = 24) -> Dict:
    """
    Detect unusual patterns or anomalies
    
    Args:
        collection: MongoDB collection
        hours: Time window to analyze
    
    Returns:
        Detected anomalies
    """
    try:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        # Get recent analyses
        total_recent = await collection.count_documents({
            "timestamp": {"$gte": time_threshold}
        })
        
        # Get high fake rate
        fake_recent = await collection.count_documents({
            "timestamp": {"$gte": time_threshold},
            "result.verdict": "FAKE"
        })
        
        fake_rate = (fake_recent / total_recent * 100) if total_recent > 0 else 0
        
        # Get slow processing count
        slow_threshold = 5000  # 5 seconds
        slow_count = await collection.count_documents({
            "timestamp": {"$gte": time_threshold},
            "result.processing_time_ms": {"$gte": slow_threshold}
        })
        
        # Detect spikes
        hourly_counts = await get_hourly_activity(collection, hours=hours)
        avg_per_hour = sum(h["total_analyses"] for h in hourly_counts) / len(hourly_counts) if hourly_counts else 0
        
        spikes = [
            h for h in hourly_counts
            if h["total_analyses"] > avg_per_hour * 2
        ]
        
        anomalies = []
        
        # Check for high fake rate
        if fake_rate > 50:
            anomalies.append({
                "type": "high_fake_rate",
                "severity": "warning",
                "message": f"High fake detection rate: {fake_rate:.1f}%",
                "value": fake_rate
            })
        
        # Check for slow processing
        if slow_count > 0:
            anomalies.append({
                "type": "slow_processing",
                "severity": "info",
                "message": f"{slow_count} analyses took over {slow_threshold}ms",
                "value": slow_count
            })
        
        # Check for traffic spikes
        if spikes:
            anomalies.append({
                "type": "traffic_spike",
                "severity": "info",
                "message": f"Detected {len(spikes)} hour(s) with unusual traffic",
                "hours": [s["hour"] for s in spikes]
            })
        
        return {
            "time_window_hours": hours,
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies,
            "baseline": {
                "total_analyses": total_recent,
                "fake_rate": round(fake_rate, 2),
                "avg_per_hour": round(avg_per_hour, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to detect anomalies: {e}")
        return {}


async def get_top_filenames(collection, limit: int = 10) -> List[Dict]:
    """
    Get most frequently analyzed filenames
    
    Args:
        collection: MongoDB collection
        limit: Number of results
    
    Returns:
        Top filenames with counts
    """
    try:
        pipeline = [
            # Group by filename
            {"$group": {
                "_id": "$input.filename",
                "count": {"$sum": 1},
                "verdicts": {"$push": "$result.verdict"},
                "last_analyzed": {"$max": "$timestamp"}
            }},
            
            # Sort by count
            {"$sort": {"count": -1}},
            
            # Limit
            {"$limit": limit},
            
            # Format
            {"$project": {
                "_id": 0,
                "filename": "$_id",
                "analysis_count": "$count",
                "last_analyzed": 1,
                "verdicts": 1
            }}
        ]
        
        results = await collection.aggregate(pipeline).to_list(length=limit)
        return results
        
    except Exception as e:
        logger.error(f"Failed to get top filenames: {e}")
        return []


async def get_celebrity_leaderboard(collection, limit: int = 10) -> List[Dict]:
    """
    Get most frequently verified celebrities
    
    Args:
        collection: MongoDB collection
        limit: Number of results
    
    Returns:
        Celebrity leaderboard
    """
    try:
        pipeline = [
            # Filter celebrity verifications
            {"$match": {"type": "celebrity_verification"}},
            
            # Group by celebrity
            {"$group": {
                "_id": "$celebrity",
                "total_checks": {"$sum": 1},
                "disputed_count": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$verification.verdict", "DISPUTED"]},
                            1,
                            0
                        ]
                    }
                },
                "fake_count": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$verification.verdict", "FAKE"]},
                            1,
                            0
                        ]
                    }
                },
                "verified_count": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$verification.verdict", "VERIFIED"]},
                            1,
                            0
                        ]
                    }
                },
                "last_checked": {"$max": "$timestamp"}
            }},
            
            # Sort by total checks
            {"$sort": {"total_checks": -1}},
            
            # Limit
            {"$limit": limit},
            
            # Format
            {"$project": {
                "_id": 0,
                "celebrity": "$_id",
                "total_checks": 1,
                "verdicts": {
                    "disputed": "$disputed_count",
                    "fake": "$fake_count",
                    "verified": "$verified_count"
                },
                "disputed_rate": {
                    "$multiply": [
                        {"$divide": ["$disputed_count", "$total_checks"]},
                        100
                    ]
                },
                "last_checked": 1
            }}
        ]
        
        results = await collection.aggregate(pipeline).to_list(length=limit)
        
        # Round disputed_rate
        for r in results:
            r["disputed_rate"] = round(r["disputed_rate"], 1)
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to get celebrity leaderboard: {e}")
        return []


async def get_time_series_data(collection, days: int = 7) -> List[Dict]:
    """
    Get time series data for visualization
    
    Args:
        collection: MongoDB collection
        days: Number of days
    
    Returns:
        Daily time series data
    """
    try:
        time_threshold = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            # Filter recent
            {"$match": {"timestamp": {"$gte": time_threshold}}},
            
            # Group by date
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$timestamp"
                    }
                },
                "total": {"$sum": 1},
                "deepfake_count": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$type", "deepfake_image"]},
                            1,
                            0
                        ]
                    }
                },
                "fake_news_count": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$type", "fake_news_text"]},
                            1,
                            0
                        ]
                    }
                },
                "celebrity_count": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$type", "celebrity_verification"]},
                            1,
                            0
                        ]
                    }
                },
                "fake_detected": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$result.verdict", "FAKE"]},
                            1,
                            0
                        ]
                    }
                }
            }},
            
            # Sort by date
            {"$sort": {"_id": 1}},
            
            # Format
            {"$project": {
                "_id": 0,
                "date": "$_id",
                "total_analyses": "$total",
                "by_type": {
                    "deepfake": "$deepfake_count",
                    "fake_news": "$fake_news_count",
                    "celebrity": "$celebrity_count"
                },
                "fake_detected": "$fake_detected"
            }}
        ]
        
        results = await collection.aggregate(pipeline).to_list(length=days)
        return results
        
    except Exception as e:
        logger.error(f"Failed to get time series data: {e}")
        return []
