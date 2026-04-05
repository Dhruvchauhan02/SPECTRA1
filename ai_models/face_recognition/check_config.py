from config import settings

print("=" * 60)
print("Configuration Test")
print("=" * 60)

print(f"✓ API Title: {settings.API_TITLE}")
print(f"✓ Device: {settings.DEVICE}")
print(f"✓ Face Threshold: {settings.FACE_CONFIDENCE_THRESHOLD}")
print(f"✓ Fusion Weights: Visual={settings.WEIGHT_VISUAL}, CLIP={settings.WEIGHT_CLIP}, Freq={settings.WEIGHT_FREQUENCY}")
print(f"✓ Total Weight: {settings.WEIGHT_VISUAL + settings.WEIGHT_CLIP + settings.WEIGHT_FREQUENCY}")

settings.validate_weights()
settings.validate_thresholds()

print("\n✅ All configuration tests passed!")