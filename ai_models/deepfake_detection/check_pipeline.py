from ai_models.deepfake_detection.pipeline_improved import ImprovedDeepfakePipeline
import os

print("=" * 60)
print("Pipeline Test")
print("=" * 60)

# Initialize
pipeline = ImprovedDeepfakePipeline(
    device="cpu",
    enable_frequency=True,
    strict_face_mode=True
)

print("✅ Pipeline initialized")

# Test on sample image (if available)
test_images = [
    "data/extracted-faces/aligned/test/test_img_from_gemini.png",
    #"data/extracted-faces/aligned/test/f1.jpg",
    "data/extracted-faces/aligned/test/r3.jpg"
]

found_test = False
for img_path in test_images:
    if os.path.exists(img_path):
        print(f"\n🖼️  Testing on: {img_path}")
        result = pipeline.analyze(img_path)
        
        print(f"  Status: {result['status']}")
        print(f"  Faces: {result.get('faces_detected', 0)}")
        
        if result.get('faces'):
            face = result['faces'][0]
            print(f"  Verdict: {face['verdict']}")
            print(f"  Visual: {face['detector_outputs']['visual']:.3f}")
            print(f"  CLIP: {face['detector_outputs']['clip']:.3f}")
            print(f"  Frequency: {face['detector_outputs']['frequency']:.3f}")
        
        found_test = True
        break

if not found_test:
    print("\n⚠️  No test images found, skipping analysis test")

print("\n✅ Pipeline test complete!")