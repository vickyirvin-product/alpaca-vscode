"""Collaboration routes for nudges and trip sharing."""

import secrets
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from database import get_db
from models.user import User
from models.trip import (
    NudgeRequest,
    NudgeInDB,
    NudgeResponse,
    ShareRequest,
    ShareResponse,
    TripInDB,
    TripResponse
)
from services.email_service import email_service
from routes.auth import get_current_user


router = APIRouter(prefix="/api/v1", tags=["collaboration"])


@router.post("/trips/{trip_id}/nudges", response_model=NudgeResponse, status_code=status.HTTP_201_CREATED)
async def send_nudge(
    trip_id: str,
    nudge_data: NudgeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send a nudge to a person to remind them to pack.
    
    If the recipient has an account, creates a notification.
    If they don't have an account, sends an invitation email.
    
    Args:
        trip_id: Trip ID
        nudge_data: Nudge request with person_id and optional message
        current_user: Authenticated user (trip owner)
    
    Returns:
        Created nudge with trip details
    """
    try:
        db = get_db()
        trips_collection = db.trips
        users_collection = db.users
        nudges_collection = db.nudges
        
        # Verify trip exists and belongs to user
        trip_doc = await trips_collection.find_one({
            "id": trip_id,
            "user_id": current_user.id
        })
        
        if not trip_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found or you don't have permission"
            )
        
        trip = TripInDB(**trip_doc)
        
        # Find the person in the trip's travelers
        person = None
        for traveler in trip.travelers:
            if traveler.id == nudge_data.person_id:
                person = traveler
                break
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found in trip"
            )
        
        # For now, we'll use a simple email format: firstname.lastname@example.com
        # In production, this would be stored with the traveler
        # For demo purposes, we'll construct an email from the person's name
        person_email = f"{person.name.lower().replace(' ', '.')}@example.com"
        
        # Check if recipient has an account
        recipient_user = await users_collection.find_one({"email": person_email})
        
        # Create nudge record
        nudge = NudgeInDB(
            id=str(ObjectId()),
            trip_id=trip_id,
            from_user_id=current_user.id,
            to_user_email=person_email,
            message=nudge_data.message,
            is_read=False,
            created_at=datetime.utcnow()
        )
        
        # Save nudge to database
        await nudges_collection.insert_one(nudge.model_dump())
        
        # Send appropriate notification
        if recipient_user:
            # User has account - send notification email
            await email_service.send_nudge_notification(
                to_email=person_email,
                from_user_name=current_user.full_name or current_user.email,
                trip_destination=trip.destination,
                trip_start_date=trip.start_date,
                message=nudge_data.message
            )
        else:
            # User doesn't have account - send invitation email
            await email_service.send_nudge_email(
                to_email=person_email,
                from_user_name=current_user.full_name or current_user.email,
                trip_destination=trip.destination,
                trip_start_date=trip.start_date,
                message=nudge_data.message
            )
        
        # Return response with trip details
        return NudgeResponse(
            id=nudge.id,
            trip_id=nudge.trip_id,
            from_user_id=nudge.from_user_id,
            to_user_email=nudge.to_user_email,
            message=nudge.message,
            is_read=nudge.is_read,
            created_at=nudge.created_at,
            trip_destination=trip.destination,
            trip_start_date=trip.start_date,
            from_user_name=current_user.full_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send nudge: {str(e)}"
        )


@router.get("/nudges", response_model=List[NudgeResponse])
async def get_nudges(
    current_user: User = Depends(get_current_user),
    unread_only: bool = False
):
    """
    Get nudges for the current user.
    
    Args:
        current_user: Authenticated user
        unread_only: If True, only return unread nudges
    
    Returns:
        List of nudges with trip details
    """
    try:
        db = get_db()
        nudges_collection = db.nudges
        trips_collection = db.trips
        users_collection = db.users
        
        # Build query
        query = {"to_user_email": current_user.email}
        if unread_only:
            query["is_read"] = False
        
        # Fetch nudges
        cursor = nudges_collection.find(query).sort("created_at", -1)
        
        nudges_response = []
        async for nudge_doc in cursor:
            nudge = NudgeInDB(**nudge_doc)
            
            # Fetch trip details
            trip_doc = await trips_collection.find_one({"id": nudge.trip_id})
            if not trip_doc:
                continue
            
            trip = TripInDB(**trip_doc)
            
            # Fetch sender details
            sender_doc = await users_collection.find_one({"id": nudge.from_user_id})
            sender_name = None
            if sender_doc:
                sender_name = sender_doc.get("full_name") or sender_doc.get("email")
            
            nudges_response.append(NudgeResponse(
                id=nudge.id,
                trip_id=nudge.trip_id,
                from_user_id=nudge.from_user_id,
                to_user_email=nudge.to_user_email,
                message=nudge.message,
                is_read=nudge.is_read,
                created_at=nudge.created_at,
                trip_destination=trip.destination,
                trip_start_date=trip.start_date,
                from_user_name=sender_name
            ))
        
        return nudges_response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch nudges: {str(e)}"
        )


@router.put("/nudges/{nudge_id}/mark-read", response_model=NudgeResponse)
async def mark_nudge_read(
    nudge_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Mark a nudge as read.
    
    Args:
        nudge_id: Nudge ID
        current_user: Authenticated user
    
    Returns:
        Updated nudge
    """
    try:
        db = get_db()
        nudges_collection = db.nudges
        trips_collection = db.trips
        users_collection = db.users
        
        # Find nudge
        nudge_doc = await nudges_collection.find_one({
            "id": nudge_id,
            "to_user_email": current_user.email
        })
        
        if not nudge_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nudge not found"
            )
        
        # Update nudge
        await nudges_collection.update_one(
            {"id": nudge_id},
            {"$set": {"is_read": True}}
        )
        
        # Fetch updated nudge
        updated_doc = await nudges_collection.find_one({"id": nudge_id})
        nudge = NudgeInDB(**updated_doc)
        
        # Fetch trip details
        trip_doc = await trips_collection.find_one({"id": nudge.trip_id})
        trip = TripInDB(**trip_doc) if trip_doc else None
        
        # Fetch sender details
        sender_doc = await users_collection.find_one({"id": nudge.from_user_id})
        sender_name = None
        if sender_doc:
            sender_name = sender_doc.get("full_name") or sender_doc.get("email")
        
        return NudgeResponse(
            id=nudge.id,
            trip_id=nudge.trip_id,
            from_user_id=nudge.from_user_id,
            to_user_email=nudge.to_user_email,
            message=nudge.message,
            is_read=nudge.is_read,
            created_at=nudge.created_at,
            trip_destination=trip.destination if trip else "Unknown",
            trip_start_date=trip.start_date if trip else "Unknown",
            from_user_name=sender_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark nudge as read: {str(e)}"
        )


