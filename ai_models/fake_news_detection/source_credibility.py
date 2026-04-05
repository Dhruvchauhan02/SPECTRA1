# ai_models/fake_news_detection/source_credibility.py
"""
Source Credibility Checker for Fake News Detection
Evaluates domain reputation and source reliability
"""

from typing import Dict
from urllib.parse import urlparse
import logging

logger = logging.getLogger("spectra.fakenews.source")


class SourceCredibilityChecker:
    """
    Check source credibility based on domain reputation
    
    Uses curated lists of:
    - High-credibility sources (news organizations, fact-checkers)
    - Low-credibility sources (known misinformation sites)
    - Medium-credibility sources (blogs, social media)
    """
    
    def __init__(self):
        # High credibility sources (mainstream news, fact-checkers)
        self.high_credibility = {
            # News agencies
            "reuters.com", "apnews.com", "bloomberg.com",
            
            # Major newspapers
            "nytimes.com", "washingtonpost.com", "wsj.com",
            "ft.com", "theguardian.com", "bbc.com", "bbc.co.uk",
            
            # Broadcast news
            "cnn.com", "nbcnews.com", "abcnews.go.com",
            "cbsnews.com", "pbs.org", "npr.org",
            
            # Fact-checkers
            "snopes.com", "factcheck.org", "politifact.com",
            "fullfact.org", "africacheck.org",
            
            # Government/Official
            "gov.uk", "gov", "europa.eu", "who.int",
            "cdc.gov", "nih.gov",
            
            # Academic
            "edu", "ac.uk", "scholar.google.com",
            "nature.com", "science.org", "sciencedirect.com"
        }
        
        # Low credibility sources (known misinformation)
        self.low_credibility = {
            "beforeitsnews.com", "yournewswire.com",
            "naturalnews.com", "infowars.com",
            "globalresearch.ca", "veteranstoday.com",
            "counterpunch.org", "thelastamericanvagabond.com",
            "collective-evolution.com", "awarenessact.com",
            "humansarefree.com", "davidicke.com",
            "neonnettle.com", "newspunch.com",
            "dailystormer.com", "theduran.com"
        }
        
        # Medium credibility (blogs, opinion sites)
        self.medium_credibility = {
            "medium.com", "substack.com", "wordpress.com",
            "blogspot.com", "tumblr.com"
        }
        
        # Social media platforms
        self.social_media = {
            "facebook.com", "twitter.com", "x.com",
            "instagram.com", "tiktok.com", "reddit.com",
            "youtube.com", "linkedin.com"
        }
    
    def check(self, url: str) -> Dict:
        """
        Check source credibility
        
        Args:
            url: Source URL to check
        
        Returns:
            Dict with:
                - domain: Extracted domain
                - credibility: HIGH, MEDIUM, LOW, or UNKNOWN
                - score: Credibility score (0-1, lower = more suspicious)
                - is_https: Whether URL uses HTTPS
                - category: Source category
        """
        # Parse URL
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "").lower()
            is_https = url.startswith("https://")
        except Exception as e:
            logger.warning(f"Failed to parse URL {url}: {e}")
            return {
                "domain": "unknown",
                "credibility": "UNKNOWN",
                "score": 0.5,
                "is_https": False,
                "category": "unknown"
            }
        
        # Check domain credibility
        credibility, score, category = self._classify_domain(domain)
        
        # Adjust score based on HTTPS
        if not is_https and credibility != "HIGH":
            score += 0.1  # Penalize non-HTTPS (higher score = more suspicious)
            score = min(score, 1.0)
        
        result = {
            "domain": domain,
            "credibility": credibility,
            "score": score,
            "is_https": is_https,
            "category": category
        }
        
        logger.debug(
            f"Source check: {domain} → {credibility} "
            f"(score: {score:.2f}, HTTPS: {is_https})"
        )
        
        return result
    
    def _classify_domain(self, domain: str) -> tuple:
        """
        Classify domain credibility
        
        Args:
            domain: Domain name
        
        Returns:
            Tuple of (credibility_level, score, category)
        """
        # Check exact match
        if domain in self.high_credibility:
            return ("HIGH", 0.1, "news_or_academic")
        
        if domain in self.low_credibility:
            return ("LOW", 0.9, "known_misinformation")
        
        if domain in self.medium_credibility:
            return ("MEDIUM", 0.5, "blog_platform")
        
        if domain in self.social_media:
            return ("MEDIUM", 0.6, "social_media")
        
        # Check TLD patterns
        tld = domain.split(".")[-1]
        
        # Educational
        if tld == "edu" or domain.endswith(".ac.uk"):
            return ("HIGH", 0.2, "academic")
        
        # Government
        if tld == "gov" or domain.endswith(".gov.uk"):
            return ("HIGH", 0.2, "government")
        
        # Check partial matches (e.g., subdomain of known source)
        for known_domain in self.high_credibility:
            if domain.endswith("." + known_domain):
                return ("HIGH", 0.2, "news_subdomain")
        
        for known_domain in self.low_credibility:
            if domain.endswith("." + known_domain):
                return ("LOW", 0.85, "misinformation_subdomain")
        
        # Unknown domain
        return ("UNKNOWN", 0.5, "unknown")
    
    def add_high_credibility(self, domain: str):
        """Add domain to high credibility list"""
        self.high_credibility.add(domain.lower().replace("www.", ""))
        logger.info(f"Added {domain} to high credibility list")
    
    def add_low_credibility(self, domain: str):
        """Add domain to low credibility list"""
        self.low_credibility.add(domain.lower().replace("www.", ""))
        logger.info(f"Added {domain} to low credibility list")
    
    def get_stats(self) -> Dict:
        """Get statistics about credibility lists"""
        return {
            "high_credibility_count": len(self.high_credibility),
            "low_credibility_count": len(self.low_credibility),
            "medium_credibility_count": len(self.medium_credibility),
            "social_media_count": len(self.social_media)
        }


