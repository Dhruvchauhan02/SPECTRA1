# test_integration.py
"""
Test MongoDB Integration with SPECTRA-AI

Run this after integrating MongoDB to verify everything works.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_mongodb_integration():
    """Test MongoDB integration"""
    
    print("=" * 70)
    print("SPECTRA-AI MongoDB Integration Test")
    print("=" * 70)
    
    try:
        # Test 1: Import modules
        print("\n✅ Test 1: Importing modules...")
        from database import mongodb
        from crud import (
            save_deepfake_analysis,
            get_recent_analyses,
            get_statistics
        )
        print("✅ All modules imported successfully")
        
        # Test 2: Connect to MongoDB
        print("\n✅ Test 2: Connecting to MongoDB...")
        connected = await mongodb.connect(
            connection_string="mongodb://localhost:27017",
            database_name="spectra_ai_test"
        )
        
        if not connected:
            print("❌ MongoDB connection failed!")
            print("   Make sure MongoDB is running: Get-Service MongoDB")
            return False
        
        print("✅ MongoDB connected")
        
        # Test 3: Save a test analysis
        print("\n✅ Test 3: Saving test analysis...")
        collection = mongodb.get_collection("analysis_history")
        
        import uuid
        from datetime import datetime
        
        test_request_id = uuid.uuid4().hex
        
        doc_id = await save_deepfake_analysis(
            collection=collection,
            request_id=test_request_id,
            input_data={
                "filename": "test.jpg",
                "size": {"width": 1280, "height": 1920}
            },
            result={
                "verdict": "REAL",
                "confidence": 0.85,
                "spectra_score": 32,
                "faces_detected": 1
            },
            metadata={
                "model_version": "test",
                "api_version": "2.0.0"
            }
        )
        
        print(f"✅ Test analysis saved with ID: {doc_id}")
        
        # Test 4: Retrieve recent analyses
        print("\n✅ Test 4: Retrieving recent analyses...")
        recent = await get_recent_analyses(collection, limit=5)
        print(f"✅ Found {len(recent)} recent analyses")
        
        if recent:
            latest = recent[0]
            print(f"   Latest: {latest['request_id'][:16]}... | {latest['result']['verdict']}")
        
        # Test 5: Get statistics
        print("\n✅ Test 5: Getting statistics...")
        stats = await get_statistics(collection)
        print(f"✅ Statistics retrieved:")
        print(f"   Total analyses: {stats.get('total_analyses', 0)}")
        print(f"   Deepfake images: {stats.get('by_type', {}).get('deepfake_image', 0)}")
        
        # Test 6: Database stats
        print("\n✅ Test 6: Getting database stats...")
        db_stats = await mongodb.get_stats()
        if db_stats:
            print(f"✅ Database stats:")
            print(f"   Collections: {db_stats.get('collections', 0)}")
            print(f"   Total documents: {db_stats.get('counts', {}).get('total', 0)}")
        
        # Test 7: Clean up test data
        print("\n✅ Test 7: Cleaning up test data...")
        await collection.delete_one({"request_id": test_request_id})
        print("✅ Test data cleaned up")
        
        # Disconnect
        await mongodb.disconnect()
        print("\n✅ MongoDB disconnected")
        
        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 70)
        print("\n✅ MongoDB integration is working correctly!")
        print("✅ Ready to integrate with main1.py!")
        
        return True
        
    except ImportError as e:
        print("\n" + "=" * 70)
        print("❌ IMPORT ERROR")
        print("=" * 70)
        print(f"\nError: {e}")
        print("\nMake sure you've copied these files:")
        print("  - database.py → project root")
        print("  - crud.py → project root")
        print("  - api/history_endpoints.py → api folder")
        return False
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ TEST FAILED")
        print("=" * 70)
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("1. Is MongoDB running? Run: Get-Service MongoDB")
        print("2. Is Motor installed? Run: pip install motor")
        print("3. Are the files in the right location?")
        import traceback
        traceback.print_exc()
        return False


async def test_endpoints():
    """Test that endpoints are accessible"""
    print("\n" + "=" * 70)
    print("Testing API Endpoints")
    print("=" * 70)
    
    try:
        import httpx
        
        base_url = "http://localhost:8000"
        
        print("\n✅ Testing if server is running...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{base_url}/health")
                if response.status_code == 200:
                    print("✅ Server is running!")
                    
                    # Test history endpoint
                    print("\n✅ Testing /history/recent endpoint...")
                    response = await client.get(f"{base_url}/history/recent?limit=5")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ History endpoint working!")
                        print(f"   Found {data.get('count', 0)} recent analyses")
                    else:
                        print(f"⚠️  History endpoint returned: {response.status_code}")
                    
                else:
                    print(f"⚠️  Server returned: {response.status_code}")
                    
            except httpx.ConnectError:
                print("⚠️  Server not running")
                print("   Start server with: python -m api.main1")
                
    except ImportError:
        print("\n⚠️  httpx not installed (optional)")
        print("   Install with: pip install httpx")
        print("   Or test manually at: http://localhost:8000/docs")


if __name__ == "__main__":
    print("\n🚀 Starting MongoDB integration tests...\n")
    
    # Run database tests
    success = asyncio.run(test_mongodb_integration())
    
    if success:
        print("\n🎯 Next steps:")
        print("1. Copy files to your project:")
        print("   - database.py")
        print("   - crud.py")
        print("   - api/history_endpoints.py")
        print("\n2. Update main1.py with MongoDB integration")
        print("   See: main1_mongodb_changes.py")
        print("\n3. Start server: python -m api.main1")
        print("\n4. Test at: http://localhost:8000/docs")
        
        # Test endpoints if server is running
        asyncio.run(test_endpoints())
    else:
        print("\n⚠️  Please fix the errors above and try again")
    
    print()
