
# Backend Development Plan - Alpaca

## 1️⃣ Executive Summary

**What We're Building:**
A FastAPI backend for Alpaca - a family packing list app that uses AI to generate personalized packing lists based on trip details. Users can create trips without signing up (localStorage), then authenticate via Google OAuth to save and share their trips.

**Key Constraints:**
- **Backend:** FastAPI (Python 3.13, async)
- **Database:** MongoDB Atlas (connection string provided)
- **Authentication:** Google OAuth 2.0 + JWT sessions
- **No Docker** - Local development only
- **API Base Path:** `/api/v1/*`
- **Testing:** Manual via frontend UI after each task
- **Git:** Sprint-based branching strategy (see Git Workflow section below)
- **Background Tasks:** Synchronous by default, `BackgroundTasks` only if necessary
- **Weather API:** OpenWeatherMap or WeatherAPI for real-time weather data

**Architecture Approach:**
- "Try Before You Sign Up" flow - users create trips in localStorage, authenticate to save
- Google OAuth for zero-friction authentication
- LLM integration for intelligent packing list generation
- Session-based access with JWT tokens
- Future-proof data model (easy to add features later)

**Sprint Structure:**
- **S0:** Environment setup + MongoDB connection
- **S1:** Google OAuth authentication
- **S2:** Trip creation with LLM integration
- **S3:** Packing list management (CRUD operations)
- **S4:** Collaboration features (sharing, delegation, nudges)
- **S5:** Enhanced features (Google Maps API, avatar management)

---

## 2️⃣ In-Scope & Success Criteria

**In-Scope Features:**
- Google OAuth authentication (login, logout, token refresh)
- Trip creation with destination, dates, travelers, activities
- **Real-time weather data** fetching for destinations and dates
- AI-powered packing list generation using OpenAI (weather-aware)
- Packing item CRUD (create, read, update, delete, check/uncheck)
- Item categorization and organization
- Delegation of items between travelers
- Nudge notifications for incomplete packing
- Google Maps API integration for destination search
- Avatar management (emoji defaults, optional upload in future)
- localStorage → Database migration for "try first" flow
- Session management with JWT tokens

**Success Criteria:**
- All frontend features functional end-to-end
- Users can create trips without auth, then save via Google login
- LLM generates contextually appropriate packing lists
- All task-level manual tests pass via UI
- Each sprint's code pushed to `main` after verification
- Backend connects to MongoDB Atlas successfully
- Google OAuth flow works seamlessly (1-click login)

---

## 3️⃣ API Design

**Base Path:** `/api/v1`

**Error Envelope:**
```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

### Authentication Endpoints

**POST /api/v1/auth/google**
- **Purpose:** Authenticate user via Google OAuth token
- **Request:**
  ```json
  {
    "token": "google_oauth_token_string"
  }
  ```
- **Response:**
  ```json
  {
    "access_token": "jwt_token",
    "refresh_token": "refresh_jwt",
    "user": {
      "id": "user_id",
      "email": "user@example.com",
      "name": "John Doe",
      "avatar": "https://google.com/avatar.jpg"
    }
  }
  ```
- **Validation:** Verify Google token, create/get user in DB

**POST /api/v1/auth/refresh**
- **Purpose:** Refresh expired JWT token
- **Request:**
  ```json
  {
    "refresh_token": "refresh_jwt"
  }
  ```
- **Response:**
  ```json
  {
    "access_token": "new_jwt_token"
  }
  ```

**POST /api/v1/auth/logout**
- **Purpose:** Invalidate refresh token
- **Request:** Bearer token in header
- **Response:**
  ```json
  {
    "message": "Logged out successfully"
  }
  ```

**GET /api/v1/auth/me**
- **Purpose:** Get current user info
- **Request:** Bearer token in header
- **Response:**
  ```json
  {
    "id": "user_id",
    "email": "user@example.com",
    "name": "John Doe",
    "avatar": "url",
    "created_at": "2026-02-03T10:00:00Z"
  }
  ```

### Trip Endpoints

**POST /api/v1/trips**
- **Purpose:** Create new trip with AI-generated packing list
- **Request:**
  ```json
  {
    "title": "Spring Trip to Japan",
    "destinations": ["Tokyo", "Kyoto"],
    "start_date": "2026-03-28",
    "end_date": "2026-04-18",
    "travelers": [
      {
        "name": "Mom",
        "age": 38,
        "type": "adult"
      },
      {
        "name": "Emma",
        "age": 10,
        "type": "child"
      }
    ],
    "activities": ["Hiking", "Sightseeing"],
    "transport": ["Walking", "Train"]
  }
  ```
- **Response:**
  ```json
  {
    "trip_id": "trip_abc123",
    "title": "Spring Trip to Japan",
    "destinations": ["Tokyo", "Kyoto"],
    "start_date": "2026-03-28",
    "end_date": "2026-04-18",
    "duration": 21,
    "weather": {
      "avg_temp": 15,
      "temp_unit": "C",
      "conditions": ["sunny", "rainy"],
      "recommendation": "Pack layers..."
    },
    "travelers": [...],
    "packing_items": [...],
    "created_at": "2026-02-03T10:00:00Z"
  }
  ```
- **Validation:** Dates valid, at least 1 destination, at least 1 traveler
- **Background:** Calls OpenAI API to generate packing list

**POST /api/v1/trips/migrate**
- **Purpose:** Migrate localStorage trip to authenticated user's account
- **Request:**
  ```json
  {
    "trip_data": {
      "title": "...",
      "destinations": [...],
      "travelers": [...],
      "packing_items": [...]
    }
  }
  ```
- **Response:**
  ```json
  {
    "trip_id": "trip_abc123",
    "message": "Trip migrated successfully"
  }
  ```
- **Validation:** User must be authenticated

**GET /api/v1/trips**
- **Purpose:** Get all trips for authenticated user
- **Request:** Bearer token in header
- **Response:**
  ```json
  {
    "trips": [
      {
        "trip_id": "trip_abc123",
        "title": "Spring Trip to Japan",
        "destinations": ["Tokyo"],
        "start_date": "2026-03-28",
        "end_date": "2026-04-18",
        "travelers_count": 4,
        "packing_progress": 45,
        "created_at": "2026-02-03T10:00:00Z"
      }
    ]
  }
  ```

**GET /api/v1/trips/{trip_id}**
- **Purpose:** Get full trip details
- **Request:** Bearer token in header
- **Response:** Full trip object with all travelers and packing items
- **Validation:** User must own trip or have shared access

**PATCH /api/v1/trips/{trip_id}**
- **Purpose:** Update trip details
- **Request:**
  ```json
  {
    "title": "Updated Title",
    "destinations": ["Tokyo", "Osaka"]
  }
  ```
- **Response:** Updated trip object
- **Validation:** User must own trip

**DELETE /api/v1/trips/{trip_id}**
- **Purpose:** Delete trip
- **Request:** Bearer token in header
- **Response:**
  ```json
  {
    "message": "Trip deleted successfully"
  }
  ```

### Packing Item Endpoints

**POST /api/v1/trips/{trip_id}/items**
- **Purpose:** Add new packing item to a specific person's packing list
- **Request:**
  ```json
  {
    "person_id": "traveler_id",
    "name": "Sunscreen",
    "emoji": "☀️",
    "quantity": 1,
    "category": "toiletries",
    "is_essential": false,
    "visible_to_kid": true
  }
  ```
- **Response:** Created item object with generated ID
- **Validation:**
  - `person_id` is REQUIRED and must exist in trip's travelers array
  - `category` must be valid enum value
  - Item is added to the specified person's packing list only
- **Frontend Context:** When user adds item via UI, they are viewing a specific person's packing list (selected avatar). The `person_id` is automatically set to that person.

**PATCH /api/v1/trips/{trip_id}/items/{item_id}**
- **Purpose:** Update packing item (check/uncheck, edit details)
- **Request:**
  ```json
  {
    "is_packed": true,
    "quantity": 2,
    "category": "clothing"
  }
  ```
- **Response:** Updated item object

**DELETE /api/v1/trips/{trip_id}/items/{item_id}**
- **Purpose:** Delete packing item
- **Response:**
  ```json
  {
    "message": "Item deleted successfully"
  }
  ```

**POST /api/v1/trips/{trip_id}/items/delegate**
- **Purpose:** Delegate items to another traveler
- **Request:**
  ```json
  {
    "item_ids": ["item1", "item2"],
    "from_person_id": "mom",
    "to_person_id": "dad"
  }
  ```
- **Response:**
  ```json
  {
    "delegated_count": 2,
    "items": [...]
  }
  ```

**POST /api/v1/trips/{trip_id}/items/move-category**
- **Purpose:** Move item to different category
- **Request:**
  ```json
  {
    "item_id": "item123",
    "new_category": "electronics"
  }
  ```
- **Response:** Updated item object

### Collaboration Endpoints

**POST /api/v1/trips/{trip_id}/nudge**
- **Purpose:** Send nudge notification to traveler
- **Request:**
  ```json
  {
    "person_id": "emma",
    "message": "Don't forget to pack!"
  }
  ```
- **Response:**
  ```json
  {
    "message": "Emma will be notified!",
    "has_account": true
  }
  ```
- **Validation:** Check if traveler has Alpaca account by email/name

**POST /api/v1/trips/{trip_id}/share**
- **Purpose:** Generate shareable link for trip
- **Request:**
  ```json
  {
    "permissions": "edit"
  }
  ```
- **Response:**
  ```json
  {
    "share_link": "https://alpacaforyou.com/trip/abc123?token=xyz",
    "expires_at": "2026-03-03T10:00:00Z"
  }
  ```

### Utility Endpoints

**GET /api/v1/destinations/search**
- **Purpose:** Search destinations using Google Maps API
- **Request:** `?query=tokyo`
- **Response:**
  ```json
  {
    "results": [
      {
        "name": "Tokyo, Japan",
        "place_id": "ChIJ...",
        "formatted_address": "Tokyo, Japan"
      }
    ]
  }
  ```

**GET /api/v1/healthz**
- **Purpose:** Health check endpoint
- **Response:**
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "timestamp": "2026-02-03T10:00:00Z"
  }
  ```