# ========== Testing ==========
if __name__ == "__main__":
    print("=" * 70)
    print("Source Credibility Checker Test")
    print("=" * 70)
    
    checker = SourceCredibilityChecker()
    
    # Test cases
    test_urls = [
        ("https://www.nytimes.com/article", "High credibility news"),
        ("https://www.reuters.com/world/article", "High credibility news agency"),
        ("http://naturalnews.com/fake-article", "Low credibility site"),
        ("https://medium.com/@user/article", "Medium credibility blog"),
        ("https://facebook.com/post/123", "Social media"),
        ("https://www.cdc.gov/health/info", "Government source"),
        ("https://mit.edu/research/paper", "Academic source"),
        ("http://unknown-blog.net/article", "Unknown source"),
    ]
    
    print("\n📊 Testing various sources:")
    print("=" * 70)
    
    for url, description in test_urls:
        result = checker.check(url)
        
        print(f"\n🔗 {description}")
        print(f"   URL: {url}")
        print(f"   Domain: {result['domain']}")
        print(f"   Credibility: {result['credibility']}")
        print(f"   Score: {result['score']:.2f}")
        print(f"   Category: {result['category']}")
        print(f"   HTTPS: {'✓' if result['is_https'] else '✗'}")
    
    # Stats
    print("\n" + "=" * 70)
    print("📈 Database Statistics")
    print("=" * 70)
    
    stats = checker.get_stats()
    print(f"  High Credibility Sources: {stats['high_credibility_count']}")
    print(f"  Low Credibility Sources: {stats['low_credibility_count']}")
    print(f"  Medium Credibility Sources: {stats['medium_credibility_count']}")
    print(f"  Social Media Platforms: {stats['social_media_count']}")
    
    print("\n" + "=" * 70)
    print("✅ All tests complete")
    print("=" * 70)
