# ai_models/fake_news_detection/news_aggregator_improved.py
"""
Improved News Aggregation with Multiple Free Sources
"""

import requests
import logging
import feedparser
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("spectra.news_aggregator")


class ImprovedNewsAggregator:
    """
    Enhanced news aggregator with multiple FREE sources
    """
    
    def __init__(
        self,
        newsapi_key: Optional[str] = None,
        gnews_key: Optional[str] = None
    ):
        self.newsapi_key = newsapi_key
        self.gnews_key = gnews_key
        
        self.newsapi_url = "https://newsapi.org/v2"
        self.gnews_url = "https://gnews.io/api/v4"
        
        logger.info("Improved News Aggregator initialized")
    
    def search_news(
        self,
        query: str,
        max_results: int = 20,
        use_all_sources: bool = True
    ) -> List[Dict]:
        """
        Search multiple sources and combine results
        
        Args:
            query: Search query
            max_results: Max results per source
            use_all_sources: Use all available sources
        
        Returns:
            Combined results from all sources
        """
        all_articles = []
        
        # 1. Google News RSS (FREE - ALWAYS AVAILABLE)
        logger.info("Searching Google News RSS...")
        google_articles = self._search_google_news_rss(query, max_results)
        all_articles.extend(google_articles)
        logger.info(f"Found {len(google_articles)} articles from Google News")
        
        # 2. NewsAPI (if key available)
        if self.newsapi_key:
            logger.info("Searching NewsAPI...")
            newsapi_articles = self._search_newsapi(query, max_results)
            all_articles.extend(newsapi_articles)
            logger.info(f"Found {len(newsapi_articles)} articles from NewsAPI")
        
        # 3. GNews (if key available)
        if self.gnews_key:
            logger.info("Searching GNews...")
            gnews_articles = self._search_gnews(query, max_results)
            all_articles.extend(gnews_articles)
            logger.info(f"Found {len(gnews_articles)} articles from GNews")
        
        # Deduplicate by URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        logger.info(f"Total unique articles: {len(unique_articles)}")
        return unique_articles
    
    def _search_google_news_rss(self, query: str, max_results: int) -> List[Dict]:
        """
        Search Google News via RSS (FREE - no API key!)
        
        This is the best free source - no limits, all time coverage
        """
        try:
            # Build Google News RSS URL
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en&gl=US&ceid=US:en"
            
            # Parse RSS feed
            feed = feedparser.parse(url)
            
            articles = []
            for entry in feed.entries[:max_results]:
                # Extract source from title if available
                source_name = "Google News"
                if hasattr(entry, 'source'):
                    source_name = entry.source.get('title', 'Google News')
                
                articles.append({
                    "source": "google_news_rss",
                    "outlet": source_name,
                    "title": entry.title,
                    "description": entry.get("summary", ""),
                    "url": entry.link,
                    "published_at": entry.get("published", ""),
                    "content": entry.get("summary", "")
                })
            
            return articles
        
        except Exception as e:
            logger.error(f"Google News RSS failed: {e}")
            return []
    
    def _search_newsapi(self, query: str, max_results: int) -> List[Dict]:
        """Search using NewsAPI"""
        try:
            from_date = datetime.now() - timedelta(days=30)
            
            params = {
                "q": query,
                "from": from_date.strftime("%Y-%m-%d"),
                "sortBy": "relevancy",
                "language": "en",
                "pageSize": min(max_results, 100),
                "apiKey": self.newsapi_key
            }
            
            url = f"{self.newsapi_url}/everything"
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"NewsAPI error: {response.status_code}")
                return []
            
            data = response.json()
            
            articles = []
            for article in data.get("articles", []):
                articles.append({
                    "source": "newsapi",
                    "outlet": article.get("source", {}).get("name"),
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "content": article.get("content"),
                    "url": article.get("url"),
                    "published_at": article.get("publishedAt"),
                    "author": article.get("author")
                })
            
            return articles
        
        except Exception as e:
            logger.error(f"NewsAPI search failed: {e}")
            return []
    
    def _search_gnews(self, query: str, max_results: int) -> List[Dict]:
        """Search using GNews API"""
        try:
            params = {
                "q": query,
                "token": self.gnews_key,
                "lang": "en",
                "max": min(max_results, 10)
            }
            
            url = f"{self.gnews_url}/search"
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"GNews error: {response.status_code}")
                return []
            
            data = response.json()
            
            articles = []
            for article in data.get("articles", []):
                articles.append({
                    "source": "gnews",
                    "outlet": article.get("source", {}).get("name"),
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "content": article.get("content"),
                    "url": article.get("url"),
                    "published_at": article.get("publishedAt")
                })
            
            return articles
        
        except Exception as e:
            logger.error(f"GNews search failed: {e}")
            return []
    
    def verify_claim_against_news(
        self,
        claim: str,
        celebrity_name: str,
        similarity_threshold: float = 0.3
    ) -> Dict:
        """
        IMPROVED verification with relaxed matching
        
        Args:
            claim: The claim to verify
            celebrity_name: Celebrity name
            similarity_threshold: Lower = more lenient (default 0.3)
        
        Returns:
            Verification result
        """
        # Get articles
        articles = self.search_news(
            query=f"{celebrity_name} {claim}",
            max_results=20
        )
        
        if not articles:
            return {
                "status": "no_evidence",
                "message": "No recent news found",
                "articles_checked": 0
            }
        
        # IMPROVED: Fuzzy matching instead of exact word matching
        claim_words = set(claim.lower().split())
        matching_articles = []
        
        for article in articles:
            title = (article.get("title") or "").lower()
            desc = (article.get("description") or "").lower()
            content = (article.get("content") or "").lower()
            
            # Combine all text
            article_text = f"{title} {desc} {content}"
            article_words = set(article_text.split())
            
            # Calculate word overlap
            common_words = claim_words & article_words
            if len(claim_words) > 0:
                similarity = len(common_words) / len(claim_words)
            else:
                similarity = 0
            
            # LOWERED THRESHOLD: 30% match instead of strict matching
            if similarity >= similarity_threshold:
                matching_articles.append({
                    "title": article["title"],
                    "url": article["url"],
                    "outlet": article["outlet"],
                    "published": article["published_at"],
                    "similarity": round(similarity, 2),
                    "source": article["source"]
                })
        
        # Sort by similarity
        matching_articles.sort(key=lambda x: x["similarity"], reverse=True)
        
        # IMPROVED: More lenient verification
        if len(matching_articles) >= 2:
            # Found in 2+ sources
            confidence = min(0.7 + (len(matching_articles) * 0.05), 0.95)
            return {
                "status": "verified",
                "message": f"Found in {len(matching_articles)} news sources",
                "articles_checked": len(articles),
                "matching_articles": matching_articles[:5],
                "confidence": confidence,
                "total_sources": len(set(a["source"] for a in matching_articles))
            }
        elif len(matching_articles) == 1:
            # Found in 1 source
            return {
                "status": "partially_verified",
                "message": "Found in 1 news source",
                "articles_checked": len(articles),
                "matching_articles": matching_articles,
                "confidence": 0.6
            }
        else:
            # Not found
            return {
                "status": "not_found",
                "message": f"No matching articles (checked {len(articles)} sources)",
                "articles_checked": len(articles),
                "confidence": 0.2
            }