---

## 4️⃣ Data Model (MongoDB Atlas)

### Collection: `users`
```json
{
  "_id": "ObjectId",
  "google_id": "string (unique)",
  "email": "string (unique, indexed)",
  "name": "string",
  "avatar_url": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```
**Indexes:** `email`, `google_id`

### Collection: `trips`
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId (ref: users)",
  "title": "string",
  "destinations": ["string"],
  "start_date": "date",
  "end_date": "date",
  "duration": "int (calculated)",
  "weather": {
    "avg_temp": "float",
    "temp_unit": "string (C or F)",
    "conditions": ["string"],
    "recommendation": "string"
  },
  "travelers": [
    {
      "id": "string (generated)",
      "name": "string",
      "age": "int",
      "type": "string (adult/child/infant)",
      "avatar_emoji": "string",
      "avatar_url": "string (optional)"
    }
  ],
  "activities": ["string"],
  "transport": ["string"],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```
**Indexes:** `user_id`, `created_at`

**Example Document:**
```json
{
  "_id": "65f1a2b3c4d5e6f7g8h9i0j1",
  "user_id": "65f1a2b3c4d5e6f7g8h9i0j0",
  "title": "Spring Trip to Japan",
  "destinations": ["Tokyo", "Kyoto"],
  "start_date": "2026-03-28T00:00:00Z",
  "end_date": "2026-04-18T00:00:00Z",
  "duration": 21,
  "weather": {
    "avg_temp": 15,
    "temp_unit": "C",
    "conditions": ["sunny", "rainy"],
    "recommendation": "Pack layers! Cherry blossom season..."
  },
  "travelers": [
    {
      "id": "mom",
      "name": "Sarah",
      "age": 38,
      "type": "adult",
      "avatar_emoji": "👩"
    },
    {
      "id": "emma",
      "name": "Emma",
      "age": 10,
      "type": "child",
      "avatar_emoji": "👧"
    }
  ],
  "activities": ["Hiking", "Sightseeing"],
  "transport": ["Walking", "Train"],
  "created_at": "2026-02-03T10:00:00Z",
  "updated_at": "2026-02-03T10:00:00Z"
}
```

### Collection: `packing_items`
```json
{
  "_id": "ObjectId",
  "trip_id": "ObjectId (ref: trips)",
  "person_id": "string (matches travelers[].id)",
  "name": "string",
  "emoji": "string",
  "quantity": "int",
  "category": "string (enum)",
  "is_packed": "boolean (default: false)",
  "is_essential": "boolean (default: false)",
  "visible_to_kid": "boolean (default: true)",
  "delegation_info": {
    "from_person_id": "string",
    "from_person_name": "string",
    "delegated_at": "datetime"
  },
  "notes": "string (optional)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```
**Indexes:** `trip_id`, `person_id`, `category`

**Categories (enum):**
- `clothing`
- `toiletries`
- `electronics`
- `documents`
- `health`
- `comfort`
- `activities`
- `baby`
- `misc`

**Example Document:**
```json
{
  "_id": "65f1a2b3c4d5e6f7g8h9i0j2",
  "trip_id": "65f1a2b3c4d5e6f7g8h9i0j1",
  "person_id": "mom",
  "name": "Passports (Family)",
  "emoji": "🛂",
  "quantity": 4,
  "category": "documents",
  "is_packed": false,
  "is_essential": true,
  "visible_to_kid": true,
  "created_at": "2026-02-03T10:00:00Z",
  "updated_at": "2026-02-03T10:00:00Z"
}
```

### Collection: `refresh_tokens`
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId (ref: users)",
  "token": "string (hashed)",
  "expires_at": "datetime",
  "created_at": "datetime"
}
```
**Indexes:** `user_id`, `expires_at`

---

## 5️⃣ Frontend Audit & Feature Map

### Home Page - Trip Wizard (`/`)

**Route:** `/`  
**Component:** `SmartWizard.tsx`

**Purpose:** Collect trip details and generate packing list

**Data Needed:**
- Destination search results (Google Maps API)
- Weather data for destination + dates
- LLM-generated packing list based on inputs

**Required Backend Endpoints:**
- `GET /api/v1/destinations/search` - Autocomplete destinations
- `POST /api/v1/trips` - Create trip with LLM generation
- `POST /api/v1/trips/migrate` - Save localStorage trip after auth

**Auth Requirement:** Optional (can create in localStorage, auth to save)

**Notes:**
- **REQUIRED fields (strictly enforced):**
  - Destination (at least 1)
  - Start date and end date
  - For children: ages are REQUIRED (core value prop for age-appropriate packing)
  - Activities (required for LLM to generate useful lists)
- **Recommended fields (yellow highlight if empty):**
  - Transport methods (helps with packing suggestions)

- Yellow highlight text for recommended fields: "Add this for better suggestions"
- Remove "Skip to demo" button
- Default kid mode level based on age: ≤6 = little, 7-11 = big, ≥12 = teenager

---

### Dashboard - Trip Overview (`/dashboard`)

**Route:** `/dashboard`  
**Component:** `Dashboard.tsx`

**Purpose:** View trip summary and manage packing lists

**Data Needed:**
- Current trip details
- All travelers
- Overall packing progress
- Trip summary card data

**Required Backend Endpoints:**
- `GET /api/v1/trips/{trip_id}` - Get full trip details
- `GET /api/v1/trips` - List all user trips

**Auth Requirement:** Yes (must be logged in)

**Notes:**
- Trip name editable via `PATCH /api/v1/trips/{trip_id}`
- Overall progress calculated from all items across all travelers

---

### Packing List - Person View

**Component:** `PersonPackingList.tsx`

**Purpose:** Manage packing items for individual traveler

**Data Needed:**
- All packing items for selected person
- Item categories
- Delegation history
- Essential items

**Required Backend Endpoints:**
- `GET /api/v1/trips/{trip_id}` - Get items (filtered by person_id on frontend)
- `POST /api/v1/trips/{trip_id}/items` - Add new item **to the currently selected person**
- `PATCH /api/v1/trips/{trip_id}/items/{item_id}` - Update item (check/uncheck, edit)
- `DELETE /api/v1/trips/{trip_id}/items/{item_id}` - Delete item
- `POST /api/v1/trips/{trip_id}/items/delegate` - Delegate items
- `POST /api/v1/trips/{trip_id}/items/move-category` - Move to different category

**Auth Requirement:** Yes

**Notes:**
- **Person-specific item addition:** When user adds an item, it's added to the currently selected person's list (the person whose avatar tab is active). The frontend passes `person_id` in the request body.
- **UI feedback:** The AddItemDialog shows "Will be added to {category} for {personName}" to clarify which person will receive the item
- Drag-and-drop to move items between categories
- Filter by essentials, unpacked, delegated
- Kid mode toggle (stored in frontend state, not backend)
- Avatar system: Default emoji based on age/gender, edit icon to upload (future feature)

---

### Collaboration Features

**Components:** `DelegateDialog.tsx`, `NudgeDialog.tsx`

**Purpose:** Share items and send reminders

**Data Needed:**
- List of travelers to delegate to
- User account status for nudge recipients

**Required Backend Endpoints:**
- `POST /api/v1/trips/{trip_id}/items/delegate` - Delegate items
- `POST /api/v1/trips/{trip_id}/nudge` - Send nudge notification
- `POST /api/v1/trips/{trip_id}/share` - Generate share link

**Auth Requirement:** Yes

**Notes:**
- Nudge confirmation text depends on recipient account status:
  - Has account: "✓ Emma will be notified!"
  - No account: "✓ We'll send Emma an invite to join Alpaca!"
- Backend checks if traveler email exists in users collection

---

## 6️⃣ Configuration & ENV Vars

**Required Environment Variables:**

```bash
# Application
APP_ENV=development
PORT=8000

