# database.py
"""
Supabase Database Connection Manager for SPECTRA-AI

Replaces MongoDB/motor with Supabase (PostgreSQL) using the supabase-py client.
"""

import os
import logging
from typing import Optional
from supabase import create_client, Client

logger = logging.getLogger("spectra.database")


class SupabaseDB:
    """Supabase connection manager — drop-in replacement for MongoDB class"""

    def __init__(self):
        self.client: Optional[Client] = None

    def connect(self) -> bool:
        """
        Connect to Supabase using environment variables.

        Required env vars:
            SUPABASE_URL  — your project URL  (e.g. https://xyz.supabase.co)
            SUPABASE_KEY  — your anon/service-role key
        """
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            logger.error(
                "❌ SUPABASE_URL and SUPABASE_KEY must be set as environment variables."
            )
            return False

        try:
            self.client = create_client(url, key)
            # Quick ping — list tables (will return empty if no rows, not an error)
            self.client.table("analysis_history").select("id").limit(1).execute()
            logger.info("✅ Connected to Supabase")
            return True
        except Exception as e:
            logger.error(f"❌ Supabase connection failed: {e}")
            return False

    def disconnect(self):
        """No persistent connection to close in supabase-py."""
        self.client = None
        logger.info("Supabase client released")

    @property
    def is_connected(self) -> bool:
        return self.client is not None

    def table(self, name: str):
        """Shortcut to access a Supabase table."""
        if not self.client:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.client.table(name)

    async def get_stats(self) -> dict:
        """Return row counts for each table (mirrors old MongoDB get_stats)."""
        if not self.client:
            return {}
        try:
            def count(table_name):
                res = self.client.table(table_name).select("id", count="exact").execute()
                return res.count or 0

            analysis   = count("analysis_history")
            celebrity  = count("celebrity_verifications")
            fakenews   = count("fake_news_analyses")

            return {
                "database": "supabase",
                "collections": 3,
                "counts": {
                    "analysis_history":        analysis,
                    "celebrity_verifications": celebrity,
                    "fake_news_analyses":      fakenews,
                    "total": analysis + celebrity + fakenews,
                },
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# ── Global singleton ──────────────────────────────────────────────────────────
supabase_db = SupabaseDB()


def get_database() -> SupabaseDB:
    """
    Return the connected database instance.

    Usage:
        db = get_database()
        db.table("analysis_history").select("*").execute()
    """
    if not supabase_db.is_connected:
        raise RuntimeError("Database not connected. Call supabase_db.connect() first.")
    return supabase_db


# ── Convenience table getters (mirrors old MongoDB helpers) ───────────────────

def get_analysis_table():
    return get_database().table("analysis_history")

def get_celebrity_table():
    return get_database().table("celebrity_verifications")

def get_fakenews_table():
    return get_database().table("fake_news_analyses")