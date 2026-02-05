"""Packing list management routes for granular item control."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from database import get_db
from models.user import User
from models.trip import (
    TripInDB,
    PackingItemInDB,
    PackingListForPerson,
    AddItemRequest,
    UpdateItemRequest,
    DelegateItemRequest,
    AddCategoryRequest,
    ChangeCategoryRequest,
    TogglePackedResponse,
    DelegationInfo
)
from routes.auth import get_current_user


router = APIRouter(prefix="/api/v1/trips", tags=["packing"])


async def get_trip_and_verify_access(
    trip_id: str,
    user_id: str
) -> TripInDB:
    """
    Helper function to get a trip and verify user access.
    
    Args:
        trip_id: Trip ID
        user_id: User ID
    
    Returns:
        Trip document
    
    Raises:
        HTTPException: If trip not found or access denied
    """
    db = get_db()
    trips_collection = db.trips
    
    trip_doc = await trips_collection.find_one({
        "id": trip_id,
        "user_id": user_id
    })
    
    if not trip_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    return TripInDB(**trip_doc)


def find_item_in_trip(
    trip: TripInDB,
    item_id: str
) -> tuple[Optional[PackingItemInDB], Optional[str]]:
    """
    Find an item by ID within a trip's packing lists.
    
    Args:
        trip: Trip document
        item_id: Item ID to find
    
    Returns:
        Tuple of (item, person_id) or (None, None) if not found
    """
    for packing_list in trip.packing_lists:
        for item in packing_list.items:
            if item.id == item_id:
                return item, packing_list.person_id
    return None, None


def validate_person_exists(trip: TripInDB, person_id: str) -> bool:
    """
    Validate that a person ID exists in the trip's travelers.
    
    Args:
        trip: Trip document
        person_id: Person ID to validate
    
    Returns:
        True if person exists, False otherwise
    """
    return any(traveler.id == person_id for traveler in trip.travelers)


@router.post("/{trip_id}/items", status_code=status.HTTP_201_CREATED)
async def add_item(
    trip_id: str,
    item_data: AddItemRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Add a new item to a specific person's packing list.
    
    Args:
        trip_id: Trip ID
        item_data: Item data including person_id, name, category, etc.
        current_user: Authenticated user
    
    Returns:
        Created item
    """
    try:
        # Get and verify trip access
        trip = await get_trip_and_verify_access(trip_id, current_user.id)
        
        # Validate person exists
        if not validate_person_exists(trip, item_data.person_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {item_data.person_id} not found in trip"
            )
        
        # Create new item
        new_item = PackingItemInDB(
            id=str(ObjectId()),
            person_id=item_data.person_id,
            name=item_data.name,
            category=item_data.category,
            is_essential=item_data.is_essential,
            notes=item_data.notes,
            emoji=item_data.emoji,
            quantity=item_data.quantity,
            is_packed=False,
            visible_to_kid=True
        )
        
        # Find or create packing list for person
        db = get_db()
        trips_collection = db.trips
        
        person_list_exists = False
        for packing_list in trip.packing_lists:
            if packing_list.person_id == item_data.person_id:
                person_list_exists = True
                break
        
        if person_list_exists:
            # Add item to existing list
            await trips_collection.update_one(
                {
                    "id": trip_id,
                    "packing_lists.person_id": item_data.person_id
                },
                {
                    "$push": {"packing_lists.$.items": new_item.model_dump()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        else:
            # Create new packing list for person
            person_name = next(
                (t.name for t in trip.travelers if t.id == item_data.person_id),
                "Unknown"
            )
            new_list = PackingListForPerson(
                person_name=person_name,
                person_id=item_data.person_id,
                items=[new_item],
                categories=[item_data.category]
            )
            await trips_collection.update_one(
                {"id": trip_id},
                {
                    "$push": {"packing_lists": new_list.model_dump()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        return new_item
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add item: {str(e)}"
        )


@router.put("/{trip_id}/items/{item_id}")
async def update_item(
    trip_id: str,
    item_id: str,
    item_data: UpdateItemRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update an item (name, category, packed status, notes).
    
    Args:
        trip_id: Trip ID
        item_id: Item ID
        item_data: Updated item data
        current_user: Authenticated user
    
    Returns:
        Updated item
    """
    try:
        # Get and verify trip access
        trip = await get_trip_and_verify_access(trip_id, current_user.id)
        
        # Find item
        item, person_id = find_item_in_trip(trip, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        # Build update dict with only provided fields
        update_fields = {}
        if item_data.name is not None:
            update_fields["packing_lists.$[list].items.$[item].name"] = item_data.name
        if item_data.category is not None:
            update_fields["packing_lists.$[list].items.$[item].category"] = item_data.category
        if item_data.is_packed is not None:
            update_fields["packing_lists.$[list].items.$[item].is_packed"] = item_data.is_packed
        if item_data.is_essential is not None:
            update_fields["packing_lists.$[list].items.$[item].is_essential"] = item_data.is_essential
        if item_data.notes is not None:
            update_fields["packing_lists.$[list].items.$[item].notes"] = item_data.notes
        if item_data.emoji is not None:
            update_fields["packing_lists.$[list].items.$[item].emoji"] = item_data.emoji
        if item_data.quantity is not None:
            update_fields["packing_lists.$[list].items.$[item].quantity"] = item_data.quantity
        
        update_fields["updated_at"] = datetime.utcnow()
        
        # Update item in database
        db = get_db()
        trips_collection = db.trips
        
        await trips_collection.update_one(
            {"id": trip_id},
            {"$set": update_fields},
            array_filters=[
                {"list.person_id": person_id},
                {"item.id": item_id}
            ]
        )
        
        # Fetch and return updated item
        updated_trip_doc = await trips_collection.find_one({"id": trip_id})
        updated_trip = TripInDB(**updated_trip_doc)
        updated_item, _ = find_item_in_trip(updated_trip, item_id)
        
        return updated_item
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update item: {str(e)}"
        )


@router.delete("/{trip_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    trip_id: str,
    item_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete an item from a packing list.
    
    Args:
        trip_id: Trip ID
        item_id: Item ID
        current_user: Authenticated user
    """
    try:
        # Get and verify trip access
        trip = await get_trip_and_verify_access(trip_id, current_user.id)
        
        # Find item to verify it exists
        item, person_id = find_item_in_trip(trip, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        # Delete item from database
        db = get_db()
        trips_collection = db.trips
        
        await trips_collection.update_one(
            {
                "id": trip_id,
                "packing_lists.person_id": person_id
            },
            {
                "$pull": {"packing_lists.$.items": {"id": item_id}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete item: {str(e)}"
        )


@router.post("/{trip_id}/items/{item_id}/delegate")
async def delegate_item(
    trip_id: str,
    item_id: str,
    delegation_data: DelegateItemRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Move an item from one person to another (delegation).
    
    Args:
        trip_id: Trip ID
        item_id: Item ID
        delegation_data: From and to person IDs
        current_user: Authenticated user
    
    Returns:
        Updated item with delegation info
    """
    try:
        # Get and verify trip access
        trip = await get_trip_and_verify_access(trip_id, current_user.id)
        
        # Find item
        item, current_person_id = find_item_in_trip(trip, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        # Verify from_person_id matches current owner
        if current_person_id != delegation_data.from_person_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item does not belong to from_person_id"
            )
        
        # Validate both persons exist
        if not validate_person_exists(trip, delegation_data.from_person_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"From person with ID {delegation_data.from_person_id} not found"
            )
        if not validate_person_exists(trip, delegation_data.to_person_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"To person with ID {delegation_data.to_person_id} not found"
            )
        
        # Get person names
        from_person_name = next(
            (t.name for t in trip.travelers if t.id == delegation_data.from_person_id),
            "Unknown"
        )
        to_person_name = next(
            (t.name for t in trip.travelers if t.id == delegation_data.to_person_id),
            "Unknown"
        )
        
        # Create delegation info
        delegation_info = DelegationInfo(
            from_person_id=delegation_data.from_person_id,
            from_person_name=from_person_name,
            delegated_at=datetime.utcnow()
        )
        
        # Update item with new person_id and delegation info
        updated_item = item.model_copy(update={
            "person_id": delegation_data.to_person_id,
            "delegation_info": delegation_info
        })
        
        db = get_db()
        trips_collection = db.trips
        
        # Remove from old person's list
        await trips_collection.update_one(
            {
                "id": trip_id,
                "packing_lists.person_id": delegation_data.from_person_id
            },
            {
                "$pull": {"packing_lists.$.items": {"id": item_id}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Check if to_person has a packing list
        to_person_list_exists = any(
            pl.person_id == delegation_data.to_person_id
            for pl in trip.packing_lists
        )
        
        if to_person_list_exists:
            # Add to existing list
            await trips_collection.update_one(
                {
                    "id": trip_id,
                    "packing_lists.person_id": delegation_data.to_person_id
                },
                {
                    "$push": {"packing_lists.$.items": updated_item.model_dump()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        else:
            # Create new list for to_person
            new_list = PackingListForPerson(
                person_name=to_person_name,
                person_id=delegation_data.to_person_id,
                items=[updated_item],
                categories=[updated_item.category]
            )
            await trips_collection.update_one(
                {"id": trip_id},
                {
                    "$push": {"packing_lists": new_list.model_dump()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        return updated_item
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delegate item: {str(e)}"
        )


@router.put("/{trip_id}/items/{item_id}/toggle-packed", response_model=TogglePackedResponse)
async def toggle_packed(
    trip_id: str,
    item_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Toggle the packed status of an item.
    
    Args:
        trip_id: Trip ID
        item_id: Item ID
        current_user: Authenticated user
    
    Returns:
        Updated packed status
    """
    try:
        # Get and verify trip access
        trip = await get_trip_and_verify_access(trip_id, current_user.id)
        
        # Find item
        item, person_id = find_item_in_trip(trip, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        # Toggle packed status
        new_packed_status = not item.is_packed
        
        # Update in database
        db = get_db()
        trips_collection = db.trips
        
        await trips_collection.update_one(
            {"id": trip_id},
            {
                "$set": {
                    "packing_lists.$[list].items.$[item].is_packed": new_packed_status,
                    "updated_at": datetime.utcnow()
                }
            },
            array_filters=[
                {"list.person_id": person_id},
                {"item.id": item_id}
            ]
        )
        
        return TogglePackedResponse(
            item_id=item_id,
            is_packed=new_packed_status,
            message=f"Item {'packed' if new_packed_status else 'unpacked'} successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle packed status: {str(e)}"
        )


@router.post("/{trip_id}/categories", status_code=status.HTTP_201_CREATED)
async def add_category(
    trip_id: str,
    category_data: AddCategoryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Add a custom category to a person's packing list.
    
    Note: Categories are dynamically managed based on items.
    This endpoint is for future extensibility.
    
    Args:
        trip_id: Trip ID
        category_data: Person ID and category name
        current_user: Authenticated user
    
    Returns:
        Success message
    """
    try:
        # Get and verify trip access
        trip = await get_trip_and_verify_access(trip_id, current_user.id)
        
        # Validate person exists
        if not validate_person_exists(trip, category_data.person_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {category_data.person_id} not found"
            )
        
        # Find person's packing list
        person_list = next(
            (pl for pl in trip.packing_lists if pl.person_id == category_data.person_id),
            None
        )
        
        if not person_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Packing list not found for person"
            )
        
        # Check if category already exists
        if category_data.category_name in person_list.categories:
            return {
                "message": "Category already exists",
                "category": category_data.category_name
            }
        
        # Add category
        db = get_db()
        trips_collection = db.trips
        
        await trips_collection.update_one(
            {
                "id": trip_id,
                "packing_lists.person_id": category_data.person_id
            },
            {
                "$addToSet": {"packing_lists.$.categories": category_data.category_name},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return {
            "message": "Category added successfully",
            "category": category_data.category_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add category: {str(e)}"
        )


@router.put("/{trip_id}/items/{item_id}/category")
async def change_item_category(
    trip_id: str,
    item_id: str,
    category_data: ChangeCategoryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Change an item's category (supports drag-and-drop).
    
    Args:
        trip_id: Trip ID
        item_id: Item ID
        category_data: New category
        current_user: Authenticated user
    
    Returns:
        Updated item
    """
    try:
        # Get and verify trip access
        trip = await get_trip_and_verify_access(trip_id, current_user.id)
        
        # Find item
        item, person_id = find_item_in_trip(trip, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        # Update category
        db = get_db()
        trips_collection = db.trips
        
        await trips_collection.update_one(
            {"id": trip_id},
            {
                "$set": {
                    "packing_lists.$[list].items.$[item].category": category_data.new_category,
                    "updated_at": datetime.utcnow()
                }
            },
            array_filters=[
                {"list.person_id": person_id},
                {"item.id": item_id}
            ]
        )
        
        # Fetch and return updated item
        updated_trip_doc = await trips_collection.find_one({"id": trip_id})
        updated_trip = TripInDB(**updated_trip_doc)
        updated_item, _ = find_item_in_trip(updated_trip, item_id)
        
        return updated_item
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change category: {str(e)}"
        )


@router.get("/{trip_id}/packing-lists/{person_id}")
async def get_person_packing_list(
    trip_id: str,
    person_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get organized packing list for a specific person.
    
    Args:
        trip_id: Trip ID
        person_id: Person ID
        current_user: Authenticated user
    
    Returns:
        Person's packing list organized by categories
    """
    try:
        # Get and verify trip access
        trip = await get_trip_and_verify_access(trip_id, current_user.id)
        
        # Validate person exists
        if not validate_person_exists(trip, person_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found"
            )
        
        # Find person's packing list
        person_list = next(
            (pl for pl in trip.packing_lists if pl.person_id == person_id),
            None
        )
        
        if not person_list:
            # Return empty list if person has no items yet
            person_name = next(
                (t.name for t in trip.travelers if t.id == person_id),
                "Unknown"
            )
            return PackingListForPerson(
                person_name=person_name,
                person_id=person_id,
                items=[],
                categories=[]
            )
        
        return person_list
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get packing list: {str(e)}"
        )