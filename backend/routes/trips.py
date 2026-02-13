"""Trip routes for creating and managing trips with intelligent packing lists."""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from database import get_db
from models.user import User
from models.trip import (
    TripCreate,
    TripInDB,
    TripResponse,
    TripListResponse,
    TravelerInDB,
    MigrationRequest
)
from services.avatar_service import avatar_service
from services.llm_service import llm_service
from services.weather_service import weather_service
from services.trip_generation_service import trip_generation_service
from routes.auth import get_current_user


router = APIRouter(prefix="/api/v1/trips", tags=["trips"])


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new trip with intelligent packing lists.
    
    Args:
        trip_data: Trip creation data including destination, dates, travelers, activities
        current_user: Authenticated user
    
    Returns:
        Created trip with generated packing lists
    """
    try:
        trip = await trip_generation_service.generate_trip(
            user_id=current_user.id,
            trip_data=trip_data
        )
        return TripResponse.from_db(trip)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create trip: {str(e)}"
        )


@router.get("", response_model=TripListResponse)
async def list_trips(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    List all trips for the current user.
    
    Args:
        current_user: Authenticated user
        skip: Number of trips to skip (pagination)
        limit: Maximum number of trips to return
    
    Returns:
        List of user's trips
    """
    try:
        db = get_db()
        trips_collection = db.trips
        
        # Query trips for current user
        cursor = trips_collection.find(
            {"user_id": current_user.id}
        ).sort("created_at", -1).skip(skip).limit(limit)
        
        trips = []
        async for trip_doc in cursor:
            # Convert MongoDB document to TripInDB
            trip = TripInDB(**trip_doc)
            trips.append(TripResponse.from_db(trip))
        
        # Get total count
        total = await trips_collection.count_documents({"user_id": current_user.id})
        
        return TripListResponse(trips=trips, total=total)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list trips: {str(e)}"
        )


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific trip by ID.
    
    Args:
        trip_id: Trip ID
        current_user: Authenticated user
    
    Returns:
        Trip details with packing lists
    """
    try:
        db = get_db()
        trips_collection = db.trips
        
        # Find trip
        trip_doc = await trips_collection.find_one({
            "id": trip_id,
            "user_id": current_user.id
        })
        
        if not trip_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        # Convert to response model
        trip = TripInDB(**trip_doc)
        return TripResponse.from_db(trip)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trip: {str(e)}"
        )


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: str,
    trip_data: TripCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing trip.
    
    This will regenerate packing lists with updated information.
    
    Args:
        trip_id: Trip ID
        trip_data: Updated trip data
        current_user: Authenticated user
    
    Returns:
        Updated trip
    """
    try:
        db = get_db()
        trips_collection = db.trips
        
        # Check if trip exists and belongs to user
        existing_trip = await trips_collection.find_one({
            "id": trip_id,
            "user_id": current_user.id
        })
        
        if not existing_trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        # Fetch updated weather data
        weather_data = None
        try:
            weather_info = await weather_service.get_forecast(
                location=trip_data.destination,
                start_date=trip_data.start_date,
                end_date=trip_data.end_date
            )
            from models.trip import WeatherInfo
            weather_data = WeatherInfo(**weather_info)
        except Exception as e:
            print(f"Weather fetch failed: {str(e)}")
        
        # Convert travelers with avatar assignment
        travelers_db = []
        for t in trip_data.travelers:
            # Assign avatar if not provided
            avatar = t.avatar
            if not avatar:
                traveler_dict = {
                    "age": t.age,
                    "gender": getattr(t, "gender", None),
                    "type": t.type
                }
                avatar = avatar_service.assign_avatar(traveler_dict)
            
            travelers_db.append(
                TravelerInDB(
                    id=str(ObjectId()),
                    name=t.name,
                    age=t.age,
                    type=t.type,
                    avatar=avatar
                )
            )
        
        # Regenerate packing lists
        packing_lists = await llm_service.generate_packing_lists(
            destination=trip_data.destination,
            start_date=trip_data.start_date,
            end_date=trip_data.end_date,
            travelers=travelers_db,
            weather_data=weather_data,
            activities=trip_data.activities,
            transport=trip_data.transport
        )
        
        # Update trip
        update_data = {
            "destination": trip_data.destination,
            "start_date": trip_data.start_date,
            "end_date": trip_data.end_date,
            "activities": trip_data.activities,
            "transport": trip_data.transport,
            "travelers": [t.model_dump() for t in travelers_db],
            "weather_data": weather_data.model_dump() if weather_data else None,
            "packing_lists": [pl.model_dump() for pl in packing_lists],
            "updated_at": datetime.utcnow()
        }
        
        await trips_collection.update_one(
            {"id": trip_id},
            {"$set": update_data}
        )
        
        # Fetch and return updated trip
        updated_trip_doc = await trips_collection.find_one({"id": trip_id})
        trip = TripInDB(**updated_trip_doc)
        return TripResponse.from_db(trip)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update trip: {str(e)}"
        )


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a trip.
    
    Args:
        trip_id: Trip ID
        current_user: Authenticated user
    """
    try:
        db = get_db()
        trips_collection = db.trips
        
        # Delete trip
        result = await trips_collection.delete_one({
            "id": trip_id,
            "user_id": current_user.id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete trip: {str(e)}"
        )


@router.post("/migrate", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def migrate_frontend_data(
    migration_data: MigrationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Migrate frontend mock data to backend format.
    
    This endpoint helps transition from frontend mock data to backend-stored trips.
    
    Args:
        migration_data: Frontend trip and packing data
        current_user: Authenticated user
    
    Returns:
        Created trip in backend format
    """
    try:
        # Parse frontend trip data
        trip_info = migration_data.trip_data
        
        # Convert to TripCreate format
        from models.trip import TravelerBase
        
        travelers = [
            TravelerBase(
                name=t.get("name"),
                age=t.get("age"),
                type=t.get("type"),
                avatar=t.get("avatar")
            )
            for t in trip_info.get("travelers", [])
        ]
        
        trip_create = TripCreate(
            destination=trip_info.get("destination"),
            start_date=trip_info.get("startDate"),
            end_date=trip_info.get("endDate"),
            activities=[],  # Extract from packing items if needed
            transport=[],
            travelers=travelers
        )
        
        # Use the regular create_trip endpoint
        return await create_trip(trip_create, current_user)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to migrate data: {str(e)}"
        )