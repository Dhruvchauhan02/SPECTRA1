import torch
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel


class CLIPDetector:
    def __init__(self, device="cpu"):
        self.device = device

        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        self.model.eval()

        self.prompts = [
            "a real photograph of a person",
            "an AI generated face",
            "a synthetic human portrait",
            "a deepfake image"
        ]

    @torch.no_grad()
    def predict_proba(self, img_bgr):
        img_rgb = img_bgr[:, :, ::-1]
        image = Image.fromarray(img_rgb)

        inputs = self.processor(
            text=self.prompts,
            images=image,
            return_tensors="pt",
            padding=True
        ).to(self.device)

        outputs = self.model(**inputs)

        logits = outputs.logits_per_image
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()

        # AI-related prompts are index 1,2,3
        p_fake = float(np.mean(probs[1:]))

        return p_fake
