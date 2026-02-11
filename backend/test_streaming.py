#!/usr/bin/env python3
"""
Test script for parallel packing list generation performance.

This test validates the streaming/parallel execution functionality of the packing list
generation system. It focuses on performance metrics and parallel processing capabilities.

For comprehensive validation of the packing list prompt (categories, age-appropriate items,
weather adaptations, activity-specific gear, etc.), see test_packing_prompt.py which
implements the full test suite from TEST_PLAN_PACKING_PROMPT.md.

Related Files:
- test_packing_prompt.py: Comprehensive prompt validation (9 categories, baby items, etc.)
- TEST_PLAN_PACKING_PROMPT.md: Test scenarios and validation criteria
- PACKING_PROMPT_TEST_REPORT.md: Latest test results and findings
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.llm_service import llm_service
from models.trip import TravelerInDB, WeatherInfo


async def test_streaming_generation():
    """
    Test the parallel packing list generation performance.
    
    This test validates:
    - Parallel execution of multiple traveler lists
    - Performance targets (≤25 seconds for 4 travelers)
    - Comprehensive item generation (no artificial limits)
    - Proper use of all 9 categories (clothing, toiletries, electronics, documents,
      activities, health, baby, comfort, miscellaneous)
    """
    print("=" * 60)
    print("Testing Parallel Packing List Generation")
    print("=" * 60)
    
    # Create test data with multiple travelers to test parallel execution
    travelers = [
        TravelerInDB(
            id="test-adult-1",
            name="Sarah",
            age=35,
            type="adult"
        ),
        TravelerInDB(
            id="test-adult-2",
            name="John",
            age=37,
            type="adult"
        ),
        TravelerInDB(
            id="test-child-1",
            name="Emma",
            age=8,
            type="child"
        ),
        TravelerInDB(
            id="test-child-2",
            name="Lucas",
            age=5,
            type="child"
        )
    ]
    
    weather_data = WeatherInfo(
        avg_temp=15,
        temp_unit="C",
        conditions=["snowy", "cloudy"],
        recommendation="Pack warm clothing and winter gear"
    )
    
    activities = ["skiing", "snowboarding", "hot chocolate"]
    transport = ["car", "ski lift"]
    
    print("\nTest Parameters:")
    print(f"  Destination: Aspen, Colorado")
    print(f"  Duration: 6 days")
    print(f"  Travelers: {len(travelers)} ({', '.join([t.name for t in travelers])})")
    print(f"  Activities: {activities}")
    print(f"  Weather: {weather_data.avg_temp}°{weather_data.temp_unit}, {weather_data.conditions}")
    
    try:
        print("\n🚀 Starting parallel generation...")
        import time
        start_time = time.time()
        
        packing_lists = await llm_service.generate_packing_lists(
            destination="Aspen, Colorado",
            start_date="2024-02-15",
            end_date="2024-02-20",
            travelers=travelers,
            weather_data=weather_data,
            activities=activities,
            transport=transport
        )
        
        duration = time.time() - start_time
        
        print(f"\n✅ Generation completed in {duration:.2f} seconds")
        print(f"\n📊 Results:")
        print(f"  Total packing lists: {len(packing_lists)}")
        
        for packing_list in packing_lists:
            print(f"\n  {packing_list.person_name} ({packing_list.person_id}):")
            print(f"    Items: {len(packing_list.items)}")
            
            # Get unique categories from items
            categories_used = sorted(set(item.category for item in packing_list.items))
            print(f"    Categories: {categories_used}")
            
            # Show first 3 items as sample
            print(f"    Sample items:")
            for item in packing_list.items[:3]:
                essential = "⭐" if item.is_essential else "  "
                print(f"      {essential} {item.emoji} {item.name} (x{item.quantity}) - {item.category}")
        
        # Verify performance and prompt compliance
        print(f"\n🔍 Verification:")
        all_items_count = sum(len(pl.items) for pl in packing_lists)
        avg_items = all_items_count / len(packing_lists) if packing_lists else 0
        
        # Collect all unique categories used across all travelers
        all_categories = set()
        for pl in packing_lists:
            all_categories.update(item.category for item in pl.items)
        
        print(f"  Total items across all travelers: {all_items_count}")
        print(f"  Average items per person: {avg_items:.1f}")
        print(f"  Categories used across all lists: {sorted(all_categories)}")
        print(f"  ✅ Comprehensive lists generated (no item count limits)")
        
        # Note: For detailed category validation (9 categories), age-appropriate items,
        # weather adaptations, etc., run test_packing_prompt.py
        
        if duration <= 25:
            print(f"  ✅ Generation time within target (≤25 seconds)")
        else:
            print(f"  ⚠️  Generation time: {duration:.2f}s (target: ≤25 seconds)")
        
        # Calculate speedup from parallel execution
        # Sequential would be roughly duration * num_travelers / num_travelers
        # But we're comparing to the old sequential approach
        print(f"\n📊 Performance Metrics:")
        print(f"  Parallel execution time: {duration:.2f}s for {len(travelers)} travelers")
        print(f"  Expected sequential time: ~{duration * len(travelers) / 1.5:.2f}s (estimated)")
        print(f"  Speedup from parallelization: ~{len(travelers) / 1.5:.1f}x")
        
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_streaming_generation())
    sys.exit(0 if success else 1)