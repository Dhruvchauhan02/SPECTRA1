# ai_models/deepfake_detection/fusion_improved.py
"""
Improved Score Fusion System for SPECTRA-AI
Enables all three detectors with weighted ensemble
"""

import numpy as np
from typing import Tuple, Dict


class ImprovedScoreFusion:
    """
    Weighted ensemble fusion with calibration and confidence zones
    """
    
    def __init__(
        self,
        w_visual: float = 0.50,
        w_clip: float = 0.35,
        w_freq: float = 0.15,
        threshold_high: float = 0.70,
        threshold_low: float = 0.30
    ):
        """
        Args:
            w_visual: Weight for EfficientNet detector (default: 0.50)
            w_clip: Weight for CLIP detector (default: 0.35)
            w_freq: Weight for frequency detector (default: 0.15)
            threshold_high: High confidence FAKE threshold (default: 0.70)
            threshold_low: High confidence REAL threshold (default: 0.30)
        """
        # Validate weights sum to 1.0
        total_weight = w_visual + w_clip + w_freq
        if not np.isclose(total_weight, 1.0):
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
        
        self.w_visual = w_visual
        self.w_clip = w_clip
        self.w_freq = w_freq
        
        self.threshold_high = threshold_high
        self.threshold_low = threshold_low
    
    def fuse(
        self, 
        p_freq: float, 
        p_visual: float, 
        p_clip: float
    ) -> Tuple[float, str]:
        """
        Fuse predictions from multiple detectors
        
        Args:
            p_freq: Frequency detector probability (0-1)
            p_visual: EfficientNet probability (0-1)
            p_clip: CLIP detector probability (0-1)
        
        Returns:
            Tuple of (final_probability, verdict)
            verdict can be: "FAKE", "REAL", or "UNCERTAIN"
        """
        # Weighted ensemble
        final_p = (
            self.w_visual * p_visual +
            self.w_clip * p_clip +
            self.w_freq * p_freq
        )
        
        # Confidence-aware verdict
        if final_p >= self.threshold_high:
            verdict = "FAKE"
        elif final_p <= self.threshold_low:
            verdict = "REAL"
        else:
            verdict = "UNCERTAIN"
        
        return final_p, verdict
    
    def fuse_with_metadata(
        self,
        p_freq: float,
        p_visual: float,
        p_clip: float
    ) -> Dict:
        """
        Fuse predictions and return detailed metadata
        
        Returns:
            Dict with:
                - final_p: Final probability
                - verdict: Classification label
                - confidence: How confident (0-1)
                - breakdown: Individual detector contributions
        """
        final_p, verdict = self.fuse(p_freq, p_visual, p_clip)
        
        # Calculate confidence (distance from uncertainty zone)
        if verdict == "FAKE":
            confidence = (final_p - self.threshold_high) / (1.0 - self.threshold_high)
        elif verdict == "REAL":
            confidence = (self.threshold_low - final_p) / self.threshold_low
        else:
            # Uncertain → low confidence
            confidence = 0.0
        
        confidence = np.clip(confidence, 0.0, 1.0)
        
        return {
            "final_p": float(final_p),
            "verdict": verdict,
            "confidence": float(confidence),
            "breakdown": {
                "visual": {
                    "probability": float(p_visual),
                    "contribution": float(self.w_visual * p_visual)
                },
                "clip": {
                    "probability": float(p_clip),
                    "contribution": float(self.w_clip * p_clip)
                },
                "frequency": {
                    "probability": float(p_freq),
                    "contribution": float(self.w_freq * p_freq)
                }
            }
        }
    
    def get_config(self) -> Dict:
        """Return current configuration"""
        return {
            "weights": {
                "visual": self.w_visual,
                "clip": self.w_clip,
                "frequency": self.w_freq
            },
            "thresholds": {
                "high": self.threshold_high,
                "low": self.threshold_low
            }
        }


