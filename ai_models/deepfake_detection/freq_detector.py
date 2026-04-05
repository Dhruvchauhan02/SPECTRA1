import cv2
import numpy as np

class FrequencyDetector:
    def __init__(self):
        self.alpha = 2.5

    def _analyze(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        magnitude = np.abs(fshift)

        magnitude = np.log1p(magnitude)

        h, w = magnitude.shape
        cx, cy = h // 2, w // 2
        r = min(cx, cy) // 4

        mask = np.ones((h, w), np.uint8)
        cv2.circle(mask, (cy, cx), r, 0, -1)

        high_freq = np.mean(magnitude[mask == 1])
        low_freq = np.mean(magnitude[mask == 0]) + 1e-8

        raw_score = high_freq / low_freq

        p_fake = 1.0 - np.exp(-self.alpha * raw_score)
        return float(np.clip(p_fake, 0.0, 1.0))

    # 🔥 REQUIRED by your pipeline
    def predict_proba(self, image):
        return self._analyze(image)
