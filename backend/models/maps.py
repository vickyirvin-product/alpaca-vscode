"""Pydantic models for Google Maps API responses."""
from pydantic import BaseModel, Field
from typing import List, Optional


class PlaceSuggestion(BaseModel):
    """Model for a place suggestion from autocomplete."""
    
    place_id: str = Field(..., description="Google Place ID")
    description: str = Field(..., description="Full description of the place")
    main_text: str = Field(..., description="Primary text (usually city name)")
    secondary_text: str = Field(..., description="Secondary text (usually country/region)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "place_id": "ChIJOwg_06VPwokRYv534QaPC8g",
                "description": "New York, NY, USA",
                "main_text": "New York",
                "secondary_text": "NY, USA"
            }
        }


class PlaceDetails(BaseModel):
    """Model for detailed place information."""
    
    place_id: str = Field(..., description="Google Place ID")
    name: str = Field(..., description="Name of the place")
    formatted_address: str = Field(..., description="Full formatted address")
    lat: float = Field(..., description="Latitude coordinate")
    lng: float = Field(..., description="Longitude coordinate")
    types: List[str] = Field(default_factory=list, description="Place types from Google")
    
    class Config:
        json_schema_extra = {
            "example": {
                "place_id": "ChIJOwg_06VPwokRYv534QaPC8g",
                "name": "New York",
                "formatted_address": "New York, NY, USA",
                "lat": 40.7127753,
                "lng": -74.0059728,
                "types": ["locality", "political"]
            }
        }


class AutocompleteResponse(BaseModel):
    """Response model for autocomplete endpoint."""
    
    suggestions: List[PlaceSuggestion] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "suggestions": [
                    {
                        "place_id": "ChIJOwg_06VPwokRYv534QaPC8g",
                        "description": "New York, NY, USA",
                        "main_text": "New York",
                        "secondary_text": "NY, USA"
                    }
                ]
            }
        }


class PlaceDetailsResponse(BaseModel):
    """Response model for place details endpoint."""
    
    place: Optional[PlaceDetails] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "place": {
                    "place_id": "ChIJOwg_06VPwokRYv534QaPC8g",
                    "name": "New York",
                    "formatted_address": "New York, NY, USA",
                    "lat": 40.7127753,
                    "lng": -74.0059728,
                    "types": ["locality", "political"]
                }
            }
        }