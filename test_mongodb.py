"""
test_mongodb.py - MongoDB Connection Test

Run this after installing MongoDB to verify everything works!
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime


async def test_connection():
    """Test MongoDB connection and basic operations"""
    
    print("=" * 70)
    print("MongoDB Connection Test")
    print("=" * 70)
    
    try:
        # 1. Connect to MongoDB
        print("\n📡 Step 1: Connecting to MongoDB...")
        client = AsyncIOMotorClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Connected successfully!")
        
        # 2. Get database
        print("\n📂 Step 2: Getting database 'spectra_ai'...")
        db = client.spectra_ai
        print("✅ Database ready")
        
        # 3. Get collection
        print("\n📋 Step 3: Getting collection 'test_collection'...")
        collection = db.test_collection
        print("✅ Collection ready")
        
        # 4. Insert a document
        print("\n📝 Step 4: Inserting test document...")
        test_doc = {
            "type": "connection_test",
            "message": "Hello from SPECTRA-AI!",
            "timestamp": datetime.utcnow(),
            "confidence": 0.95,
            "metadata": {
                "test": True,
                "version": "1.0"
            }
        }
        
        result = await collection.insert_one(test_doc)
        print(f"✅ Document inserted!")
        print(f"   Generated ID: {result.inserted_id}")
        
        # 5. Find the document
        print("\n🔍 Step 5: Finding the document...")
        found_doc = await collection.find_one({"type": "connection_test"})
        
        if found_doc:
            print("✅ Document found!")
            print(f"   ID: {found_doc['_id']}")
            print(f"   Message: {found_doc['message']}")
            print(f"   Timestamp: {found_doc['timestamp']}")
            print(f"   Confidence: {found_doc['confidence']}")
        else:
            print("❌ Document not found!")
            return False
        
        # 6. Update the document
        print("\n✏️  Step 6: Updating document...")
        update_result = await collection.update_one(
            {"type": "connection_test"},
            {"$set": {
                "reviewed": True,
                "confidence": 0.99,
                "updated_at": datetime.utcnow()
            }}
        )
        print(f"✅ Updated {update_result.modified_count} document(s)")
        
        # 7. Verify update
        updated_doc = await collection.find_one({"type": "connection_test"})
        print(f"   New confidence: {updated_doc['confidence']}")
        print(f"   Reviewed: {updated_doc.get('reviewed', False)}")
        
        # 8. Count documents
        print("\n📊 Step 7: Counting documents...")
        count = await collection.count_documents({})
        print(f"✅ Total documents in collection: {count}")
        
        # 9. Find multiple documents
        print("\n📚 Step 8: Finding all documents...")
        cursor = collection.find().limit(5)
        docs = await cursor.to_list(length=5)
        print(f"✅ Found {len(docs)} document(s)")
        
        # 10. Clean up
        print("\n🗑️  Step 9: Cleaning up test data...")
        delete_result = await collection.delete_many({"type": "connection_test"})
        print(f"✅ Deleted {delete_result.deleted_count} test document(s)")
        
        # Final verification
        final_count = await collection.count_documents({})
        print(f"📊 Final document count: {final_count}")
        
        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 70)
        print("\n✅ MongoDB is working correctly with Python!")
        print("✅ You're ready to integrate with SPECTRA-AI!")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ TEST FAILED")
        print("=" * 70)
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("1. Is MongoDB installed? Run: mongod --version")
        print("2. Is MongoDB running? Run: Get-Service MongoDB")
        print("3. Is it on port 27017? Check MongoDB config")
        print("4. Did you install Motor? Run: pip install motor")
        
        return False


if __name__ == "__main__":
    print("\n🚀 Starting MongoDB connection test...\n")
    success = asyncio.run(test_connection())
    
    if success:
        print("\n🎯 Next steps:")
        print("1. Run: python save_analysis.py")
        print("2. Try MongoDB Compass to see your data visually")
        print("3. Ready to integrate with SPECTRA-AI!")
    else:
        print("\n⚠️  Please fix the errors above and try again")
    
    print()
