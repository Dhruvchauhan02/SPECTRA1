# ai_models/fake_news_detection/social_media_monitor.py
"""
Social Media Monitoring Module for SPECTRA-AI
Monitors Twitter/X, Instagram, Facebook for viral content about celebrities
"""

import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("spectra.social_monitor")


class SocialMediaMonitor:
    """
    Monitor social media platforms for viral content
    
    Supports:
    - Twitter/X API v2
    - Instagram Graph API
    - Facebook Graph API
    """
    
    def __init__(
        self,
        twitter_bearer_token: Optional[str] = None,
        instagram_access_token: Optional[str] = None,
        facebook_access_token: Optional[str] = None
    ):
        """
        Initialize social media monitor
        
        Args:
            twitter_bearer_token: Twitter/X API v2 Bearer Token
            instagram_access_token: Instagram Graph API access token
            facebook_access_token: Facebook Graph API access token
        """
        self.twitter_token = twitter_bearer_token
        self.instagram_token = instagram_access_token
        self.facebook_token = facebook_access_token
        
        # API endpoints
        self.twitter_url = "https://api.twitter.com/2/tweets/search/recent"
        self.instagram_url = "https://graph.instagram.com"
        self.facebook_url = "https://graph.facebook.com/v18.0"
        
        logger.info("Social Media Monitor initialized")
    
    def search_twitter(
        self,
        query: str,
        max_results: int = 10,
        verified_only: bool = False
    ) -> List[Dict]:
        """
        Search Twitter/X for posts about a topic
        
        Args:
            query: Search query (e.g., "Elon Musk")
            max_results: Maximum number of tweets to return
            verified_only: Only return tweets from verified accounts
        
        Returns:
            List of tweet data
        """
        if not self.twitter_token:
            logger.warning("Twitter API token not configured")
            return []
        
        try:
            # Build query
            search_query = query
            if verified_only:
                search_query += " is:verified"
            
            # Add filters for viral content
            search_query += " -is:retweet min_retweets:100"
            
            headers = {"Authorization": f"Bearer {self.twitter_token}"}
            
            params = {
                "query": search_query,
                "max_results": min(max_results, 100),
                "tweet.fields": "created_at,public_metrics,author_id,entities",
                "user.fields": "verified,username,name",
                "expansions": "author_id"
            }
            
            response = requests.get(
                self.twitter_url,
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Twitter API error: {response.status_code}")
                return []
            
            data = response.json()
            
            # Parse results
            tweets = []
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            
            for tweet in data.get("data", []):
                author = users.get(tweet["author_id"], {})
                
                tweets.append({
                    "platform": "twitter",
                    "id": tweet["id"],
                    "text": tweet["text"],
                    "author": {
                        "id": author.get("id"),
                        "username": author.get("username"),
                        "name": author.get("name"),
                        "verified": author.get("verified", False)
                    },
                    "metrics": {
                        "retweets": tweet.get("public_metrics", {}).get("retweet_count", 0),
                        "likes": tweet.get("public_metrics", {}).get("like_count", 0),
                        "replies": tweet.get("public_metrics", {}).get("reply_count", 0)
                    },
                    "created_at": tweet.get("created_at"),
                    "url": f"https://twitter.com/i/web/status/{tweet['id']}"
                })
            
            logger.info(f"Found {len(tweets)} tweets for query: {query}")
            return tweets
        
        except Exception as e:
            logger.error(f"Twitter search failed: {e}")
            return []
    
    def get_verified_account_posts(
        self,
        username: str,
        platform: str = "twitter",
        max_results: int = 10
    ) -> List[Dict]:
        """
        Get recent posts from a verified account (official source)
        
        Args:
            username: Account username
            platform: Platform name ("twitter", "instagram", "facebook")
            max_results: Maximum posts to retrieve
        
        Returns:
            List of posts from verified account
        """
        if platform == "twitter":
            return self._get_twitter_user_posts(username, max_results)
        elif platform == "instagram":
            return self._get_instagram_posts(username, max_results)
        elif platform == "facebook":
            return self._get_facebook_posts(username, max_results)
        else:
            logger.warning(f"Unsupported platform: {platform}")
            return []
    
    def _get_twitter_user_posts(self, username: str, max_results: int) -> List[Dict]:
        """Get posts from specific Twitter user"""
        if not self.twitter_token:
            return []
        
        try:
            # First, get user ID
            user_url = f"https://api.twitter.com/2/users/by/username/{username}"
            headers = {"Authorization": f"Bearer {self.twitter_token}"}
            
            user_response = requests.get(user_url, headers=headers, timeout=10)
            if user_response.status_code != 200:
                logger.error(f"Failed to get user ID for {username}")
                return []
            
            user_id = user_response.json()["data"]["id"]
            
            # Get user's tweets
            tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            params = {
                "max_results": min(max_results, 100),
                "tweet.fields": "created_at,public_metrics"
            }
            
            tweets_response = requests.get(
                tweets_url,
                headers=headers,
                params=params,
                timeout=10
            )
            
            if tweets_response.status_code != 200:
                return []
            
            tweets_data = tweets_response.json()
            
            posts = []
            for tweet in tweets_data.get("data", []):
                posts.append({
                    "platform": "twitter",
                    "text": tweet["text"],
                    "created_at": tweet["created_at"],
                    "metrics": tweet.get("public_metrics", {}),
                    "url": f"https://twitter.com/{username}/status/{tweet['id']}"
                })
            
            return posts
        
        except Exception as e:
            logger.error(f"Failed to get Twitter posts for {username}: {e}")
            return []
    
    def _get_instagram_posts(self, username: str, max_results: int) -> List[Dict]:
        """Get posts from Instagram (placeholder)"""
        logger.warning("Instagram API integration not yet implemented")
        return []
    
    def _get_facebook_posts(self, username: str, max_results: int) -> List[Dict]:
        """Get posts from Facebook (placeholder)"""
        logger.warning("Facebook API integration not yet implemented")
        return []
    
    def detect_viral_content(
        self,
        celebrity_name: str,
        platforms: List[str] = ["twitter"],
        viral_threshold: int = 1000
    ) -> List[Dict]:
        """
        Detect viral content about a celebrity
        
        Args:
            celebrity_name: Name of celebrity/personality
            platforms: List of platforms to check
            viral_threshold: Minimum engagement to consider "viral"
        
        Returns:
            List of viral posts
        """
        all_viral = []
        
        for platform in platforms:
            if platform == "twitter":
                posts = self.search_twitter(
                    query=celebrity_name,
                    max_results=50
                )
                
                # Filter for viral content
                viral = [
                    p for p in posts
                    if (p["metrics"]["retweets"] + p["metrics"]["likes"]) >= viral_threshold
                ]
                
                all_viral.extend(viral)
        
        # Sort by engagement
        all_viral.sort(
            key=lambda x: x["metrics"]["retweets"] + x["metrics"]["likes"],
            reverse=True
        )
        
        logger.info(
            f"Found {len(all_viral)} viral posts about {celebrity_name}"
        )
        
        return all_viral


# ========== Testing ==========
if __name__ == "__main__":
    print("=" * 70)
    print("Social Media Monitor Test")
    print("=" * 70)
    
    import os
    
    # Get API key from environment
    twitter_token = os.getenv("TWITTER_BEARER_TOKEN")
    
    if not twitter_token:
        print("\n⚠️  No Twitter API token found")
        print("Set environment variable: TWITTER_BEARER_TOKEN")
        print("\nGet token from: https://developer.twitter.com/")
        print("\n✅ Module loaded successfully (no live test)")
    else:
        # Test with real API
        monitor = SocialMediaMonitor(twitter_bearer_token=twitter_token)
        
        # Search for posts about a celebrity
        print("\n🔍 Searching for posts about 'Elon Musk'...")
        tweets = monitor.search_twitter("Elon Musk", max_results=5)
        
        if tweets:
            print(f"\n📊 Found {len(tweets)} tweets:\n")
            for i, tweet in enumerate(tweets, 1):
                print(f"{i}. @{tweet['author']['username']}")
                print(f"   {tweet['text'][:100]}...")
                print(f"   💚 {tweet['metrics']['likes']} | 🔄 {tweet['metrics']['retweets']}")
                print(f"   ✓ Verified: {tweet['author']['verified']}")
                print()
        else:
            print("No tweets found")
    
    print("=" * 70)
    print("✅ Test complete")
    print("=" * 70)
