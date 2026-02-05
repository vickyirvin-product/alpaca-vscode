"""Google Maps service for destination autocomplete and place details."""
import httpx
from typing import List, Optional
from config import settings


class MapsService:
    """Service for interacting with Google Maps APIs."""
    
    def __init__(self):
        self.api_key = settings.google_maps_api_key
        self.places_base_url = "https://maps.googleapis.com/maps/api/place"
    
    async def autocomplete_destination(self, query: str) -> List[dict]:
        """
        Get place suggestions using Google Places Autocomplete API.
        
        Args:
            query: Search query string
            
        Returns:
            List of place suggestions with place_id and description
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        if not query or len(query.strip()) < 2:
            return []
        
        url = f"{self.places_base_url}/autocomplete/json"
        params = {
            "input": query,
            "key": self.api_key,
            "types": "(cities)",  # Focus on cities and destinations
            "language": "en"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK":
                if data.get("status") == "ZERO_RESULTS":
                    return []
                raise Exception(f"Google Places API error: {data.get('status')}")
            
            predictions = data.get("predictions", [])
            results = []
            
            for prediction in predictions:
                # Extract main text (city name) and secondary text (country/region)
                structured_formatting = prediction.get("structured_formatting", {})
                results.append({
                    "place_id": prediction.get("place_id"),
                    "description": prediction.get("description"),
                    "main_text": structured_formatting.get("main_text", ""),
                    "secondary_text": structured_formatting.get("secondary_text", "")
                })
            
            return results
    
    async def get_place_details(self, place_id: str) -> Optional[dict]:
        """
        Get detailed information about a place using Google Places Details API.
        
        Args:
            place_id: Google Place ID
            
        Returns:
            Dictionary with place details including coordinates
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        if not place_id:
            return None
        
        url = f"{self.places_base_url}/details/json"
        params = {
            "place_id": place_id,
            "key": self.api_key,
            "fields": "place_id,name,formatted_address,geometry,types"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK":
                if data.get("status") == "NOT_FOUND":
                    return None
                raise Exception(f"Google Places API error: {data.get('status')}")
            
            result = data.get("result", {})
            geometry = result.get("geometry", {})
            location = geometry.get("location", {})
            
            return {
                "place_id": result.get("place_id"),
                "name": result.get("name"),
                "formatted_address": result.get("formatted_address"),
                "lat": location.get("lat"),
                "lng": location.get("lng"),
                "types": result.get("types", [])
            }


# Singleton instance
maps_service = MapsService()