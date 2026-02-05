# Sprint 5: Enhanced Features - Setup Guide

## Overview

Sprint 5 implements two major enhancements to the Alpaca For You backend:

1. **Google Maps Integration** - Destination autocomplete and place details
2. **Smart Avatar Assignment** - Automatic emoji avatar assignment based on traveler attributes

## Features Implemented

### 1. Google Maps Integration

#### Components Created

- **Service**: [`backend/services/maps_service.py`](backend/services/maps_service.py)
  - `autocomplete_destination(query)` - Returns place suggestions
  - `get_place_details(place_id)` - Returns detailed place information

- **Models**: [`backend/models/maps.py`](backend/models/maps.py)
  - `PlaceSuggestion` - Autocomplete suggestion model
  - `PlaceDetails` - Detailed place information model
  - `AutocompleteResponse` - API response wrapper
  - `PlaceDetailsResponse` - API response wrapper

- **Routes**: [`backend/routes/maps.py`](backend/routes/maps.py)
  - `GET /api/v1/maps/autocomplete?query={query}` - Destination autocomplete
  - `GET /api/v1/maps/place/{place_id}` - Get place details

#### API Endpoints

##### Autocomplete Endpoint

```http
GET /api/v1/maps/autocomplete?query=New York
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "suggestions": [
    {
      "place_id": "ChIJOwg_06VPwokRYv534QaPC8g",
      "description": "New York, NY, USA",
      "main_text": "New York",
      "secondary_text": "NY, USA"
    }
  ]
}
```

##### Place Details Endpoint

```http
GET /api/v1/maps/place/ChIJOwg_06VPwokRYv534QaPC8g
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "place": {
    "place_id": "ChIJOwg_06VPwokRYv534QaPC8g",
    "name": "New York",
    "formatted_address": "New York, NY, USA",
    "lat": 40.7127753,
    "lng": -74.0059728,
    "types": ["locality", "political"]
  }
}
```

### 2. Smart Avatar Assignment

#### Components Created

- **Service**: [`backend/services/avatar_service.py`](backend/services/avatar_service.py)
  - `assign_avatar(traveler)` - Assigns appropriate emoji based on age, gender, and type
  - `get_avatar_description(avatar)` - Returns human-readable description

#### Avatar Logic

The avatar assignment follows these rules:

| Age Range | Gender | Avatar | Description |
|-----------|--------|--------|-------------|
| 0-2 years | Any | 👶 | Baby (gender-neutral) |
| 3-12 years | Female | 👧 | Girl |
| 3-12 years | Male | 👦 | Boy |
| 3-12 years | Unknown | 🧑 | Person |
| 13-17 years | Female | 👩 | Teen Girl / Woman |
| 13-17 years | Male | 👨 | Teen Boy / Man |
| 13-17 years | Unknown | 🧑 | Person |
| 18+ years | Female | 👩 | Woman |
| 18+ years | Male | 👨 | Man |
| 18+ years | Unknown | 🧑 | Person |

**Type Override**: The `type` field (infant/child/adult) can override age-based logic.

#### Integration

Avatar assignment is automatically integrated into trip creation and updates:

- [`backend/routes/trips.py`](backend/routes/trips.py) - Modified to assign avatars during traveler creation
- [`backend/models/trip.py`](backend/models/trip.py) - Avatar field already present in `TravelerBase` model

## Setup Instructions

### 1. Google Maps API Setup

#### Step 1: Get Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - **Places API**
   - **Places API (New)** (recommended for better features)
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy your API key

#### Step 2: Restrict API Key (Recommended)

1. Click on your API key to edit it
2. Under "API restrictions":
   - Select "Restrict key"
   - Choose "Places API"
3. Under "Application restrictions":
   - For development: "None"
   - For production: "HTTP referrers" or "IP addresses"

#### Step 3: Configure Environment

Add your API key to `.env`:

```bash
GOOGLE_MAPS_API_KEY=your_actual_api_key_here
```

### 2. Install Dependencies

The required dependency `httpx` should already be in [`requirements.txt`](backend/requirements.txt). If not, add it:

```bash
pip install httpx
```

### 3. Verify Configuration

Check that [`backend/config.py`](backend/config.py) includes:

```python
# Google Maps API Configuration
google_maps_api_key: str
```

### 4. Test the Integration

Run the test suites:

```bash
# Test Google Maps integration
pytest backend/test_maps.py -v

# Test avatar assignment
pytest backend/test_avatars.py -v

# Run all tests
pytest backend/ -v
```

## Usage Examples

### Frontend Integration - Destination Autocomplete

```typescript
// Example: Using the autocomplete endpoint in frontend
async function searchDestinations(query: string) {
  const response = await fetch(
    `/api/v1/maps/autocomplete?query=${encodeURIComponent(query)}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  const data = await response.json();
  return data.suggestions;
}

