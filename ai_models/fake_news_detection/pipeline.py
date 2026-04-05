# ai_models/fake_news_detection/pipeline.py
"""
Complete Fake News Detection Pipeline for SPECTRA-AI
Multi-signal analysis for text-based misinformation detection
"""

import os
import torch
import logging
from typing import Dict, List, Optional, Tuple
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification
import numpy as np

logger = logging.getLogger("spectra.fakenews")


class FakeNewsPipeline:
    """
    Production-ready fake news detection pipeline

    Components:
    1. Linguistic Analysis (pattern detection)
    2. Source Credibility (domain reputation)
    3. Claim Extraction
    4. Google Custom Search (validate claim coverage)
    5. NewsAPI article fetch
    6. Gemini fact-check (dominant signal)
    7. Signal Fusion
    """

    def __init__(
        self,
        model_name: str = "microsoft/deberta-v3-small",
        device: str = "cpu",
        use_entailment: bool = False,
        search_api_key: Optional[str] = None,
        enable_text_encoding: bool = False,
        newsapi_key: Optional[str] = None,
        gnews_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,   # kept for compatibility, unused
    ):
        self.device = device
        self.enable_text_encoding = enable_text_encoding
        logger.info(f"Initializing Fake News Pipeline")

        # Text encoder (disabled by default for speed)
        if enable_text_encoding:
            logger.info("Loading text encoder...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name).to(device)
            self.model.eval()
        else:
            logger.info("Text encoding disabled (faster startup)")
            self.tokenizer = None
            self.model = None

        # Core components
        from .linguistic_analyzer import LinguisticAnalyzer
        from .source_credibility import SourceCredibilityChecker
        from .claim_extractor import ClaimExtractor
        from .fusion import FakeNewsFusion

        self.linguistic_analyzer = LinguisticAnalyzer()
        self.source_checker = SourceCredibilityChecker()
        self.claim_extractor = ClaimExtractor()
        self.fusion = FakeNewsFusion()

        # Entailment model (optional)
        self.entailment_model = None
        if use_entailment:
            try:
                self.entailment_model = AutoModelForSequenceClassification.from_pretrained(
                    "microsoft/deberta-v3-base-tasksource-nli"
                ).to(device)
                self.entailment_model.eval()
                logger.info("Entailment model loaded")
            except Exception as e:
                logger.warning(f"Could not load entailment model: {e}")

        # Evidence retriever (Bing/Google via EvidenceRetriever class)
        self.evidence_retriever = None
        if search_api_key:
            from .evidence_retrieval import EvidenceRetriever
            self.evidence_retriever = EvidenceRetriever(search_api_key)
            logger.info("Evidence retriever ready")

        # NewsAPI + GNews aggregator
        self.news_aggregator = None
        self.smart_verifier = None
        if newsapi_key or gnews_key:
            try:
                from .news_aggregator import ImprovedNewsAggregator
                from .smart_verification import SmartNewsVerification
                self.news_aggregator = ImprovedNewsAggregator(
                    newsapi_key=newsapi_key,
                    gnews_key=gnews_key
                )
                self.smart_verifier = SmartNewsVerification()
                logger.info("NewsAPI fact-checking layer ready")
            except Exception as e:
                logger.warning(f"NewsAPI unavailable: {e}")

        # Gemini fact-checker (primary AI signal)
        self.gpt_checker = None
        _gemini_key = os.getenv("GEMINI_API_KEY")
        if _gemini_key:
            try:
                from .gemini_factchecker import GeminiFactChecker
                self.gpt_checker = GeminiFactChecker(api_key=_gemini_key)
                logger.info("Gemini fact-checker ready")
            except Exception as e:
                logger.warning(f"Gemini fact-checker unavailable: {e}")
        else:
            logger.warning("GEMINI_API_KEY not set — Gemini fact-checking disabled")

        logger.info("Fake News Pipeline initialized")

    # ------------------------------------------------------------------
    # Google Custom Search helper
    # ------------------------------------------------------------------
    def _google_search(self, query: str) -> List[Dict]:
        """Search Google Custom Search API and return result items."""
        api_key = os.getenv("GOOGLE_API_KEY", "")
        cx      = os.getenv("GOOGLE_CX", "")

        if not api_key or not cx:
            logger.warning("GOOGLE_API_KEY or GOOGLE_CX not set — skipping Google search")
            return []

        try:
            resp = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"q": query, "key": api_key, "cx": cx, "num": 5},
                timeout=10
            )
            if resp.status_code != 200:
                logger.warning(f"Google search error: {resp.status_code}")
                return []
            return resp.json().get("items", [])
        except Exception as e:
            logger.warning(f"Google search failed: {e}")
            return []

    # ------------------------------------------------------------------
    # Main analyze method
    # ------------------------------------------------------------------
    def analyze(
        self,
        text: str,
        url: Optional[str] = None,
        enable_evidence_search: bool = False,
        max_claims: int = 3
    ) -> Dict:
        """
        Analyze text for fake news indicators.

        Returns dict with status, verdict, confidence, spectra_score,
        signals, breakdown, explanation.
        """
        import requests as _requests
        global requests
        requests = _requests

        logger.info(f"Analyzing text ({len(text)} chars)")

        try:
            # 1. Text encoding (optional)
            if self.enable_text_encoding:
                self._encode_text(text)

            # 2. Linguistic analysis
            linguistic_signals = self.linguistic_analyzer.analyze(text)

            # 3. Source credibility
            source_signals = None
            if url:
                source_signals = self.source_checker.check(url)

            # 4. Claim extraction
            claims = self.claim_extractor.extract(text, max_claims=max_claims)
            logger.info(f"Extracted {len(claims)} claims")
            top_claim = claims[0]["text"] if claims else text[:300]

            # 5. Evidence retrieval (optional)
            evidence_results = []
            if enable_evidence_search and self.evidence_retriever and claims:
                for claim in claims:
                    evidence = self.evidence_retriever.retrieve(claim["text"], max_results=3)
                    evidence_results.append({
                        "claim": claim["text"],
                        "evidence": evidence,
                        "num_sources": len(evidence)
                    })

            # 6. Entailment verification (optional)
            verification_signals = None
            if self.entailment_model and claims:
                verification_signals = self._verify_claims(claims, evidence_results)

            # 6b. Google Custom Search — validate claim coverage
            google_score = 0.5   # neutral default
            search_results = self._google_search(top_claim)
            if search_results:
                keywords = [w for w in top_claim.lower().split() if len(w) > 3]
                match_count = 0
                for item in search_results:
                    title = (item.get("title") or "").lower()
                    if any(word in title for word in keywords):
                        match_count += 1          # increment once per match
                if match_count >= 3:
                    google_score = 0.2            # well covered → likely real
                elif match_count == 0:
                    google_score = 0.7            # no coverage → suspicious
                else:
                    google_score = 0.45           # partial coverage → uncertain
                logger.info(f"Google matches: {match_count} → google_score={google_score}")
            else:
                google_score = 0.55              # no results → slightly suspicious
                logger.info("Google search returned no results")

            # 6c. Fetch NewsAPI articles (used by Gemini and SmartVerifier)
            articles = []
            if self.news_aggregator:
                try:
                    articles = self.news_aggregator.search_news(top_claim, max_results=15)
                    logger.info(f"Fetched {len(articles)} NewsAPI articles")
                except Exception as e:
                    logger.warning(f"NewsAPI fetch failed: {e}")

            # 6d. Gemini fact-check (primary AI signal)
            gpt_result = None
            if self.gpt_checker:
                try:
                    gpt_result = self.gpt_checker.check(claim=top_claim, articles=articles)
                    logger.info(
                        f"Gemini: {gpt_result.get('verdict')} "
                        f"({gpt_result.get('confidence', 0):.0%} conf)"
                    )
                except Exception as e:
                    logger.warning(f"Gemini fact-check failed: {e}")

            # SmartVerifier fallback (only if Gemini unavailable)
            newsapi_result = None
            if not gpt_result and self.smart_verifier and articles:
                try:
                    newsapi_result = self.smart_verifier.verify_claim_with_context(
                        claim=top_claim, articles=articles
                    )
                    logger.info(f"SmartVerifier: {newsapi_result.get('verdict')}")
                except Exception as e:
                    logger.warning(f"SmartVerifier failed: {e}")

            # 7. Base fusion (linguistic + source)
            verdict_result = self.fusion.fuse(
                linguistic=linguistic_signals,
                source=source_signals,
                verification=verification_signals,
                num_claims=len(claims)
            )

            # 7b. Blend Google score into base (25% weight)
            base = verdict_result["final_score"]
            verdict_result["final_score"] = 0.75 * base + 0.25 * google_score
            verdict_result["breakdown"]["google_search"] = google_score

            # 7c. Gemini override (70% Gemini, 30% blended base)
            if gpt_result and gpt_result.get("verdict") != "UNCERTAIN":
                gpt_score = gpt_result["raw_score"]
                blended = 0.70 * gpt_score + 0.30 * verdict_result["final_score"]
                verdict_result["final_score"] = blended
                verdict_result["breakdown"]["gemini_factcheck"] = gpt_score
                logger.info(f"Gemini blended final_score={blended:.3f}")

            elif newsapi_result:
                nv = newsapi_result.get("verdict", "")
                nc = newsapi_result.get("confidence", 0.5)
                bs = verdict_result["final_score"]
                if nv == "FAKE":
                    adjusted = bs * 0.4 + 0.6 * nc
                elif nv == "DISPUTED":
                    adjusted = bs * 0.5 + 0.5 * 0.6
                elif nv == "VERIFIED":
                    adjusted = bs * 0.4 + 0.6 * (1 - nc)
                elif nv == "PARTIALLY_VERIFIED":
                    adjusted = bs * 0.7 + 0.3 * (1 - nc)
                else:
                    adjusted = bs
                verdict_result["final_score"] = min(max(adjusted, 0.0), 1.0)
                verdict_result["breakdown"]["newsapi"] = verdict_result["final_score"]

            # 7d. Fallback rule-based scoring (only when Gemini failed)
            if not gpt_result or gpt_result.get("verdict") == "UNCERTAIN":
                text_lower = text.lower()
                fallback_score = 0.0
                if any(w in text_lower for w in ["month", "year", "100%", "guarantee"]):
                    fallback_score += 0.3
                if any(w in text_lower for w in ["breaking", "shocking", "viral", "must watch"]):
                    fallback_score += 0.2
                if not articles:
                    fallback_score += 0.15
                if text.isupper():
                    fallback_score += 0.15
                if fallback_score > 0:
                    verdict_result["final_score"] = min(
                        verdict_result["final_score"] + fallback_score * 0.3, 1.0
                    )
                    verdict_result["breakdown"]["fallback_rules"] = fallback_score
                    logger.info(f"Fallback rules added {fallback_score:.2f}")

            # 8. Re-apply verdict thresholds after all adjustments
            fs = verdict_result["final_score"]
            if fs >= 0.65:
                verdict_result["label"] = "LIKELY_FAKE"
                verdict_result["confidence"] = min((fs - 0.65) / 0.35, 1.0)
            elif fs <= 0.35:
                verdict_result["label"] = "LIKELY_REAL"
                verdict_result["confidence"] = min((0.35 - fs) / 0.35, 1.0)
            else:
                verdict_result["label"] = "UNCERTAIN"
                verdict_result["confidence"] = min(abs(fs - 0.5) / 0.15, 1.0)
            verdict_result["confidence"] = round(
                min(max(verdict_result["confidence"], 0.0), 1.0), 3
            )

            # 9. Generate explanation
            explanation = self._generate_explanation(
                verdict_result, linguistic_signals, source_signals, claims
            )
            if gpt_result:
                gv = gpt_result.get("verdict", "UNCERTAIN")
                gr = gpt_result.get("reasoning", "")
                gc = gpt_result.get("confidence", 0)
                gs = gpt_result.get("sources_used", 0)
                explanation += (
                    f" [Gemini Fact-Check ({gv}, {gc:.0%} confidence, "
                    f"{gs} sources used): {gr}]"
                )
            elif newsapi_result:
                nv = newsapi_result.get("verdict", "UNVERIFIED")
                msg = newsapi_result.get("message", "")
                explanation += f" [NewsAPI: {nv} — {msg}]"

            return {
                "status":        "success",
                "verdict":       verdict_result["label"],
                "confidence":    verdict_result["confidence"],
                "spectra_score": int(verdict_result["final_score"] * 100),
                "signals": {
                    "linguistic":       linguistic_signals,
                    "source":           source_signals,
                    "claims": {
                        "extracted": [c["text"] for c in claims],
                        "count":     len(claims)
                    },
                    "evidence":          evidence_results if evidence_results else None,
                    "verification":      verification_signals,
                    "gemini_factcheck":  gpt_result,
                    "newsapi_factcheck": newsapi_result,
                    "google_score":      google_score,
                },
                "breakdown":    verdict_result["breakdown"],
                "explanation":  explanation
            }

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _encode_text(self, text: str) -> np.ndarray:
        max_length = 512
        inputs = self.tokenizer(
            text, padding=True, truncation=True,
            max_length=max_length, return_tensors="pt"
        ).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state[:, 0, :].cpu().numpy()[0]

    def _verify_claims(self, claims: List[Dict], evidence_results: List[Dict]) -> Optional[Dict]:
        if not self.entailment_model:
            return None
        verifications = []
        for i, claim in enumerate(claims):
            claim_text = claim["text"]
            if i < len(evidence_results) and evidence_results[i]["evidence"]:
                for evidence in evidence_results[i]["evidence"][:3]:
                    evidence_text = evidence.get("snippet", "")
                    if evidence_text:
                        stance = self._classify_entailment(claim_text, evidence_text)
                        verifications.append({
                            "claim":      claim_text,
                            "evidence":   evidence_text,
                            "stance":     stance["label"],
                            "confidence": stance["confidence"]
                        })
        if verifications:
            stances = [v["stance"] for v in verifications]
            refute_count  = stances.count("REFUTES")
            support_count = stances.count("SUPPORTS")
            total = refute_count + support_count
            return {
                "verifications": verifications,
                "refute_count":  refute_count,
                "support_count": support_count,
                "refute_ratio":  refute_count / total if total > 0 else 0.5
            }
        return None

    def _classify_entailment(self, claim: str, evidence: str) -> Dict:
        inputs = self.tokenizer(
            claim, evidence, padding=True, truncation=True,
            max_length=512, return_tensors="pt"
        ).to(self.device)
        with torch.no_grad():
            outputs = self.entailment_model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0].cpu().numpy()
        label_map = {0: "REFUTES", 1: "NEUTRAL", 2: "SUPPORTS"}
        pred_idx = int(np.argmax(probs))
        return {"label": label_map[pred_idx], "confidence": float(probs[pred_idx])}

    def _generate_explanation(
        self,
        verdict: Dict,
        linguistic: Dict,
        source: Optional[Dict],
        claims: List[Dict]
    ) -> str:
        parts = []
        label      = verdict["label"]
        confidence = verdict["confidence"]

        if label == "LIKELY_FAKE":
            parts.append(
                f"This content shows strong indicators of misinformation "
                f"(confidence: {confidence:.0%})."
            )
        elif label == "LIKELY_REAL":
            parts.append(
                f"This content appears credible based on available analysis "
                f"(confidence: {confidence:.0%})."
            )
        else:
            parts.append(
                "Unable to determine credibility with high confidence. "
                "Manual fact-checking recommended."
            )

        breakdown = verdict.get("breakdown", {})
        if breakdown.get("linguistic", 0) > 0.6:
            flags = []
            if linguistic.get("has_clickbait"):    flags.append("clickbait language")
            if linguistic.get("high_emotion"):     flags.append("emotional manipulation")
            if linguistic.get("excessive_caps"):   flags.append("excessive capitalization")
            if linguistic.get("low_complexity"):   flags.append("overly simplistic writing")
            if flags:
                parts.append(f"Linguistic red flags: {', '.join(flags)}.")

        if source:
            if source.get("credibility") == "LOW":
                parts.append(f"Source ({source['domain']}) has low credibility.")
            elif source.get("credibility") == "HIGH":
                parts.append(f"Source ({source['domain']}) is a recognised credible outlet.")

        if claims:
            parts.append(f"Analysed {len(claims)} verifiable claim(s).")

        return " ".join(parts)