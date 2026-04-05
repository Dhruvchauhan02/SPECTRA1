# tests/test_speed.py
import time
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_models.fake_news_detection import FakeNewsPipeline

# Initialize
print("Initializing pipeline...")
start = time.time()
pipeline = FakeNewsPipeline(device="cpu")
init_time = time.time() - start
print(f"✅ Initialization: {init_time:.2f}s")

# Test analysis
texts = [
    "SHOCKING: You WON'T BELIEVE what scientists found! " * 10,
    "The Federal Reserve announced interest rate decisions today. " * 10,
    "Amazing breakthrough! Doctors HATE this one trick! " * 10
]
for i, text in enumerate(texts, 1):
    start = time.time()
    result = pipeline.analyze(text)
    elapsed = time.time() - start
    print(f"Test {i}: {elapsed*1000:.0f}ms - {result['verdict']}")
    
print(f"\nTest text: {text[:80]}...")
print("\nAnalyzing text...")

# Warmup run
result = pipeline.analyze(text)

# Check if analysis actually worked
print("\n" + "="*60)
print("VERIFICATION:")
print("="*60)
print(f"Status: {result.get('status', 'MISSING')}")
print(f"Verdict: {result.get('verdict', 'MISSING')}")
print(f"Score: {result.get('spectra_score', 'MISSING')}/100")
print(f"Confidence: {result.get('confidence', 'MISSING'):.0%}")

if result.get('signals'):
    ling = result['signals'].get('linguistic', {})
    print(f"\nLinguistic Signals:")
    print(f"  Clickbait: {ling.get('has_clickbait', 'MISSING')}")
    print(f"  High Emotion: {ling.get('high_emotion', 'MISSING')}")
    print(f"  Excessive Caps: {ling.get('excessive_caps', 'MISSING')}")
else:
    print("\n⚠️ WARNING: No signals detected!")

print("\n" + "="*60)
print("PERFORMANCE TEST:")
print("="*60)

# Timed runs
times = []
for i in range(5):
    start = time.time()
    result = pipeline.analyze(text)
    elapsed = time.time() - start
    times.append(elapsed)
    print(f"Run {i+1}: {elapsed*1000:.0f}ms - Verdict: {result.get('verdict', 'ERROR')}")

avg_time = sum(times) / len(times)
print(f"\n📊 Average: {avg_time*1000:.0f}ms")
print(f"✅ Performance: {'GOOD' if avg_time < 1.0 else 'NEEDS OPTIMIZATION'}")