// Usage in a search input
const suggestions = await searchDestinations("Paris");
// Returns: [{ place_id: "...", description: "Paris, France", ... }]
```

### Frontend Integration - Place Details

```typescript
// Example: Getting place details after selection
async function getPlaceDetails(placeId: string) {
  const response = await fetch(
    `/api/v1/maps/place/${placeId}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  const data = await response.json();
  return data.place;
}

// Usage after user selects a destination
const place = await getPlaceDetails(selectedPlaceId);
// Returns: { name: "Paris", lat: 48.8566, lng: 2.3522, ... }
```

### Backend Integration - Avatar Assignment

```python
# Avatar assignment happens automatically during trip creation
# No manual intervention needed

# Example: Creating a trip with travelers
trip_data = {
    "destination": "Paris, France",
    "start_date": "2024-07-01",
    "end_date": "2024-07-10",
    "travelers": [
        {"name": "John", "age": 35, "gender": "male", "type": "adult"},
        {"name": "Jane", "age": 33, "gender": "female", "type": "adult"},
        {"name": "Emma", "age": 8, "gender": "female", "type": "child"},
        {"name": "Baby", "age": 1, "type": "infant"}
    ]
}

# Avatars will be automatically assigned:
# John: 👨, Jane: 👩, Emma: 👧, Baby: 👶
```

## API Authentication

All Maps API endpoints require authentication. Include the JWT access token in the Authorization header:

```http
Authorization: Bearer {access_token}
```

## Error Handling

### Google Maps API Errors

The service handles various error scenarios:

- **Empty/Short Query**: Returns empty array
- **No Results**: Returns empty array
- **API Errors**: Raises HTTPException with appropriate status code
- **Network Errors**: Raises HTTPException with 503 status

### Avatar Assignment Errors

Avatar assignment is defensive and always returns a valid emoji:

- **Missing Data**: Uses default avatar (🧑)
- **Invalid Age**: Treats as infant (👶)
- **Unknown Gender**: Uses gender-neutral avatar (🧑)

## Testing

### Test Coverage

#### Maps Tests ([`backend/test_maps.py`](backend/test_maps.py))

- ✅ Successful autocomplete requests
- ✅ Empty and short queries
- ✅ Zero results handling
- ✅ API error handling
- ✅ Network error handling
- ✅ Successful place details requests
- ✅ Invalid place ID handling
- ✅ Model validation

#### Avatar Tests ([`backend/test_avatars.py`](backend/test_avatars.py))

- ✅ Infant avatar assignment (0-2 years)
- ✅ Child avatar assignment (3-12 years)
- ✅ Teen avatar assignment (13-17 years)
- ✅ Adult avatar assignment (18+ years)
- ✅ Gender-based selection
- ✅ Type override logic
- ✅ Edge cases (empty data, unknown gender, etc.)
- ✅ Integration scenarios (family trips, teen groups)

### Running Tests

```bash
# Run all Sprint 5 tests
pytest backend/test_maps.py backend/test_avatars.py -v

# Run with coverage
pytest backend/test_maps.py backend/test_avatars.py --cov=backend/services --cov=backend/models --cov-report=html

# Run specific test class
pytest backend/test_avatars.py::TestAvatarAssignmentChildren -v
```

## Configuration Reference

### Environment Variables

```bash
# Required for Google Maps integration
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Other existing variables
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=alpacaforyou
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
JWT_SECRET_KEY=your_secret_key_here
OPENAI_API_KEY=your_openai_api_key_here
WEATHER_API_KEY=your_weatherapi_com_key_here
```

### Configuration File

[`backend/config.py`](backend/config.py) includes:

```python
class Settings(BaseSettings):
    # ... other settings ...
    
    # Google Maps API Configuration
    google_maps_api_key: str
```

## Troubleshooting

### Google Maps API Issues

**Problem**: "Google Maps API unavailable" error

**Solutions**:
1. Verify API key is correct in `.env`
2. Check that Places API is enabled in Google Cloud Console
3. Verify API key restrictions allow your server's IP/domain
4. Check API quota limits in Google Cloud Console

**Problem**: "REQUEST_DENIED" status

**Solutions**:
1. Enable Places API in Google Cloud Console
2. Check API key restrictions
3. Verify billing is enabled (required for Places API)

### Avatar Assignment Issues

**Problem**: All travelers getting default avatar (🧑)

**Solutions**:
1. Ensure `gender` field is provided in traveler data
2. Check that `age` field is a valid integer
3. Verify gender values are "male" or "female" (case-insensitive)

**Problem**: Wrong avatar for age group

**Solutions**:
1. Check the `type` field - it overrides age-based logic
2. Verify age boundaries (0-2: infant, 3-12: child, 13-17: teen, 18+: adult)

## Next Steps

### Recommended Enhancements

1. **Frontend Autocomplete Component**
   - Create a reusable destination search component
   - Implement debouncing for API calls
   - Add loading states and error handling

2. **Avatar Customization**
   - Allow users to manually override assigned avatars
   - Add more avatar options (skin tones, accessories)
   - Store custom avatar preferences

3. **Maps Features**
   - Add geocoding for address validation
   - Implement distance calculations
   - Add map visualization for destinations

4. **Performance Optimization**
   - Cache frequent autocomplete queries
   - Implement request rate limiting
   - Add Redis caching for place details

## Related Documentation

- [Sprint 1: Authentication Setup](backend/AUTH_SETUP.md)
- [Sprint 2: Trip Management](backend/SPRINT2_SETUP.md)
- [Sprint 3: Packing Lists](backend/SPRINT3_SETUP.md)
- [Sprint 4: Collaboration Features](backend/SPRINT4_SETUP.md)
- [Google Places API Documentation](https://developers.google.com/maps/documentation/places/web-service)

## Support

For issues or questions:
1. Check test files for usage examples
2. Review error messages in application logs
3. Verify environment configuration
4. Check Google Cloud Console for API status

---

**Sprint 5 Complete** ✅

All features implemented, tested, and documented.