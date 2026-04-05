from ai_models.deepfake_detection.pipeline import DeepfakePipeline


def main():
    pipeline = DeepfakePipeline(device="cpu")

    image_path = "data/extracted-faces/aligned/test/f4.jpg"   # change to your test image

    result = pipeline.analyze(image_path)

    print("\n--- FORENSIC ANALYSIS RESULT ---")
    print(f"Visual     P(fake): {result['p_visual']:.3f}")
    print(f"Frequency  P(fake): {result['p_freq']:.3f}")
    print(f"CLIP       P(fake): {result['p_clip']:.3f}")
    print("--------------------------------")
    print(f"Final      P(fake): {result['final_p']:.3f}")
    print(f"Verdict: {result['verdict']}")


if __name__ == "__main__":
    main()
