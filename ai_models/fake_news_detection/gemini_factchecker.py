# ai_models/fake_news_detection/gemini_factchecker.py
"""
Gemini-Powered Fact Checker for SPECTRA-AI
Uses Google Gemini 2.0 Flash via HTTP (no SDK needed).
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional

logger = logging.getLogger("spectra.gemini_factchecker")


class GeminiFactChecker:
    """
    Uses Google Gemini to verdict a claim as:
      LIKELY_FAKE | UNCERTAIN | LIKELY_REAL
    """

    MODEL = "gemini-2.0-flash"
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    SYSTEM_PROMPT = """You are a professional fact-checker for SPECTRA-AI, a misinformation detection platform.

Your job: analyze a claim and decide if it is true, false, or uncertain — based ONLY on the news articles provided.

Rules:
- If credible sources (BBC, Reuters, AP, ESPN, NDTV, Times of India, etc.) confirm the claim -> LIKELY_REAL
- If articles debunk or contradict the claim -> LIKELY_FAKE
- If articles are unrelated or insufficient -> UNCERTAIN
- If the claim is clearly absurd with no coverage -> LIKELY_FAKE
- Do NOT use your own training knowledge - rely ONLY on the provided articles
- Be strict: a specific event claim needs specific evidence

Respond ONLY in this exact JSON format, no markdown, no extra text:
{
  "verdict": "LIKELY_FAKE",
  "confidence": 0.85,
  "reasoning": "one sentence explanation",
  "sources_used": 3
}"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")
        logger.info(f"GeminiFactChecker initialized (model: {self.MODEL})")

    def check(self, claim: str, articles: List[Dict]) -> Dict:
        """
        Fact-check a claim using Gemini with news articles as context.

        Args:
            claim: The claim to verify
            articles: List of dicts with title, description, outlet, url

        Returns:
            Dict with verdict, confidence, reasoning, sources_used, raw_score
        """
        if not claim or not claim.strip():
            return self._uncertain("Empty claim")

        # Build article context (max 8 articles, 300 chars each)
        context_lines = []
        for i, art in enumerate(articles[:8], 1):
            title  = (art.get("title") or "").strip()
            desc   = (art.get("description") or art.get("content") or "").strip()[:300]
            outlet = (art.get("outlet") or art.get("source") or "Unknown").strip()
            if title:
                context_lines.append(
                    f"[Article {i}] Source: {outlet}\nTitle: {title}\nSummary: {desc}"
                )

        if not context_lines:
            return self._uncertain("No articles available for context")

        context_text = "\n\n".join(context_lines)
        full_prompt = (
            f"{self.SYSTEM_PROMPT}\n\n"
            f"CLAIM TO FACT-CHECK:\n\"{claim}\"\n\n"
            f"NEWS ARTICLES ({len(context_lines)} articles):\n{context_text}\n\n"
            f"Based ONLY on the articles above, return your JSON verdict."
        )

        url = self.API_URL.format(model=self.MODEL)
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 300,
            }
        }

        try:
            response = requests.post(
                url,
                params={"key": self.api_key},
                json=payload,
                timeout=20
            )

            if response.status_code != 200:
                logger.error(f"Gemini API error {response.status_code}: {response.text[:300]}")
                return self._uncertain(f"Gemini API error: {response.status_code}")

            data = response.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            logger.debug(f"Gemini raw response: {raw_text}")

            # Strip markdown fences if present
            if "```" in raw_text:
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            raw_text = raw_text.strip()

            parsed       = json.loads(raw_text)
            verdict      = parsed.get("verdict", "UNCERTAIN")
            confidence   = float(parsed.get("confidence", 0.5))
            reasoning    = parsed.get("reasoning", "")
            sources_used = int(parsed.get("sources_used", 0))

            # Map to numeric score (0 = real, 1 = fake)
            if verdict == "LIKELY_FAKE":
                raw_score = 0.5 + confidence * 0.5
            elif verdict == "LIKELY_REAL":
                raw_score = 0.5 - confidence * 0.5
            else:
                raw_score = 0.5

            logger.info(
                f"Gemini: {verdict} conf={confidence:.0%} "
                f"score={raw_score:.2f} sources={sources_used} | {reasoning[:80]}"
            )

            return {
                "verdict":           verdict,
                "confidence":        confidence,
                "reasoning":         reasoning,
                "sources_used":      sources_used,
                "raw_score":         raw_score,
                "articles_provided": len(context_lines),
                "model":             self.MODEL,
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON: {e} | raw: {raw_text[:200]}")
            return self._uncertain(f"JSON parse error: {e}")
        except Exception as e:
            logger.error(f"Gemini fact-check failed: {e}", exc_info=True)
            return self._uncertain(f"Gemini error: {str(e)}")

    def _uncertain(self, reason: str) -> Dict:
        logger.warning(f"Returning UNCERTAIN: {reason}")
        return {
            "verdict":           "UNCERTAIN",
            "confidence":        0.3,
            "reasoning":         reason,
            "sources_used":      0,
            "raw_score":         0.5,
            "articles_provided": 0,
            "model":             self.MODEL,
        }