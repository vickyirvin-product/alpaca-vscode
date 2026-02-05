# Sprint 3: Packing List Management - Setup Guide

## Overview

Sprint 3 implements granular item control for packing lists with person-specific management, delegation, and categorization. This sprint builds on the trip creation functionality from Sprint 2 and adds comprehensive item-level operations.

## Features Implemented

### 1. Item Management
- ✅ Add items to specific person's packing list
- ✅ Update item properties (name, category, packed status, notes)
- ✅ Delete items from packing lists
- ✅ Toggle packed status with single endpoint

### 2. Delegation System
- ✅ Move items between people
- ✅ Track delegation history (who delegated, when)
- ✅ Preserve delegation information

### 3. Category Management
- ✅ Change item categories (supports drag-and-drop)
- ✅ Add custom categories to person's list
- ✅ Dynamic category tracking

### 4. Person-Specific Views
- ✅ Retrieve organized packing list for specific person
- ✅ Category-based organization
- ✅ Item count and progress tracking

## API Endpoints

All endpoints require authentication via JWT token in the `Authorization` header.

### Add Item
```http
POST /api/v1/trips/{trip_id}/items
Content-Type: application/json
Authorization: Bearer <token>

{
  "person_id": "string",
  "name": "string",
  "category": "clothing|toiletries|electronics|documents|health|comfort|activities|baby|misc",
  "is_essential": false,
  "notes": "string (optional)",
  "emoji": "📦",
  "quantity": 1
}
```

**Response:** Created item object (201)

### Update Item
```http
PUT /api/v1/trips/{trip_id}/items/{item_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "string (optional)",
  "category": "string (optional)",
  "is_packed": true/false (optional),
  "is_essential": true/false (optional),
  "notes": "string (optional)",
  "emoji": "string (optional)",
  "quantity": 1 (optional)
}
```

**Response:** Updated item object (200)

### Delete Item
```http
DELETE /api/v1/trips/{trip_id}/items/{item_id}
Authorization: Bearer <token>
```

**Response:** No content (204)

### Delegate Item
```http
POST /api/v1/trips/{trip_id}/items/{item_id}/delegate
Content-Type: application/json
Authorization: Bearer <token>

{
  "from_person_id": "string",
  "to_person_id": "string"
}
```

**Response:** Updated item with delegation info (200)

### Toggle Packed Status
```http
PUT /api/v1/trips/{trip_id}/items/{item_id}/toggle-packed
Authorization: Bearer <token>
```

**Response:**
```json
{
  "item_id": "string",
  "is_packed": true/false,
  "message": "Item packed/unpacked successfully"
}
```

### Add Category
```http
POST /api/v1/trips/{trip_id}/categories
Content-Type: application/json
Authorization: Bearer <token>

{
  "person_id": "string",
  "category_name": "string"
}
```

**Response:** Success message (201)

### Change Item Category
```http
PUT /api/v1/trips/{trip_id}/items/{item_id}/category
Content-Type: application/json
Authorization: Bearer <token>

{
  "new_category": "string"
}
```

**Response:** Updated item object (200)

### Get Person's Packing List
```http
GET /api/v1/trips/{trip_id}/packing-lists/{person_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "person_name": "string",
  "person_id": "string",
  "items": [
    {
      "id": "string",
      "person_id": "string",
      "name": "string",
      "emoji": "string",
      "quantity": 1,
      "category": "string",
      "notes": "string",
      "is_packed": false,
      "is_essential": false,
      "visible_to_kid": true,
      "delegated_to": null,
      "delegation_info": {
        "from_person_id": "string",
        "from_person_name": "string",
        "delegated_at": "2026-02-03T20:00:00Z"
      }
    }
  ],
  "categories": ["clothing", "toiletries", "electronics"]
}
```

## Data Models

### PackingItemInDB
```python
{
  "id": str,                    # UUID
  "person_id": str,             # Owner's UUID
  "name": str,                  # Item name
  "emoji": str,                 # Visual identifier
  "quantity": int,              # Number of items
  "category": str,              # One of predefined categories
  "notes": Optional[str],       # Additional notes
  "is_packed": bool,            # Packed status
  "is_essential": bool,         # Essential item flag
  "visible_to_kid": bool,       # Kid mode visibility
  "delegated_to": Optional[str],# Delegation target (future use)
  "delegation_info": Optional[DelegationInfo]  # Delegation history
}
```

### DelegationInfo
```python
{
  "from_person_id": str,        # Original owner's UUID
  "from_person_name": str,      # Original owner's name
  "delegated_at": datetime      # When delegation occurred
}
```

### PackingListForPerson
```python
{
  "person_name": str,           # Person's name
  "person_id": str,             # Person's UUID
  "items": List[PackingItemInDB],  # All items for this person
  "categories": List[str]       # Categories with items
}
```

## Database Structure

Items are stored within each person's `packing_list` array in the Trip document:

