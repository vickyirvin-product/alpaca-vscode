#!/usr/bin/env python3
"""
Performance test for packing list generation optimizations.
Tests the improvements made to achieve 15-20 second generation times.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List
import statistics
from bson import ObjectId

from services.llm_service import LLMService
from models.trip import TravelerInDB, WeatherInfo


class PerformanceTest:
    def __init__(self):
        self.llm_service = LLMService()
        self.results: List[Dict] = []
    
    def create_test_data(self, scenario: str) -> Dict:
        """Create test data for different scenarios."""
        base_date = datetime.now() + timedelta(days=30)
        
        scenarios = {
            "simple": {
                "destination": "San Diego, CA",
                "duration": 3,
                "travelers": [
                    TravelerInDB(
                        id=str(ObjectId()),
                        name="Mom",
                        type="adult",
                        age=35,
                        avatar="mom.jpeg"
                    ),
                    TravelerInDB(
                        id=str(ObjectId()),
                        name="Child",
                        type="child",
                        age=5,
                        avatar="child.jpeg"
                    )
                ],
                "activities": ["Beach"],
                "transport": []
            },
            "complex": {
                "destination": "Aspen, CO",
                "duration": 7,
                "travelers": [
                    TravelerInDB(
                        id=str(ObjectId()),
                        name="Dad",
                        type="adult",
                        age=40,
                        avatar="dad.jpeg"
                    ),
                    TravelerInDB(
                        id=str(ObjectId()),
                        name="Mom",
                        type="adult",
                        age=38,
                        avatar="mom.jpeg"
                    ),
                    TravelerInDB(
                        id=str(ObjectId()),
                        name="Teen",
                        type="child",
                        age=15,
                        avatar="teen.jpeg"
                    ),
                    TravelerInDB(
                        id=str(ObjectId()),
                        name="Child",
                        type="child",
                        age=8,
                        avatar="child.jpeg"
                    )
                ],
                "activities": ["Skiing/Snowboarding", "Hiking"],
                "transport": ["Flight", "Rental Car"]
            },
            "medium": {
                "destination": "Paris, France",
                "duration": 5,
                "travelers": [
                    TravelerInDB(
                        id=str(ObjectId()),
                        name="Mom",
                        type="adult",
                        age=35,
                        avatar="mom.jpeg"
                    ),
                    TravelerInDB(
                        id=str(ObjectId()),
                        name="Child",
                        type="child",
                        age=10,
                        avatar="child.jpeg"
                    )
                ],
                "activities": ["Sightseeing", "Museums"],
                "transport": ["Flight"]
            }
        }
        
        data = scenarios[scenario]
        return {
            "destination": data["destination"],
            "start_date": base_date.isoformat(),
            "end_date": (base_date + timedelta(days=data["duration"])).isoformat(),
            "travelers": data["travelers"],
            "activities": data["activities"],
            "transport": data["transport"],
            "duration": data["duration"]
        }
    
    async def run_single_test(self, scenario: str, run_number: int) -> Dict:
        """Run a single performance test."""
        print(f"\n{'='*60}")
        print(f"Test Run #{run_number} - Scenario: {scenario.upper()}")
        print(f"{'='*60}")
        
        test_data = self.create_test_data(scenario)
        
        # Mock weather data
        weather_data = WeatherInfo(
            avg_temp=65,
            temp_unit="F",
            conditions=["sunny"],
            recommendation="Pack light layers."
        )
        
        start_time = time.time()
        
        try:
            # Generate packing lists using the actual service method
            results = await self.llm_service.generate_packing_lists(
                destination=test_data["destination"],
                start_date=test_data["start_date"],
                end_date=test_data["end_date"],
                travelers=test_data["travelers"],
                weather_data=weather_data,
                activities=test_data["activities"],
                transport=test_data["transport"]
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Analyze results
            success_count = len(results)
            failure_count = len(test_data["travelers"]) - success_count
            total_items = sum(len(r.items) for r in results)
            
            result = {
                "scenario": scenario,
                "run": run_number,
                "duration": duration,
                "travelers": len(test_data["travelers"]),
                "success_count": success_count,
                "failure_count": failure_count,
                "total_items": total_items,
                "success_rate": (success_count / len(test_data["travelers"])) * 100,
                "avg_items_per_traveler": total_items / len(test_data["travelers"]) if success_count > 0 else 0,
                "status": "✅ PASS" if failure_count == 0 and duration <= 20 else "❌ FAIL"
            }
            
            # Print results
            print(f"\n📊 Results:")
            print(f"  Duration: {duration:.2f}s")
            print(f"  Travelers: {len(test_data['travelers'])}")
            print(f"  Successful: {success_count}/{len(test_data['travelers'])}")
            print(f"  Failed: {failure_count}/{len(test_data['travelers'])}")
            print(f"  Total Items: {total_items}")
            print(f"  Avg Items/Traveler: {result['avg_items_per_traveler']:.1f}")
            print(f"  Success Rate: {result['success_rate']:.1f}%")
            print(f"  Status: {result['status']}")
            
            if failure_count > 0:
                print(f"\n⚠️  Some travelers failed to generate lists")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            result = {
                "scenario": scenario,
                "run": run_number,
                "duration": duration,
                "travelers": len(test_data["travelers"]),
                "success_count": 0,
                "failure_count": len(test_data["travelers"]),
                "total_items": 0,
                "success_rate": 0,
                "avg_items_per_traveler": 0,
                "status": "❌ FAIL",
                "error": str(e)
            }
            
            print(f"\n❌ Test failed with error: {e}")
            return result
    
    async def run_performance_suite(self):
        """Run comprehensive performance test suite."""
        print("\n" + "="*60)
        print("PACKING LIST GENERATION PERFORMANCE TEST SUITE")
        print("="*60)
        print(f"Target: 15-20 seconds per generation")
        print(f"Target Success Rate: >99%")
        print("="*60)
        
        # Test scenarios
        scenarios = [
            ("simple", 3),    # Simple scenario, 3 runs
            ("medium", 3),    # Medium scenario, 3 runs
            ("complex", 2),   # Complex scenario, 2 runs
        ]
        
        all_results = []
        
        for scenario, runs in scenarios:
            for run in range(1, runs + 1):
                result = await self.run_single_test(scenario, run)
                all_results.append(result)
                self.results.append(result)
                
                # Brief pause between tests
                if run < runs:
                    await asyncio.sleep(2)
        
        # Generate summary report
        self.print_summary_report()
    
    def print_summary_report(self):
        """Print comprehensive summary report."""
        print("\n" + "="*60)
        print("PERFORMANCE TEST SUMMARY")
        print("="*60)
        
        if not self.results:
            print("No test results available.")
            return
        
        # Overall statistics
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "✅ PASS"])
        failed_tests = total_tests - passed_tests
        
        durations = [r["duration"] for r in self.results]
        success_rates = [r["success_rate"] for r in self.results]
        
        print(f"\n📈 Overall Statistics:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests} ({(passed_tests/total_tests)*100:.1f}%)")
        print(f"  Failed: {failed_tests} ({(failed_tests/total_tests)*100:.1f}%)")
        
        print(f"\n⏱️  Duration Statistics:")
        print(f"  Average: {statistics.mean(durations):.2f}s")
        print(f"  Median: {statistics.median(durations):.2f}s")
        print(f"  Min: {min(durations):.2f}s")
        print(f"  Max: {max(durations):.2f}s")
        print(f"  Std Dev: {statistics.stdev(durations):.2f}s" if len(durations) > 1 else "  Std Dev: N/A")
        
        print(f"\n✅ Success Rate Statistics:")
        print(f"  Average: {statistics.mean(success_rates):.1f}%")
        print(f"  Min: {min(success_rates):.1f}%")
        print(f"  Max: {max(success_rates):.1f}%")
        
        # Performance by scenario
        print(f"\n📊 Performance by Scenario:")
        for scenario in ["simple", "medium", "complex"]:
            scenario_results = [r for r in self.results if r["scenario"] == scenario]
            if scenario_results:
                avg_duration = statistics.mean([r["duration"] for r in scenario_results])
                avg_success = statistics.mean([r["success_rate"] for r in scenario_results])
                print(f"  {scenario.capitalize()}:")
                print(f"    Avg Duration: {avg_duration:.2f}s")
                print(f"    Avg Success Rate: {avg_success:.1f}%")
        
        # Target achievement
        print(f"\n🎯 Target Achievement:")
        within_target = len([r for r in self.results if r["duration"] <= 20])
        print(f"  Within 20s target: {within_target}/{total_tests} ({(within_target/total_tests)*100:.1f}%)")
        
        within_optimal = len([r for r in self.results if 15 <= r["duration"] <= 20])
        print(f"  Within 15-20s optimal: {within_optimal}/{total_tests} ({(within_optimal/total_tests)*100:.1f}%)")
        
        high_success = len([r for r in self.results if r["success_rate"] >= 99])
        print(f"  Success rate ≥99%: {high_success}/{total_tests} ({(high_success/total_tests)*100:.1f}%)")
        
        # Final verdict
        print(f"\n{'='*60}")
        avg_duration = statistics.mean(durations)
        avg_success = statistics.mean(success_rates)
        
        if avg_duration <= 20 and avg_success >= 99:
            print("🎉 PERFORMANCE TARGETS ACHIEVED!")
            print(f"   Average duration: {avg_duration:.2f}s (target: ≤20s)")
            print(f"   Average success rate: {avg_success:.1f}% (target: ≥99%)")
        else:
            print("⚠️  PERFORMANCE TARGETS NOT MET")
            if avg_duration > 20:
                print(f"   Duration: {avg_duration:.2f}s (target: ≤20s) ❌")
            else:
                print(f"   Duration: {avg_duration:.2f}s (target: ≤20s) ✅")
            
            if avg_success < 99:
                print(f"   Success rate: {avg_success:.1f}% (target: ≥99%) ❌")
            else:
                print(f"   Success rate: {avg_success:.1f}% (target: ≥99%) ✅")
        
        print("="*60)


async def main():
    """Main test execution."""
    test = PerformanceTest()
    await test.run_performance_suite()


if __name__ == "__main__":
    asyncio.run(main())