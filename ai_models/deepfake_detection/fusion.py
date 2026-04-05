class ScoreFusion:
    def __init__(self):
        self.threshold = 0.55

    def fuse(self, p_freq, p_visual, p_clip):
        final_p = p_visual

        if final_p >= self.threshold:
            verdict = "FAKE"
        else:
            verdict = "REAL"

        return final_p, verdict
