"""Public weather routes for guest users."""

from fastapi import APIRouter, HTTPException, status
from services.weather_service import weather_service

router = APIRouter(prefix="/api/v1/weather", tags=["weather"])


@router.get("/forecast")
async def get_weather_forecast(
    location: str,
    start_date: str,
    end_date: str
):
    """
    Get weather forecast for a location and date range.
    
    This is a public endpoint that doesn't require authentication,
    allowing guest users to get weather data for their trips.
    
    Args:
        location: Destination (city name, coordinates, etc.)
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)
    
    Returns:
        Weather forecast data including temperature, conditions, and recommendations
    """
    try:
        weather_data = await weather_service.get_forecast(
            location=location,
            start_date=start_date,
            end_date=end_date
        )
        return weather_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch weather data: {str(e)}"
        )