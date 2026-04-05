import numpy as np
from ai_models.face_recognition.matcher import FaceMatcher

# Load two embeddings (change filenames as needed)
emb1 = np.load("data/embeddings/aligned_0.npy")
emb2 = np.load("data/embeddings/aligned_1.npy")

matcher = FaceMatcher(threshold=0.6)
score, is_match = matcher.is_same_person(emb1, emb2)

print("Similarity Score:", score)

if is_match:
    print("✅ Same person")
else:
    print("❌ Different person")