```javascript
{
  "_id": ObjectId,
  "id": "trip_uuid",
  "user_id": "user_uuid",
  "destination": "Tokyo, Japan",
  "packing_lists": [
    {
      "person_name": "Sarah (Mom)",
      "person_id": "person_uuid",
      "items": [
        {
          "id": "item_uuid",
          "person_id": "person_uuid",
          "name": "Passport",
          "category": "documents",
          "is_packed": false,
          "is_essential": true,
          // ... other fields
        }
      ],
      "categories": ["documents", "clothing", "toiletries"]
    }
  ]
}
```

## Business Logic

### Helper Functions

#### `get_trip_and_verify_access(trip_id, user_id)`
- Fetches trip from database
- Verifies user owns the trip
- Raises 404 if not found or access denied

#### `find_item_in_trip(trip, item_id)`
- Searches all packing lists for item
- Returns tuple of (item, person_id)
- Returns (None, None) if not found

#### `validate_person_exists(trip, person_id)`
- Checks if person_id exists in trip's travelers
- Returns boolean

### Delegation Flow

1. Validate both from_person and to_person exist
2. Verify item belongs to from_person
3. Create delegation info with timestamp
4. Remove item from from_person's list
5. Update item with new person_id and delegation_info
6. Add item to to_person's list (create list if needed)

### Category Management

Categories are dynamically managed based on items:
- When adding an item, category is added to person's categories list
- Categories can be changed via drag-and-drop (category change endpoint)
- Custom categories can be added for future use

## Testing

### Run Tests
```bash
# Run packing list tests
python -m backend.test_packing

# Expected output:
# ✓ All imports successful
# ✓ Database connected successfully
# ✓ Test trip created successfully
# ✓ Item added successfully
# ✓ Item found successfully
# ✓ Item updated successfully
# ✓ Packed status toggled successfully
# ✓ Item delegated successfully
# ✓ Category changed successfully
```

### Test Coverage

The test suite covers:
- ✅ Adding items to packing lists
- ✅ Finding items by ID
- ✅ Updating item properties
- ✅ Toggling packed status
- ✅ Delegating items between people
- ✅ Category management
- ✅ Person validation
- ✅ Retrieving person-specific lists

## Error Handling

### 404 Not Found
- Trip not found
- Item not found
- Person not found in trip

### 400 Bad Request
- Item doesn't belong to from_person_id (delegation)
- Invalid category
- Invalid person_id

### 403 Forbidden
- User doesn't own the trip

### 500 Internal Server Error
- Database errors
- Unexpected failures

## Integration with Frontend

### Drag-and-Drop Support

The API supports drag-and-drop operations:

1. **Category Change**: Use `PUT /items/{item_id}/category`
2. **Delegation**: Use `POST /items/{item_id}/delegate`

### Real-time Updates

After any modification:
1. Frontend should refetch the trip or person's packing list
2. Use `GET /trips/{trip_id}` for full trip data
3. Use `GET /packing-lists/{person_id}` for person-specific view

### Kid Mode

Items have `visible_to_kid` flag for kid mode filtering:
- Essential items are always visible
- Non-essential items can be hidden from kids

## Security

All endpoints require authentication:
- JWT token in Authorization header
- User must own the trip
- Person IDs are validated against trip travelers

## Performance Considerations

### MongoDB Array Filters

The implementation uses MongoDB array filters for efficient updates:
```javascript
db.trips.updateOne(
  { "id": trip_id },
  { "$set": { "packing_lists.$[list].items.$[item].is_packed": true } },
  { arrayFilters: [
    { "list.person_id": person_id },
    { "item.id": item_id }
  ]}
)
```

### Indexing Recommendations

For optimal performance, create indexes:
```javascript
db.trips.createIndex({ "id": 1, "user_id": 1 })
db.trips.createIndex({ "packing_lists.person_id": 1 })
db.trips.createIndex({ "packing_lists.items.id": 1 })
```

## Next Steps

### Sprint 4 Suggestions
- Template management (save/load packing lists)
- Sharing packing lists with other users
- Printing/exporting packing lists
- Item suggestions based on destination/weather
- Progress tracking and statistics
- Reminders and notifications

## Troubleshooting

### Common Issues

**Issue**: Items not appearing after adding
- **Solution**: Ensure person_id matches a traveler in the trip

**Issue**: Delegation fails
- **Solution**: Verify both from_person_id and to_person_id exist in trip

**Issue**: Category change not working
- **Solution**: Use valid category from predefined list

**Issue**: 404 on item operations
- **Solution**: Verify item_id exists and belongs to the trip

## API Documentation

Full interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Files Modified/Created

### New Files
- `backend/routes/packing.py` - Packing list management routes
- `backend/test_packing.py` - Comprehensive test suite
- `backend/SPRINT3_SETUP.md` - This documentation

### Modified Files
- `backend/models/trip.py` - Added request/response models
- `backend/main.py` - Registered packing router

## Conclusion

Sprint 3 successfully implements comprehensive packing list management with:
- ✅ Granular item control
- ✅ Person-specific management
- ✅ Delegation system with history
- ✅ Category management
- ✅ Full test coverage
- ✅ Complete documentation

The system is ready for frontend integration and supports all planned features including drag-and-drop, delegation, and real-time updates.