from ai_models.deepfake_detection.fusion_improved import ImprovedScoreFusion

print("=" * 60)
print("Fusion Test")
print("=" * 60)

fusion = ImprovedScoreFusion(
    w_visual=0.50,
    w_clip=0.35,
    w_freq=0.15
)

# Test case: High visual, medium CLIP, low freq
final_p, verdict = fusion.fuse(
    p_freq=0.2,
    p_visual=0.85,
    p_clip=0.4
)

print(f"Input: visual=0.85, clip=0.4, freq=0.2")
print(f"Output: final_p={final_p:.3f}, verdict={verdict}")

expected_p = 0.50 * 0.85 + 0.35 * 0.4 + 0.15 * 0.2
print(f"Expected: {expected_p:.3f}")

assert abs(final_p - expected_p) < 0.001, "Fusion calculation incorrect!"
print("\n✅ Fusion test passed!")