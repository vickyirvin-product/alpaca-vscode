from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


# Traveler Models
class TravelerBase(BaseModel):
    """Base traveler model."""
    name: str
    age: int
    type: Literal["adult", "child", "infant"]
    avatar: Optional[str] = None


class TravelerInDB(TravelerBase):
    """Traveler model as stored in database."""
    id: str = Field(default_factory=lambda: str(ObjectId()))


class TravelerResponse(TravelerBase):
    """Traveler model for API responses."""
    id: str


# Weather Models
class WeatherInfo(BaseModel):
    """Weather information for the trip."""
    avg_temp: float
    temp_unit: Literal["C", "F"] = "C"
    conditions: List[Literal["sunny", "rainy", "cloudy", "snowy", "mixed"]]
    recommendation: str
    forecast_data: Optional[dict] = None  # Raw forecast data from API


# Packing Item Models
class DelegationInfo(BaseModel):
    """Information about item delegation."""
    from_person_id: str
    from_person_name: str
    delegated_at: datetime


class PackingItemBase(BaseModel):
    """Base packing item model."""
    name: str
    emoji: str = "📦"
    quantity: int = 1
    category: str  # Changed from Literal to str to allow activity-specific categories
    notes: Optional[str] = None


class PackingItemInDB(PackingItemBase):
    """Packing item as stored in database."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    person_id: str
    is_packed: bool = False
    is_essential: bool = False
    visible_to_kid: bool = True
    delegated_to: Optional[str] = None
    delegation_info: Optional[DelegationInfo] = None


class PackingItemResponse(PackingItemBase):
    """Packing item for API responses."""
    id: str
    person_id: str
    is_packed: bool
    is_essential: bool
    visible_to_kid: bool
    delegated_to: Optional[str] = None
    delegation_info: Optional[DelegationInfo] = None


# Packing List Models
class PackingListForPerson(BaseModel):
    """Packing list organized by person."""
    person_name: str
    person_id: str
    items: List[PackingItemInDB]
    categories: List[str]  # List of categories this person has items in


# Trip Models
class TripBase(BaseModel):
    """Base trip model."""
    destination: str
    start_date: str  # ISO date string
    end_date: str  # ISO date string
    activities: List[str] = []
    transport: List[str] = []


class TripCreate(TripBase):
    """Model for creating a new trip."""
    travelers: List[TravelerBase]


class TripInDB(TripBase):
    """Trip model as stored in database."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    travelers: List[TravelerInDB]
    weather_data: Optional[WeatherInfo] = None
    packing_lists: List[PackingListForPerson] = []
    share_token: Optional[str] = None
    share_expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class TripResponse(TripBase):
    """Trip model for API responses."""
    id: str
    user_id: str
    travelers: List[TravelerResponse]
    weather_data: Optional[WeatherInfo] = None
    packing_lists: List[PackingListForPerson] = []
    duration: int  # Calculated field
    created_at: str  # ISO datetime string
    updated_at: str  # ISO datetime string
    
    @classmethod
    def from_db(cls, trip: TripInDB) -> "TripResponse":
        """Convert database model to response model."""
        from datetime import datetime as dt
        
        # Calculate duration
        start = dt.fromisoformat(trip.start_date)
        end = dt.fromisoformat(trip.end_date)
        duration = (end - start).days + 1
        
        return cls(
            id=trip.id,
            user_id=trip.user_id,
            destination=trip.destination,
            start_date=trip.start_date,
            end_date=trip.end_date,
            activities=trip.activities,
            transport=trip.transport,
            travelers=[
                TravelerResponse(
                    id=t.id,
                    name=t.name,
                    age=t.age,
                    type=t.type,
                    avatar=t.avatar
                )
                for t in trip.travelers
            ],
            weather_data=trip.weather_data,
            packing_lists=trip.packing_lists,
            duration=duration,
            created_at=trip.created_at.isoformat(),
            updated_at=trip.updated_at.isoformat()
        )


class TripListResponse(BaseModel):
    """Response model for listing trips."""
    trips: List[TripResponse]
    total: int


# Packing List Request/Response Models
class AddItemRequest(BaseModel):
    """Request model for adding a new packing item."""
    person_id: str
    name: str
    category: str  # Changed from Literal to str to allow activity-specific categories
    is_essential: bool = False
    notes: Optional[str] = None
    emoji: str = "📦"
    quantity: int = 1


class UpdateItemRequest(BaseModel):
    """Request model for updating a packing item."""
    name: Optional[str] = None
    category: Optional[str] = None  # Changed from Literal to str to allow activity-specific categories
    is_packed: Optional[bool] = None
    is_essential: Optional[bool] = None
    notes: Optional[str] = None
    emoji: Optional[str] = None
    quantity: Optional[int] = None


class DelegateItemRequest(BaseModel):
    """Request model for delegating an item to another person."""
    from_person_id: str
    to_person_id: str


class AddCategoryRequest(BaseModel):
    """Request model for adding a custom category."""
    person_id: str
    category_name: str


class ChangeCategoryRequest(BaseModel):
    """Request model for changing an item's category."""
    new_category: str


class TogglePackedResponse(BaseModel):
    """Response model for toggling packed status."""
    item_id: str
    is_packed: bool
    message: str


# Nudge Models
class NudgeRequest(BaseModel):
    """Request model for sending a nudge."""
    person_id: str
    message: Optional[str] = None


class NudgeInDB(BaseModel):
    """Nudge model as stored in database."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    trip_id: str
    from_user_id: str
    to_user_email: EmailStr
    message: Optional[str] = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NudgeResponse(NudgeInDB):
    """Nudge response with trip details."""
    trip_destination: str
    trip_start_date: str
    from_user_name: Optional[str] = None


# Share Models
class ShareRequest(BaseModel):
    """Request model for generating a share link."""
    expiration_days: Optional[int] = None  # None = no expiration


class ShareResponse(BaseModel):
    """Response model for share link generation."""
    share_url: str
    share_token: str
    expires_at: Optional[datetime] = None


# Migration Models
class MigrationRequest(BaseModel):
    """Request model for migrating frontend mock data."""
    trip_data: dict
    packing_items: List[dict]