import cv2
import numpy as np

def preprocess_face(face_img):
    # Resize
    face = cv2.resize(face_img, (112, 112))

    # BGR → RGB
    face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

    # Convert to float32
    face = face.astype(np.float32)

    # Normalize to [-1, 1]
    face = (face - 127.5) / 128.0

    # HWC → CHW
    face = np.transpose(face, (2, 0, 1))

    # Add batch dimension
    face = np.expand_dims(face, axis=0)

    return face
