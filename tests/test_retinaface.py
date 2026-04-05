import cv2
import os
from ai_models.face_recognition.detector import RetinaFaceDetector
from ai_models.face_recognition.align import align_face

# Paths
IMAGE_PATH = "data/images/test2.jpg"
OUTPUT_DIR = "data/extracted-faces/aligned/test"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load image
image = cv2.imread(IMAGE_PATH)

# Detect faces
detector = RetinaFaceDetector()
faces = detector.detect(image)

print(f"Detected faces: {len(faces)}")

# Align & save faces
for i, face in enumerate(faces):
    aligned_face = align_face(image, face.kps)
    output_path = os.path.join(OUTPUT_DIR, f"aligned_{i}.jpg")
    cv2.imwrite(output_path, aligned_face)

print(f"Aligned faces saved to: {OUTPUT_DIR}")
