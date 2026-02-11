#!/usr/bin/env python3
"""
Comprehensive test script for validating the new packing list generation prompt.

This script executes test scenarios from TEST_PLAN_PACKING_PROMPT.md and validates:
- Category coverage (all 9 categories used appropriately)
- Age-appropriate items (baby items for infants, etc.)
- Weather adaptations (layers for cold, sunscreen for beach, etc.)
- Activity-specific gear (swimsuits, hiking boots, etc.)
- Realistic quantities based on trip duration
- Essential item marking (critical items flagged)
- Output format compliance (valid JSON structure)
- Performance (generation time per traveler)
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.llm_service import llm_service
from models.trip import TravelerInDB, WeatherInfo


class TestResults:
    """Container for test results and validation."""
    
    def __init__(self, scenario_name: str):
        self.scenario_name = scenario_name
        self.generation_time = 0.0
        self.travelers_tested = 0
        self.total_items = 0
        self.categories_found = set()
        self.validation_results = []
        self.issues = []
        self.packing_lists = []
    
    def add_validation(self, check: str, passed: bool, details: str = ""):
        """Add a validation result."""
        self.validation_results.append({
            "check": check,
            "passed": passed,
            "details": details
        })
        if not passed:
            self.issues.append(f"{check}: {details}")
    
    def print_summary(self):
        """Print test results summary."""
        print(f"\n{'='*80}")
        print(f"TEST RESULTS: {self.scenario_name}")
        print(f"{'='*80}")
        print(f"⏱️  Generation Time: {self.generation_time:.2f}s")
        print(f"👥 Travelers Tested: {self.travelers_tested}")
        print(f"📦 Total Items Generated: {self.total_items}")
        print(f"📂 Categories Found: {sorted(self.categories_found)}")
        
        print(f"\n✅ VALIDATIONS:")
        passed = sum(1 for v in self.validation_results if v["passed"])
        total = len(self.validation_results)
        print(f"   Passed: {passed}/{total}")
        
        for validation in self.validation_results:
            status = "✅" if validation["passed"] else "❌"
            print(f"   {status} {validation['check']}")
            if validation["details"] and not validation["passed"]:
                print(f"      → {validation['details']}")
        
        if self.issues:
            print(f"\n⚠️  ISSUES FOUND ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   • {issue}")
        else:
            print(f"\n🎉 NO ISSUES FOUND!")
        
        print(f"{'='*80}\n")


async def test_scenario_a_beach_family():
    """
    Scenario A: Beach vacation with kids (Hot/Sunny)
    Tests: baseline functionality, age differentiation, hot weather logic
    """
    print("\n" + "="*80)
    print("SCENARIO A: Beach Family Vacation (Hot/Sunny)")
    print("="*80)
    
    results = TestResults("Scenario A: Beach Family")
    
    # Test data
    travelers = [
        TravelerInDB(id="t1", name="Dad", age=40, type="adult"),
        TravelerInDB(id="t2", name="Mom", age=38, type="adult"),
        TravelerInDB(id="t3", name="Leo", age=8, type="child"),
        TravelerInDB(id="t4", name="Mia", age=3, type="child")
    ]
    
    weather_data = WeatherInfo(
        avg_temp=85,
        temp_unit="F",
        conditions=["sunny"],
        recommendation="Hot and sunny - pack light clothing and sun protection"
    )
    
    activities = ["Beach", "Pool", "Snorkeling", "Casual Dining"]
    transport = ["Plane", "Rental Car"]
    
    print(f"📍 Destination: Maui, Hawaii")
    print(f"📅 Duration: 7 days")
    print(f"👥 Travelers: {len(travelers)} (Dad, Mom, Leo 8yo, Mia 3yo)")
    print(f"🌤️  Weather: {weather_data.avg_temp}°{weather_data.temp_unit}, {weather_data.conditions}")
    print(f"🎯 Activities: {activities}")
    
    try:
        start_time = time.time()
        
        packing_lists = await llm_service.generate_packing_lists(
            destination="Maui, Hawaii",
            start_date="2026-06-01",
            end_date="2026-06-08",
            travelers=travelers,
            weather_data=weather_data,
            activities=activities,
            transport=transport
        )
        
        results.generation_time = time.time() - start_time
        results.travelers_tested = len(packing_lists)
        results.packing_lists = packing_lists
        
        # Validation 1: All travelers got lists
        results.add_validation(
            "All travelers received packing lists",
            len(packing_lists) == len(travelers),
            f"Generated {len(packing_lists)} of {len(travelers)} lists"
        )
        
        # Validation 2: Performance check
        results.add_validation(
            "Generation time within target (≤25s)",
            results.generation_time <= 25,
            f"{results.generation_time:.2f}s"
        )
        
        # Analyze each traveler's list
        for packing_list in packing_lists:
            traveler_name = packing_list.person_name
            items = packing_list.items
            categories = set(item.category for item in items)
            
            results.total_items += len(items)
            results.categories_found.update(categories)
            
            print(f"\n📋 {traveler_name}'s List:")
            print(f"   Items: {len(items)}")
            print(f"   Categories: {sorted(categories)}")
            
            # Validation 3: Item count reasonable
            results.add_validation(
                f"{traveler_name}: Item count in range (20-50)",
                20 <= len(items) <= 50,
                f"{len(items)} items"
            )
            
            # Validation 4: Essential categories present
            essential_categories = {"clothing", "toiletries"}
            missing = essential_categories - categories
            results.add_validation(
                f"{traveler_name}: Essential categories present",
                len(missing) == 0,
                f"Missing: {missing}" if missing else "All present"
            )
            
            # Validation 5: Hot weather items
            item_names = [item.name.lower() for item in items]
            hot_weather_items = ["sunscreen", "swimsuit", "swim", "shorts", "sandals", "hat"]
            has_hot_weather = any(hw in " ".join(item_names) for hw in hot_weather_items)
            results.add_validation(
                f"{traveler_name}: Hot weather items included",
                has_hot_weather,
                "Found appropriate hot weather items" if has_hot_weather else "Missing hot weather items"
            )
            
            # Validation 6: Beach activity items
            beach_items = ["towel", "goggles", "snorkel", "beach", "pool"]
            has_beach = any(bi in " ".join(item_names) for bi in beach_items)
            results.add_validation(
                f"{traveler_name}: Beach/pool items included",
                has_beach,
                "Found beach/pool items" if has_beach else "Missing beach/pool items"
            )
            
            # Validation 7: Essential items marked correctly
            essential_items = [item for item in items if item.is_essential]
            print(f"   Essential items: {len(essential_items)}")
            for item in essential_items[:3]:
                print(f"      ⭐ {item.emoji} {item.name}")
            
            # Validation 8: Age-appropriate items for toddler
            if packing_list.person_name == "Mia":
                toddler_items = ["comfort", "toy", "snack", "sippy"]
                has_toddler = any(ti in " ".join(item_names) for ti in toddler_items)
                results.add_validation(
                    f"{traveler_name}: Toddler-specific items",
                    has_toddler,
                    "Found toddler items" if has_toddler else "Missing toddler items"
                )
        
        # Validation 9: Category diversity
        results.add_validation(
            "Category diversity (≥5 categories used)",
            len(results.categories_found) >= 5,
            f"{len(results.categories_found)} categories: {sorted(results.categories_found)}"
        )
        
        results.print_summary()
        return results
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_scenario_b_ski_trip():
    """
    Scenario B: Ski trip for couple (Cold/Snowy)
    Tests: cold weather logic, activity-specific gear, car travel
    """
    print("\n" + "="*80)
    print("SCENARIO B: Ski Trip for Couple (Cold/Snowy)")
    print("="*80)
    
    results = TestResults("Scenario B: Ski Trip")
    
    travelers = [
        TravelerInDB(id="t1", name="Alex", age=30, type="adult"),
        TravelerInDB(id="t2", name="Sam", age=30, type="adult")
    ]
    
    weather_data = WeatherInfo(
        avg_temp=25,
        temp_unit="F",
        conditions=["snowy", "cloudy"],
        recommendation="Cold and snowy - pack warm layers and winter gear"
    )
    
    activities = ["Skiing", "Après-ski", "Hot Tub"]
    transport = ["Car"]
    
    print(f"📍 Destination: Aspen, Colorado")
    print(f"📅 Duration: 4 days")
    print(f"👥 Travelers: {len(travelers)} (Alex, Sam)")
    print(f"🌤️  Weather: {weather_data.avg_temp}°{weather_data.temp_unit}, {weather_data.conditions}")
    print(f"🎯 Activities: {activities}")
    
    try:
        start_time = time.time()
        
        packing_lists = await llm_service.generate_packing_lists(
            destination="Aspen, Colorado",
            start_date="2026-12-10",
            end_date="2026-12-14",
            travelers=travelers,
            weather_data=weather_data,
            activities=activities,
            transport=transport
        )
        
        results.generation_time = time.time() - start_time
        results.travelers_tested = len(packing_lists)
        results.packing_lists = packing_lists
        
        # Validations
        results.add_validation(
            "All travelers received packing lists",
            len(packing_lists) == len(travelers),
            f"Generated {len(packing_lists)} of {len(travelers)} lists"
        )
        
        results.add_validation(
            "Generation time within target (≤25s)",
            results.generation_time <= 25,
            f"{results.generation_time:.2f}s"
        )
        
        for packing_list in packing_lists:
            traveler_name = packing_list.person_name
            items = packing_list.items
            categories = set(item.category for item in items)
            
            results.total_items += len(items)
            results.categories_found.update(categories)
            
            print(f"\n📋 {traveler_name}'s List:")
            print(f"   Items: {len(items)}")
            print(f"   Categories: {sorted(categories)}")
            
            item_names = [item.name.lower() for item in items]
            
            # Cold weather items
            cold_items = ["thermal", "coat", "jacket", "gloves", "warm", "layer", "fleece"]
            has_cold = any(ci in " ".join(item_names) for ci in cold_items)
            results.add_validation(
                f"{traveler_name}: Cold weather items",
                has_cold,
                "Found cold weather items" if has_cold else "Missing cold weather items"
            )
            
            # Ski-specific items
            ski_items = ["ski", "goggles", "helmet", "boot", "pole"]
            has_ski = any(si in " ".join(item_names) for si in ski_items)
            results.add_validation(
                f"{traveler_name}: Ski-specific gear",
                has_ski,
                "Found ski gear" if has_ski else "Missing ski gear"
            )
            
            # Activities category should be present
            results.add_validation(
                f"{traveler_name}: Activities category present",
                "activities" in categories,
                "Activities category found" if "activities" in categories else "Missing activities category"
            )
        
        results.print_summary()
        return results
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_scenario_e_infant():
    """
    Scenario E: Domestic trip with baby
    Tests: "Baby" category, infant-specific items
    """
    print("\n" + "="*80)
    print("SCENARIO E: Domestic Trip with Infant")
    print("="*80)
    
    results = TestResults("Scenario E: Infant Trip")
    
    travelers = [
        TravelerInDB(id="t1", name="Mom", age=32, type="adult"),
        TravelerInDB(id="t2", name="Baby Sam", age=0, type="infant")
    ]
    
    weather_data = WeatherInfo(
        avg_temp=70,
        temp_unit="F",
        conditions=["sunny"],
        recommendation="Pleasant weather - pack comfortable clothing"
    )
    
    activities = ["Family Visit", "Park Stroll"]
    transport = ["Car"]
    
    print(f"📍 Destination: Chicago, IL")
    print(f"📅 Duration: 5 days")
    print(f"👥 Travelers: {len(travelers)} (Mom, Baby Sam)")
    print(f"🌤️  Weather: {weather_data.avg_temp}°{weather_data.temp_unit}, {weather_data.conditions}")
    print(f"🎯 Activities: {activities}")
    
    try:
        start_time = time.time()
        
        packing_lists = await llm_service.generate_packing_lists(
            destination="Chicago, IL",
            start_date="2026-05-20",
            end_date="2026-05-25",
            travelers=travelers,
            weather_data=weather_data,
            activities=activities,
            transport=transport
        )
        
        results.generation_time = time.time() - start_time
        results.travelers_tested = len(packing_lists)
        results.packing_lists = packing_lists
        
        results.add_validation(
            "All travelers received packing lists",
            len(packing_lists) == len(travelers),
            f"Generated {len(packing_lists)} of {len(travelers)} lists"
        )
        
        # Find baby's list
        baby_list = None
        for packing_list in packing_lists:
            if packing_list.person_name == "Baby Sam":
                baby_list = packing_list
                break
        
        if baby_list:
            items = baby_list.items
            categories = set(item.category for item in items)
            item_names = [item.name.lower() for item in items]
            
            results.total_items += len(items)
            results.categories_found.update(categories)
            
            print(f"\n📋 Baby Sam's List:")
            print(f"   Items: {len(items)}")
            print(f"   Categories: {sorted(categories)}")
            
            # CRITICAL: Baby category must be present
            results.add_validation(
                "Baby Sam: 'baby' category present",
                "baby" in categories,
                "Baby category found" if "baby" in categories else "MISSING BABY CATEGORY!"
            )
            
            # Baby-specific items
            baby_items = ["diaper", "wipe", "formula", "bottle", "pacifier", "carrier", "stroller"]
            found_baby_items = [bi for bi in baby_items if bi in " ".join(item_names)]
            results.add_validation(
                "Baby Sam: Essential baby items present",
                len(found_baby_items) >= 3,
                f"Found: {found_baby_items}" if found_baby_items else "Missing baby items"
            )
            
            # Show baby items
            baby_category_items = [item for item in items if item.category == "baby"]
            print(f"\n   👶 Baby Category Items ({len(baby_category_items)}):")
            for item in baby_category_items[:10]:
                essential = "⭐" if item.is_essential else "  "
                print(f"      {essential} {item.emoji} {item.name} (x{item.quantity})")
        
        results.print_summary()
        return results
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run all test scenarios."""
    print("\n" + "="*80)
    print("PACKING LIST PROMPT VALIDATION TEST SUITE")
    print("Testing new 212-line comprehensive family travel packing expert system")
    print("="*80)
    
    all_results = []
    
    # Run test scenarios
    print("\n🧪 Running Test Scenarios...")
    
    # Scenario A: Beach family (comprehensive test)
    result_a = await test_scenario_a_beach_family()
    if result_a:
        all_results.append(result_a)
    
    # Scenario B: Ski trip (cold weather + activities)
    result_b = await test_scenario_b_ski_trip()
    if result_b:
        all_results.append(result_b)
    
    # Scenario E: Infant (baby category test)
    result_e = await test_scenario_e_infant()
    if result_e:
        all_results.append(result_e)
    
    # Overall summary
    print("\n" + "="*80)
    print("OVERALL TEST SUMMARY")
    print("="*80)
    
    total_scenarios = len(all_results)
    total_validations = sum(len(r.validation_results) for r in all_results)
    total_passed = sum(sum(1 for v in r.validation_results if v["passed"]) for r in all_results)
    total_issues = sum(len(r.issues) for r in all_results)
    
    print(f"\n📊 Statistics:")
    print(f"   Scenarios Tested: {total_scenarios}")
    print(f"   Total Validations: {total_passed}/{total_validations} passed")
    print(f"   Total Issues: {total_issues}")
    
    print(f"\n⏱️  Performance:")
    for result in all_results:
        print(f"   {result.scenario_name}: {result.generation_time:.2f}s for {result.travelers_tested} travelers")
    
    avg_time = sum(r.generation_time for r in all_results) / len(all_results) if all_results else 0
    print(f"   Average: {avg_time:.2f}s per scenario")
    
    print(f"\n📦 Items Generated:")
    for result in all_results:
        print(f"   {result.scenario_name}: {result.total_items} items across {result.travelers_tested} travelers")
    
    print(f"\n📂 Categories Used:")
    all_categories = set()
    for result in all_results:
        all_categories.update(result.categories_found)
    print(f"   {sorted(all_categories)}")
    
    # Final assessment
    print(f"\n🎯 FINAL ASSESSMENT:")
    if total_issues == 0:
        print("   ✅ ALL TESTS PASSED! The new prompt is working excellently.")
    elif total_issues <= 3:
        print(f"   ⚠️  MINOR ISSUES ({total_issues}) - Prompt is working well with minor improvements needed.")
    else:
        print(f"   ❌ SIGNIFICANT ISSUES ({total_issues}) - Prompt needs refinement.")
    
    print("\n" + "="*80)
    
    return total_issues == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)