# ai_models/fake_news_detection/fusion.py
"""
Signal Fusion Module for Fake News Detection
Combines linguistic, source, and verification signals into final verdict
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger("spectra.fakenews.fusion")


class FakeNewsFusion:
    """
    Fuse multiple detection signals into final verdict
    
    Signal weights:
    - Linguistic: 40% (manipulation patterns, emotion, complexity)
    - Source: 30% (domain credibility)
    - Verification: 30% (claim fact-checking)
    """
    
    def __init__(
        self,
        w_linguistic: float = 0.40,
        w_source: float = 0.30,
        w_verification: float = 0.30,
        threshold_fake: float = 0.70,
        threshold_real: float = 0.30
    ):
        """
        Initialize fusion system
        
        Args:
            w_linguistic: Weight for linguistic signals
            w_source: Weight for source credibility
            w_verification: Weight for claim verification
            threshold_fake: Threshold for LIKELY_FAKE verdict
            threshold_real: Threshold for LIKELY_REAL verdict
        """
        # Validate weights
        total = w_linguistic + w_source + w_verification
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        
        self.w_linguistic = w_linguistic
        self.w_source = w_source
        self.w_verification = w_verification
        
        self.threshold_fake = threshold_fake
        self.threshold_real = threshold_real
        
        logger.debug(
            f"Fusion weights: ling={w_linguistic:.2f}, "
            f"source={w_source:.2f}, verify={w_verification:.2f}"
        )
    
    def fuse(
        self,
        linguistic: Dict,
        source: Optional[Dict],
        verification: Optional[Dict],
        num_claims: int = 0
    ) -> Dict:
        """
        Fuse all signals into final verdict
        
        Args:
            linguistic: Linguistic analysis results
            source: Source credibility results (optional)
            verification: Claim verification results (optional)
            num_claims: Number of claims extracted
        
        Returns:
            Dict with:
                - label: LIKELY_FAKE, LIKELY_REAL, or UNCERTAIN
                - final_score: Aggregated score (0-1, higher = more likely fake)
                - confidence: Confidence in verdict (0-1)
                - breakdown: Score breakdown by signal type
        """
        # 1. Linguistic score (0-1, higher = more suspicious)
        ling_score = self._compute_linguistic_score(linguistic)
        
        # 2. Source score (0-1, higher = more suspicious)
        if source:
            source_score = source["score"]  # Already 0-1 from source checker
        else:
            source_score = 0.5  # Unknown
        
        # 3. Verification score (0-1, higher = more suspicious)
        if verification:
            verify_score = verification["refute_ratio"]
        else:
            verify_score = 0.5  # Unknown
        
        # 4. Weighted fusion
        # Adjust weights if some signals are missing
        actual_w_ling = self.w_linguistic
        actual_w_source = self.w_source if source else 0
        actual_w_verify = self.w_verification if verification else 0
        
        # Renormalize weights
        total_weight = actual_w_ling + actual_w_source + actual_w_verify
        if total_weight > 0:
            actual_w_ling /= total_weight
            actual_w_source /= total_weight
            actual_w_verify /= total_weight
        
        final_score = (
            actual_w_ling * ling_score +
            actual_w_source * source_score +
            actual_w_verify * verify_score
        )
        
        # 5. Determine verdict
        if final_score >= self.threshold_fake:
            label = "LIKELY_FAKE"
            confidence = (final_score - self.threshold_fake) / (1.0 - self.threshold_fake)
        elif final_score <= self.threshold_real:
            label = "LIKELY_REAL"
            confidence = (self.threshold_real - final_score) / self.threshold_real
        else:
            label = "UNCERTAIN"
            # Confidence decreases as we move toward middle
            distance_from_middle = abs(final_score - 0.5)
            confidence = distance_from_middle / 0.2  # 0.5 ± 0.2 is uncertainty zone
        
        confidence = min(max(confidence, 0.0), 1.0)
        
        result = {
            "label": label,
            "final_score": final_score,
            "confidence": confidence,
            "breakdown": {
                "linguistic": ling_score,
                "source": source_score,
                "verification": verify_score
            },
            "weights_used": {
                "linguistic": actual_w_ling,
                "source": actual_w_source,
                "verification": actual_w_verify
            }
        }
        
        logger.info(
            f"Fusion result: {label} (score={final_score:.3f}, "
            f"conf={confidence:.2%})"
        )
        
        return result
    
    def _compute_linguistic_score(self, linguistic: Dict) -> float:
        """
        Compute linguistic suspicion score
        
        Args:
            linguistic: Linguistic analysis results
        
        Returns:
            Score from 0 (credible) to 1 (suspicious)
        """
        score = 0.0
        
        # Clickbait (strong indicator)
        if linguistic.get("has_clickbait", False):
            score += 0.25
        
        # Additional clickbait count
        clickbait_count = linguistic.get("clickbait_count", 0)
        score += min(clickbait_count * 0.05, 0.15)
        
        # Emotional manipulation
        if linguistic.get("high_emotion", False):
            score += 0.20
        
        # Excessive capitalization
        if linguistic.get("excessive_caps", False):
            score += 0.15
        
        # Sensationalism (exclamations)
        if linguistic.get("high_sensationalism", False):
            score += 0.15
        
        # Low complexity (overly simple writing)
        if linguistic.get("low_complexity", False):
            score += 0.10
        
        # High hedging (vague language)
        if linguistic.get("high_hedging", False):
            score += 0.10
        
        # Extreme sentiment
        sentiment = abs(linguistic.get("sentiment_polarity", 0))
        if sentiment > 0.7:
            score += 0.15
        
        # Authority appeals without proper attribution
        authority_count = linguistic.get("authority_appeals", 0)
        score += min(authority_count * 0.05, 0.15)
        
        # Cap at 1.0
        score = min(score, 1.0)
        
        logger.debug(f"Linguistic score: {score:.3f}")
        
        return score


# ========== Testing ==========
if __name__ == "__main__":
    print("=" * 70)
    print("Fake News Fusion Test")
    print("=" * 70)
    
    fusion = FakeNewsFusion()
    
    # Test 1: Highly suspicious content
    print("\n📰 Test 1: Highly Suspicious Content")
    print("-" * 70)
    
    linguistic_suspicious = {
        "has_clickbait": True,
        "clickbait_count": 3,
        "high_emotion": True,
        "excessive_caps": True,
        "high_sensationalism": True,
        "low_complexity": True,
        "sentiment_polarity": 0.9,
        "authority_appeals": 5
    }
    
    source_suspicious = {
        "domain": "fake-news.com",
        "credibility": "LOW",
        "score": 0.9
    }
    
    result = fusion.fuse(
        linguistic=linguistic_suspicious,
        source=source_suspicious,
        verification=None
    )
    
    print(f"Verdict: {result['label']}")
    print(f"Score: {result['final_score']:.3f}")
    print(f"Confidence: {result['confidence']:.0%}")
    print(f"\nBreakdown:")
    for signal, score in result['breakdown'].items():
        print(f"  {signal.capitalize()}: {score:.3f}")
    
    # Test 2: Credible content
    print("\n" + "=" * 70)
    print("📰 Test 2: Credible Content")
    print("-" * 70)
    
    linguistic_credible = {
        "has_clickbait": False,
        "clickbait_count": 0,
        "high_emotion": False,
        "excessive_caps": False,
        "high_sensationalism": False,
        "low_complexity": False,
        "sentiment_polarity": 0.1,
        "authority_appeals": 1
    }
    
    source_credible = {
        "domain": "reuters.com",
        "credibility": "HIGH",
        "score": 0.1
    }
    
    result = fusion.fuse(
        linguistic=linguistic_credible,
        source=source_credible,
        verification=None
    )
    
    print(f"Verdict: {result['label']}")
    print(f"Score: {result['final_score']:.3f}")
    print(f"Confidence: {result['confidence']:.0%}")
    print(f"\nBreakdown:")
    for signal, score in result['breakdown'].items():
        print(f"  {signal.capitalize()}: {score:.3f}")
    
    # Test 3: Uncertain content
    print("\n" + "=" * 70)
    print("📰 Test 3: Uncertain Content")
    print("-" * 70)
    
    linguistic_mixed = {
        "has_clickbait": True,
        "clickbait_count": 1,
        "high_emotion": False,
        "excessive_caps": False,
        "high_sensationalism": False,
        "low_complexity": False,
        "sentiment_polarity": 0.3
    }
    
    source_unknown = {
        "domain": "unknown-blog.com",
        "credibility": "UNKNOWN",
        "score": 0.5
    }
    
    result = fusion.fuse(
        linguistic=linguistic_mixed,
        source=source_unknown,
        verification=None
    )
    
    print(f"Verdict: {result['label']}")
    print(f"Score: {result['final_score']:.3f}")
    print(f"Confidence: {result['confidence']:.0%}")
    print(f"\nBreakdown:")
    for signal, score in result['breakdown'].items():
        print(f"  {signal.capitalize()}: {score:.3f}")
    
    print("\n" + "=" * 70)
    print("✅ All tests complete")
    print("=" * 70)
