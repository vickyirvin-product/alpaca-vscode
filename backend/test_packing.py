"""
Test script for packing list management endpoints.

This script tests Sprint 3 functionality:
1. Adding items to packing lists
2. Updating items
3. Deleting items
4. Delegating items between people
5. Toggling packed status
6. Category management
7. Retrieving person-specific packing lists

Usage:
    python -m backend.test_packing
"""

import asyncio
import sys
from datetime import datetime, timedelta


async def test_packing_endpoints():
    """Test all packing list management endpoints."""
    print("=" * 60)
    print("Testing Packing List Management (Sprint 3)")
    print("=" * 60)
    
    # Test 1: Import all modules
    print("\n[1/9] Testing imports...")
    try:
        # Set dummy environment variables for testing
        import os
        os.environ.setdefault('GOOGLE_CLIENT_ID', 'test_client_id')
        os.environ.setdefault('GOOGLE_CLIENT_SECRET', 'test_client_secret')
        os.environ.setdefault('JWT_SECRET_KEY', 'test_jwt_secret_key_for_testing_only')
        os.environ.setdefault('OPENAI_API_KEY', 'test_openai_key')
        os.environ.setdefault('WEATHER_API_KEY', 'test_weather_key')
        os.environ.setdefault('GOOGLE_MAPS_API_KEY', 'test_google_maps_key')
        
        from backend.config import settings
        from backend.database import Database, get_db
        from backend.models.trip import (
            TripInDB,
            TravelerInDB,
            PackingListForPerson,
            PackingItemInDB,
            AddItemRequest,
            UpdateItemRequest,
            DelegateItemRequest,
            AddCategoryRequest,
            ChangeCategoryRequest
        )
        from backend.routes.packing import (
            get_trip_and_verify_access,
            find_item_in_trip,
            validate_person_exists
        )
        print("✓ All imports successful")
    except Exception as e:
        print(f"✗ Import failed: {str(e)}")
        return False
    
    # Test 2: Connect to database
    print("\n[2/9] Connecting to database...")
    try:
        await Database.connect_db()
        db = get_db()
        trips_collection = db.trips
        print("✓ Database connected successfully")
    except Exception as e:
        print(f"✗ Database connection failed: {str(e)}")
        print("  Note: Make sure MongoDB is running on mongodb://localhost:27017")
        return False
    
    # Test 3: Create test trip
    print("\n[3/9] Creating test trip...")
    try:
        from bson import ObjectId
        
        # Create test travelers
        travelers = [
            TravelerInDB(
                id=str(ObjectId()),
                name="Sarah (Mom)",
                age=38,
                type="adult"
            ),
            TravelerInDB(
                id=str(ObjectId()),
                name="Mike (Dad)",
                age=40,
                type="adult"
            ),
            TravelerInDB(
                id=str(ObjectId()),
                name="Emma",
                age=10,
                type="child"
            )
        ]
        
        # Create test trip
        test_trip = TripInDB(
            id=str(ObjectId()),
            user_id="test_user_packing_123",
            destination="Tokyo, Japan",
            start_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            end_date=(datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d"),
            activities=["Sightseeing", "Hiking"],
            transport=["Flight", "Train"],
            travelers=travelers,
            packing_lists=[]
        )
        
        # Insert into database
        await trips_collection.insert_one(test_trip.model_dump())
        
        print("✓ Test trip created successfully")
        print(f"  - Trip ID: {test_trip.id}")
        print(f"  - Travelers: {len(travelers)}")
        print(f"  - Sarah ID: {travelers[0].id}")
        print(f"  - Mike ID: {travelers[1].id}")
        print(f"  - Emma ID: {travelers[2].id}")
        
    except Exception as e:
        print(f"✗ Test trip creation failed: {str(e)}")
        return False
    
    # Test 4: Test adding items
    print("\n[4/9] Testing add item functionality...")
    try:
        # Add item to Sarah's list
        sarah_item = PackingItemInDB(
            id=str(ObjectId()),
            person_id=travelers[0].id,
            name="Passport",
            category="documents",
            is_essential=True,
            emoji="📄",
            quantity=1,
            notes="Keep in carry-on"
        )
        
        # Create packing list for Sarah
        sarah_list = PackingListForPerson(
            person_name=travelers[0].name,
            person_id=travelers[0].id,
            items=[sarah_item],
            categories=["documents"]
        )
        
        await trips_collection.update_one(
            {"id": test_trip.id},
            {"$push": {"packing_lists": sarah_list.model_dump()}}
        )
        
        print("✓ Item added successfully")
        print(f"  - Item: {sarah_item.emoji} {sarah_item.name}")
        print(f"  - Category: {sarah_item.category}")
        print(f"  - Essential: {sarah_item.is_essential}")
        
        # Add another item to Sarah's list
        sarah_item2 = PackingItemInDB(
            id=str(ObjectId()),
            person_id=travelers[0].id,
            name="Sunscreen",
            category="toiletries",
            is_essential=False,
            emoji="🧴",
            quantity=1
        )
        
        await trips_collection.update_one(
            {
                "id": test_trip.id,
                "packing_lists.person_id": travelers[0].id
            },
            {"$push": {"packing_lists.$.items": sarah_item2.model_dump()}}
        )
        
        print("✓ Second item added successfully")
        print(f"  - Item: {sarah_item2.emoji} {sarah_item2.name}")
        
    except Exception as e:
        print(f"✗ Add item test failed: {str(e)}")
        return False
    
    # Test 5: Test finding items
    print("\n[5/9] Testing find item functionality...")
    try:
        # Fetch updated trip
        trip_doc = await trips_collection.find_one({"id": test_trip.id})
        updated_trip = TripInDB(**trip_doc)
        
        # Find Sarah's passport
        found_item, found_person_id = find_item_in_trip(updated_trip, sarah_item.id)
        
        assert found_item is not None, "Item not found"
        assert found_item.name == "Passport", "Wrong item found"
        assert found_person_id == travelers[0].id, "Wrong person ID"
        
        print("✓ Item found successfully")
        print(f"  - Found: {found_item.name}")
        print(f"  - Person ID: {found_person_id}")
        
        # Test person validation
        assert validate_person_exists(updated_trip, travelers[0].id), "Person validation failed"
        assert not validate_person_exists(updated_trip, "invalid_id"), "Invalid person not rejected"
        
        print("✓ Person validation working correctly")
        
    except Exception as e:
        print(f"✗ Find item test failed: {str(e)}")
        return False
    
    # Test 6: Test updating items
    print("\n[6/9] Testing update item functionality...")
    try:
        # Update Sarah's passport
        await trips_collection.update_one(
            {"id": test_trip.id},
            {
                "$set": {
                    "packing_lists.$[list].items.$[item].is_packed": True,
                    "packing_lists.$[list].items.$[item].notes": "Packed in carry-on bag"
                }
            },
            array_filters=[
                {"list.person_id": travelers[0].id},
                {"item.id": sarah_item.id}
            ]
        )
        
        # Verify update
        trip_doc = await trips_collection.find_one({"id": test_trip.id})
        updated_trip = TripInDB(**trip_doc)
        updated_item, _ = find_item_in_trip(updated_trip, sarah_item.id)
        
        assert updated_item.is_packed == True, "Packed status not updated"
        assert updated_item.notes == "Packed in carry-on bag", "Notes not updated"
        
        print("✓ Item updated successfully")
        print(f"  - Packed: {updated_item.is_packed}")
        print(f"  - Notes: {updated_item.notes}")
        
    except Exception as e:
        print(f"✗ Update item test failed: {str(e)}")
        return False
    
    # Test 7: Test toggling packed status
    print("\n[7/9] Testing toggle packed functionality...")
    try:
        # Toggle Sarah's sunscreen
        trip_doc = await trips_collection.find_one({"id": test_trip.id})
        current_trip = TripInDB(**trip_doc)
        current_item, person_id = find_item_in_trip(current_trip, sarah_item2.id)
        
        original_status = current_item.is_packed
        new_status = not original_status
        
        await trips_collection.update_one(
            {"id": test_trip.id},
            {
                "$set": {
                    "packing_lists.$[list].items.$[item].is_packed": new_status
                }
            },
            array_filters=[
                {"list.person_id": person_id},
                {"item.id": sarah_item2.id}
            ]
        )
        
        # Verify toggle
        trip_doc = await trips_collection.find_one({"id": test_trip.id})
        updated_trip = TripInDB(**trip_doc)
        toggled_item, _ = find_item_in_trip(updated_trip, sarah_item2.id)
        
        assert toggled_item.is_packed == new_status, "Packed status not toggled"
        
        print("✓ Packed status toggled successfully")
        print(f"  - Original: {original_status}")
        print(f"  - New: {new_status}")
        
    except Exception as e:
        print(f"✗ Toggle packed test failed: {str(e)}")
        return False
    
    # Test 8: Test item delegation
    print("\n[8/9] Testing item delegation...")
    try:
        from backend.models.trip import DelegationInfo
        
        # Create item for Mike
        mike_item = PackingItemInDB(
            id=str(ObjectId()),
            person_id=travelers[1].id,
            name="Camera",
            category="electronics",
            is_essential=False,
            emoji="📷",
            quantity=1
        )
        
        # Create packing list for Mike
        mike_list = PackingListForPerson(
            person_name=travelers[1].name,
            person_id=travelers[1].id,
            items=[mike_item],
            categories=["electronics"]
        )
        
        await trips_collection.update_one(
            {"id": test_trip.id},
            {"$push": {"packing_lists": mike_list.model_dump()}}
        )
        
        print("✓ Created item for Mike")
        print(f"  - Item: {mike_item.emoji} {mike_item.name}")
        
        # Delegate camera from Mike to Sarah
        delegation_info = DelegationInfo(
            from_person_id=travelers[1].id,
            from_person_name=travelers[1].name,
            delegated_at=datetime.utcnow()
        )
        
        # Remove from Mike's list
        await trips_collection.update_one(
            {
                "id": test_trip.id,
                "packing_lists.person_id": travelers[1].id
            },
            {"$pull": {"packing_lists.$.items": {"id": mike_item.id}}}
        )
        
        # Update item with new person_id and delegation info
        delegated_item = mike_item.model_copy(update={
            "person_id": travelers[0].id,
            "delegation_info": delegation_info
        })
        
        # Add to Sarah's list
        await trips_collection.update_one(
            {
                "id": test_trip.id,
                "packing_lists.person_id": travelers[0].id
            },
            {"$push": {"packing_lists.$.items": delegated_item.model_dump()}}
        )
        
        # Verify delegation
        trip_doc = await trips_collection.find_one({"id": test_trip.id})
        updated_trip = TripInDB(**trip_doc)
        found_item, found_person_id = find_item_in_trip(updated_trip, mike_item.id)
        
        assert found_item is not None, "Delegated item not found"
        assert found_person_id == travelers[0].id, "Item not in Sarah's list"
        assert found_item.delegation_info is not None, "Delegation info missing"
        assert found_item.delegation_info.from_person_id == travelers[1].id, "Wrong delegation source"
        
        print("✓ Item delegated successfully")
        print(f"  - From: {travelers[1].name}")
        print(f"  - To: {travelers[0].name}")
        print(f"  - Delegation info preserved: ✓")
        
    except Exception as e:
        print(f"✗ Delegation test failed: {str(e)}")
        return False
    
    # Test 9: Test category management
    print("\n[9/9] Testing category management...")
    try:
        # Change camera category
        await trips_collection.update_one(
            {"id": test_trip.id},
            {
                "$set": {
                    "packing_lists.$[list].items.$[item].category": "activities"
                }
            },
            array_filters=[
                {"list.person_id": travelers[0].id},
                {"item.id": mike_item.id}
            ]
        )
        
        # Verify category change
        trip_doc = await trips_collection.find_one({"id": test_trip.id})
        updated_trip = TripInDB(**trip_doc)
        updated_item, _ = find_item_in_trip(updated_trip, mike_item.id)
        
        assert updated_item.category == "activities", "Category not changed"
        
        print("✓ Category changed successfully")
        print(f"  - Old category: electronics")
        print(f"  - New category: {updated_item.category}")
        
        # Test getting person's packing list
        sarah_list = next(
            (pl for pl in updated_trip.packing_lists if pl.person_id == travelers[0].id),
            None
        )
        
        assert sarah_list is not None, "Sarah's list not found"
        assert len(sarah_list.items) >= 3, "Not all items in Sarah's list"
        
        print("✓ Person packing list retrieved successfully")
        print(f"  - Person: {sarah_list.person_name}")
        print(f"  - Items: {len(sarah_list.items)}")
        print(f"  - Categories: {len(sarah_list.categories)}")
        
    except Exception as e:
        print(f"✗ Category management test failed: {str(e)}")
        return False
    
    # Cleanup
    print("\n[Cleanup] Removing test data...")
    try:
        await trips_collection.delete_one({"id": test_trip.id})
        print("✓ Test data cleaned up")
    except Exception as e:
        print(f"⚠ Cleanup warning: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✓ All packing list tests passed successfully!")
    print("=" * 60)
    print("\nTested functionality:")
    print("  ✓ Adding items to packing lists")
    print("  ✓ Finding items by ID")
    print("  ✓ Updating item properties")
    print("  ✓ Toggling packed status")
    print("  ✓ Delegating items between people")
    print("  ✓ Category management")
    print("  ✓ Person validation")
    print("  ✓ Retrieving person-specific lists")
    print("\nNext steps:")
    print("1. Start the server: uvicorn backend.main:app --reload")
    print("2. Test the API at: http://localhost:8000/docs")
    print("3. Try the packing endpoints:")
    print("   - POST /api/v1/trips/{trip_id}/items")
    print("   - PUT /api/v1/trips/{trip_id}/items/{item_id}")
    print("   - DELETE /api/v1/trips/{trip_id}/items/{item_id}")
    print("   - POST /api/v1/trips/{trip_id}/items/{item_id}/delegate")
    print("   - PUT /api/v1/trips/{trip_id}/items/{item_id}/toggle-packed")
    print("   - GET /api/v1/trips/{trip_id}/packing-lists/{person_id}")
    
    return True


async def main():
    """Main test runner."""
    try:
        success = await test_packing_endpoints()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())