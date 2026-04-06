# ai_models/deepfake_detection/pipeline.py
"""
SPECTRA-AI Deepfake Detection Pipeline
RESTORED: Uses only EfficientNet (your trained model)
"""

import cv2
import logging
from typing import Dict

from ai_models.face_recognition.detector import RetinaFaceDetector
from ai_models.deepfake_detection.efficientnet_detector import EfficientNetDeepfakeDetector
# CLIPDetector disabled — too heavy for free deployment (600MB download)
# Fusion uses only EfficientNet score anyway
class _DummyCLIP:
    def predict_proba(self, img): return 0.5

from ai_models.deepfake_detection.fusion import ScoreFusion

logger = logging.getLogger("spectra.pipeline")


class DeepfakePipeline:
    """
    Original working pipeline
    Uses ONLY your EfficientNet model (no dilution from other detectors)
    """
    
    def __init__(self, device="cpu", model_path="efficientnet_b0_spectra.pth"):
        """
        Initialize pipeline with original configuration
        
        Args:
            device: Computation device
            model_path: Path to your trained EfficientNet model
        """
        logger.info("Initializing DeepfakePipeline (ORIGINAL - EfficientNet only)")
        
        self.face_detector = RetinaFaceDetector()
        
        self.visual = EfficientNetDeepfakeDetector(model_path)
        
        # CLIP disabled — using dummy (not used in fusion anyway)
        self.clip = _DummyCLIP()
        
        # Fusion uses ONLY visual score
        self.fusion = ScoreFusion()
        
        logger.info("✅ Pipeline ready (using ONLY your EfficientNet model)")
    def analyze(self, image_path):
        """ 
        Analyze image - EXACT original behavior
        
        Args:
            image_path: Path to image file
        
        Returns:
            Detection results
        """
        img_bgr = cv2.imread(image_path)

        if img_bgr is None:
            return {
                "status": "error",
                "message": "Image could not be read"
            }

        faces = self.face_detector.detect(img_bgr)

        face_results = []

        real_faces_detected = 0 if faces is None else len(faces)
        '''
        # ⭐ Fallback (if no faces detected, analyze whole image)
        if real_faces_detected == 0:
            logger.warning("No face detected in image")
            return {
                "status": "failed",
                "error": "NO_FACE_DETECTED",
                "faces_detected": 0,
                "faces": []
        }
        '''
        h, w = img_bgr.shape[:2]

        if real_faces_detected == 0:
            logger.warning("⚠️ No face detected → using fallback (full image)")
        # Use full image as a single face
            faces = [{
                "bbox": [0, 0, w, h],
                "det_score": 1.0
            }]

            real_faces_detected = 1

        # ⭐ Multi-face (analyze each detected faces

        for idx, f in enumerate(faces):

            x1, y1, x2, y2 = map(int, f["bbox"])

            h, w, _ = img_bgr.shape
            margin_x = int((x2 - x1) * 0.2)
            margin_y = int((y2 - y1) * 0.2)
            x1 = max(0, x1 - margin_x)
            y1 = max(0, y1 - margin_y)
            x2 = min(w, x2 + margin_x)
            y2 = min(h, y2 + margin_y)

            face = img_bgr[y1:y2, x1:x2]

            p_visual = self.visual.predict_proba(face)
            p_clip = self.clip.predict_proba(face)
            p_freq = 0.0

            # Fusion uses ONLY p_visual (ignores others)
            final_p, verdict = self.fusion.fuse(
                p_freq=p_freq,
                p_visual=p_visual,
                p_clip=p_clip
            )

            face_results.append({
                "face_id": idx,
                "final_p": float(final_p),
                "verdict": verdict,
                "det_score": float(f["det_score"])
            })

        return {
            "status": "success",
            "faces_detected": real_faces_detected,
            "faces": face_results
        }


# For backwards compatibility
ImprovedDeepfakePipeline = DeepfakePipeline