@router.post("/trips/{trip_id}/share", response_model=ShareResponse)
async def generate_share_link(
    trip_id: str,
    share_data: ShareRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a public share link for a trip.
    
    Only the trip owner can generate share links.
    
    Args:
        trip_id: Trip ID
        share_data: Share request with optional expiration
        current_user: Authenticated user (trip owner)
    
    Returns:
        Share link details
    """
    try:
        db = get_db()
        trips_collection = db.trips
        
        # Verify trip exists and belongs to user
        trip_doc = await trips_collection.find_one({
            "id": trip_id,
            "user_id": current_user.id
        })
        
        if not trip_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found or you don't have permission"
            )
        
        # Generate secure token
        share_token = secrets.token_urlsafe(32)
        
        # Calculate expiration
        expires_at = None
        if share_data.expiration_days:
            expires_at = datetime.utcnow() + timedelta(days=share_data.expiration_days)
        
        # Update trip with share token
        await trips_collection.update_one(
            {"id": trip_id},
            {
                "$set": {
                    "share_token": share_token,
                    "share_expires_at": expires_at,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Generate share URL (in production, use actual domain)
        share_url = f"https://alpacaforyou.com/shared/{share_token}"
        
        return ShareResponse(
            share_url=share_url,
            share_token=share_token,
            expires_at=expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate share link: {str(e)}"
        )


@router.get("/trips/shared/{share_token}", response_model=TripResponse)
async def get_shared_trip(share_token: str):
    """
    Access a trip via share token (no authentication required).
    
    Args:
        share_token: Share token
    
    Returns:
        Trip details
    """
    try:
        db = get_db()
        trips_collection = db.trips
        
        # Find trip by share token
        trip_doc = await trips_collection.find_one({"share_token": share_token})
        
        if not trip_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared trip not found"
            )
        
        trip = TripInDB(**trip_doc)
        
        # Check if share link has expired
        if trip.share_expires_at and trip.share_expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Share link has expired"
            )
        
        # Return trip details
        return TripResponse.from_db(trip)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to access shared trip: {str(e)}"
        )


@router.delete("/trips/{trip_id}/share", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share_link(
    trip_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Revoke share access for a trip.
    
    Only the trip owner can revoke share links.
    
    Args:
        trip_id: Trip ID
        current_user: Authenticated user (trip owner)
    """
    try:
        db = get_db()
        trips_collection = db.trips
        
        # Verify trip exists and belongs to user
        trip_doc = await trips_collection.find_one({
            "id": trip_id,
            "user_id": current_user.id
        })
        
        if not trip_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found or you don't have permission"
            )
        
        # Remove share token
        await trips_collection.update_one(
            {"id": trip_id},
            {
                "$set": {
                    "share_token": None,
                    "share_expires_at": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke share link: {str(e)}"
        )