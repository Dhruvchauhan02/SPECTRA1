# tests/test_profile.py
import time
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_models.fake_news_detection import FakeNewsPipeline

print("Profiling Fake News Detection Pipeline\n")
print("=" * 60)

# Initialize
print("Initializing pipeline...")
start = time.time()
pipeline = FakeNewsPipeline(device="cpu")
print(f"✅ Init: {time.time()-start:.2f}s\n")

# Test text
text = "Sample article text for testing. " * 50

# Profile each component
print("Profiling components:")
print("-" * 60)

# 1. Text encoding
start = time.time()
embedding = pipeline._encode_text(text)
t_encode = time.time() - start
print(f"1. Text Encoding:       {t_encode*1000:>8.0f}ms")

# 2. Linguistic analysis
start = time.time()
ling = pipeline.linguistic_analyzer.analyze(text)
t_ling = time.time() - start
print(f"2. Linguistic Analysis: {t_ling*1000:>8.0f}ms")

# 3. Claim extraction
start = time.time()
claims = pipeline.claim_extractor.extract(text, max_claims=3)
t_claims = time.time() - start
print(f"3. Claim Extraction:    {t_claims*1000:>8.0f}ms")

# 4. Full analysis
print("\n" + "=" * 60)
start = time.time()
result = pipeline.analyze(text, enable_evidence_search=False)
t_total = time.time() - start
print(f"Total Analysis Time:    {t_total*1000:>8.0f}ms")

print("\n" + "=" * 60)
print(f"Bottleneck: Text Encoding is {t_encode/t_total*100:.0f}% of total time")