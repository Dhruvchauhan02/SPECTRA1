import os
import numpy as np
from ai_models.face_recognition.embedder import FaceEmbedder

# Folder containing aligned faces from Step 2
input_folder = "data/extracted-faces/aligned/test"

# Folder to store embeddings
output_folder = "data/embeddings"
os.makedirs(output_folder, exist_ok=True)

# Initialize embedder
embedder = FaceEmbedder(model_name="Facenet")

# Process each aligned face image
for file in os.listdir(input_folder):
    if file.lower().endswith((".jpg", ".png", ".jpeg")):
        img_path = os.path.join(input_folder, file)

        try:
            embedding = embedder.get_embedding(img_path)

            # Save embedding as .npy file
            save_path = os.path.join(output_folder, file.rsplit(".", 1)[0] + ".npy")
            np.save(save_path, embedding)

            print(f"✅ {file} → saved to {save_path}")

        except Exception as e:
            print(f"❌ {file} → error: {e}")
