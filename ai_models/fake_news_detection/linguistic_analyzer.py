# ai_models/fake_news_detection/linguistic_analyzer.py
"""
Linguistic Analysis Module for Fake News Detection
Detects manipulation patterns, emotional language, and credibility indicators
"""

import re
from typing import Dict
import logging

logger = logging.getLogger("spectra.fakenews.linguistic")


class LinguisticAnalyzer:
    """
    Analyze text for linguistic manipulation patterns
    
    Detects:
    - Clickbait language
    - Emotional manipulation
    - Complexity issues
    - Vague/hedging language
    - Credibility markers
    """
    
    def __init__(self):
        # Clickbait keywords
        self.clickbait_keywords = [
            "shocking", "unbelievable", "you won't believe",
            "what happens next", "doctors hate", "one weird trick",
            "mind-blowing", "jaw-dropping", "amazing discovery",
            "scientists shocked", "this changes everything",
            "what they don't want you to know", "breaking news",
            "exclusive reveal", "secret revealed"
        ]
        
        # Emotional manipulation words
        self.emotion_words = {
            "positive": [
                "amazing", "incredible", "wonderful", "fantastic",
                "revolutionary", "groundbreaking", "miracle"
            ],
            "negative": [
                "terrible", "horrible", "disaster", "catastrophe",
                "crisis", "devastating", "shocking", "outrage"
            ],
            "fear": [
                "danger", "threat", "warning", "alert", "beware",
                "scared", "terrified", "panic", "fear"
            ]
        }
        
        # Hedging/vague language
        self.hedging_words = [
            "maybe", "possibly", "might", "could", "perhaps",
            "allegedly", "reportedly", "supposedly", "claims",
            "some say", "many believe"
        ]
        
        # Authority manipulation
        self.false_authority = [
            "scientists", "doctors", "experts", "studies show",
            "research proves", "new study reveals"
        ]
    
    def analyze(self, text: str) -> Dict:
        """
        Perform complete linguistic analysis
        
        Args:
            text: Input text to analyze
        
        Returns:
            Dict with linguistic features and red flags
        """
        text_lower = text.lower()
        
        # Basic text statistics
        words = text.split()
        sentences = self._split_sentences(text)
        
        # 1. Clickbait detection
        has_clickbait = self._detect_clickbait(text_lower)
        clickbait_count = sum(
            text_lower.count(kw) for kw in self.clickbait_keywords
        )
        
        # 2. Emotional manipulation
        emotion_scores = self._analyze_emotion(text_lower)
        high_emotion = (
            emotion_scores["total_emotion"] > 0.15 or
            emotion_scores["fear_score"] > 0.05
        )
        
        # 3. Capitalization analysis
        caps_ratio = self._analyze_caps(text)
        excessive_caps = caps_ratio > 0.1
        
        # 4. Sentence complexity
        avg_sentence_length = len(words) / max(len(sentences), 1)
        low_complexity = avg_sentence_length < 8
        
        # 5. Vocabulary diversity
        unique_ratio = len(set([w.lower() for w in words])) / max(len(words), 1)
        
        # 6. Hedging language
        hedging_count = sum(
            1 for word in self.hedging_words if word in text_lower
        )
        high_hedging = hedging_count > 3
        
        # 7. False authority appeals
        authority_count = sum(
            1 for phrase in self.false_authority if phrase in text_lower
        )
        
        # 8. Question marks (sensationalism)
        question_count = text.count("?")
        question_ratio = question_count / max(len(sentences), 1)
        
        # 9. Exclamation marks (sensationalism)
        exclamation_count = text.count("!")
        exclamation_ratio = exclamation_count / max(len(sentences), 1)
        
        # 10. URL/link count
        url_count = len(re.findall(r'http[s]?://\S+', text))
        
        # Aggregate signals
        result = {
            # Text statistics
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "unique_words_ratio": round(unique_ratio, 3),
            
            # Clickbait
            "has_clickbait": has_clickbait,
            "clickbait_count": clickbait_count,
            
            # Emotion
            "emotion_scores": emotion_scores,
            "high_emotion": high_emotion,
            "sentiment_polarity": emotion_scores["sentiment_polarity"],
            
            # Formatting
            "caps_ratio": round(caps_ratio, 3),
            "excessive_caps": excessive_caps,
            
            # Complexity
            "low_complexity": low_complexity,
            
            # Credibility markers
            "hedging_count": hedging_count,
            "high_hedging": high_hedging,
            "authority_appeals": authority_count,
            
            # Sensationalism
            "question_ratio": round(question_ratio, 2),
            "exclamation_ratio": round(exclamation_ratio, 2),
            "high_sensationalism": exclamation_ratio > 0.3,
            
            # Other
            "url_count": url_count
        }
        
        logger.debug(
            f"Linguistic analysis: clickbait={has_clickbait}, "
            f"emotion={high_emotion}, caps={excessive_caps}"
        )
        
        return result
    
    def _detect_clickbait(self, text_lower: str) -> bool:
        """Check if text contains clickbait language"""
        return any(kw in text_lower for kw in self.clickbait_keywords)
    
    def _analyze_emotion(self, text_lower: str) -> Dict:
        """Analyze emotional content"""
        # Count emotional words
        positive_count = sum(
            text_lower.count(w) for w in self.emotion_words["positive"]
        )
        negative_count = sum(
            text_lower.count(w) for w in self.emotion_words["negative"]
        )
        fear_count = sum(
            text_lower.count(w) for w in self.emotion_words["fear"]
        )
        
        # Calculate scores
        words = text_lower.split()
        word_count = max(len(words), 1)
        
        positive_score = positive_count / word_count
        negative_score = negative_count / word_count
        fear_score = fear_count / word_count
        
        total_emotion = positive_score + negative_score + fear_score
        
        # Sentiment polarity (-1 to 1)
        if positive_count + negative_count > 0:
            sentiment = (positive_count - negative_count) / (positive_count + negative_count)
        else:
            sentiment = 0.0
        
        return {
            "positive_score": round(positive_score, 4),
            "negative_score": round(negative_score, 4),
            "fear_score": round(fear_score, 4),
            "total_emotion": round(total_emotion, 4),
            "sentiment_polarity": round(sentiment, 3)
        }
    
    def _analyze_caps(self, text: str) -> float:
        """Analyze capitalization ratio"""
        if len(text) == 0:
            return 0.0
        
        # Count uppercase letters
        caps_count = sum(1 for c in text if c.isupper())
        
        # Calculate ratio
        return caps_count / len(text)
    
    def _split_sentences(self, text: str) -> list:
        """Split text into sentences"""
        # Simple sentence splitting
        text = text.replace("! ", ".\n").replace("? ", ".\n")
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        return sentences


