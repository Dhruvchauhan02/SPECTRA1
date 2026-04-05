# export_utils.py
"""
Export and Utility Functions for SPECTRA-AI

Export data to CSV/JSON, cleanup old data, backup utilities.
"""

import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict
from io import StringIO
import logging

logger = logging.getLogger("spectra.export")


async def export_to_json(collection, query: Dict = None, limit: int = None) -> str:
    """
    Export data to JSON format
    
    Args:
        collection: MongoDB collection
        query: Filter query (optional)
        limit: Max documents to export
    
    Returns:
        JSON string
    """
    try:
        cursor = collection.find(query or {})
        
        if limit:
            cursor = cursor.limit(limit)
        
        documents = await cursor.to_list(length=limit or 1000)
        
        # Convert ObjectId to string
        for doc in documents:
            doc["_id"] = str(doc["_id"])
            # Convert datetime to string
            if "timestamp" in doc:
                doc["timestamp"] = doc["timestamp"].isoformat()
        
        json_str = json.dumps(documents, indent=2, default=str)
        logger.info(f"Exported {len(documents)} documents to JSON")
        
        return json_str
        
    except Exception as e:
        logger.error(f"Failed to export to JSON: {e}")
        raise


async def export_to_csv(collection, query: Dict = None, limit: int = None) -> str:
    """
    Export data to CSV format
    
    Args:
        collection: MongoDB collection
        query: Filter query (optional)
        limit: Max documents to export
    
    Returns:
        CSV string
    """
    try:
        cursor = collection.find(query or {})
        
        if limit:
            cursor = cursor.limit(limit)
        
        documents = await cursor.to_list(length=limit or 1000)
        
        if not documents:
            return ""
        
        # Flatten nested documents for CSV
        flattened = []
        for doc in documents:
            # Convert UTC to India time (UTC+5:30)
            timestamp = doc.get("timestamp", "")
            if timestamp:
                utc_time = timestamp
                # Add 5 hours 30 minutes for India Standard Time
                india_time = utc_time + timedelta(hours=5, minutes=30)
                timestamp_str = india_time.strftime("%Y-%m-%d %H:%M:%S IST")
            else:
                timestamp_str = ""
            
            flat = {
                "id": str(doc["_id"]),
                "request_id": doc.get("request_id", ""),
                "type": doc.get("type", ""),
                "timestamp_utc": doc.get("timestamp", "").isoformat() if doc.get("timestamp") else "",
                "timestamp_india": timestamp_str,
                "filename": doc.get("input", {}).get("filename", ""),
                "verdict": doc.get("result", {}).get("verdict", ""),
                "confidence": doc.get("result", {}).get("confidence", ""),
                "spectra_score": doc.get("result", {}).get("spectra_score", ""),
                "faces_detected": doc.get("result", {}).get("faces_detected", ""),
                "processing_time_ms": doc.get("result", {}).get("processing_time_ms", ""),
                "model_version": doc.get("metadata", {}).get("model_version", ""),
                "device": doc.get("metadata", {}).get("device", "")
            }
            flattened.append(flat)
        
        # Create CSV
        output = StringIO()
        if flattened:
            fieldnames = flattened[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened)
        
        csv_str = output.getvalue()
        logger.info(f"Exported {len(documents)} documents to CSV")
        
        return csv_str
        
    except Exception as e:
        logger.error(f"Failed to export to CSV: {e}")
        raise


async def cleanup_old_data(collection, days: int = 30, dry_run: bool = True) -> Dict:
    """
    Clean up old analysis data
    
    Args:
        collection: MongoDB collection
        days: Delete data older than this many days
        dry_run: If True, only count without deleting
    
    Returns:
        Cleanup statistics
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Count old documents
        count = await collection.count_documents({
            "timestamp": {"$lt": cutoff_date}
        })
        
        if dry_run:
            logger.info(f"DRY RUN: Would delete {count} documents older than {days} days")
            return {
                "dry_run": True,
                "documents_to_delete": count,
                "cutoff_date": cutoff_date.isoformat(),
                "status": "simulation_only"
            }
        
        # Actually delete
        result = await collection.delete_many({
            "timestamp": {"$lt": cutoff_date}
        })
        
        logger.info(f"Deleted {result.deleted_count} old documents")
        
        return {
            "dry_run": False,
            "documents_deleted": result.deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old data: {e}")
        raise


async def backup_collection(collection, backup_name: str = None) -> Dict:
    """
    Create a backup of the collection
    
    Args:
        collection: MongoDB collection
        backup_name: Optional backup name
    
    Returns:
        Backup info
    """
    try:
        if not backup_name:
            backup_name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Get database
        db = collection.database
        
        # Copy collection
        await db.command({
            "cloneCollection": collection.name,
            "from": backup_name
        })
        
        count = await collection.count_documents({})
        
        logger.info(f"Created backup: {backup_name} ({count} documents)")
        
        return {
            "backup_name": backup_name,
            "documents_backed_up": count,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        # Return simple backup info (actual MongoDB backup would need mongodump)
        return {
            "backup_name": backup_name,
            "status": "use_mongodump_for_full_backup",
            "command": f"mongodump --db spectra_ai --collection {collection.name}",
            "error": str(e)
        }


async def get_storage_info(db) -> Dict:
    """
    Get storage and database size information
    
    Args:
        db: MongoDB database
    
    Returns:
        Storage statistics
    """
    try:
        stats = await db.command("dbStats")
        
        return {
            "database": stats.get("db"),
            "collections": stats.get("collections"),
            "total_size_bytes": stats.get("dataSize", 0),
            "total_size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
            "index_size_mb": round(stats.get("indexSize", 0) / (1024 * 1024), 2),
            "storage_size_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2),
            "avg_object_size_bytes": stats.get("avgObjSize", 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to get storage info: {e}")
        return {}


async def validate_data_integrity(collection) -> Dict:
    """
    Validate data integrity and find issues
    
    Args:
        collection: MongoDB collection
    
    Returns:
        Validation results
    """
    try:
        issues = []
        
        # Check for missing required fields
        missing_verdict = await collection.count_documents({
            "type": "deepfake_image",
            "result.verdict": {"$exists": False}
        })
        
        if missing_verdict > 0:
            issues.append({
                "type": "missing_verdict",
                "count": missing_verdict,
                "severity": "warning"
            })
        
        # Check for invalid confidence values
        invalid_confidence = await collection.count_documents({
            "$or": [
                {"result.confidence": {"$lt": 0}},
                {"result.confidence": {"$gt": 1}}
            ]
        })
        
        if invalid_confidence > 0:
            issues.append({
                "type": "invalid_confidence",
                "count": invalid_confidence,
                "severity": "error"
            })
        
        # Check for future timestamps
        future_timestamps = await collection.count_documents({
            "timestamp": {"$gt": datetime.utcnow()}
        })
        
        if future_timestamps > 0:
            issues.append({
                "type": "future_timestamp",
                "count": future_timestamps,
                "severity": "warning"
            })
        
        total_docs = await collection.count_documents({})
        
        return {
            "total_documents": total_docs,
            "issues_found": len(issues),
            "issues": issues,
            "status": "healthy" if not issues else "issues_detected"
        }
        
    except Exception as e:
        logger.error(f"Failed to validate data integrity: {e}")
        return {"status": "validation_failed", "error": str(e)}
