from deepface import DeepFace

class FaceEmbedder:
    def __init__(self, model_name="Facenet"):
        self.model_name = model_name

    def get_embedding(self, img_path):
        result = DeepFace.represent(
            img_path=img_path,
            model_name=self.model_name,
            enforce_detection=False  # important: faces are already cropped
        )
        return result[0]["embedding"]
