# ai_models/fake_news_detection/__init__.py
"""
SPECTRA-AI Fake News Detection Module

Multi-signal text analysis for misinformation detection:
- Linguistic pattern analysis
- Source credibility checking
- Claim extraction and verification
- Evidence-based fact-checking
"""

from .pipeline import FakeNewsPipeline
from .linguistic_analyzer import LinguisticAnalyzer
from .source_credibility import SourceCredibilityChecker
from .claim_extractor import ClaimExtractor
from .fusion import FakeNewsFusion

__all__ = [
    "FakeNewsPipeline",
    "analyze_article",
    "batch_analyze",
    "LinguisticAnalyzer",
    "SourceCredibilityChecker",
    "ClaimExtractor",
    "FakeNewsFusion",
]

__version__ = "1.0.0"
