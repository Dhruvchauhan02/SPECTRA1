# ai_models/fake_news_detection/evidence_retrieval.py
"""
Evidence Retrieval Module for SPECTRA-AI
Supports Bing, Google Custom Search, and DuckDuckGo.
"""

import os
import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger("spectra.fakenews.evidence")


class EvidenceRetriever:
    """
    Retrieve evidence from web search.

    Supported API types: 'bing', 'google', 'duckduckgo'
    """

    ENDPOINTS = {
        "bing":   "https://api.bing.microsoft.com/v7.0/search",
        "google": "https://www.googleapis.com/customsearch/v1",
    }

    def __init__(
        self,
        api_key: str,
        api_type: str = "google",
        cache_enabled: bool = True,
        google_cx: Optional[str] = None,
    ):
        self.api_key       = api_key
        self.api_type      = api_type.lower()
        self.cache_enabled = cache_enabled
        self.cache: Dict   = {} if cache_enabled else {}
        # Google Custom Search Engine ID — read from arg or env
        self.google_cx     = google_cx or os.getenv("GOOGLE_CX", "")

        if self.api_type not in self.ENDPOINTS and self.api_type != "duckduckgo":
            raise ValueError(
                f"Unsupported API type: {api_type}. "
                f"Supported: bing, google, duckduckgo"
            )
        logger.info(f"EvidenceRetriever initialized ({api_type})")

    def retrieve(self, query: str, max_results: int = 5, language: str = "en") -> List[Dict]:
        cache_key = f"{query}:{max_results}:{language}"
        if self.cache_enabled and cache_key in self.cache:
            return self.cache[cache_key]

        if self.api_type == "bing":
            results = self._search_bing(query, max_results, language)
        elif self.api_type == "google":
            results = self._search_google(query, max_results, language)
        elif self.api_type == "duckduckgo":
            results = self._search_duckduckgo(query, max_results)
        else:
            return []

        if self.cache_enabled:
            self.cache[cache_key] = results

        logger.info(f"Retrieved {len(results)} results for: {query[:60]}")
        return results

    def _search_bing(self, query: str, max_results: int, language: str) -> List[Dict]:
        try:
            resp = requests.get(
                self.ENDPOINTS["bing"],
                headers={"Ocp-Apim-Subscription-Key": self.api_key},
                params={
                    "q":               query,
                    "count":           max_results,
                    "mkt":             f"{language}-US",
                    "textDecorations": False,
                    "textFormat":      "Raw",
                },
                timeout=10
            )
            if resp.status_code != 200:
                logger.error(f"Bing error: {resp.status_code}")
                return []
            evidence = []
            for item in resp.json().get("webPages", {}).get("value", []):
                evidence.append({
                    "title":   item.get("name", ""),
                    "snippet": item.get("snippet", ""),
                    "url":     item.get("url", ""),
                    "date":    item.get("datePublished", ""),
                    "source":  "bing",
                })
            return evidence
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            return []

    def _search_google(self, query: str, max_results: int, language: str) -> List[Dict]:
        if not self.google_cx:
            logger.warning("GOOGLE_CX not set — skipping Google Custom Search")
            return []
        try:
            resp = requests.get(
                self.ENDPOINTS["google"],
                params={
                    "key": self.api_key,
                    "cx":  self.google_cx,
                    "q":   query,
                    "num": min(max_results, 10),
                    "lr":  f"lang_{language}",
                },
                timeout=10
            )
            if resp.status_code != 200:
                logger.error(f"Google CSE error: {resp.status_code} — {resp.text[:200]}")
                return []
            evidence = []
            for item in resp.json().get("items", []):
                evidence.append({
                    "title":   item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url":     item.get("link", ""),
                    "date":    "",
                    "source":  "google",
                })
            return evidence
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return []

    def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict]:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "title":   r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url":     r.get("href", ""),
                    "date":    "",
                    "source":  "duckduckgo",
                }
                for r in results
            ]
        except ImportError:
            logger.warning("duckduckgo_search not installed. pip install duckduckgo-search")
            return []
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []

    def clear_cache(self):
        self.cache.clear()
        logger.info("Evidence cache cleared")