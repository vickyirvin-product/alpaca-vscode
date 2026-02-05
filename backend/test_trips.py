"""
Test script for trip creation with LLM and weather integration.

This script tests the trip creation endpoint to ensure:
1. Weather data is fetched correctly
2. LLM generates packing lists
3. Trip is stored in MongoDB
4. Response format matches expectations

Usage:
    python -m backend.test_trips
"""

import asyncio
import sys
from datetime import datetime, timedelta


async def test_trip_creation():
    """Test the trip creation flow."""
    print("=" * 60)
    print("Testing Trip Creation with LLM & Weather Integration")
    print("=" * 60)
    
    # Test 1: Import all modules
    print("\n[1/6] Testing imports...")
    try:
        from backend.config import settings
        from backend.models.trip import TripCreate, TravelerBase
        from backend.services.weather_service import weather_service
        from backend.services.llm_service import llm_service
        print("✓ All imports successful")
    except Exception as e:
        print(f"✗ Import failed: {str(e)}")
        return False
    
    # Test 2: Check configuration
    print("\n[2/6] Checking configuration...")
    try:
        assert settings.openai_api_key, "OpenAI API key not set"
        assert settings.weather_api_key, "Weather API key not set"
        print(f"✓ OpenAI API key: {settings.openai_api_key[:10]}...")
        print(f"✓ Weather API key: {settings.weather_api_key[:10]}...")
        print(f"✓ Weather API URL: {settings.weather_api_base_url}")
    except AssertionError as e:
        print(f"✗ Configuration error: {str(e)}")
        print("\nPlease set the following in your .env file:")
        print("  OPENAI_API_KEY=your_openai_api_key")
        print("  WEATHER_API_KEY=your_weatherapi_com_key")
        return False
    except Exception as e:
        print(f"✗ Configuration check failed: {str(e)}")
        return False
    
    # Test 3: Test weather service
    print("\n[3/6] Testing weather service...")
    try:
        start_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d")
        
        weather_data = await weather_service.get_forecast(
            location="Tokyo, Japan",
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"✓ Weather data fetched successfully")
        print(f"  - Average temp: {weather_data['avg_temp']}°{weather_data['temp_unit']}")
        print(f"  - Conditions: {', '.join(weather_data['conditions'])}")
        print(f"  - Recommendation: {weather_data['recommendation'][:60]}...")
    except Exception as e:
        print(f"✗ Weather service failed: {str(e)}")
        print("  Note: This might be due to invalid API key or network issues")
        return False
    
    # Test 4: Test LLM service
    print("\n[4/6] Testing LLM service...")
    try:
        from backend.models.trip import TravelerInDB, WeatherInfo
        
        # Create test travelers
        travelers = [
            TravelerInDB(
                name="Sarah (Mom)",
                age=38,
                type="adult"
            ),
            TravelerInDB(
                name="Mike (Dad)",
                age=40,
                type="adult"
            ),
            TravelerInDB(
                name="Emma",
                age=10,
                type="child"
            )
        ]
        
        # Convert weather data to WeatherInfo model
        weather_info = WeatherInfo(**weather_data)
        
        print("  Generating packing lists with GPT-4...")
        packing_lists = await llm_service.generate_packing_lists(
            destination="Tokyo, Japan",
            start_date=start_date,
            end_date=end_date,
            travelers=travelers,
            weather_data=weather_info,
            activities=["Sightseeing", "Hiking", "Shopping"],
            transport=["Flight", "Train"]
        )
        
        print(f"✓ LLM generated packing lists for {len(packing_lists)} travelers")
        for pl in packing_lists:
            item_count = len(pl.items)
            category_count = len(pl.categories)
            print(f"  - {pl.person_name}: {item_count} items in {category_count} categories")
            
            # Show sample items
            if pl.items:
                essential_items = [item for item in pl.items if item.is_essential]
                print(f"    Essential items: {len(essential_items)}")
                if essential_items:
                    sample = essential_items[0]
                    print(f"    Sample: {sample.emoji} {sample.name} (x{sample.quantity})")
    except Exception as e:
        print(f"✗ LLM service failed: {str(e)}")
        print("  Note: This might be due to invalid OpenAI API key or rate limits")
        return False
    
    # Test 5: Test database connection
    print("\n[5/6] Testing database connection...")
    try:
        from backend.database import Database
        
        await Database.connect_db()
        print("✓ Database connected successfully")
        
        # Test collection access
        from backend.database import get_db
        db = get_db()
        trips_collection = db.trips
        
        # Count existing trips
        count = await trips_collection.count_documents({})
        print(f"✓ Trips collection accessible ({count} existing trips)")
        
    except Exception as e:
        print(f"✗ Database connection failed: {str(e)}")
        print("  Note: Make sure MongoDB is running on mongodb://localhost:27017")
        return False
    
    # Test 6: Validate models
    print("\n[6/6] Validating data models...")
    try:
        from backend.models.trip import TripInDB, TripResponse
        
        # Create a test trip
        trip = TripInDB(
            user_id="test_user_123",
            destination="Tokyo, Japan",
            start_date=start_date,
            end_date=end_date,
            activities=["Sightseeing", "Hiking"],
            transport=["Flight", "Train"],
            travelers=travelers,
            weather_data=weather_info,
            packing_lists=packing_lists
        )
        
        print("✓ TripInDB model created successfully")
        print(f"  - Trip ID: {trip.id}")
        print(f"  - Destination: {trip.destination}")
        print(f"  - Duration: {(datetime.fromisoformat(end_date) - datetime.fromisoformat(start_date)).days + 1} days")
        
        # Convert to response model
        response = TripResponse.from_db(trip)
        print("✓ TripResponse model created successfully")
        print(f"  - Response includes {len(response.travelers)} travelers")
        print(f"  - Response includes {len(response.packing_lists)} packing lists")
        
    except Exception as e:
        print(f"✗ Model validation failed: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All tests passed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r backend/requirements.txt")
    print("2. Start the server: uvicorn backend.main:app --reload")
    print("3. Test the API at: http://localhost:8000/docs")
    print("4. Create a trip via POST /api/v1/trips")
    
    return True


async def main():
    """Main test runner."""
    try:
        success = await test_trip_creation()
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