# Database
MONGODB_URI=mongodb+srv://product_db_user:7gMzRaDoxdE3vwgK@alpacacluster.immqteh.mongodb.net/?appName=AlpacaCluster

# Authentication
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
JWT_SECRET=your_random_secret_key_here
JWT_EXPIRES_IN=3600
REFRESH_TOKEN_EXPIRES_IN=2592000

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# External APIs
OPENAI_API_KEY=your_openai_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
WEATHER_API_KEY=your_weather_api_key

# Optional
LOG_LEVEL=INFO
```

**Configuration Notes:**
- `JWT_EXPIRES_IN` = 1 hour (3600 seconds)
- `REFRESH_TOKEN_EXPIRES_IN` = 30 days (2592000 seconds)
- CORS origins should include frontend dev server URL
- MongoDB URI provided by user (already configured)

---

## 6️⃣.1 Git Workflow Strategy

**Why Sprint-Based Branching:**
- Provides safety net for reverting entire sprints if needed
- Simpler than feature-per-task branching (less overhead)
- Maintains clean `main` branch as production-ready code
- Easy to track progress (one branch per sprint)

**Workflow:**

### Sprint 0 (Setup):
- Work directly on `main` (nothing to break yet)
- Initial commit creates the foundation

### Sprint 1+ (All Feature Sprints):
1. **Start of Sprint:** Create branch from `main`
   ```bash
   git checkout main
   git pull origin main
   git checkout -b sprint/s1-auth  # or s2-trips, s3-packing, etc.
   ```

2. **During Sprint:** Commit after each completed task
   ```bash
   git add .
   git commit -m "S1-T1: Implement Google OAuth configuration"
   git push origin sprint/s1-auth
   ```

3. **End of Sprint:** After ALL tasks pass manual tests
   ```bash
   git checkout main
   git merge sprint/s1-auth --no-ff  # Keep sprint history
   git push origin main
   git branch -d sprint/s1-auth  # Delete local branch
   git push origin --delete sprint/s1-auth  # Delete remote branch
   ```

**Branch Naming Convention:**
- `sprint/s0-setup`
- `sprint/s1-auth`
- `sprint/s2-trips`
- `sprint/s3-packing`
- `sprint/s4-collaboration`
- `sprint/s5-enhanced`

**Rollback Strategy:**
If a sprint fails or needs to be reverted:
```bash
git checkout main
git revert -m 1 <merge-commit-hash>  # Revert the entire sprint merge
git push origin main
```

**Benefits:**
- ✅ Easy to revert entire sprints without affecting other work
- ✅ Clean commit history (one merge per sprint)
- ✅ Can continue working on next sprint while previous is being tested
- ✅ Simple enough for solo developer + AI pair programming
- ✅ Scales to team collaboration later if needed

---

## 7️⃣ Background Work

**LLM Packing List Generation:**

**Trigger:** User submits trip creation form (`POST /api/v1/trips`)

**Purpose:** Generate comprehensive, personalized packing lists using OpenAI GPT-4 with expert system

**Architecture:** Per-traveler parallel generation for optimal performance (40-50% faster)

**Flow:**
1. User submits trip details (destination, dates, travelers, activities)
2. Backend validates input and fetches weather data
3. Backend calculates trip parameters (duration, laundry access, season)
4. For each traveler, backend generates focused prompt with comprehensive context
5. LLM calls executed in parallel using `asyncio.gather()`
6. Each traveler receives personalized list based on their age, needs, and trip context
7. Backend saves items to `packing_items` collection
8. Response includes trip + generated items with weather data

**Idempotency:** Not required (each trip creation is unique)

**UI Feedback:** Frontend shows loading spinner during generation (~15-25 seconds for parallel execution)

**Comprehensive System Prompt (212 lines):**

The system implements a sophisticated family travel packing expert that includes:

1. **Trip Analysis Framework:**
   - Duration calculation and outfit rotation (laundry every 3-4 days if >5 days)
   - Season/climate determination
   - Activity-specific gear identification
   - Transport-based luggage constraints
   - Traveler profile analysis

2. **Detailed Category Guidance (9 categories):**
   - Clothing, Toiletries, Health, Documents, Electronics
   - Comfort, Activities, Baby, Misc
   - Each with specific item examples and guidance

3. **Intelligent Adjustments:**
   - Weather-based (cold/hot/rainy/variable)
   - Activity-based (hiking/beach/skiing/formal)
   - Transport-based (carry-on/checked/car/international)
   - Age-based (infant/toddler/child/teen/adult)

**Enhanced User Prompt Structure:**
```
# TRIP DETAILS
Destination: Tokyo, Japan
Duration: 21 days
- Laundry Access: Assume available every 3-4 days

