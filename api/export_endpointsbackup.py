# api/export_endpoints.py
"""
Export and Utility Endpoints for SPECTRA-AI — Supabase edition
"""

from fastapi import HTTPException, Query
from fastapi.responses import Response
from datetime import datetime, timedelta, timezone
import json
import csv
import io
import logging

logger = logging.getLogger("spectra.api.export")


def add_export_endpoints(app, supabase_db, verify_api_key):

    def table(name):
        return supabase_db.client.table(name)

    # ── /export/json ──────────────────────────────────────────
    @app.get("/export/json")
    async def export_json(
        type: str = Query(None),
        limit: int = Query(100, ge=1, le=10000)
    ):
        try:
            q = table("analysis_history").select("*").order("timestamp", desc=True).limit(limit)
            if type:
                q = q.eq("type", type)
            rows = q.execute().data or []

            json_data = json.dumps(rows, indent=2, default=str)
            return Response(
                content=json_data,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=spectra_export_{type or 'all'}.json"}
            )
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── /export/csv ───────────────────────────────────────────
    @app.get("/export/csv")
    async def export_csv(
        type: str = Query(None),
        limit: int = Query(100, ge=1, le=10000)
    ):
        try:
            q = table("analysis_history").select("*").order("timestamp", desc=True).limit(limit)
            if type:
                q = q.eq("type", type)
            rows = q.execute().data or []

            if not rows:
                csv_data = "No data found"
            else:
                output = io.StringIO()
                # Flatten top-level keys only
                fieldnames = ["id", "request_id", "type", "timestamp"]
                writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)
                csv_data = output.getvalue()

            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=spectra_export_{type or 'all'}.csv"}
            )
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── /admin/cleanup ────────────────────────────────────────
    @app.post("/admin/cleanup")
    async def cleanup_old_data(
        days: int = Query(30, ge=1, le=365),
        dry_run: bool = Query(True)
    ):
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

            # Count rows that would be deleted
            count_res = (
                table("analysis_history")
                .select("id", count="exact")
                .lt("timestamp", cutoff)
                .execute()
            )
            would_delete = count_res.count or 0

            if dry_run:
                return {
                    "status": "dry_run",
                    "would_delete": would_delete,
                    "cutoff_date": cutoff,
                    "message": "Run with dry_run=false to actually delete"
                }

            # Actually delete
            table("analysis_history").delete().lt("timestamp", cutoff).execute()
            return {
                "status": "success",
                "deleted": would_delete,
                "cutoff_date": cutoff
            }
        except Exception as e:
            logger.error(f"Failed to cleanup data: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── /admin/storage-info ───────────────────────────────────
    @app.get("/admin/storage-info")
    async def get_storage_info():
        try:
            stats = await supabase_db.get_stats()
            return {
                "status": "success",
                "storage_info": {
                    "database": "Supabase (PostgreSQL)",
                    "counts": stats.get("counts", {}),
                    "note": "Detailed storage size available in Supabase Dashboard → Database"
                }
            }
        except Exception as e:
            logger.error(f"Failed to get storage info: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── /admin/validate ───────────────────────────────────────
    @app.get("/admin/validate")
    async def validate_data():
        try:
            rows = table("analysis_history").select("id, request_id, type, result").execute().data or []

            missing_request_id = sum(1 for r in rows if not r.get("request_id"))
            missing_result     = sum(1 for r in rows if not r.get("result"))
            missing_type       = sum(1 for r in rows if not r.get("type"))

            return {
                "status": "success",
                "validation": {
                    "total_rows":          len(rows),
                    "missing_request_id":  missing_request_id,
                    "missing_result":      missing_result,
                    "missing_type":        missing_type,
                    "healthy":             missing_request_id == 0 and missing_result == 0
                }
            }
        except Exception as e:
            logger.error(f"Failed to validate data: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── /admin/backup-info ────────────────────────────────────
    @app.get("/admin/backup-info")
    async def get_backup_info():
        return {
            "status": "success",
            "backup_methods": {
                "supabase_dashboard": {
                    "description": "Supabase built-in backups (Pro plan)",
                    "url": "https://supabase.com/dashboard → Database → Backups"
                },
                "export_json": {
                    "description": "Export via API",
                    "endpoint": "/export/json?limit=10000"
                },
                "export_csv": {
                    "description": "Export via API (CSV format)",
                    "endpoint": "/export/csv?limit=10000"
                }
            },
            "recommendations": [
                "Use Supabase Dashboard for point-in-time recovery (Pro plan)",
                "Schedule regular JSON exports via /export/json",
                "Store exports in separate cloud storage",
                "Keep at least 7 days of exports"
            ]
        }

    logger.info("✅ Export endpoints added")