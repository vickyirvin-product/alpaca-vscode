"""Test script for weather caching functionality."""

import asyncio
import time
from services.weather_service import weather_service


async def test_weather_cache():
    """Test weather caching with multiple requests."""
    
    print("=" * 60)
    print("WEATHER CACHE TEST")
    print("=" * 60)
    
    # Test parameters
    location = "San Francisco"
    start_date = "2026-03-01"
    end_date = "2026-03-07"
    
    print(f"\nTest Parameters:")
    print(f"  Location: {location}")
    print(f"  Date Range: {start_date} to {end_date}")
    print(f"  Cache TTL: 6 hours")
    
    # Initial cache stats
    print("\n" + "-" * 60)
    print("Initial Cache Stats:")
    stats = weather_service.get_cache_stats()
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Cache Size: {stats['cache_size']}")
    print(f"  Hit Rate: {stats['hit_rate_percent']}%")
    
    # First request - should be a cache MISS
    print("\n" + "-" * 60)
    print("TEST 1: First request (should be cache MISS)")
    start_time = time.time()
    try:
        result1 = await weather_service.get_forecast(location, start_date, end_date)
        elapsed1 = time.time() - start_time
        print(f"✓ Request completed in {elapsed1:.3f}s")
        print(f"  Temperature: {result1['avg_temp']}°{result1['temp_unit']}")
        print(f"  Conditions: {', '.join(result1['conditions'])}")
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return
    
    # Check cache stats after first request
    stats = weather_service.get_cache_stats()
    print(f"\nCache Stats After First Request:")
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Cache Size: {stats['cache_size']}")
    print(f"  Hit Rate: {stats['hit_rate_percent']}%")
    
    # Second request - should be a cache HIT
    print("\n" + "-" * 60)
    print("TEST 2: Second request (should be cache HIT)")
    start_time = time.time()
    try:
        result2 = await weather_service.get_forecast(location, start_date, end_date)
        elapsed2 = time.time() - start_time
        print(f"✓ Request completed in {elapsed2:.3f}s")
        print(f"  Temperature: {result2['avg_temp']}°{result2['temp_unit']}")
        print(f"  Conditions: {', '.join(result2['conditions'])}")
        print(f"\n  Speed improvement: {elapsed1/elapsed2:.1f}x faster!")
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return
    
    # Check cache stats after second request
    stats = weather_service.get_cache_stats()
    print(f"\nCache Stats After Second Request:")
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Cache Size: {stats['cache_size']}")
    print(f"  Hit Rate: {stats['hit_rate_percent']}%")
    
    # Third request with different location - should be cache MISS
    print("\n" + "-" * 60)
    print("TEST 3: Different location (should be cache MISS)")
    location2 = "New York"
    start_time = time.time()
    try:
        result3 = await weather_service.get_forecast(location2, start_date, end_date)
        elapsed3 = time.time() - start_time
        print(f"✓ Request completed in {elapsed3:.3f}s")
        print(f"  Temperature: {result3['avg_temp']}°{result3['temp_unit']}")
        print(f"  Conditions: {', '.join(result3['conditions'])}")
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return
    
    # Fourth request - repeat second location, should be cache HIT
    print("\n" + "-" * 60)
    print("TEST 4: Repeat second location (should be cache HIT)")
    start_time = time.time()
    try:
        result4 = await weather_service.get_forecast(location2, start_date, end_date)
        elapsed4 = time.time() - start_time
        print(f"✓ Request completed in {elapsed4:.3f}s")
        print(f"  Temperature: {result4['avg_temp']}°{result4['temp_unit']}")
        print(f"  Conditions: {', '.join(result4['conditions'])}")
        print(f"\n  Speed improvement: {elapsed3/elapsed4:.1f}x faster!")
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return
    
    # Test case normalization
    print("\n" + "-" * 60)
    print("TEST 5: Case normalization (should be cache HIT)")
    location_upper = "SAN FRANCISCO"  # Same as first request but uppercase
    start_time = time.time()
    try:
        result5 = await weather_service.get_forecast(location_upper, start_date, end_date)
        elapsed5 = time.time() - start_time
        print(f"✓ Request completed in {elapsed5:.3f}s")
        print(f"  Location normalized: '{location_upper}' -> cache key matches '{location}'")
        print(f"  Speed improvement: {elapsed1/elapsed5:.1f}x faster!")
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return
    
    # Final cache stats
    print("\n" + "-" * 60)
    print("FINAL CACHE STATS:")
    stats = weather_service.get_cache_stats()
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Cache Hits: {stats['hits']}")
    print(f"  Cache Misses: {stats['misses']}")
    print(f"  Cache Size: {stats['cache_size']}/{stats['max_size']}")
    print(f"  Hit Rate: {stats['hit_rate_percent']}%")
    
    # Verify results
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    expected_hits = 3  # Requests 2, 4, and 5 should be hits
    expected_misses = 2  # Requests 1 and 3 should be misses
    
    if stats['hits'] == expected_hits and stats['misses'] == expected_misses:
        print("✓ ALL TESTS PASSED!")
        print(f"  Expected: {expected_hits} hits, {expected_misses} misses")
        print(f"  Actual: {stats['hits']} hits, {stats['misses']} misses")
        print(f"  Cache is working correctly with {stats['hit_rate_percent']}% hit rate")
    else:
        print("✗ TEST FAILED!")
        print(f"  Expected: {expected_hits} hits, {expected_misses} misses")
        print(f"  Actual: {stats['hits']} hits, {stats['misses']} misses")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_weather_cache())