# TRAVELER PROFILE
Name: Sarah (Mom)
Age: 38 years old
Type: adult

# TRIP CONDITIONS
Weather Forecast:
- Average Temperature: 15°C
- Conditions: sunny, rainy, cloudy

Planned Activities: Hiking, Sightseeing, Shopping
Transportation: Walking, Train

# YOUR TASK
Generate complete, comprehensive packing list covering:
1. All 9 Categories (where applicable)
2. Smart Quantity Calculations (based on duration and laundry)
3. Age-Appropriate Items
4. Weather & Activity Adaptations
5. Essential Item Marking

Return JSON with "items" array following specified format.
```

**Key Features:**
- Comprehensive coverage across all relevant categories
- Realistic quantities based on trip duration and laundry access
- Age-appropriate items tailored to each traveler
- Weather-appropriate clothing and gear
- Activity-specific equipment
- Essential items correctly marked
- Helpful emojis and practical notes

**Error Handling:**
- Robust error handling for parallel requests
- If one traveler fails, others still succeed
- Graceful degradation with meaningful error messages
- Fallback to template list if all LLM calls fail

---

## 8️⃣ Integrations

### Google OAuth 2.0

**Purpose:** User authentication (login/signup)

**Flow:**
1. Frontend displays "Continue with Google" button
2. User clicks → Google OAuth popup
3. User authorizes → Google returns token to frontend
4. Frontend sends token to `POST /api/v1/auth/google`
5. Backend verifies token with Google
6. Backend creates/gets user in DB
7. Backend returns JWT + refresh token

**Extra ENV Vars:**
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

**Library:** `google-auth` (Python)

---

### OpenAI API (GPT-4)

**Purpose:** Generate intelligent packing lists

**Flow:**
1. User creates trip
2. Backend constructs prompt with trip details
3. Backend calls OpenAI API
4. Parse JSON response into packing items
5. Save to database

**Extra ENV Vars:**
- `OPENAI_API_KEY`

**Library:** `openai` (Python)

**Model:** `gpt-4o-mini` (cost-effective and fast)

---

### Google Maps API

**Purpose:** Destination search autocomplete

**Flow:**
1. User types in destination field
2. Frontend debounces input (300ms)
3. Frontend calls `GET /api/v1/destinations/search?query=tokyo`
4. Backend calls Google Places API
5. Returns formatted results

**Extra ENV Vars:**
- `GOOGLE_MAPS_API_KEY`

**Library:** `googlemaps` (Python)

**API:** Places API (Autocomplete)

---

### Weather API

**Purpose:** Fetch real-time weather forecasts for trip destinations

**Flow:**
1. User creates trip with destination + dates
2. Backend calls Weather API with location + date range
3. Parse forecast data (temperature, conditions, precipitation)
4. Calculate averages and generate recommendation
5. Include weather context in LLM prompt for smarter packing suggestions
6. Store weather data in trip object

**Extra ENV Vars:**
- `WEATHER_API_KEY`

**Library:** `requests` (Python) or `httpx` for async

**API:** WeatherAPI.com (recommended) or OpenWeatherMap

**Free Tier:** WeatherAPI.com offers 1M calls/month, 14-day forecast

---

## 9️⃣ Testing Strategy (Manual via Frontend)

**Validation Approach:**
- All testing done through frontend UI
- Every task includes Manual Test Step + User Test Prompt
- After all tasks in sprint pass → commit and push to `main`
- If any fail → fix and retest before pushing

**Test Data:**
- Use real Google account for OAuth testing
- Create test trips with various scenarios (different ages, destinations, activities)
- Test edge cases (single traveler, infant, long trips, etc.)

**No Automated Tests:**
- No unit tests, integration tests, or E2E tests required
- Focus on manual validation through UI

---

## 🔟 Dynamic Sprint Plan & Backlog

---

## 🧱 S0 – Environment Setup & Frontend Connection

**Objectives:**
- Create FastAPI skeleton with `/api/v1` base path
- Connect to MongoDB Atlas using provided connection string
- Implement `/healthz` endpoint with DB ping
- Enable CORS for frontend
- Initialize Git repo with single `main` branch
- Create `.gitignore` file at root
- Push initial code to GitHub

**User Stories:**
- As a developer, I can run the backend locally and see it connect to MongoDB
- As a developer, I can call `/healthz` and verify database connection
- As a frontend developer, I can make API calls without CORS errors

**Tasks:**

### Task 1: Create FastAPI Project Structure
- Create `main.py` with FastAPI app
- Create `app/` directory structure:
  - `app/api/v1/` - API routes
  - `app/core/` - Config, security
  - `app/db/` - Database connection
  - `app/models/` - Pydantic models
  - `app/services/` - Business logic
- Create `requirements.txt` with dependencies:
  - `fastapi`
  - `uvicorn[standard]`
  - `motor` (async MongoDB driver)
  - `pydantic>=2.0`
  - `python-dotenv`
  - `python-jose[cryptography]`
  - `google-auth`
  - `openai`
  - `googlemaps`
- Create `.env.example` with all required variables

**Manual Test Step:**
- Run `uvicorn main:app --reload` → Server starts on port 8000

**User Test Prompt:**
> "Start the backend with `uvicorn main:app --reload`. Confirm it runs without errors and shows 'Application startup complete' in terminal."

---

### Task 2: Configure MongoDB Atlas Connection
- Create `app/db/mongodb.py` with Motor client
- Use connection string: `mongodb+srv://product_db_user:7gMzRaDoxdE3vwgK@alpacacluster.immqteh.mongodb.net/?appName=AlpacaCluster`
- Implement connection pooling
- Add connection error handling
- Create database: `alpaca_db`
- Create collections: `users`, `trips`, `packing_items`, `refresh_tokens`

