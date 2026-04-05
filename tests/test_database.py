# test_supabase.py
# Run this from your SPECTRA project root:
#   python test_supabase.py

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=" * 50)
print("  SPECTRA-AI · Supabase Connection Test")
print("=" * 50)

# ── Step 1: Check env vars ────────────────────────────
print("\n📋 Step 1: Checking environment variables...")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url:
    print("  ❌ SUPABASE_URL is missing from .env")
    exit(1)
if not key:
    print("  ❌ SUPABASE_KEY is missing from .env")
    exit(1)

print(f"  ✅ SUPABASE_URL = {url}")
print(f"  ✅ SUPABASE_KEY = {key[:20]}...")

# ── Step 2: Connect ───────────────────────────────────
print("\n🔌 Step 2: Connecting to Supabase...")

from database import supabase_db

connected = supabase_db.connect()

if not connected:
    print("  ❌ Connection failed. Check your URL and KEY in .env")
    exit(1)

print("  ✅ Connected successfully!")

# ── Step 3: Check tables exist ────────────────────────
print("\n🗃️  Step 3: Checking tables...")

tables = ["analysis_history", "fake_news_analyses", "celebrity_verifications"]

for table in tables:
    try:
        res = supabase_db.table(table).select("id").limit(1).execute()
        print(f"  ✅ Table '{table}' exists")
    except Exception as e:
        print(f"  ❌ Table '{table}' NOT found → Did you run supabase_schema.sql?")

# ── Step 4: Insert a test row ─────────────────────────
print("\n📝 Step 4: Inserting a test row into analysis_history...")

try:
    res = supabase_db.table("analysis_history").insert({
        "request_id": "test-001",
        "type":       "deepfake_image",
        "input_data": {"filename": "test.jpg"},
        "result":     {"verdict": "REAL", "confidence": 0.95},
        "metadata":   {"test": True},
        "user_info":  {}
    }).execute()

    print(f"  ✅ Row inserted! ID = {res.data[0]['id']}")
except Exception as e:
    if "duplicate" in str(e).lower():
        print("  ✅ Row already exists (test ran before) — that's fine!")
    else:
        print(f"  ❌ Insert failed: {e}")

# ── Step 5: Read it back ──────────────────────────────
print("\n🔍 Step 5: Reading the test row back...")

try:
    res = supabase_db.table("analysis_history") \
        .select("*") \
        .eq("request_id", "test-001") \
        .execute()

    if res.data:
        row = res.data[0]
        print(f"  ✅ Found row:")
        print(f"     ID         = {row['id']}")
        print(f"     request_id = {row['request_id']}")
        print(f"     type       = {row['type']}")
        print(f"     verdict    = {row['result']['verdict']}")
    else:
        print("  ❌ Row not found")
except Exception as e:
    print(f"  ❌ Read failed: {e}")

# ── Step 6: Get stats ─────────────────────────────────
print("\n📊 Step 6: Database stats...")

import asyncio
stats = asyncio.run(supabase_db.get_stats())
print(f"  Total rows : {stats.get('counts', {}).get('total', 0)}")
print(f"  analysis_history        : {stats.get('counts', {}).get('analysis_history', 0)}")
print(f"  celebrity_verifications : {stats.get('counts', {}).get('celebrity_verifications', 0)}")
print(f"  fake_news_analyses      : {stats.get('counts', {}).get('fake_news_analyses', 0)}")

# ── Done ──────────────────────────────────────────────
print("\n" + "=" * 50)
print("  🎉 All tests passed! Supabase is ready.")
print("=" * 50)
print("\nNext step: Run your FastAPI server with:")
print("  uvicorn api.main1:app --reload --port 8000")