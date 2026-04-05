"""
save_analysis.py - Save SPECTRA-AI Analysis to MongoDB

This demonstrates how to save deepfake detection results to MongoDB
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid


async def save_deepfake_analysis():
    """Save a SPECTRA-AI deepfake analysis result to MongoDB"""
    
    print("=" * 70)
    print("SPECTRA-AI → MongoDB Integration Demo")
    print("=" * 70)
    
    # Connect to MongoDB
    print("\n📡 Connecting to MongoDB...")
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.spectra_ai
    collection = db.analysis_history
    print("✅ Connected to spectra_ai.analysis_history")
    
    # Simulate a SPECTRA-AI analysis result
    # (This is what your /analyze-image endpoint returns)
    analysis_result = {
        # Unique request ID
        "request_id": uuid.uuid4().hex,
        
        # Analysis type
        "type": "deepfake_image",
        
        # Timestamp
        "timestamp": datetime.utcnow(),
        
        # Input information
        "input": {
            "filename": "test_image.jpg",
            "original_size": {
                "width": 3072,
                "height": 4608
            },
            "processed_size": {
                "width": 1280,
                "height": 1920
            },
            "file_hash": "abc123def456789"  # For deduplication
        },
        
        # Analysis result
        "result": {
            "verdict": "REAL",
            "confidence": 0.85,
            "spectra_score": 32,  # 0-100 scale
            "faces_detected": 1,
            "processing_time_ms": 1058,
            
            # Per-face results
            "faces": [
                {
                    "face_id": 1,
                    "bbox": [100, 150, 400, 550],
                    "final_p": 0.32,  # Probability of being fake
                    "verdict": "REAL",
                    "det_score": 0.95,
                    
                    # Individual detector scores
                    "scores": {
                        "visual": 0.32,
                        "clip": 0.28,
                        "frequency": 0.35
                    }
                }
            ]
        },
        
        # System metadata
        "metadata": {
            "model_version": "efficientnet_b0",
            "api_version": "2.0.0",
            "device": "cpu",
            "pipeline": "original"
        },
        
        # Optional: User information
        "user": {
            "ip_address": "127.0.0.1",
            "user_agent": "Mozilla/5.0..."
        }
    }
    
    # Save to MongoDB
    print("\n💾 Saving analysis result...")
    insert_result = await collection.insert_one(analysis_result)
    print(f"✅ Saved successfully!")
    print(f"   MongoDB ID: {insert_result.inserted_id}")
    print(f"   Request ID: {analysis_result['request_id']}")
    
    # Retrieve and display
    print("\n🔍 Retrieving saved analysis...")
    saved = await collection.find_one({"request_id": analysis_result["request_id"]})
    
    if saved:
        print("✅ Found in database:")
        print(f"   Type: {saved['type']}")
        print(f"   Verdict: {saved['result']['verdict']}")
        print(f"   Confidence: {saved['result']['confidence']}")
        print(f"   Faces detected: {saved['result']['faces_detected']}")
        print(f"   Processing time: {saved['result']['processing_time_ms']}ms")
        print(f"   Timestamp: {saved['timestamp']}")
    
    # Show database statistics
    print("\n📊 Database Statistics:")
    total = await collection.count_documents({})
    real_count = await collection.count_documents({"result.verdict": "REAL"})
    fake_count = await collection.count_documents({"result.verdict": "FAKE"})
    
    print(f"   Total analyses: {total}")
    print(f"   REAL verdicts: {real_count}")
    print(f"   FAKE verdicts: {fake_count}")
    
    # Show recent analyses
    print("\n📋 Recent Analyses (last 5):")
    cursor = collection.find().sort("timestamp", -1).limit(5)
    recent = await cursor.to_list(length=5)
    
    for i, doc in enumerate(recent, 1):
        print(f"\n   {i}. {doc['input']['filename']}")
        print(f"      Verdict: {doc['result']['verdict']} ({doc['result']['confidence']:.2f})")
        print(f"      Timestamp: {doc['timestamp']}")
    
    print("\n" + "=" * 70)
    print("✅ SPECTRA-AI analysis successfully saved to MongoDB!")
    print("=" * 70)


async def query_examples():
    """Show some useful query examples"""
    
    print("\n" + "=" * 70)
    print("MongoDB Query Examples")
    print("=" * 70)
    
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.spectra_ai
    collection = db.analysis_history
    
    # Example 1: Find all FAKE verdicts
    print("\n1️⃣  Find all FAKE verdicts:")
    fake_analyses = await collection.find(
        {"result.verdict": "FAKE"}
    ).to_list(length=10)
    print(f"   Found {len(fake_analyses)} fake analyses")
    
    # Example 2: High-confidence detections
    print("\n2️⃣  Find high-confidence detections (>= 0.9):")
    high_conf = await collection.find(
        {"result.confidence": {"$gte": 0.9}}
    ).to_list(length=10)
    print(f"   Found {len(high_conf)} high-confidence analyses")
    
    # Example 3: Recent analyses (last hour)
    print("\n3️⃣  Find analyses from last hour:")
    from datetime import timedelta
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent = await collection.find(
        {"timestamp": {"$gte": one_hour_ago}}
    ).to_list(length=100)
    print(f"   Found {len(recent)} analyses in last hour")
    
    # Example 4: Multi-face images
    print("\n4️⃣  Find images with multiple faces:")
    multi_face = await collection.find(
        {"result.faces_detected": {"$gt": 1}}
    ).to_list(length=10)
    print(f"   Found {len(multi_face)} multi-face images")
    
    # Example 5: Search by filename
    print("\n5️⃣  Search by filename pattern:")
    pattern = await collection.find(
        {"input.filename": {"$regex": "test", "$options": "i"}}  # Case-insensitive
    ).to_list(length=10)
    print(f"   Found {len(pattern)} images matching 'test'")


if __name__ == "__main__":
    print("\n🚀 Running SPECTRA-AI MongoDB integration demo...\n")
    
    # Save an analysis
    asyncio.run(save_deepfake_analysis())
    
    # Show query examples
    asyncio.run(query_examples())
    
    print("\n🎯 Next steps:")
    print("1. Integrate this into main1.py")
    print("2. Auto-save every analysis")
    print("3. Build API endpoints to query history")
    print("4. Create analytics dashboard")
    print()
