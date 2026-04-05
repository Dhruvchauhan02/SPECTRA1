# ai_models/fake_news_detection/celebrity_verification.py
"""
Celebrity Fake News Verification System for SPECTRA-AI
Integrated system for monitoring and verifying celebrity-related claims
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Try relative imports first, fall back to absolute
try:
    from .social_media_monitor import SocialMediaMonitor
    from .news_aggregator import ImprovedNewsAggregator
    from .cross_reference import CrossReferenceVerifier
except ImportError:
    from ai_models.fake_news_detection.social_media_monitor import SocialMediaMonitor
    from ai_models.fake_news_detection.news_aggregator import ImprovedNewsAggregator
    from ai_models.fake_news_detection.cross_reference import CrossReferenceVerifier

logger = logging.getLogger("spectra.celebrity_verification")


class CelebrityVerificationSystem:
    """
    Complete system for celebrity fake news detection.

    Features:
    - Monitor social media for viral celebrity content
    - Cross-reference with official news sources
    - Verify against celebrity's official accounts
    - Real-time monitoring and alerts
    """

    def __init__(
        self,
        twitter_bearer_token: Optional[str] = None,
        news_api_key: Optional[str] = None,
        gnews_api_key: Optional[str] = None,
    ):
        logger.info("Initializing Celebrity Verification System")

        self.social_monitor = SocialMediaMonitor(
            twitter_bearer_token=twitter_bearer_token
        )
        self.news_aggregator = ImprovedNewsAggregator(
            newsapi_key=news_api_key,
            gnews_key=gnews_api_key,
        )
        self.cross_reference = CrossReferenceVerifier(
            social_monitor=self.social_monitor,
            news_aggregator=self.news_aggregator,
        )

        logger.info("✅ Celebrity Verification System ready")

    def verify_celebrity_claim(
        self,
        claim: str,
        celebrity_name: str,
        source_url: Optional[str] = None,
    ) -> Dict:
        """
        Verify a specific claim about a celebrity.

        Returns a report whose shape the API and frontend both expect:
          {
            "request_id":      str,
            "timestamp":       str,
            "claim":           str,
            "celebrity":       str,
            "verification": {               ← dict, NOT a raw string
                "verdict":    str,          ← "VERIFIED" | "DISPUTED" | "FAKE" | "UNVERIFIED" | "PARTIALLY_VERIFIED"
                "confidence": float,
            },
            "confidence":      float,       ← top-level copy for convenience
            "explanation":     str,
            "evidence_summary": dict,
            "recommendation":  str,
            "sources":         List[dict],  ← FIX: list the frontend reads for source cards
            "full_evidence":   dict,
          }
        """
        logger.info(f"Verifying claim about {celebrity_name}: {claim[:80]}")

        # Run cross-reference verification
        verification = self.cross_reference.verify_claim(
            claim_text=claim,
            celebrity_name=celebrity_name,
        )

        if source_url:
            verification["source_url"] = source_url

        # --- FIX: verification["verification_status"] is the verdict string ---
        verdict     = verification.get("verification_status", "UNVERIFIED")
        confidence  = verification.get("confidence", 0.0)
        explanation = verification.get("explanation", "No explanation available.")
        recommendation = verification.get("recommendation", self._generate_recommendation_from_verdict(verdict, confidence))

        # --- FIX: build a normalised sources list for the frontend ---
        sources = self._extract_sources(verification)

        report = {
            "request_id":    datetime.now().strftime("%Y%m%d%H%M%S"),
            "timestamp":     datetime.now().isoformat(),
            "claim":         claim,
            "celebrity":     celebrity_name,
            # FIX: wrap verdict + confidence in a dict so frontend can do
            #   result["verification"]["verdict"]  and
            #   result["verification"]["confidence"]
            "verification": {
                "verdict":    verdict,
                "confidence": confidence,
            },
            # Also expose at top level for convenience
            "confidence":    confidence,
            "explanation":   explanation,
            "evidence_summary": self._summarize_evidence(verification.get("evidence", {})),
            "recommendation": recommendation,
            # FIX: normalised sources list — frontend reads result["sources"]
            "sources":       sources,
            "full_evidence": verification.get("evidence", {}),
        }

        logger.info(f"Verification complete: {verdict} ({confidence:.0%})")
        return report

    # ── helpers ───────────────────────────────────────────────────────────────

    def _extract_sources(self, verification: Dict) -> List[Dict]:
        """
        Build a unified sources list from wherever smart_verification stored them.

        smart_verification may return:
          - confirming_sources: [{outlet, title, url}, ...]
          - debunking_sources:  [{outlet, title, url}, ...]

        We normalise both into the shape the frontend expects:
          {title, source, published_at, url}
        """
        sources: List[Dict] = []

        for key in ("confirming_sources", "debunking_sources"):
            for s in verification.get(key, []):
                sources.append({
                    "title":        s.get("title", "Untitled"),
                    "source":       s.get("outlet", "Unknown"),
                    "published_at": s.get("published_at", ""),
                    "url":          s.get("url", ""),
                })

        # Also check inside the nested evidence dict (cross_reference path)
        evidence = verification.get("evidence", {})
        news_ev  = evidence.get("news_articles", {})
        for key in ("confirming_sources", "debunking_sources", "articles"):
            for s in news_ev.get(key, []):
                entry = {
                    "title":        s.get("title", "Untitled"),
                    "source":       s.get("outlet") or s.get("source", "Unknown"),
                    "published_at": s.get("published_at", ""),
                    "url":          s.get("url", ""),
                }
                # Avoid duplicates
                if entry not in sources:
                    sources.append(entry)

        return sources

    def _summarize_evidence(self, evidence: Dict) -> Dict:
        """Create concise evidence summary."""
        summary = {}

        if evidence.get("official_account"):
            official = evidence["official_account"]
            summary["official_account"] = official.get("status", "unknown")

        if evidence.get("news_articles"):
            news = evidence["news_articles"]
            summary["news_verification"] = {
                "status":        news.get("status", "unknown"),
                "articles_found": news.get("articles_checked", 0),
            }

        if evidence.get("social_media"):
            social = evidence["social_media"]
            summary["social_media"] = {
                "status":     social.get("status", "unknown"),
                "posts_found": social.get("total_posts", 0),
            }

        return summary

    def _generate_recommendation_from_verdict(self, verdict: str, confidence: float) -> str:
        """Fallback recommendation when cross_reference doesn't supply one."""
        if verdict == "VERIFIED" and confidence > 0.8:
            return "This claim is verified. Safe to trust and share."
        if verdict == "VERIFIED":
            return "This claim is likely true but verify additional sources before sharing."
        if verdict in ("DISPUTED", "FAKE"):
            return "⚠️ WARNING: This claim is disputed or debunked. Do NOT share without verification."
        if verdict == "PARTIALLY_VERIFIED":
            return "Claim found in limited sources. Wait for additional confirmation before sharing."
        return "Claim cannot be verified. Treat with high skepticism."

    # ── Monitoring ────────────────────────────────────────────────────────────

    def monitor_celebrity(
        self,
        celebrity_name: str,
        viral_threshold: int = 1000,
        alert_on_fake: bool = True,
    ) -> Dict:
        """Monitor a celebrity for viral fake news."""
        logger.info(f"Monitoring {celebrity_name} for viral content")

        monitoring_result = self.cross_reference.monitor_celebrity_mentions(
            celebrity_name=celebrity_name,
            viral_threshold=viral_threshold,
        )

        if monitoring_result["status"] == "no_viral_content":
            return {
                "status":    "clean",
                "celebrity": celebrity_name,
                "message":   "No significant viral content detected",
                "timestamp": datetime.now().isoformat(),
            }

        verifications = monitoring_result.get("verifications", [])
        alerts = []
        for v in verifications:
            vs = v.get("verification_status", "")
            if vs == "DISPUTED" and alert_on_fake:
                alerts.append({
                    "type":        "DISPUTED_CONTENT",
                    "claim":       v.get("claim", "")[:200],
                    "confidence":  v.get("confidence", 0),
                    "explanation": v.get("explanation", ""),
                })
            elif vs == "UNVERIFIED":
                alerts.append({
                    "type":        "UNVERIFIED_CONTENT",
                    "claim":       v.get("claim", "")[:200],
                    "confidence":  v.get("confidence", 0),
                    "explanation": v.get("explanation", ""),
                })

        return {
            "status":    "alerts_found" if alerts else "monitored",
            "celebrity": celebrity_name,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "viral_posts": monitoring_result.get("viral_posts_found", 0),
                "verified":    monitoring_result.get("verified_posts", 0),
                "disputed":    monitoring_result.get("disputed_posts", 0),
                "unverified":  monitoring_result.get("unverified_posts", 0),
            },
            "alerts":      alerts,
            "full_report": monitoring_result,
        }

    def batch_verify_celebrities(
        self,
        celebrities: List[str],
        viral_threshold: int = 1000,
    ) -> Dict:
        """Monitor multiple celebrities at once."""
        results = {}
        for celebrity in celebrities:
            try:
                results[celebrity] = self.monitor_celebrity(
                    celebrity_name=celebrity,
                    viral_threshold=viral_threshold,
                )
            except Exception as e:
                logger.error(f"Failed to monitor {celebrity}: {e}")
                results[celebrity] = {"status": "error", "message": str(e)}

        total_alerts = sum(
            len(r.get("alerts", []))
            for r in results.values()
            if isinstance(r, dict)
        )

        return {
            "status":                "success",
            "celebrities_monitored": len(celebrities),
            "total_alerts":          total_alerts,
            "results":               results,
            "timestamp":             datetime.now().isoformat(),
        }


# ── Convenience function ──────────────────────────────────────────────────────

def quick_verify(
    claim: str,
    celebrity: str,
    twitter_token: Optional[str] = None,
    news_key: Optional[str] = None,
) -> Dict:
    system = CelebrityVerificationSystem(
        twitter_bearer_token=twitter_token,
        news_api_key=news_key,
    )
    return system.verify_celebrity_claim(claim, celebrity)
