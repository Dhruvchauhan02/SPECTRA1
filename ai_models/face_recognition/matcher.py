import numpy as np
from numpy.linalg import norm

class FaceMatcher:
    def __init__(self, threshold=0.6):
        self.threshold = threshold

    def cosine_similarity(self, emb1, emb2):
        return np.dot(emb1, emb2) / (norm(emb1) * norm(emb2))

    def is_same_person(self, emb1, emb2):
        score = self.cosine_similarity(emb1, emb2)
        return score, score >= self.threshold
