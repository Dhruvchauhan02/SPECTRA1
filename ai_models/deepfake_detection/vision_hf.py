import torch
import numpy as np
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification


class VisionHFDetector:
    def __init__(self, device="cpu"):
        self.device = device

        self.processor = AutoImageProcessor.from_pretrained(
            "dima806/deepfake_vs_real_image_detection"
        )
        self.model = AutoModelForImageClassification.from_pretrained(
            "dima806/deepfake_vs_real_image_detection"
        ).to(device)

        self.model.eval()

    @torch.no_grad()
    def predict_proba(self, img_bgr):
        # 🔒 SAFETY CHECK (CRITICAL)
        if img_bgr is None:
            return 0.0

        if not isinstance(img_bgr, np.ndarray):
            return 0.0

        if img_bgr.size == 0:
            return 0.0

        # Convert BGR → RGB safely
        img_rgb = img_bgr[:, :, ::-1]

        # Continue normal inference
        inputs = self.processor(images=img_rgb, return_tensors="pt").to(self.device)
        outputs = self.model(**inputs)

        probs = outputs.logits.softmax(dim=-1)[0]

        # Assumes index 1 = fake (adjust if needed)
        return float(probs[1])

