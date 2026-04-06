# ai_models/face_recognition/detector.py

import cv2
from insightface.app import FaceAnalysis


class RetinaFaceDetector:
    def __init__(self):
        self.app = FaceAnalysis(
            name="buffalo_sc",  # lightweight model — buffalo_l is 500MB, too heavy for free tier,
            providers=["CPUExecutionProvider"]
        )
        self.app.prepare(ctx_id=0, det_size=(640, 640))

    def detect(self, image):
        faces = self.app.get(image)
        return faces

    def detect_and_align(self, img_bgr):
        """
        Used by Step 5 pipeline.
        Returns list of aligned face images (BGR).
        """

        faces = self.app.get(img_bgr)
        aligned_faces = []

        for face in faces:
            # Preferred: InsightFace aligned crop
            if hasattr(face, "crop_img") and face.crop_img is not None:
                aligned_faces.append(face.crop_img)
            else:
                # Fallback: crop using bounding box
                x1, y1, x2, y2 = map(int, face.bbox)
                crop = img_bgr[y1:y2, x1:x2]
                if crop.size > 0:
                    aligned_faces.append(crop)

        return aligned_faces
