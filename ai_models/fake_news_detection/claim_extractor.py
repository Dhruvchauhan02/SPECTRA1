# ai_models/fake_news_detection/claim_extractor.py
"""
Claim Extraction Module for Fake News Detection
Extracts verifiable factual claims from text
"""

from typing import List, Dict
import re
import logging

logger = logging.getLogger("spectra.fakenews.claims")


class ClaimExtractor:
    """
    Extract verifiable claims from text
    
    Identifies sentences that:
    - Make factual assertions
    - Are not questions or opinions
    - Contain specific information (numbers, names, dates)
    - Can be fact-checked
    """
    
    def __init__(self):
        # Patterns that indicate factual claims
        self.claim_indicators = [
            r'\d+%',  # Percentages
            r'\$\d+',  # Money amounts
            r'\d{4}',  # Years
            r'according to',
            r'study (shows|finds|reveals)',
            r'research (shows|indicates)',
            r'experts? (say|claim|believe)',
            r'scientists? (discover|found)',
            r'data (shows|reveals|indicates)',
        ]
        
        # Patterns that indicate non-claims (filter out)
        self.non_claim_indicators = [
            r'^\s*what\s',  # Questions
            r'^\s*how\s',
            r'^\s*why\s',
            r'^\s*when\s',
            r'^\s*where\s',
            r'\?$',  # Questions
            r'^\s*i (think|believe|feel)',  # Opinions
            r'^\s*in my opinion',
            r'^\s*it seems',
            r'^\s*perhaps',
            r'^\s*maybe',
        ]
    
    def extract(self, text: str, max_claims: int = 10) -> List[Dict]:
        """
        Extract verifiable claims from text
        
        Args:
            text: Input text
            max_claims: Maximum number of claims to extract
        
        Returns:
            List of dicts with:
                - text: Claim text
                - confidence: Extraction confidence (0-1)
                - type: Claim type (statistical, temporal, etc.)
                - position: Position in original text
        """
        # Split into sentences
        sentences = self._split_sentences(text)
        
        claims = []
        
        for i, sentence in enumerate(sentences):
            # Check if sentence is a claim
            is_claim, confidence, claim_type = self._is_claim(sentence)
            
            if is_claim and len(sentence.split()) > 5:  # Minimum length
                claims.append({
                    "text": sentence.strip(),
                    "confidence": confidence,
                    "type": claim_type,
                    "position": i,
                    "word_count": len(sentence.split())
                })
        
        # Sort by confidence
        claims.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Limit to max_claims
        claims = claims[:max_claims]
        
        logger.debug(f"Extracted {len(claims)} claims from {len(sentences)} sentences")
        
        return claims
    
    def _is_claim(self, sentence: str) -> tuple:
        """
        Check if sentence is a verifiable claim
        
        Args:
            sentence: Sentence to check
        
        Returns:
            Tuple of (is_claim, confidence, claim_type)
        """
        sentence_lower = sentence.lower()
        
        # Filter out non-claims
        for pattern in self.non_claim_indicators:
            if re.search(pattern, sentence_lower):
                return (False, 0.0, "non_claim")
        
        # Check for claim indicators
        confidence = 0.5  # Base confidence
        claim_types = []
        
        # Statistical claims (numbers, percentages)
        if re.search(r'\d+%', sentence):
            confidence += 0.2
            claim_types.append("statistical")
        
        if re.search(r'\$\d+', sentence):
            confidence += 0.15
            claim_types.append("financial")
        
        # Temporal claims (dates, years)
        if re.search(r'\d{4}', sentence):
            confidence += 0.1
            claim_types.append("temporal")
        
        if re.search(r'(yesterday|today|tomorrow|last (week|month|year))', sentence_lower):
            confidence += 0.1
            claim_types.append("temporal")
        
        # Authority claims (studies, experts)
        if re.search(r'according to', sentence_lower):
            confidence += 0.15
            claim_types.append("authority")
        
        if re.search(r'study (shows|finds|reveals)', sentence_lower):
            confidence += 0.2
            claim_types.append("authority")
        
        if re.search(r'(expert|scientist|researcher)s? (say|claim|found)', sentence_lower):
            confidence += 0.15
            claim_types.append("authority")
        
        # Named entities (proper nouns - simplified check)
        if re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', sentence):
            confidence += 0.1
            claim_types.append("named_entity")
        
        # Causal claims
        if re.search(r'(cause|lead to|result in|due to|because of)', sentence_lower):
            confidence += 0.1
            claim_types.append("causal")
        
        # Comparative claims
        if re.search(r'(more|less|higher|lower|better|worse) than', sentence_lower):
            confidence += 0.1
            claim_types.append("comparative")
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        # Determine if it's a claim (confidence > threshold)
        is_claim = confidence > 0.6
        
        # Determine primary claim type
        claim_type = claim_types[0] if claim_types else "general"
        
        return (is_claim, confidence, claim_type)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Replace common abbreviations to avoid false splits
        text = text.replace("Dr.", "Dr").replace("Mr.", "Mr").replace("Mrs.", "Mrs")
        text = text.replace("U.S.", "US").replace("U.K.", "UK")
        
        # Split on sentence boundaries
        text = text.replace("! ", ".\n").replace("? ", ".\n")
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        
        return sentences


# ========== Testing ==========
if __name__ == "__main__":
    print("=" * 70)
    print("Claim Extractor Test")
    print("=" * 70)
    
    extractor = ClaimExtractor()
    
    # Test article
    test_text = """
    A new study reveals that 75% of Americans drink coffee daily.
    This is a significant increase from 2020, when only 60% reported
    regular coffee consumption.
    
    Dr. John Smith, a nutrition expert at Harvard, says that
    moderate coffee intake is associated with health benefits.
    The research was published in the Journal of Nutrition.
    
    How does coffee affect your health? Many people wonder about this.
    I think coffee is great, but that's just my opinion.
    
    According to the study, coffee drinkers live longer than non-drinkers.
    This effect was observed across all age groups.
    """
    
    print("\n📄 Test Article:")
    print("-" * 70)
    print(test_text.strip())
    print("-" * 70)
    
    # Extract claims
    print("\n🔍 Extracting claims...")
    claims = extractor.extract(test_text)
    
    print(f"\n📋 Extracted {len(claims)} Claims:")
    print("=" * 70)
    
    for i, claim in enumerate(claims, 1):
        print(f"\n{i}. {claim['text']}")
        print(f"   Type: {claim['type']}")
        print(f"   Confidence: {claim['confidence']:.2f}")
        print(f"   Position: Sentence #{claim['position']}")
        print(f"   Words: {claim['word_count']}")
    
    print("\n" + "=" * 70)
    print("✅ Test complete")
    print("=" * 70)
    
    # Test edge cases
    print("\n📝 Testing Edge Cases:")
    print("-" * 70)
    
    edge_cases = [
        "What is the capital of France?",  # Question - should be filtered
        "I think Paris is beautiful.",  # Opinion - should be filtered
        "Paris is the capital of France.",  # Factual claim - should be extracted
        "The Eiffel Tower is 300 meters tall.",  # Numerical claim - should be extracted
    ]
    
    for text in edge_cases:
        claims = extractor.extract(text)
        print(f"\nText: {text}")
        print(f"  Claims found: {len(claims)}")
        if claims:
            print(f"  Type: {claims[0]['type']}, Confidence: {claims[0]['confidence']:.2f}")
    
    print("\n" + "=" * 70)
    print("✅ All tests complete")
    print("=" * 70)
