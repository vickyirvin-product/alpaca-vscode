"""
Test script to verify activity-specific category fix.

This test ensures that:
1. Activity items use the exact activity name as the category (e.g., "skiing/snowboarding")
2. All travelers get the same activity items (unless age-inappropriate)
3. No generic "activities" category is used
"""

import asyncio
import sys
from services.llm_service import llm_service
from models.trip import TravelerInDB, WeatherInfo


async def test_skiing_trip():
    """Test a skiing trip to ensure activity categories are correct."""
    print("\n" + "="*80)
    print("TEST: Skiing Trip - Activity Category Validation")
    print("="*80)
    
    # Create test travelers
    travelers = [
        TravelerInDB(
            id="adult-1",
            name="Sarah",
            age=35,
            type="adult"
        ),
        TravelerInDB(
            id="child-1",
            name="Emma",
            age=8,
            type="child"
        ),
        TravelerInDB(
            id="infant-1",
            name="Baby",
            age=1,
            type="infant"
        )
    ]
    
    # Weather data
    weather_data = WeatherInfo(
        avg_temp=25,
        temp_unit="F",
        conditions=["snowy"],
        recommendation="Pack warm layers and winter gear"
    )
    
    # Activities - note the exact format
    activities = ["Skiing/Snowboarding"]
    
    print(f"\n📋 Test Setup:")
    print(f"  Destination: Aspen, Colorado")
    print(f"  Duration: 5 days")
    print(f"  Activities: {activities}")
    print(f"  Travelers: {len(travelers)}")
    for t in travelers:
        print(f"    - {t.name} ({t.age}y, {t.type})")
    
    # Generate packing lists
    print(f"\n🚀 Generating packing lists...")
    packing_lists = await llm_service.generate_packing_lists(
        destination="Aspen, Colorado",
        start_date="2026-03-01",
        end_date="2026-03-05",
        travelers=travelers,
        weather_data=weather_data,
        activities=activities,
        transport=["Flying", "Rental Car"]
    )
    
    print(f"\n✅ Successfully generated {len(packing_lists)} packing lists")
    
    # Validate results
    print(f"\n🔍 VALIDATION RESULTS:")
    print("="*80)
    
    all_valid = True
    expected_category = "skiing/snowboarding"
    
    for packing_list in packing_lists:
        print(f"\n👤 {packing_list.person_name}:")
        print(f"  Total items: {len(packing_list.items)}")
        print(f"  Categories: {packing_list.categories}")
        
        # Check for activity items
        activity_items = [item for item in packing_list.items if "*" in item.name]
        
        if activity_items:
            print(f"  Activity items found: {len(activity_items)}")
            for item in activity_items:
                status = "✅" if item.category == expected_category else "❌"
                print(f"    {status} {item.name} → category: '{item.category}'")
                if item.category != expected_category:
                    all_valid = False
                    print(f"       ERROR: Expected '{expected_category}', got '{item.category}'")
        else:
            # Infants shouldn't have activity items
            if packing_list.person_name == "Baby":
                print(f"  ✅ No activity items (appropriate for infant)")
            else:
                print(f"  ⚠️  WARNING: No activity items found (expected for {packing_list.person_name})")
        
        # Check for generic "activities" category
        if "activities" in packing_list.categories:
            print(f"  ❌ ERROR: Found generic 'activities' category (should not exist)")
            all_valid = False
    
    print("\n" + "="*80)
    if all_valid:
        print("✅ TEST PASSED: All activity items use correct category")
    else:
        print("❌ TEST FAILED: Some items have incorrect categories")
    print("="*80)
    
    return all_valid


async def test_beach_trip():
    """Test a beach trip to ensure activity categories are correct."""
    print("\n" + "="*80)
    print("TEST: Beach Trip - Activity Category Validation")
    print("="*80)
    
    # Create test travelers
    travelers = [
        TravelerInDB(
            id="adult-1",
            name="Mike",
            age=40,
            type="adult"
        ),
        TravelerInDB(
            id="child-1",
            name="Lucas",
            age=10,
            type="child"
        )
    ]
    
    # Weather data
    weather_data = WeatherInfo(
        avg_temp=85,
        temp_unit="F",
        conditions=["sunny"],
        recommendation="Pack light, breathable clothing and sun protection"
    )
    
    # Activities
    activities = ["Beach", "Snorkeling"]
    
    print(f"\n📋 Test Setup:")
    print(f"  Destination: Maui, Hawaii")
    print(f"  Duration: 7 days")
    print(f"  Activities: {activities}")
    print(f"  Travelers: {len(travelers)}")
    for t in travelers:
        print(f"    - {t.name} ({t.age}y, {t.type})")
    
    # Generate packing lists
    print(f"\n🚀 Generating packing lists...")
    packing_lists = await llm_service.generate_packing_lists(
        destination="Maui, Hawaii",
        start_date="2026-06-15",
        end_date="2026-06-21",
        travelers=travelers,
        weather_data=weather_data,
        activities=activities,
        transport=["Flying"]
    )
    
    print(f"\n✅ Successfully generated {len(packing_lists)} packing lists")
    
    # Validate results
    print(f"\n🔍 VALIDATION RESULTS:")
    print("="*80)
    
    all_valid = True
    expected_categories = {"beach", "snorkeling"}
    
    for packing_list in packing_lists:
        print(f"\n👤 {packing_list.person_name}:")
        print(f"  Total items: {len(packing_list.items)}")
        print(f"  Categories: {packing_list.categories}")
        
        # Check for activity items
        activity_items = [item for item in packing_list.items if "*" in item.name]
        
        if activity_items:
            print(f"  Activity items found: {len(activity_items)}")
            for item in activity_items:
                is_valid = item.category in expected_categories
                status = "✅" if is_valid else "❌"
                print(f"    {status} {item.name} → category: '{item.category}'")
                if not is_valid:
                    all_valid = False
                    print(f"       ERROR: Expected one of {expected_categories}, got '{item.category}'")
        else:
            print(f"  ⚠️  WARNING: No activity items found")
        
        # Check for generic "activities" category
        if "activities" in packing_list.categories:
            print(f"  ❌ ERROR: Found generic 'activities' category (should not exist)")
            all_valid = False
    
    print("\n" + "="*80)
    if all_valid:
        print("✅ TEST PASSED: All activity items use correct categories")
    else:
        print("❌ TEST FAILED: Some items have incorrect categories")
    print("="*80)
    
    return all_valid


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("ACTIVITY CATEGORY FIX - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    results = []
    
    # Test 1: Skiing trip
    try:
        result1 = await test_skiing_trip()
        results.append(("Skiing Trip", result1))
    except Exception as e:
        print(f"\n❌ Skiing trip test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("Skiing Trip", False))
    
    # Test 2: Beach trip
    try:
        result2 = await test_beach_trip()
        results.append(("Beach Trip", result2))
    except Exception as e:
        print(f"\n❌ Beach trip test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("Beach Trip", False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    print("\n" + "="*80)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("="*80)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("="*80)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)