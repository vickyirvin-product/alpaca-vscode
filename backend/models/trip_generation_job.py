from datetime import datetime
from typing import Literal, Optional, Dict, Any

from pydantic import BaseModel, Field
from bson import ObjectId


class TripGenerationJob(BaseModel):
    """Represents a trip generation background job."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    status: Literal["pending", "processing", "completed", "failed"] = "pending"
    trip_data: Dict[str, Any]
    trip_id: Optional[str] = None
    error_message: Optional[str] = None
    error_type: Optional[Literal["timeout", "validation", "api_error", "transient", "unknown"]] = None
    retry_count: int = 0
    max_retries: int = 2
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TripGenerationJobResponse(BaseModel):
    """Response payload for job status endpoints."""
    job_id: str = Field(alias="jobId")
    status: Literal["pending", "processing", "completed", "failed"]
    trip_id: Optional[str] = Field(default=None, alias="tripId")
    error: Optional[str] = None
    error_type: Optional[str] = Field(default=None, alias="errorType")
    retry_count: int = Field(default=0, alias="retryCount")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    class Config:
        populate_by_name = True


class JobStats(BaseModel):
    """Statistics about trip generation jobs."""
    pending: int = 0
    processing: int = 0
    completed: int = 0
    failed: int = 0
    stuck: int = 0
    total: int = 0