**Manual Test Step:**
- Backend logs show "Connected to MongoDB Atlas" on startup

**User Test Prompt:**
> "Start the backend. Check terminal logs for 'Connected to MongoDB Atlas' message. If you see connection errors, verify the MongoDB URI in `.env`."

---

### Task 3: Implement Health Check Endpoint
- Create `GET /healthz` endpoint
- Ping MongoDB to verify connection
- Return JSON with status, database state, timestamp
- Handle database connection failures gracefully

**Manual Test Step:**
- Open browser → `http://localhost:8000/healthz` → See `{"status": "healthy", "database": "connected"}`

**User Test Prompt:**
> "Open your browser and go to `http://localhost:8000/healthz`. You should see a JSON response showing healthy status and database connected."

---

### Task 4: Enable CORS for Frontend
- Install `fastapi.middleware.cors`
- Configure CORS middleware
- Allow origins from `.env` (`CORS_ORIGINS`)
- Allow credentials, all methods, all headers

**Manual Test Step:**
- Start frontend dev server
- Open browser console → Make fetch request to `/healthz` → No CORS errors

**User Test Prompt:**
> "Start both backend and frontend. Open browser DevTools → Console. Run: `fetch('http://localhost:8000/healthz').then(r => r.json()).then(console.log)`. You should see the health check response without CORS errors."

---

### Task 5: Initialize Git Repository
- Run `git init` at project root
- Create `.gitignore` with:
  - `__pycache__/`
  - `*.pyc`
  - `.env`
  - `.venv/`
  - `venv/`
  - `.DS_Store`
  - `*.log`
- Set default branch to `main`: `git branch -M main`
- Create initial commit
- Create GitHub repo and push

**Manual Test Step:**
- Run `git log` → See initial commit
- Check GitHub → Repo exists with code

**User Test Prompt:**
> "Run `git log` in terminal. You should see your initial commit. Then check GitHub to confirm the repository exists with your code."

---

**Definition of Done:**
- Backend runs locally on port 8000
- MongoDB Atlas connection successful
- `/healthz` endpoint returns 200 OK with DB status
- Frontend can call backend without CORS errors
- Git repo initialized with `main` branch
- Code pushed to GitHub

**Post-Sprint:**
- Work done directly on `main` (Sprint 0 only - nothing to break yet)
- Commit all changes: `git commit -m "S0: Complete environment setup and MongoDB connection"`
- Push to `main`: `git push origin main`
- **Note:** Starting with Sprint 1, we'll use sprint branches (see Git Workflow section)

---

## 🧩 S1 – Google OAuth Authentication

**Objectives:**
- Implement Google OAuth 2.0 authentication
- Create JWT token generation and validation
- Build auth endpoints (login, logout, refresh, me)
- Store users in MongoDB
- Protect routes with JWT middleware

**User Stories:**
- As a user, I can click "Continue with Google" and authenticate
- As a user, I receive a JWT token after successful login
- As a user, I can refresh my expired token
- As a user, I can logout and invalidate my session

**Tasks:**

### Task 1: Set Up Google OAuth Configuration
- Install `google-auth` library
- Create `app/core/security.py` for auth utilities
- Add Google OAuth verification function
- Configure Google Client ID and Secret from `.env`
- Create function to verify Google token

**Manual Test Step:**
- Call verification function with test Google token → Returns user info

**User Test Prompt:**
> "Get a Google OAuth token from the Google OAuth Playground. Test the verification function returns your email and name."

---

### Task 2: Implement JWT Token Generation
- Install `python-jose[cryptography]`
- Create JWT encoding/decoding functions in `app/core/security.py`
- Generate access tokens (1 hour expiry)
- Generate refresh tokens (30 day expiry)
- Add token validation middleware

**Manual Test Step:**
- Create test user in MongoDB → Retrieve by email → Verify data matches

**User Test Prompt:**
> "Use MongoDB Compass or CLI to insert a test user. Then use the backend to retrieve it by email. Verify all fields match."

---

### Task 4: Build POST /api/v1/auth/google Endpoint
- Create `app/api/v1/auth.py` router
- Implement Google OAuth login endpoint
- Verify Google token
- Create or get user from database
- Generate JWT access + refresh tokens
- Store refresh token in database
- Return tokens + user info

**Manual Test Step:**
- Frontend sends Google token → Backend returns JWT + user data

**User Test Prompt:**
> "In the frontend, click 'Continue with Google'. After authorizing, check the Network tab. You should see a response with access_token, refresh_token, and your user info."

---

### Task 5: Build Token Refresh and Logout Endpoints
- Implement `POST /api/v1/auth/refresh` endpoint
- Implement `POST /api/v1/auth/logout` endpoint
- Implement `GET /api/v1/auth/me` endpoint
- Create JWT authentication dependency for protected routes
- Add token validation middleware

**Manual Test Step:**
- Login → Get tokens → Refresh token → Verify new access token works
- Logout → Verify refresh token invalidated

**User Test Prompt:**
> "After logging in, wait for access token to expire (or manually expire it). Use the refresh token to get a new access token. Then logout and verify the refresh token no longer works."

---

**Definition of Done:**
- Google OAuth login works end-to-end
- JWT tokens generated and validated correctly
- Users stored in MongoDB with proper indexes
- Token refresh mechanism functional
- Logout invalidates refresh tokens
- Protected routes require valid JWT

**Post-Sprint:**
- Test full auth flow via frontend
- Merge sprint branch to `main`:
  ```bash
  git checkout main
  git merge sprint/s1-auth --no-ff
  git push origin main
  git branch -d sprint/s1-auth
  ```

---

## 🧩 S2 – Trip Creation with LLM Integration

**Objectives:**
- Implement trip creation endpoint
- Integrate OpenAI GPT-4 for packing list generation
- Store trips and packing items in MongoDB
- Implement localStorage → DB migration endpoint
- Add trip retrieval endpoints

