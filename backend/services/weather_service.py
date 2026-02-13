"""Weather service for fetching forecast data from WeatherAPI.com."""

import httpx
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config import settings

# Configure logging
logger = logging.getLogger(__name__)


class WeatherCache:
    """Simple in-memory cache with TTL for weather data."""
    
    def __init__(self, ttl_hours: int = 6, max_size: int = 1000):
        """
        Initialize the cache.
        
        Args:
            ttl_hours: Time-to-live in hours for cached entries
            max_size: Maximum number of entries to store
        """
        self._cache: Dict[str, Tuple[datetime, Dict]] = {}
        self._ttl = timedelta(hours=ttl_hours)
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        logger.info(f"Weather cache initialized with TTL={ttl_hours}h, max_size={max_size}")
    
    def _normalize_key(self, location: str, start_date: str, end_date: str) -> str:
        """
        Create a normalized cache key.
        
        Args:
            location: Location string
            start_date: Start date in ISO format
            end_date: End date in ISO format
        
        Returns:
            Normalized cache key
        """
        # Normalize location: lowercase and strip whitespace
        normalized_location = location.lower().strip()
        return f"{normalized_location}:{start_date}:{end_date}"
    
    def get(self, location: str, start_date: str, end_date: str) -> Optional[Dict]:
        """
        Retrieve cached weather data if available and not expired.
        
        Args:
            location: Location string
            start_date: Start date in ISO format
            end_date: End date in ISO format
        
        Returns:
            Cached data if available and valid, None otherwise
        """
        key = self._normalize_key(location, start_date, end_date)
        
        if key not in self._cache:
            self._misses += 1
            logger.debug(f"Cache MISS for key: {key}")
            return None
        
        cached_time, cached_data = self._cache[key]
        
        # Check if cache entry has expired
        if datetime.now() - cached_time > self._ttl:
            # Remove expired entry
            del self._cache[key]
            self._misses += 1
            logger.debug(f"Cache EXPIRED for key: {key}")
            return None
        
        self._hits += 1
        logger.debug(f"Cache HIT for key: {key}")
        return cached_data
    
    def set(self, location: str, start_date: str, end_date: str, data: Dict) -> None:
        """
        Store weather data in cache.
        
        Args:
            location: Location string
            start_date: Start date in ISO format
            end_date: End date in ISO format
            data: Weather data to cache
        """
        key = self._normalize_key(location, start_date, end_date)
        
        # Implement simple LRU-like cleanup if cache is full
        if len(self._cache) >= self._max_size:
            self._cleanup_old_entries()
        
        self._cache[key] = (datetime.now(), data)
        logger.debug(f"Cache SET for key: {key}")
    
    def _cleanup_old_entries(self) -> None:
        """Remove oldest 20% of entries when cache is full."""
        if not self._cache:
            return
        
        # Sort by timestamp and remove oldest 20%
        sorted_items = sorted(self._cache.items(), key=lambda x: x[1][0])
        num_to_remove = max(1, len(sorted_items) // 5)
        
        for key, _ in sorted_items[:num_to_remove]:
            del self._cache[key]
        
        logger.info(f"Cache cleanup: removed {num_to_remove} old entries")
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(self._cache),
            "max_size": self._max_size
        }
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")


class WeatherService:
    """Service for interacting with WeatherAPI.com with caching support."""
    
    def __init__(self):
        self.api_key = settings.weather_api_key
        self.base_url = settings.weather_api_base_url
        self._cache = WeatherCache(
            ttl_hours=settings.weather_cache_ttl_hours,
            max_size=settings.weather_cache_max_size
        )
    
    async def get_forecast(
        self,
        location: str,
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Fetch weather forecast for a location and date range with caching.
        
        Args:
            location: Destination (city name, coordinates, etc.)
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
        
        Returns:
            Dictionary containing weather data and recommendations
        """
        try:
            # Check cache first
            cached_data = self._cache.get(location, start_date, end_date)
            if cached_data is not None:
                logger.info(f"Returning cached weather data for {location}")
                return cached_data
            
            # Cache miss - fetch from API
            logger.info(f"Fetching fresh weather data for {location}")
            
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
            
            # Store in cache (only cache successful responses)
            self._cache.set(location, start_date, end_date, weather_info)
            
            return weather_info
            
        except httpx.HTTPError as e:
            logger.error(f"Weather API request failed: {str(e)}")
            raise Exception(f"Weather API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to fetch weather data: {str(e)}")
            raise Exception(f"Failed to fetch weather data: {str(e)}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = self._cache.get_stats()
        logger.info(f"Cache stats: {stats}")
        return stats
    
    def clear_cache(self) -> None:
        """Clear the weather cache."""
        self._cache.clear()
        logger.info("Weather cache cleared")
    
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
        
        # Calculate average temperature in Fahrenheit (US standard)
        temps = [day["day"]["avgtemp_f"] for day in forecast_days]
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
            "temp_unit": "F",
            "conditions": conditions,
            "recommendation": recommendation,
            "forecast_data": {
                "location": data.get("location", {}).get("name", ""),
                "country": data.get("location", {}).get("country", ""),
                "daily_forecasts": [
                    {
                        "date": day["date"],
                        "max_temp_f": day["day"]["maxtemp_f"],
                        "min_temp_f": day["day"]["mintemp_f"],
                        "avg_temp_f": day["day"]["avgtemp_f"],
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
            
            # Categorize conditions - prioritize snow over rain
            # Check for snow first (higher priority in winter locations)
            if snow_chance > 30 or "snow" in condition_text:
                conditions_set.add("snowy")
            # Only check rain if snow is not present
            elif rain_chance > 30 or "rain" in condition_text:
                conditions_set.add("rainy")
            # Check for cloudy conditions
            elif "cloud" in condition_text or "overcast" in condition_text:
                conditions_set.add("cloudy")
            # Default to sunny/clear
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
            avg_temp: Average temperature in Fahrenheit
            conditions: List of weather conditions
            total_days: Total trip duration
            forecast_days: Forecast data
        
        Returns:
            Recommendation string
        """
        recommendations = []
        
        # Temperature-based recommendations (Fahrenheit)
        if avg_temp < 50:
            recommendations.append("Pack warm layers and a heavy jacket")
        elif avg_temp < 68:
            recommendations.append("Pack layers - it will be cool")
        elif avg_temp < 77:
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
            temps = [day["day"]["avgtemp_f"] for day in forecast_days]
            temp_range = max(temps) - min(temps)
            if temp_range > 18:  # 18°F ≈ 10°C
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
            "avg_temp": 68.0,
            "temp_unit": "F",
            "conditions": ["sunny"],
            "recommendation": "Check local weather closer to your trip date.",
            "forecast_data": None
        }


# Singleton instance
weather_service = WeatherService()