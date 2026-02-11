"""LLM routes for AI-powered features."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from services.llm_service import llm_service
from models.trip import PackingItemInDB

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])


class TravelerData(BaseModel):
    """Traveler data for packing list generation."""
    id: str
    name: str
    age: int
    type: str
    avatar: Optional[str] = None


class PackingListRequest(BaseModel):
    """Request model for generating packing lists."""
    destination: str
    start_date: str = Field(alias='startDate')
    end_date: str = Field(alias='endDate')
    activities: List[str]
    transport: Optional[List[str]] = []
    weather: Dict[str, Any]
    travelers: List[TravelerData]
    
    class Config:
        populate_by_name = True  # Allows both snake_case and camelCase


@router.post("/generate-packing-list")
async def generate_packing_list(request: PackingListRequest):
    """
    Generate context-aware packing lists using LLM.
    
    This endpoint uses AI to create personalized packing lists based on:
    - Destination and weather conditions
    - Trip duration
    - Traveler types (adults, children, infants)
    - Planned activities
    
    Returns a list of packing items for all travelers.
    """
    print("🔍 DEBUG - Backend received request:")
    print(f"  Destination: {request.destination}")
    print(f"  Activities: {request.activities}")
    print(f"  Transport: {request.transport}")
    print(f"  Travelers: {[t.name for t in request.travelers]}")
    
    try:
        # Convert request data to format expected by LLM service
        from models.trip import TravelerInDB, WeatherInfo
        
        # Convert travelers
        travelers = [
            TravelerInDB(
                id=t.id,
                name=t.name,
                age=t.age,
                type=t.type,
                avatar=t.avatar
            )
            for t in request.travelers
        ]
        
        # Convert weather data
        weather_data = None
        if request.weather:
            weather_data = WeatherInfo(
                avg_temp=request.weather.get('avgTemp', 20),
                temp_unit=request.weather.get('tempUnit', 'C'),
                conditions=request.weather.get('conditions', ['sunny']),
                recommendation=request.weather.get('recommendation', '')
            )
        
        # Generate packing lists using LLM
        packing_lists = await llm_service.generate_packing_lists(
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
            travelers=travelers,
            weather_data=weather_data,
            activities=request.activities,
            transport=request.transport or []
        )
        
        # Flatten packing lists into a single array of items
        all_items = []
        print(f"🔍 DEBUG - Number of packing lists returned: {len(packing_lists)}")
        
        for packing_list in packing_lists:
            print(f"🔍 DEBUG - Processing list for {packing_list.person_name} (ID: {packing_list.person_id})")
            print(f"🔍 DEBUG - Number of items in this list: {len(packing_list.items)}")
            
            for item in packing_list.items:
                # Convert to dict format expected by frontend
                item_dict = {
                    "id": item.id,
                    "name": item.name,
                    "emoji": item.emoji,
                    "quantity": item.quantity,
                    "category": item.category,
                    "isPacked": item.is_packed,
                    "isEssential": item.is_essential,
                    "visibleToKid": item.visible_to_kid,
                    "personId": item.person_id,
                    "notes": item.notes
                }
                all_items.append(item_dict)
        
        print(f"🔍 DEBUG - Total items being returned to frontend: {len(all_items)}")
        if all_items:
            print(f"🔍 DEBUG - Sample item: {all_items[0]}")
        
        return all_items
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate packing list: {str(e)}"
        )