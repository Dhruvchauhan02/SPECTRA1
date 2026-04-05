# ai_models/fake_news_detection/smart_verification.py
"""
Content-Aware News Verification
Understands CONTEXT, not just keywords
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger("spectra.smart_verification")


class SmartNewsVerification:
    """
    Intelligent verification that understands article context
    """
    
    # Keywords that indicate an article is DEBUNKING fake news
    DEBUNKING_KEYWORDS = [
        "fake", "false", "debunk", "fact check", "hoax", 
        "misinformation", "disinformation", "myth", "rumor",
        "denied", "denies", "refutes", "clarifies", "quashes",
        "not true", "baseless", "unverified", "speculation"
    ]
    
    # Keywords that indicate CONFIRMATION
    CONFIRMATION_KEYWORDS = [
        "confirms", "confirmed", "officially", "announced",
        "statement", "press release", "spokesperson said",
        "verified", "authenticated", "corroborated"
    ]
    
    # Trusted news sources (high credibility)
    TRUSTED_SOURCES = [
        "reuters", "associated press", "ap news", "bbc",
        "bloomberg", "financial times", "the guardian",
        "the new york times", "washington post", "wsj",
        "pti", "ani", "the hindu", "indian express"
    ]
    
    def verify_claim_with_context(
        self,
        claim: str,
        articles: List[Dict],
        similarity_threshold: float = 0.3
    ) -> Dict:
        """
        Verify claim with CONTEXT UNDERSTANDING
        
        Args:
            claim: The claim to verify
            articles: List of articles from news aggregator
            similarity_threshold: Minimum word overlap
        
        Returns:
            Detailed verification result with context analysis
        """
        if not articles:
            return {
                "status": "no_evidence",
                "verdict": "UNVERIFIED",
                "confidence": 0.2,
                "message": "No articles found",
                "articles_analyzed": 0
            }
        
        # Analyze each article
        confirming_articles = []
        debunking_articles = []
        neutral_articles = []
        
        claim_words = set(claim.lower().split())
        
        for article in articles:
            analysis = self._analyze_article_context(
                article, 
                claim_words,
                similarity_threshold
            )
            
            if analysis["category"] == "confirming":
                confirming_articles.append(analysis)
            elif analysis["category"] == "debunking":
                debunking_articles.append(analysis)
            elif analysis["category"] == "neutral":
                neutral_articles.append(analysis)
        
        # Decision Logic
        return self._make_verification_decision(
            claim=claim,
            confirming=confirming_articles,
            debunking=debunking_articles,
            neutral=neutral_articles,
            total_articles=len(articles)
        )
    
    def _analyze_article_context(
        self,
        article: Dict,
        claim_words: set,
        similarity_threshold: float
    ) -> Dict:
        """
        Analyze if article is CONFIRMING, DEBUNKING, or NEUTRAL
        """
        title = (article.get("title") or "").lower()
        desc = (article.get("description") or "").lower()
        content = (article.get("content") or "").lower()
        outlet = (article.get("outlet") or "").lower()
        
        # Combine all text
        article_text = f"{title} {desc} {content}"
        article_words = set(article_text.split())
        
        # Calculate word overlap
        common_words = claim_words & article_words
        if len(claim_words) > 0:
            similarity = len(common_words) / len(claim_words)
        else:
            similarity = 0
        
        # Check if article is relevant
        if similarity < similarity_threshold:
            return {
                "category": "irrelevant",
                "similarity": similarity,
                "article": article
            }
        
        # Check for DEBUNKING keywords
        debunking_count = sum(
            1 for keyword in self.DEBUNKING_KEYWORDS 
            if keyword in article_text
        )
        
        # Check for CONFIRMATION keywords
        confirmation_count = sum(
            1 for keyword in self.CONFIRMATION_KEYWORDS 
            if keyword in article_text
        )
        
        # Check source credibility
        is_trusted = any(
            source in outlet 
            for source in self.TRUSTED_SOURCES
        )
        
        # Categorize
        if debunking_count >= 2:
            # Article is DEBUNKING the claim
            category = "debunking"
            confidence = 0.8 if is_trusted else 0.6
        
        elif confirmation_count >= 2:
            # Article is CONFIRMING the claim
            category = "confirming"
            confidence = 0.9 if is_trusted else 0.7
        
        else:
            # Neutral/unclear
            category = "neutral"
            confidence = 0.5
        
        return {
            "category": category,
            "similarity": similarity,
            "confidence": confidence,
            "is_trusted_source": is_trusted,
            "debunking_signals": debunking_count,
            "confirmation_signals": confirmation_count,
            "article": article
        }
    
    def _make_verification_decision(
        self,
        claim: str,
        confirming: List[Dict],
        debunking: List[Dict],
        neutral: List[Dict],
        total_articles: int
    ) -> Dict:
        """
        Make final verification decision based on article analysis
        """
        # Count trusted sources
        trusted_confirming = sum(
            1 for a in confirming 
            if a["is_trusted_source"]
        )
        
        trusted_debunking = sum(
            1 for a in debunking 
            if a["is_trusted_source"]
        )
        
        # DECISION LOGIC
        
        # If 2+ trusted sources are DEBUNKING → FAKE
        if trusted_debunking >= 2:
            return {
                "status": "debunked",
                "verdict": "FAKE",
                "confidence": 0.95,
                "message": f"This claim has been debunked by {trusted_debunking} trusted sources",
                "evidence": {
                    "debunking_articles": len(debunking),
                    "trusted_debunking": trusted_debunking,
                    "confirming_articles": len(confirming),
                    "articles_analyzed": total_articles
                },
                "recommendation": "⚠️ WARNING: This claim has been debunked by fact-checkers. Do NOT share.",
                "debunking_sources": [
                    {
                        "outlet": a["article"]["outlet"],
                        "title": a["article"]["title"],
                        "url": a["article"]["url"]
                    }
                    for a in debunking[:3]
                ]
            }
        
        # If ANY sources are debunking (even 1) → DISPUTED
        elif len(debunking) > 0:
            return {
                "status": "disputed",
                "verdict": "DISPUTED",
                "confidence": 0.7,
                "message": f"This claim is disputed. Found {len(debunking)} articles debunking it vs {len(confirming)} confirming",
                "evidence": {
                    "debunking_articles": len(debunking),
                    "confirming_articles": len(confirming),
                    "articles_analyzed": total_articles
                },
                "recommendation": "Conflicting information found. Verify with official sources before sharing."
            }
        
        # If 2+ trusted sources are CONFIRMING and NO debunking → VERIFIED
        elif trusted_confirming >= 2 and len(debunking) == 0:
            return {
                "status": "verified",
                "verdict": "VERIFIED",
                "confidence": 0.9,
                "message": f"Confirmed by {trusted_confirming} trusted news sources",
                "evidence": {
                    "confirming_articles": len(confirming),
                    "trusted_confirming": trusted_confirming,
                    "articles_analyzed": total_articles
                },
                "recommendation": "This claim is verified by trusted sources. Safe to share.",
                "confirming_sources": [
                    {
                        "outlet": a["article"]["outlet"],
                        "title": a["article"]["title"],
                        "url": a["article"]["url"]
                    }
                    for a in confirming[:3]
                ]
            }
        
        # If 1 trusted source confirming → PARTIALLY VERIFIED
        elif trusted_confirming == 1:
            return {
                "status": "partially_verified",
                "verdict": "PARTIALLY_VERIFIED",
                "confidence": 0.6,
                "message": "Found in 1 trusted source",
                "evidence": {
                    "confirming_articles": len(confirming),
                    "articles_analyzed": total_articles
                },
                "recommendation": "Claim found in one source. Wait for additional confirmation before sharing."
            }
        
        # Default: UNCERTAIN
        else:
            return {
                "status": "uncertain",
                "verdict": "UNVERIFIED",
                "confidence": 0.3,
                "message": f"No clear confirmation or debunking found ({total_articles} articles analyzed)",
                "evidence": {
                    "neutral_articles": len(neutral),
                    "articles_analyzed": total_articles
                },
                "recommendation": "Cannot verify this claim. Treat with skepticism until confirmed by trusted sources."
            }


# ========== Integration Function ==========
def verify_with_smart_analysis(
    claim: str,
    celebrity: str,
    news_aggregator,
    max_articles: int = 20
) -> Dict:
    """
    Verify claim using smart context-aware analysis
    
    Args:
        claim: The claim to verify
        celebrity: Celebrity name
        news_aggregator: NewsAggregator instance
        max_articles: Max articles to analyze
    
    Returns:
        Smart verification result
    """
    # Get articles
    articles = news_aggregator.search_news(
        query=f"{celebrity} {claim}",
        max_results=max_articles
    )
    
    # Analyze with context understanding
    verifier = SmartNewsVerification()
    result = verifier.verify_claim_with_context(
        claim=claim,
        articles=articles
    )
    
    return result


# ========== Test ==========
if __name__ == "__main__":
    print("=" * 70)
    print("Smart News Verification Test")
    print("=" * 70)
    
    # Test with fake claim
    test_articles = [
        {
            "title": "Fake Times Now Graphic About PM Modi Announcing Retirement Goes Viral as Real",
            "description": "A fake graphic has been debunked by fact-checkers",
            "outlet": "The Quint",
            "url": "https://example.com/1"
        },
        {
            "title": "'I never said 75': Mohan Bhagwat quashes retirement rumours",
            "description": "RSS chief denies retirement rumors",
            "outlet": "The Economic Times",
            "url": "https://example.com/2"
        }
    ]
    
    verifier = SmartNewsVerification()
    result = verifier.verify_claim_with_context(
        claim="Modi announced retirement",
        articles=test_articles
    )
    
    print(f"\n✅ Verdict: {result['verdict']}")
    print(f"📊 Confidence: {result['confidence']:.0%}")
    print(f"💬 Message: {result['message']}")
    print(f"💡 Recommendation: {result['recommendation']}")
    
    print("\n" + "=" * 70)
    print("✅ Test complete")
    print("=" * 70)