# ========== Testing ==========
if __name__ == "__main__":
    print("=" * 70)
    print("Linguistic Analyzer Test")
    print("=" * 70)
    
    analyzer = LinguisticAnalyzer()
    
    # Test 1: Clickbait article
    print("\n📰 Test 1: Clickbait Article")
    print("-" * 70)
    
    clickbait_text = """
    SHOCKING Discovery! You Won't BELIEVE What Scientists Found!
    
    Doctors HATE This One Weird Trick That Changes EVERYTHING!
    The medical establishment doesn't want you to know this secret!
    
    This is ABSOLUTELY MIND-BLOWING! Click here NOW!
    """
    
    print(clickbait_text.strip())
    print("\n" + "-" * 70)
    
    result = analyzer.analyze(clickbait_text)
    
    print("\n📊 Analysis Results:")
    print(f"  Clickbait: {result['has_clickbait']} (count: {result['clickbait_count']})")
    print(f"  High Emotion: {result['high_emotion']}")
    print(f"  Excessive Caps: {result['excessive_caps']} (ratio: {result['caps_ratio']:.1%})")
    print(f"  Sentiment: {result['sentiment_polarity']:.2f}")
    print(f"  Sensationalism: {result['high_sensationalism']}")
    
    # Test 2: Neutral article
    print("\n" + "=" * 70)
    print("📰 Test 2: Neutral Article")
    print("-" * 70)
    
    neutral_text = """
    The Federal Reserve announced today that it would maintain
    current interest rates at 5.25-5.50 percent. This decision
    comes after the latest economic data showed inflation
    continuing to moderate toward the Fed's 2% target.
    
    The committee will continue to monitor economic indicators
    and adjust policy as needed to support maximum employment
    and price stability.
    """
    
    print(neutral_text.strip())
    print("\n" + "-" * 70)
    
    result = analyzer.analyze(neutral_text)
    
    print("\n📊 Analysis Results:")
    print(f"  Clickbait: {result['has_clickbait']}")
    print(f"  High Emotion: {result['high_emotion']}")
    print(f"  Excessive Caps: {result['excessive_caps']}")
    print(f"  Sentiment: {result['sentiment_polarity']:.2f}")
    print(f"  Avg Sentence Length: {result['avg_sentence_length']} words")
    
    print("\n" + "=" * 70)
    print("✅ All tests complete")
    print("=" * 70)
