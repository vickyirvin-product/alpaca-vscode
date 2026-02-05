"""Weather service for fetching forecast data from WeatherAPI.com."""

import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config import settings


class WeatherService:
    """Service for interacting with WeatherAPI.com."""
    
    def __init__(self):
        self.api_key = settings.weather_api_key
        self.base_url = settings.weather_api_base_url
    
    async def get_forecast(
        self,
        location: str,
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Fetch weather forecast for a location and date range.
        
        Args:
            location: Destination (city name, coordinates, etc.)
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
        
        Returns:
            Dictionary containing weather data and recommendations
        """
        try:
            # Parse dates
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            days_count = (end - start).days + 1
            
            # WeatherAPI.com supports up to 14 days forecast
            # For longer trips, we'll get the first 14 days
            forecast_days = min(days_count, 14)
            
            async with httpx.AsyncClient() as client:
                # Fetch forecast data
                response = await client.get(
                    f"{self.base_url}/forecast.json",
                    params={
                        "key": self.api_key,
                        "q": location,
                        "days": forecast_days,
                        "aqi": "no",
                        "alerts": "no"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
            
            # Parse and structure the weather data
            weather_info = self._parse_forecast_data(data, days_count)
            return weather_info
            
        except httpx.HTTPError as e:
            raise Exception(f"Weather API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to fetch weather data: {str(e)}")
    
    def _parse_forecast_data(self, data: Dict, total_days: int) -> Dict:
        """
        Parse raw weather API data into structured format.
        
        Args:
            data: Raw API response
            total_days: Total trip duration in days
        
        Returns:
            Structured weather information
        """
        forecast_days = data.get("forecast", {}).get("forecastday", [])
        
        if not forecast_days:
            return self._get_default_weather()
        
        # Calculate average temperature
        temps = [day["day"]["avgtemp_c"] for day in forecast_days]
        avg_temp = sum(temps) / len(temps)
        
        # Determine conditions
        conditions = self._determine_conditions(forecast_days)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            avg_temp,
            conditions,
            total_days,
            forecast_days
        )
        
        return {
            "avg_temp": round(avg_temp, 1),
            "temp_unit": "C",
            "conditions": conditions,
            "recommendation": recommendation,
            "forecast_data": {
                "location": data.get("location", {}).get("name", ""),
                "country": data.get("location", {}).get("country", ""),
                "daily_forecasts": [
                    {
                        "date": day["date"],
                        "max_temp_c": day["day"]["maxtemp_c"],
                        "min_temp_c": day["day"]["mintemp_c"],
                        "avg_temp_c": day["day"]["avgtemp_c"],
                        "condition": day["day"]["condition"]["text"],
                        "chance_of_rain": day["day"]["daily_chance_of_rain"],
                        "chance_of_snow": day["day"]["daily_chance_of_snow"]
                    }
                    for day in forecast_days
                ]
            }
        }
    
    def _determine_conditions(self, forecast_days: List[Dict]) -> List[str]:
        """
        Determine overall weather conditions from forecast.
        
        Args:
            forecast_days: List of daily forecast data
        
        Returns:
            List of condition strings
        """
        conditions_set = set()
        
        for day in forecast_days:
            condition_text = day["day"]["condition"]["text"].lower()
            rain_chance = day["day"]["daily_chance_of_rain"]
            snow_chance = day["day"]["daily_chance_of_snow"]
            
            # Categorize conditions
            if snow_chance > 30 or "snow" in condition_text:
                conditions_set.add("snowy")
            elif rain_chance > 30 or "rain" in condition_text:
                conditions_set.add("rainy")
            elif "cloud" in condition_text or "overcast" in condition_text:
                conditions_set.add("cloudy")
            elif "sun" in condition_text or "clear" in condition_text:
                conditions_set.add("sunny")
        
        # If multiple conditions, mark as mixed
        if len(conditions_set) > 2:
            return ["mixed"]
        
        return list(conditions_set) if conditions_set else ["sunny"]
    
    def _generate_recommendation(
        self,
        avg_temp: float,
        conditions: List[str],
        total_days: int,
        forecast_days: List[Dict]
    ) -> str:
        """
        Generate packing recommendation based on weather.
        
        Args:
            avg_temp: Average temperature in Celsius
            conditions: List of weather conditions
            total_days: Total trip duration
            forecast_days: Forecast data
        
        Returns:
            Recommendation string
        """
        recommendations = []
        
        # Temperature-based recommendations
        if avg_temp < 10:
            recommendations.append("Pack warm layers and a heavy jacket")
        elif avg_temp < 20:
            recommendations.append("Pack layers - it will be cool")
        elif avg_temp < 25:
            recommendations.append("Pack light layers for mild weather")
        else:
            recommendations.append("Pack light, breathable clothing")
        
        # Condition-based recommendations
        if "rainy" in conditions or "mixed" in conditions:
            recommendations.append("Don't forget rain gear!")
        
        if "snowy" in conditions:
            recommendations.append("Winter gear essential")
        
        # Check temperature variation
        if forecast_days:
            temps = [day["day"]["avgtemp_c"] for day in forecast_days]
            temp_range = max(temps) - min(temps)
            if temp_range > 10:
                recommendations.append("Temperature varies - pack versatile items")
        
        # Duration note
        if total_days > 14:
            recommendations.append(
                f"Long trip ({total_days} days) - consider laundry options"
            )
        
        return ". ".join(recommendations) + "."
    
    def _get_default_weather(self) -> Dict:
        """Return default weather data when API fails."""
        return {
            "avg_temp": 20.0,
            "temp_unit": "C",
            "conditions": ["sunny"],
            "recommendation": "Check local weather closer to your trip date.",
            "forecast_data": None
        }


# Singleton instance
weather_service = WeatherService()