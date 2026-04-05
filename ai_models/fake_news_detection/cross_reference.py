# ai_models/fake_news_detection/cross_reference.py
"""
Cross-reference verification with smart context understanding
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger("spectra.cross_reference")


class CrossReferenceVerifier:
    """
    Cross-reference claims across news and social media with smart analysis
    """
    
    def __init__(self, social_monitor, news_aggregator):
        self.social_monitor = social_monitor
        self.news_aggregator = news_aggregator
        logger.info("Cross-reference verifier initialized")
    
    def verify_claim(
        self,
        claim_text: str,
        celebrity_name: str
    ) -> Dict:
        """
        Verify claim using smart context-aware analysis
        
        Args:
            claim_text: The claim to verify
            celebrity_name: Celebrity name
        
        Returns:
            Verification result with proper format
        """
        try:
            # Try to use smart verification if available
            try:
                from ai_models.fake_news_detection.smart_verification import verify_with_smart_analysis
                
                smart_result = verify_with_smart_analysis(
                    claim=claim_text,
                    celebrity=celebrity_name,
                    news_aggregator=self.news_aggregator,
                    max_articles=20
                )
                
                # Transform smart result to expected format
                return self._transform_smart_result(smart_result)
            
            except ImportError:
                # Fallback to old method if smart verification not available
                logger.warning("Smart verification not available, using basic method")
                return self._basic_verification(claim_text, celebrity_name)
        
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return self._error_result(str(e))
    
    def _transform_smart_result(self, smart_result: Dict) -> Dict:
        """
        Transform smart verification result to expected format
        
        Converts:
          {verdict: "VERIFIED", ...} 
        To:
          {verification_status: "VERIFIED", ...}
        """
        # Map verdict to verification_status
        verdict = smart_result.get("verdict", "UNVERIFIED")
        
        return {
            "verification_status": verdict,
            "confidence": smart_result.get("confidence", 0.5),
            "explanation": smart_result.get("message", "No explanation available"),
            "evidence": {
                "official_account": {
                    "status": "no_official_account",
                    "message": "No verified account found in database"
                },
                "news_articles": {
                    "status": smart_result.get("status", "uncertain"),
                    "message": smart_result.get("message", ""),
                    "articles_checked": smart_result.get("evidence", {}).get("articles_analyzed", 0),
                    "confidence": smart_result.get("confidence", 0.5),
                    **smart_result.get("evidence", {})
                },
                "social_media": {
                    "status": "no_discussion",
                    "message": "Twitter API not configured"
                }
            },
            "recommendation": smart_result.get("recommendation", "Unable to verify claim"),
            # Include full smart result for debugging
            "_smart_result": smart_result
        }
    
    def _basic_verification(self, claim_text: str, celebrity_name: str) -> Dict:
        """
        Fallback: Basic verification without smart analysis
        """
        # Get news articles
        articles = self.news_aggregator.search_news(
            query=f"{celebrity_name} {claim_text}",
            max_results=20
        )
        
        if not articles or len(articles) == 0:
            return {
                "verification_status": "UNVERIFIED",
                "confidence": 0.2,
                "explanation": "No recent news found about this claim",
                "evidence": {
                    "official_account": {
                        "status": "no_official_account",
                        "message": "No verified account found"
                    },
                    "news_articles": {
                        "status": "no_evidence",
                        "message": "No articles found",
                        "articles_checked": 0,
                        "confidence": 0.2
                    },
                    "social_media": {
                        "status": "no_discussion",
                        "message": "Twitter API not configured"
                    }
                }
            }
        
        # Simple keyword matching (old method)
        claim_words = set(claim_text.lower().split())
        matching_count = 0
        
        for article in articles:
            title = (article.get("title") or "").lower()
            desc = (article.get("description") or "").lower()
            
            article_text = f"{title} {desc}"
            article_words = set(article_text.split())
            
            common = claim_words & article_words
            if len(claim_words) > 0:
                similarity = len(common) / len(claim_words)
                if similarity >= 0.3:
                    matching_count += 1
        
        # Make decision
        if matching_count >= 2:
            status = "VERIFIED"
            confidence = min(0.7 + (matching_count * 0.05), 0.9)
            message = f"Found in {matching_count} news sources (basic matching)"
        elif matching_count == 1:
            status = "PARTIALLY_VERIFIED"
            confidence = 0.6
            message = "Found in 1 news source"
        else:
            status = "UNVERIFIED"
            confidence = 0.3
            message = f"No clear confirmation found ({len(articles)} articles checked)"
        
        return {
            "verification_status": status,
            "confidence": confidence,
            "explanation": message,
            "evidence": {
                "official_account": {
                    "status": "no_official_account",
                    "message": "No verified account found"
                },
                "news_articles": {
                    "status": "verified" if matching_count >= 2 else "uncertain",
                    "message": message,
                    "articles_checked": len(articles),
                    "matching_articles": matching_count,
                    "confidence": confidence
                },
                "social_media": {
                    "status": "no_discussion",
                    "message": "Twitter API not configured"
                }
            }
        }
    
    def _error_result(self, error_message: str) -> Dict:
        """
        Return error result in expected format
        """
        return {
            "verification_status": "ERROR",
            "confidence": 0.0,
            "explanation": f"Verification error: {error_message}",
            "evidence": {
                "official_account": {
                    "status": "error",
                    "message": error_message
                },
                "news_articles": {
                    "status": "error",
                    "message": error_message,
                    "articles_checked": 0
                },
                "social_media": {
                    "status": "error",
                    "message": error_message
                }
            }
        }
    
    def monitor_celebrity_mentions(
        self,
        celebrity_name: str,
        viral_threshold: int = 1000
    ) -> Dict:
        """
        Monitor celebrity for viral content
        
        Args:
            celebrity_name: Celebrity to monitor
            viral_threshold: Engagement threshold
        
        Returns:
            Monitoring result
        """
        try:
            # This would use Twitter API if available
            # For now, return not available
            return {
                "status": "no_viral_content",
                "message": "Twitter API not configured",
                "viral_posts_found": 0,
                "verified_posts": 0,
                "disputed_posts": 0,
                "unverified_posts": 0,
                "verifications": []
            }
        
        except Exception as e:
            logger.error(f"Monitoring failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "viral_posts_found": 0
            }


# Export
__all__ = ['CrossReferenceVerifier']