**User Stories:**
- As a user, I can create a trip with destination, dates, and travelers
- As a user, I receive an AI-generated packing list based on my trip details
- As a user, I can migrate my localStorage trip to my account after logging in
- As a user, I can view all my saved trips

**Tasks:**

### Task 1: Create Trip and Packing Item Models
- Create `app/models/trip.py` with Pydantic models
- Create `app/models/packing_item.py` with Pydantic models
- Define validation rules (dates, travelers, categories)
- Create request/response schemas

**Manual Test Step:**
- Validate test trip data against Pydantic models → No validation errors

**User Test Prompt:**
> "Create a test trip object in Python and validate it against the Trip model. Verify all required fields are enforced."

---

### Task 2: Implement Weather API Integration
- Create `app/services/weather_service.py`
- Integrate WeatherAPI.com (or OpenWeatherMap)
- Fetch 14-day forecast for destination
- Calculate average temperature for trip dates
- Determine predominant conditions (sunny, rainy, etc.)
- Generate weather recommendation text
- Handle API failures (use historical averages as fallback)
- Cache weather data to reduce API calls

**Manual Test Step:**
- Call weather service with "Tokyo" + March dates → Receive forecast with avg temp ~15°C, rainy conditions

**User Test Prompt:**
> "Use Python REPL to call the weather service with Tokyo and March 28 - April 18 dates. Verify it returns temperature averages and conditions like 'rainy' or 'sunny'."

---

### Task 3: Implement Comprehensive LLM Integration (Weather-Aware Expert System)
- Create `app/services/llm_service.py`
- Implement comprehensive 212-line system prompt (`_get_single_traveler_system_prompt()`)
- Implement enhanced user prompt builder (`_build_single_traveler_prompt()`)
- Design per-traveler parallel generation architecture using `asyncio.gather()`
- Include detailed trip analysis framework:
  - Duration and laundry access calculations
  - Season/climate determination
  - Activity-specific gear identification
  - Transport-based constraints
  - Age-specific guidance (infant/toddler/child/teen/adult)
- Implement detailed category guidance for all 9 categories
- Add intelligent adjustments for weather, activities, transport, and age
- Parse LLM JSON response into packing items with robust error handling
- Add fallback to template list if LLM fails
- Test with various trip scenarios (different ages, destinations, durations)

**System Prompt Features:**
- Comprehensive family travel packing expert role definition
- Trip analysis framework (duration, laundry, season, activities, transport)
- Detailed guidance for 9 categories with specific item examples
- Intelligent weather/activity/transport/age-based adjustments
- Quality standards and output format specifications
- Example output structure with proper JSON format

**User Prompt Enhancements:**
- Comprehensive trip details with laundry access calculations
- Detailed traveler profile with age-specific guidance
- Weather forecast with temperature and conditions
- Planned activities and transportation methods
- Clear task breakdown covering all 9 categories
- Smart quantity calculation instructions
- Age-appropriate item requirements
- Weather and activity adaptation guidelines
- Essential item marking criteria

**Manual Test Step:**
- Call LLM service with test trip + weather data → Receive comprehensive categorized packing items with:
  - Weather-appropriate suggestions (rain gear for rainy weather, layers for variable conditions)
  - Age-appropriate items (baby items for infants, comfort items for children)
  - Activity-specific gear (hiking boots, ski equipment, beach items)
  - Realistic quantities based on duration and laundry access
  - Properly marked essential items

**User Test Prompt:**
> "Use Python REPL to call the LLM service with a test trip (Tokyo, 21 days, 2 adults, 1 child age 10, hiking/sightseeing, rainy weather, 15°C). Verify it returns a comprehensive packing list with:
> - Rain jackets and umbrellas for rainy conditions
> - Layers for variable spring weather
> - Age-appropriate items for the 10-year-old (kid-friendly toiletries, entertainment)
> - Hiking gear in 'activities' category
> - Realistic clothing quantities (4-5 outfits with laundry access noted)
> - Essential items properly marked (passports, medications, chargers)
> - Items across all relevant categories (clothing, toiletries, health, documents, electronics, comfort, activities, misc)"

---

### Task 4: Build POST /api/v1/trips Endpoint
- Create `app/api/v1/trips.py` router
- Implement trip creation endpoint
- **Validate required fields:**
  - Destination (at least 1)
  - Start date and end date (end must be after start)
  - All travelers must have name, age, and type
  - For children: age is REQUIRED
- Call weather service to get forecast
- Call LLM service with trip details + weather data
- Save trip to MongoDB (including weather data)
- Save packing items to MongoDB
- Return complete trip with items and weather
- Add proper error handling with clear messages

**Manual Test Step:**
- Frontend submits trip form → Backend fetches weather → Generates packing list → Returns full data with weather card

**User Test Prompt:**
> "In the frontend, fill out the trip creation form with all required fields (destination, dates, traveler names and ages). Submit and watch the Network tab. You should see a POST to /api/v1/trips that returns your trip with weather data and an AI-generated packing list (takes 5-8 seconds due to weather + LLM calls)."

---

### Task 5: Build Trip Migration Endpoint
- Implement `POST /api/v1/trips/migrate` endpoint
- Accept localStorage trip data
- Validate and sanitize data
- Associate trip with authenticated user
- Save to database
- Return trip ID

**Manual Test Step:**
- Create trip in localStorage → Login → Migrate trip → Verify trip now in database

**User Test Prompt:**
> "Create a trip without logging in (it saves to localStorage). Then login with Google. The app should automatically migrate your trip. Check the Network tab for a POST to /api/v1/trips/migrate."

---

### Task 6: Build Trip Retrieval Endpoints
- Implement `GET /api/v1/trips` (list all user trips)
- Implement `GET /api/v1/trips/{trip_id}` (get single trip)
- Implement `PATCH /api/v1/trips/{trip_id}` (update trip)
- Implement `DELETE /api/v1/trips/{trip_id}` (delete trip)
- Add authorization checks (user must own trip)

**Manual Test Step:**
- Create multiple trips → List trips → Get single trip → Update trip → Delete trip

**User Test Prompt:**
> "After creating a few trips, refresh the dashboard. You should see all your trips listed. Click on one to view details. Try editing the trip title and verify it saves."

---

**Definition of Done:**
- Weather API integration works and returns accurate forecasts
- Trip creation works with weather-aware LLM-generated packing lists
- Required field validation enforced (destination, dates, traveler names/ages)
- localStorage trips can be migrated to user accounts
- All trip CRUD operations functional
- Proper authorization on trip endpoints
- LLM integration handles errors gracefully
- Weather data displayed in trip summary

**Post-Sprint:**
- Test trip creation with various scenarios (different destinations, seasons, traveler ages)
- Verify LLM generates weather-appropriate lists (rain gear for rainy destinations, etc.)
- Verify child ages produce age-appropriate items
- Merge sprint branch to `main`:
  ```bash
  git checkout main
  git merge sprint/s2-trips --no-ff
  git push origin main
  ```

---

