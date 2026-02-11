"""API routes for Google Maps integration."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Annotated, Optional
import httpx

from models.maps import (
    AutocompleteResponse,
    PlaceDetailsResponse,
    PlaceSuggestion,
    PlaceDetails
)
from services.maps_service import maps_service
from routes.auth import get_current_user_optional
from models.user import UserInDB


router = APIRouter(prefix="/api/v1/maps", tags=["maps"])


@router.get(
    "/autocomplete",
    response_model=AutocompleteResponse,
    summary="Get destination autocomplete suggestions"
)
async def autocomplete_destination(
    input: Annotated[str, Query(min_length=2, description="Search query for destination")],
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
) -> AutocompleteResponse:
    """
    Get destination autocomplete suggestions using Google Places API.
    
    - **input**: Search query string (minimum 2 characters)
    
    Returns a list of place suggestions with place IDs and descriptions.
    Authentication is optional.
    """
    try:
        results = await maps_service.autocomplete_destination(input)
        suggestions = [PlaceSuggestion(**result) for result in results]
        return AutocompleteResponse(suggestions=suggestions)
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Google Maps API unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch autocomplete suggestions: {str(e)}"
        )


@router.get(
    "/place/{place_id}",
    response_model=PlaceDetailsResponse,
    summary="Get detailed place information"
)
async def get_place_details(
    place_id: str,
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
) -> PlaceDetailsResponse:
    """
    Get detailed information about a place using Google Places API.
    
    - **place_id**: Google Place ID from autocomplete
    
    Returns detailed place information including coordinates.
    Authentication is optional.
    """
    try:
        result = await maps_service.get_place_details(place_id)
        
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Place not found: {place_id}"
            )
        
        place = PlaceDetails(**result)
        return PlaceDetailsResponse(place=place)
    
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Google Maps API unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch place details: {str(e)}"
        )