class CalibratedScoreFusion(ImprovedScoreFusion):
    """
    Fusion with temperature scaling calibration
    """
    
    def __init__(
        self,
        w_visual: float = 0.50,
        w_clip: float = 0.35,
        w_freq: float = 0.15,
        threshold_high: float = 0.70,
        threshold_low: float = 0.30,
        temp_visual: float = 1.0,
        temp_clip: float = 1.0,
        temp_freq: float = 1.0
    ):
        super().__init__(w_visual, w_clip, w_freq, threshold_high, threshold_low)
        
        self.temp_visual = temp_visual
        self.temp_clip = temp_clip
        self.temp_freq = temp_freq
    
    def _calibrate_probability(self, p: float, temperature: float) -> float:
        """
        Apply temperature scaling to probability
        
        Args:
            p: Raw probability (0-1)
            temperature: Scaling factor (>1 = less confident, <1 = more confident)
        
        Returns:
            Calibrated probability
        """
        # Avoid log(0) and division by zero
        p = np.clip(p, 1e-8, 1 - 1e-8)
        
        # Convert to logit
        logit = np.log(p / (1 - p))
        
        # Apply temperature
        calibrated_logit = logit / temperature
        
        # Convert back to probability
        calibrated_p = 1 / (1 + np.exp(-calibrated_logit))
        
        return float(calibrated_p)
    
    def fuse(
        self,
        p_freq: float,
        p_visual: float,
        p_clip: float
    ) -> Tuple[float, str]:
        """
        Fuse predictions with calibration applied
        """
        # Apply calibration
        p_visual_cal = self._calibrate_probability(p_visual, self.temp_visual)
        p_clip_cal = self._calibrate_probability(p_clip, self.temp_clip)
        p_freq_cal = self._calibrate_probability(p_freq, self.temp_freq)
        
        # Use parent class fusion with calibrated probabilities
        return super().fuse(p_freq_cal, p_visual_cal, p_clip_cal)


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("SPECTRA-AI Improved Fusion System Test")
    print("=" * 60)
    
    # Test 1: Basic fusion
    print("\nTest 1: Basic Weighted Ensemble")
    fusion = ImprovedScoreFusion()
    
    test_cases = [
        (0.1, 0.8, 0.3, "High visual, medium CLIP"),
        (0.9, 0.9, 0.9, "All high - clearly fake"),
        (0.1, 0.1, 0.1, "All low - clearly real"),
        (0.5, 0.5, 0.5, "All medium - uncertain"),
    ]
    
    for p_freq, p_visual, p_clip, description in test_cases:
        final_p, verdict = fusion.fuse(p_freq, p_visual, p_clip)
        print(f"\n{description}")
        print(f"  Inputs: freq={p_freq:.2f}, visual={p_visual:.2f}, clip={p_clip:.2f}")
        print(f"  Output: final_p={final_p:.3f}, verdict={verdict}")
    
    # Test 2: Detailed metadata
    print("\n" + "=" * 60)
    print("Test 2: Fusion with Metadata")
    print("=" * 60)
    
    result = fusion.fuse_with_metadata(
        p_freq=0.2,
        p_visual=0.85,
        p_clip=0.4
    )
    
    print(f"\nFinal Probability: {result['final_p']:.3f}")
    print(f"Verdict: {result['verdict']}")
    print(f"Confidence: {result['confidence']:.3f}")
    print("\nBreakdown:")
    for detector, scores in result['breakdown'].items():
        print(f"  {detector.upper()}: p={scores['probability']:.3f}, "
              f"contribution={scores['contribution']:.3f}")
    
    # Test 3: Calibrated fusion
    print("\n" + "=" * 60)
    print("Test 3: Calibrated Fusion")
    print("=" * 60)
    
    calibrated_fusion = CalibratedScoreFusion(
        temp_visual=1.2,  # Less confident
        temp_clip=0.8,    # More confident
        temp_freq=1.0     # No change
    )
    
    print("\nSame inputs, with calibration:")
    final_p_cal, verdict_cal = calibrated_fusion.fuse(
        p_freq=0.2,
        p_visual=0.85,
        p_clip=0.4
    )
    
    print(f"  Uncalibrated: final_p={final_p:.3f}, verdict={verdict}")
    print(f"  Calibrated:   final_p={final_p_cal:.3f}, verdict={verdict_cal}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed")
    print("=" * 60)