## 🧩 S3 – Packing List Management

**Objectives:**
- Implement packing item CRUD operations
- Add item check/uncheck functionality
- Implement category management
- Add item delegation between travelers
- Build filtering and sorting

**User Stories:**
- As a user, I can add custom items to my packing list
- As a user, I can check off items as I pack them
- As a user, I can edit item details (quantity, category, notes)
- As a user, I can delete items I don't need
- As a user, I can move items between categories
- As a user, I can delegate items to other travelers

**Tasks:**

### Task 1: Build Packing Item CRUD Endpoints
- Implement `POST /api/v1/trips/{trip_id}/items` (create item)
  - **CRITICAL:** `person_id` is REQUIRED in request body
  - Validate `person_id` exists in trip's travelers array
  - Item is added ONLY to the specified person's packing list
  - Frontend automatically sets `person_id` to the currently selected person (active avatar tab)
- Implement `PATCH /api/v1/trips/{trip_id}/items/{item_id}` (update item)
- Implement `DELETE /api/v1/trips/{trip_id}/items/{item_id}` (delete item)
- Validate category is valid enum value

**Manual Test Step:**
- Select Mom's tab → Add item → Item appears in Mom's list only
- Select Dad's tab → Add item → Item appears in Dad's list only
- Verify items don't appear in other people's lists
- Edit item → Changes saved
- Delete item → Item removed

**User Test Prompt:**
> "Click on Mom's avatar tab to view her packing list. Click 'Add Item' and notice the text says 'Will be added to {category} for Mom'. Add the item and verify it appears only in Mom's list. Then switch to Dad's tab and add an item there - it should only appear in Dad's list."

---

### Task 2: Implement Item Check/Uncheck
- Update PATCH endpoint to handle `is_packed` toggle
- Update `is_essential` toggle
- Calculate packing progress on frontend
- Optimize for frequent updates

**Manual Test Step:**
- Check item → Item marked as packed
- Uncheck item → Item marked as unpacked
- Progress bar updates correctly

**User Test Prompt:**
> "Click the checkbox next to a packing item. It should immediately show as checked. The progress bar at the top should update. Uncheck it and verify the progress decreases."

---

### Task 3: Build Item Delegation Endpoint
- Implement `POST /api/v1/trips/{trip_id}/items/delegate`
- Accept list of item IDs and target person
- Update items with delegation info (from, to, timestamp)
- Return updated items

**Manual Test Step:**
- Select items → Delegate to another person → Items move to their list with delegation badge

**User Test Prompt:**
> "In Mom's packing list, click the delegate icon on a category. Choose Dad as the recipient. The items should disappear from Mom's list with a swoosh animation and appear in Dad's list with a 'Delegated from Mom' badge."

---

### Task 4: Build Category Management Endpoint
- Implement `POST /api/v1/trips/{trip_id}/items/move-category`
- Validate new category is valid
- Update item category
- Support drag-and-drop category changes

**Manual Test Step:**
- Drag item to different category → Item moves and saves

**User Test Prompt:**
> "Drag a packing item from 'Clothing' to 'Electronics'. The item should move to the new category. Refresh the page to verify the change persisted."

---

### Task 5: Add Filtering and Sorting
- Items already filtered on frontend
- Ensure backend returns all necessary data
- Optimize queries for large packing lists
- Add indexes on frequently queried fields

**Manual Test Step:**
- Filter by essentials → Only essential items shown
- Filter by unpacked → Only unpacked items shown
- Filter by delegated → Only delegated items shown

**User Test Prompt:**
> "Click the filter icon and select 'Essentials Only'. You should only see items marked as essential. Clear the filter and try 'Unpacked Only' and 'Delegated Only'."

---

**Definition of Done:**
- All packing item CRUD operations work
- Check/uncheck updates immediately
- Delegation works with proper attribution
- Category changes persist
- Filters work correctly

**Post-Sprint:**
- Test with large packing lists (50+ items)
- Verify performance is acceptable
- Merge sprint branch to `main`:
  ```bash
  git checkout main
  git merge sprint/s3-packing --no-ff
  git push origin main
  ```

---

## 🧩 S4 – Collaboration Features

**Objectives:**
- Implement nudge notifications
- Build trip sharing functionality
- Add email notifications (optional for V1)
- Check user account status for nudges

**User Stories:**
- As a user, I can nudge family members to pack their items
- As a user, I can share my trip with others via link
- As a user, I receive appropriate feedback based on recipient account status

**Tasks:**

### Task 1: Build Nudge Endpoint
- Implement `POST /api/v1/trips/{trip_id}/nudge`
- Accept person_id and optional message
- Check if person has Alpaca account (by email/name matching)
- Return appropriate confirmation message
- Log nudge in database (optional)

**Manual Test Step:**
- Nudge person with account → "Emma will be notified!"
- Nudge person without account → "We'll send Emma an invite!"

**User Test Prompt:**
> "Click the nudge icon next to a traveler's name. If they have an Alpaca account, you should see 'Emma will be notified!'. If not, you should see 'We'll send Emma an invite to join Alpaca!'."

---

### Task 2: Build Trip Sharing Endpoint
- Implement `POST /api/v1/trips/{trip_id}/share`
- Generate unique shareable token
- Create share link with token
- Set expiration (30 days default)
- Store share token in database
- Return shareable URL

**Manual Test Step:**
- Generate share link → Copy link → Open in incognito → Can view trip

**User Test Prompt:**
> "Click the share button and generate a share link. Copy the link and open it in an incognito window. You should be able to view (and optionally edit) the trip without logging in."

---

### Task 3: Implement Share Token Validation
- Create middleware to validate share tokens
- Allow access to trip if valid token provided
- Check token expiration
- Support both authenticated and anonymous access

**Manual Test Step:**
- Access trip with valid token → Success
- Access trip with expired token → Error
- Access trip with invalid token → Error

**User Test Prompt:**
> "Use a share link to access a trip. Verify you can view it. Then manually modify the token in the URL and verify you get an error."

---

### Task 4: Add Email Notification Service (Optional)
- Create `app/services/email_service.py`
- Integrate with email provider (SendGrid, AWS SES, etc.)
- Send nudge emails to users with accounts
- Send invite emails to users without accounts
- Add email templates

**Manual Test Step:**
- Nudge user → Email received with trip details

**User Test Prompt:**
> "Nudge a family member. Check their email inbox for a notification from Alpaca with a link to the trip."

**Note:** This task is optional for V1. Can be implemented in future sprint if time allows.

---

**Definition of Done:**
- Nudge functionality works with account status detection
- Trip sharing generates valid shareable links
- Share tokens validated correctly
- Email notifications sent (if implemented)

**Post-Sprint:**
- Test sharing with multiple users
- Verify nudges show correct messages
- Merge sprint branch to `main`:
  ```bash
  git checkout main
  git merge sprint/s4-collaboration --no-ff
  git push origin main
  ```

---

