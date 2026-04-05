# tests/test_fake_news.py
"""
Comprehensive Test Suite for Fake News Detection Module
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ========== Component Tests ==========

class TestLinguisticAnalyzer:
    """Test linguistic analysis component"""
    
    def test_imports(self):
        """Test that linguistic analyzer can be imported"""
        from ai_models.fake_news_detection.linguistic_analyzer import LinguisticAnalyzer
        analyzer = LinguisticAnalyzer()
        assert analyzer is not None
    
    def test_clickbait_detection(self):
        """Test clickbait detection"""
        from ai_models.fake_news_detection.linguistic_analyzer import LinguisticAnalyzer
        
        analyzer = LinguisticAnalyzer()
        
        # Clickbait text
        clickbait = "You WON'T BELIEVE what happens next! SHOCKING discovery!"
        result = analyzer.analyze(clickbait)
        
        assert result["has_clickbait"] == True
        assert result["excessive_caps"] == True
        assert result["high_sensationalism"] == True
    
    def test_neutral_text(self):
        """Test analysis of neutral text"""
        from ai_models.fake_news_detection.linguistic_analyzer import LinguisticAnalyzer
        
        analyzer = LinguisticAnalyzer()
        
        neutral = """
        The Federal Reserve announced today that it would maintain
        current interest rates. This decision comes after economic
        data showed continued growth.
        """
        
        result = analyzer.analyze(neutral)
        
        assert result["has_clickbait"] == False
        assert result["excessive_caps"] == False
        assert result["high_emotion"] == False


class TestSourceCredibility:
    """Test source credibility checker"""
    
    def test_imports(self):
        """Test that source checker can be imported"""
        from ai_models.fake_news_detection.source_credibility import SourceCredibilityChecker
        checker = SourceCredibilityChecker()
        assert checker is not None
    
    def test_high_credibility_source(self):
        """Test high credibility source detection"""
        from ai_models.fake_news_detection.source_credibility import SourceCredibilityChecker
        
        checker = SourceCredibilityChecker()
        
        result = checker.check("https://www.reuters.com/article")
        
        assert result["credibility"] == "HIGH"
        assert result["score"] < 0.3
        assert result["is_https"] == True
    
    def test_low_credibility_source(self):
        """Test low credibility source detection"""
        from ai_models.fake_news_detection.source_credibility import SourceCredibilityChecker
        
        checker = SourceCredibilityChecker()
        
        result = checker.check("http://naturalnews.com/article")
        
        assert result["credibility"] == "LOW"
        assert result["score"] > 0.7
    
    def test_unknown_source(self):
        """Test unknown source handling"""
        from ai_models.fake_news_detection.source_credibility import SourceCredibilityChecker
        
        checker = SourceCredibilityChecker()
        
        result = checker.check("https://unknown-blog.com/article")
        
        assert result["credibility"] == "UNKNOWN"
        assert 0.4 <= result["score"] <= 0.6


class TestClaimExtractor:
    """Test claim extraction"""
    
    def test_imports(self):
        """Test that claim extractor can be imported"""
        from ai_models.fake_news_detection.claim_extractor import ClaimExtractor
        extractor = ClaimExtractor()
        assert extractor is not None
    
    def test_extract_statistical_claim(self):
        """Test extraction of statistical claims"""
        from ai_models.fake_news_detection.claim_extractor import ClaimExtractor
        
        extractor = ClaimExtractor()
        
        text = "Studies show that 75% of Americans drink coffee daily."
        
        claims = extractor.extract(text)
        
        assert len(claims) > 0
        assert "statistical" in claims[0]["type"]
        assert claims[0]["confidence"] > 0.6
    
    def test_filter_questions(self):
        """Test that questions are filtered out"""
        from ai_models.fake_news_detection.claim_extractor import ClaimExtractor
        
        extractor = ClaimExtractor()
        
        text = "What is the capital of France? Where is Paris located?"
        
        claims = extractor.extract(text)
        
        # Questions should be filtered out
        assert len(claims) == 0
    
    def test_filter_opinions(self):
        """Test that opinions are filtered out"""
        from ai_models.fake_news_detection.claim_extractor import ClaimExtractor
        
        extractor = ClaimExtractor()
        
        text = "I think coffee is great. In my opinion, it tastes good."
        
        claims = extractor.extract(text)
        
        # Opinions should be filtered out
        assert len(claims) == 0


class TestFusion:
    """Test signal fusion"""
    
    def test_imports(self):
        """Test that fusion can be imported"""
        from ai_models.fake_news_detection.fusion import FakeNewsFusion
        fusion = FakeNewsFusion()
        assert fusion is not None
    
    def test_weights_validation(self):
        """Test that fusion validates weights"""
        from ai_models.fake_news_detection.fusion import FakeNewsFusion
        
        # Invalid weights (don't sum to 1.0)
        with pytest.raises(ValueError):
            FakeNewsFusion(
                w_linguistic=0.5,
                w_source=0.5,
                w_verification=0.5  # Total = 1.5
            )
    
    def test_suspicious_content(self):
        """Test fusion on suspicious content"""
        from ai_models.fake_news_detection.fusion import FakeNewsFusion
        
        fusion = FakeNewsFusion()
        
        # Highly suspicious signals
        linguistic = {
            "has_clickbait": True,
            "clickbait_count": 5,
            "high_emotion": True,
            "excessive_caps": True,
            "high_sensationalism": True,
            "sentiment_polarity": 0.9
        }
        
        source = {
            "credibility": "LOW",
            "score": 0.9
        }
        
        result = fusion.fuse(
            linguistic=linguistic,
            source=source,
            verification=None
        )
        
        assert result["label"] == "LIKELY_FAKE"
        assert result["final_score"] > 0.7
    
    def test_credible_content(self):
        """Test fusion on credible content"""
        from ai_models.fake_news_detection.fusion import FakeNewsFusion
        
        fusion = FakeNewsFusion()
        
        # Credible signals
        linguistic = {
            "has_clickbait": False,
            "clickbait_count": 0,
            "high_emotion": False,
            "excessive_caps": False,
            "high_sensationalism": False,
            "sentiment_polarity": 0.1
        }
        
        source = {
            "credibility": "HIGH",
            "score": 0.1
        }
        
        result = fusion.fuse(
            linguistic=linguistic,
            source=source,
            verification=None
        )
        
        assert result["label"] == "LIKELY_REAL"
        assert result["final_score"] < 0.3


# ========== Integration Tests ==========

class TestPipeline:
    """Test complete pipeline integration"""
    
    def test_pipeline_initialization(self):
        """Test that pipeline initializes without errors"""
        from ai_models.fake_news_detection import FakeNewsPipeline
        
        pipeline = FakeNewsPipeline(device="cpu")
        assert pipeline is not None
    
    def test_analyze_clickbait_article(self):
        """Test analysis of clickbait article"""
        from ai_models.fake_news_detection import FakeNewsPipeline
        
        pipeline = FakeNewsPipeline(device="cpu")
        
        text = """
        BREAKING: You Won't BELIEVE This SHOCKING Discovery!
        
        Scientists are STUNNED by what they found! The medical
        establishment DOESN'T WANT YOU TO KNOW this one weird trick!
        
        This changes EVERYTHING! Click here NOW to learn more!
        """
        
        result = pipeline.analyze(
            text=text,
            url="https://fake-news.com/article"
        )
        
        assert result["status"] == "success"
        assert result["verdict"] in ["LIKELY_FAKE", "UNCERTAIN"]
        assert result["spectra_score"] > 50
    
    def test_analyze_credible_article(self):
        """Test analysis of credible article"""
        from ai_models.fake_news_detection import FakeNewsPipeline
        
        pipeline = FakeNewsPipeline(device="cpu")
        
        text = """
        The Federal Reserve announced today that it would maintain
        interest rates at current levels. The decision comes after
        reviewing recent economic indicators showing continued
        moderate growth and inflation trending toward the 2% target.
        
        The committee will continue to monitor economic data and
        adjust monetary policy as appropriate to support maximum
        employment and price stability.
        """
        
        result = pipeline.analyze(
            text=text,
            url="https://reuters.com/article"
        )
        
        assert result["status"] == "success"
        assert result["verdict"] in ["LIKELY_REAL", "UNCERTAIN"]
        assert result["spectra_score"] < 70
    
    def test_analyze_short_text(self):
        """Test that very short text is handled properly"""
        from ai_models.fake_news_detection import FakeNewsPipeline
        
        pipeline = FakeNewsPipeline(device="cpu")
        
        # Text too short
        short_text = "This is short."
        
        # Should still work, just with fewer claims
        result = pipeline.analyze(text=short_text)
        
        # May not extract many claims, but shouldn't crash
        assert result["status"] == "success"


# ========== Performance Tests ==========

class TestPerformance:
    """Test performance characteristics"""
    
    def test_analysis_speed(self):
        """Test that analysis completes in reasonable time"""
        import time
        from ai_models.fake_news_detection import FakeNewsPipeline
        
        pipeline = FakeNewsPipeline(device="cpu")
        
        text = "Sample text for testing performance. " * 50
        
        pipeline.analyze(text)

        start = time.time()
        result = pipeline.analyze(text)
        elapsed = time.time() - start
        
        # Should complete in under 5 seconds on CPU
        assert elapsed < 2.0, f"Analysis took {elapsed:.2f}s (expected < 2s)"
        assert result["status"] == "success"
    
        print(f"✅ Analysis speed: {elapsed*1000:.0f}ms")
    
    def test_batch_processing(self):
        """Test batch analysis capability"""
        from ai_models.fake_news_detection import batch_analyze
        
        articles = [
            {"text": "Article one with some content. " * 20},
            {"text": "Article two with different content. " * 20},
            {"text": "Article three with more content. " * 20},
        ]
        
        results = batch_analyze(articles, device="cpu")
        
        assert len(results) == 3
        for result in results:
            assert result["status"] == "success"


# ========== Utility Functions ==========

def run_all_tests():
    """Run all tests with pytest"""
    print("=" * 70)
    print("SPECTRA-AI Fake News Detection Tests")
    print("=" * 70)
    
    # Run pytest
    result = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ])
    
    print("\n" + "=" * 70)
    if result == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 70)
    
    return result


if __name__ == "__main__":
    exit(run_all_tests())