# Test
if __name__ == "__main__":
    print("=" * 70)
    print("Improved News Aggregator Test")
    print("=" * 70)
    
    import os
    
    aggregator = ImprovedNewsAggregator(
        newsapi_key=os.getenv("NEWS_API_KEY")
    )
    
    # Test Google News RSS (always works - no API key needed)
    print("\n🔍 Testing Google News RSS (FREE)...")
    articles = aggregator.search_news("Elon Musk Tesla", max_results=5)
    
    print(f"\n📰 Found {len(articles)} articles:\n")
    for i, article in enumerate(articles[:5], 1):
        print(f"{i}. {article['title']}")
        print(f"   Source: {article['outlet']} ({article['source']})")
        print(f"   URL: {article['url'][:60]}...")
        print()
    
    # Test verification
    print("\n" + "=" * 70)
    print("Testing claim verification...")
    print("=" * 70)
    
    claim = "Elon Musk announces Tesla news"
    result = aggregator.verify_claim_against_news(claim, "Elon Musk")
    
    print(f"\nClaim: {claim}")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Confidence: {result.get('confidence', 0):.0%}")
    print(f"Articles checked: {result['articles_checked']}")
    
    if result.get('matching_articles'):
        print(f"\nMatching articles:")
        for i, art in enumerate(result['matching_articles'][:3], 1):
            print(f"  {i}. {art['title']}")
            print(f"     Similarity: {art['similarity']:.0%}")
    
    print("\n" + "=" * 70)
    print("✅ Test complete")
    print("=" * 70)
