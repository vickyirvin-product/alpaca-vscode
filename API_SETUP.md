# API Configuration Setup

## Overview
This document describes the API configuration between the frontend and backend services.

## Backend Server
- **URL**: `http://localhost:8000`
- **Status**: ✅ Running (Terminal 5)
- **Framework**: FastAPI with Uvicorn
- **Location**: `/Users/vickyirvin/Apps/alpacaforyou/backend`

### Available Endpoints
- `GET /` - Root endpoint (Welcome message)
- `GET /healthz` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)
- `/auth/*` - Authentication endpoints
- `/trips/*` - Trip management endpoints
- `/packing/*` - Packing list endpoints
- `/collaboration/*` - Collaboration endpoints
- `/maps/*` - Maps and location endpoints

### CORS Configuration
The backend is configured to accept requests from:
- `http://localhost:5173` (Vite default)
- `http://localhost:8080` (Current frontend dev server)
- `http://localhost:3000` (Common React dev port)

## Frontend Configuration

### Environment Variables
Created `.env.local` file with:
```
VITE_API_BASE_URL=http://localhost:8000
```

### API Client
Created `src/lib/api.ts` with:
- Centralized API client using native `fetch`
- Automatic error handling
- Cookie-based authentication support
- TypeScript support
- Methods: `get`, `post`, `put`, `patch`, `delete`

### Usage Example
```typescript
import { api, checkHealth } from '@/lib/api';

// Health check
const health = await checkHealth();

// GET request
const trips = await api.get('/trips');

// POST request
const newTrip = await api.post('/trips', {
  name: 'Summer Vacation',
  destination: 'Hawaii'
});
```

## Development Workflow

### Starting the Backend
The backend is already running in Terminal 5:
```bash
cd backend && ./venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Starting the Frontend
```bash
npm run dev
# or
bun run dev
```
Frontend will run on `http://localhost:8080`

### Testing the Connection
1. Backend health check: `http://localhost:8000/healthz`
2. API documentation: `http://localhost:8000/docs`
3. Frontend can import and use the API client from `@/lib/api`

## Next Steps
1. Start the frontend dev server: `npm run dev` or `bun run dev`
2. Test API connectivity using the `checkHealth()` function
3. Implement specific API calls for authentication, trips, packing lists, etc.
4. Handle authentication tokens and user sessions

## Notes
- The `.env.local` file is git-ignored (already in `.gitignore` as `*.local`)
- All API keys are configured in `backend/.env`
- MongoDB connection is active and working
- CORS is properly configured for local development