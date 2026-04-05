import numpy as np

class ForensicCalibrator:
    def __init__(self):
        # TEMP weights (until freq detector is fixed)
        self.w_visual = 0.40
        self.w_freq   = 0.25   # REDUCED (unstable currently)
        self.w_clip   = 0.35

        # Stronger decision bands
        self.t_fake = 0.60
        self.t_real = 0.40

    def normalize(self, p):
        # Clamp
        p = max(0.001, min(0.999, float(p)))

        # Sigmoid sharpening
        return 1 / (1 + np.exp(-7 * (p - 0.5)))

    def fuse(self, p_visual, p_freq, p_clip):
        # 🚨 Clamp frequency (fix instability)
        p_freq = min(p_freq, 0.90)

        nv = self.normalize(p_visual)
        nf = self.normalize(p_freq)
        nc = self.normalize(p_clip)

        final = (
            self.w_visual * nv +
            self.w_freq   * nf +
            self.w_clip   * nc
        )

        return float(final)

    def verdict(self, final_p):
        if final_p >= self.t_fake:
            return "FAKE"
        elif final_p <= self.t_real:
            return "REAL"
        else:
            return "UNCERTAIN"
