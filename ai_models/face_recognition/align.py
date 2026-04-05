# ai_models/face_recognition/align.py

import cv2
import numpy as np
from .config import IMAGE_SIZE


def align_face(image, landmarks):
    """
    landmarks: (5, 2) -> left eye, right eye, nose, left mouth, right mouth
    """
    src = np.array(landmarks, dtype=np.float32)

    dst = np.array([
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041]
    ], dtype=np.float32)

    dst[:, 0] *= IMAGE_SIZE / 112
    dst[:, 1] *= IMAGE_SIZE / 112

    transform = cv2.estimateAffinePartial2D(src, dst)[0]
    aligned = cv2.warpAffine(image, transform, (IMAGE_SIZE, IMAGE_SIZE))

    return aligned