## 🧩 S5 – Enhanced Features

**Objectives:**
- Integrate Google Maps API for destination search
- Implement avatar emoji defaults
- Add weather data fetching (optional)
- Performance optimizations

**User Stories:**
- As a user, I can search for destinations with autocomplete
- As a user, I see appropriate emoji avatars based on traveler age/type
- As a user, I see weather recommendations for my destination

**Tasks:**

### Task 1: Implement Google Maps Destination Search
- Create `app/services/maps_service.py`
- Implement `GET /api/v1/destinations/search` endpoint
- Call Google Places API Autocomplete
- Format results for frontend
- Add caching for common searches (optional)

**Manual Test Step:**
- Type "tok" in destination field → See "Tokyo, Japan" suggestion

**User Test Prompt:**
> "In the trip creation form, start typing a destination like 'tok'. You should see autocomplete suggestions including 'Tokyo, Japan'. Select one and verify it fills the field."

---

### Task 2: Implement Avatar Emoji Logic
- Create `app/services/avatar_service.py`
- Implement function to assign emoji based on age/gender/type
- Rules:
  - Adult woman: 👩
  - Adult man: 👨
  - Infant (<1): 👶
  - Young child (2-6): 👧 or 👦
  - Older child (7-11): 👧 or 👦
  - Teenager (12+): 👩 or 👨
- Apply during trip creation
- Store in traveler object

**Manual Test Step:**
- Create trip with various ages → Verify appropriate emojis assigned

**User Test Prompt:**
> "Create a trip with travelers of different ages (infant, child, teenager, adult). Check the dashboard and verify each has an appropriate emoji avatar."

---

### Task 3: Add Weather Data Fetching (REQUIRED)
- Integrate weather API (OpenWeatherMap or WeatherAPI.com)
- Create `app/services/weather_service.py`
- Fetch weather forecast for destination + date range
- Calculate average temperature (convert to C/F based on user preference)
- Determine conditions (sunny, rainy, cloudy, snowy, mixed)
- Generate weather-aware recommendation for LLM prompt
- Store weather data in trip object
- Handle API failures gracefully (use historical averages as fallback)

**API Recommendation:** Use WeatherAPI.com (free tier: 1M calls/month, 14-day forecast)

**Manual Test Step:**
- Create trip for Tokyo in March → See weather recommendation about cherry blossoms and rain
- Create trip for Alaska in December → See cold weather gear recommendations

**User Test Prompt:**
> "Create a trip to Tokyo in March. After the packing list is generated, you should see a weather card mentioning cherry blossom season, temperatures around 15°C (59°F), and rain gear recommendations. The packing list should include rain jackets and layers."

**Note:** Weather data is CORE to the value proposition - it makes packing lists contextually intelligent. This is NOT optional.

---

### Task 4: Performance Optimizations
- Add database indexes on frequently queried fields
- Implement query result caching (Redis optional)
- Optimize LLM prompts for faster responses
- Add request/response compression
- Monitor and log slow queries

**Manual Test Step:**
- Create trip with 50+ items → Response time < 5 seconds
- Load dashboard with 10 trips → Response time < 2 seconds

**User Test Prompt:**
> "Create several trips with many items. Navigate between them and verify the app feels responsive. Check the Network tab to ensure API responses are fast (<2 seconds for most requests)."

---

### Task 5: Error Handling and Logging
- Implement comprehensive error handling
- Add structured logging
- Log all API requests
- Log LLM failures with fallback
- Add error monitoring (Sentry optional)

**Manual Test Step:**
- Trigger various errors → Verify appropriate error messages shown
- Check logs → Verify errors logged with context

**User Test Prompt:**
> "Try to create a trip with invalid data (e.g., end date before start date). You should see a clear error message. Check the backend logs to verify the error was logged."

---

**Definition of Done:**
- Google Maps autocomplete works smoothly
- Avatar emojis assigned correctly
- Weather data displayed (if implemented)
- App performance is acceptable
- Errors handled gracefully with logging

**Post-Sprint:**
- Performance test with realistic data volumes
- Review logs for any issues
- Merge sprint branch to `main`:
  ```bash
  git checkout main
  git merge sprint/s5-enhanced --no-ff
  git push origin main
  ```

---

## ✅ Final Checklist

Before considering the backend complete, verify:

- [ ] All endpoints documented in API Design section are implemented
- [ ] MongoDB Atlas connection stable and performant
- [ ] Google OAuth login works end-to-end
- [ ] LLM generates reasonable packing lists
- [ ] All CRUD operations functional
- [ ] Delegation and collaboration features work
- [ ] Google Maps autocomplete functional
- [ ] Error handling comprehensive
- [ ] All manual tests pass
- [ ] Code pushed to GitHub `main` branch
- [ ] Frontend successfully integrates with all endpoints
- [ ] No CORS errors
- [ ] Performance acceptable (<5s for LLM, <2s for other requests)

---

## 🚀 Next Steps After V1

**Future Enhancements (Not in Scope for Initial Backend):**
- Avatar image uploads (file storage + CDN)
- Email notifications for nudges
- Real-time collaboration (WebSockets)
- Template library (save/reuse packing lists)
- Multi-trip planning
- Packing list analytics
- Mobile app API support
- Social features (share trips publicly)
- Premium features (unlimited trips, advanced AI)

**Technical Debt to Address:**
- Add automated tests (unit, integration, E2E)
- Implement proper caching layer (Redis)
- Add rate limiting
- Implement database migrations
- Add API versioning strategy
- Set up CI/CD pipeline
- Add monitoring and alerting
- Implement backup strategy

---

## 📚 Resources

**Documentation:**
- FastAPI: https://fastapi.tiangolo.com/
- Motor (MongoDB): https://motor.readthedocs.io/
- Pydantic V2: https://docs.pydantic.dev/
- Google OAuth: https://developers.google.com/identity/protocols/oauth2
- OpenAI API: https://platform.openai.com/docs/
- Google Maps API: https://developers.google.com/maps/documentation/

**Development Tools:**
- MongoDB Compass (GUI for MongoDB)
- Postman (API testing)
- Google OAuth Playground (token testing)

---

**END OF BACKEND DEVELOPMENT PLAN**

This plan provides a complete roadmap for building the Alpaca backend. Each sprint builds on the previous one, with clear tasks, manual testing steps, and user-facing test prompts. The architecture supports the "try before you sign up" flow while being future-proof for additional features.
- Generate test JWT → Decode it → Verify payload matches

**User Test Prompt:**
> "Use Python REPL to generate a JWT token and decode it. Verify the payload contains user_id and expiration time."

---

### Task 3: Create User Model and Database Operations
- Create `app/models/user.py` with Pydantic models
- Create `app/db/users.py` with CRUD operations:
  - `get_user_by_email()`
  - `get_user_by_google_id()`
  - `create_user()`
  - `update_user()`
- Add indexes on `email` and `google_id` fields

