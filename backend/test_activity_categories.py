"""
Test script to verify activity-specific categories are working correctly.
This tests the changes made to enable dynamic activity-based categories.
"""

import asyncio
from services.llm_service import LLMService
from models.trip import TravelerInDB, WeatherInfo

async def test_skiing_trip():
    """Test that a skiing trip generates a 'skiing' category instead of generic 'activities'."""
    
    print("=" * 80)
    print("TESTING ACTIVITY-SPECIFIC CATEGORIES - SKIING TRIP")
    print("=" * 80)
    
    # Create test data for a skiing trip
    travelers = [
        TravelerInDB(
            id="test-adult-1",
            name="John",
            age=35,
            type="adult"
        ),
        TravelerInDB(
            id="test-child-1",
            name="Emma",
            age=8,
            type="child"
        )
    ]
    
    weather_data = WeatherInfo(
        avg_temp=25,
        temp_unit="F",
        conditions=["snowy", "cloudy"],
        recommendation="Pack warm layers and winter gear for cold, snowy conditions."
    )
    
    activities = ["Skiing", "Snowboarding"]
    transport = ["Car"]
    
    # Initialize LLM service
    llm_service = LLMService()
    
    print("\n📋 Test Parameters:")
    print(f"  Destination: Aspen, Colorado")
    print(f"  Duration: 5 days")
    print(f"  Travelers: {len(travelers)}")
    print(f"  Activities: {activities}")
    print(f"  Weather: {weather_data.avg_temp}°{weather_data.temp_unit}, {weather_data.conditions}")
    
    try:
        print("\n🚀 Generating packing lists...")
        packing_lists = await llm_service.generate_packing_lists(
            destination="Aspen, Colorado",
            start_date="2026-03-01",
            end_date="2026-03-05",
            travelers=travelers,
            weather_data=weather_data,
            activities=activities,
            transport=transport
        )
        
        print(f"\n✅ Successfully generated {len(packing_lists)} packing lists")
        
        # Analyze categories
        print("\n" + "=" * 80)
        print("CATEGORY ANALYSIS")
        print("=" * 80)
        
        for packing_list in packing_lists:
            print(f"\n👤 {packing_list.person_name}:")
            print(f"   Total Items: {len(packing_list.items)}")
            print(f"   Categories: {', '.join(packing_list.categories)}")
            
            # Check for activity-specific categories
            activity_categories = [cat for cat in packing_list.categories 
                                 if cat not in ["clothing", "toiletries", "electronics", 
                                              "documents", "health", "comfort", 
                                              "activities", "baby", "misc"]]
            
            if activity_categories:
                print(f"   ✅ ACTIVITY-SPECIFIC CATEGORIES FOUND: {', '.join(activity_categories)}")
            else:
                print(f"   ⚠️  No activity-specific categories (using generic 'activities')")
            
            # Show items in activity-related categories
            skiing_items = [item for item in packing_list.items 
                          if 'skiing' in item.category.lower() or 
                             'snowboarding' in item.category.lower() or
                             item.category == 'activities']
            
            if skiing_items:
                print(f"\n   Activity-Related Items ({len(skiing_items)}):")
                for item in skiing_items[:10]:  # Show first 10
                    print(f"     • {item.emoji} {item.name} (x{item.quantity}) - Category: {item.category}")
                if len(skiing_items) > 10:
                    print(f"     ... and {len(skiing_items) - 10} more")
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        all_categories = set()
        for packing_list in packing_lists:
            all_categories.update(packing_list.categories)
        
        activity_specific = [cat for cat in all_categories 
                           if cat not in ["clothing", "toiletries", "electronics", 
                                        "documents", "health", "comfort", 
                                        "activities", "baby", "misc"]]
        
        if activity_specific:
            print(f"✅ SUCCESS: Activity-specific categories detected: {', '.join(activity_specific)}")
            print("   The system is now creating dedicated categories for major activities!")
        else:
            print("⚠️  WARNING: No activity-specific categories found.")
            print("   Items may still be in the generic 'activities' category.")
        
        print(f"\nAll categories used: {', '.join(sorted(all_categories))}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_skiing_trip())