# Alpaca

Alpaca is an intelligent packing list assistant that helps families prepare for trips. It uses a comprehensive AI-powered family travel packing expert system to generate personalized, context-aware packing lists based on destination weather, trip duration, activities, transportation, and individual traveler needs.

## AI-Powered Packing Lists

**Comprehensive Expert System:**
- **212-line system prompt** implementing sophisticated family travel packing expertise
- **Per-traveler parallel generation** for optimal performance (15-25 seconds)
- **9 category coverage**: Clothing, Toiletries, Health, Documents, Electronics, Comfort, Activities, Baby, Misc
- **Intelligent adjustments** based on weather, activities, transport, and traveler age
- **Smart quantities** calculated from trip duration and laundry access
- **Age-appropriate recommendations** for infants, toddlers, children, teens, and adults

## 🚀 Quick Start

**New to the project?** Start here:
- 📖 **[Quick Start Guide](QUICK_START.md)** - Get up and running in minutes
- 📚 **[Complete Setup Guide](LOCAL_SETUP_GUIDE.md)** - Detailed setup instructions with troubleshooting

### TL;DR - Start Development

**Option 1: Automated (Recommended)**
```bash
./start-dev.sh
```

**Option 2: Manual**
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Prerequisites

*   Node.js 18+ & npm
*   Python 3.9+
*   MongoDB Atlas account (already configured)
*   API Keys (see [Quick Start Guide](QUICK_START.md)):
    - Google OAuth credentials
    - OpenAI API key
    - WeatherAPI.com key
    - Google Maps API key

## 🧪 Testing & Documentation

We have comprehensive documentation for the integrated application:

*   **[Testing Guide](TESTING_GUIDE.md)**: Step-by-step instructions for testing authentication, trip creation, and packing features.
*   **[Integration Summary](INTEGRATION_COMPLETE.md)**: Overview of the full-stack architecture and completed features.
*   **[API Setup](API_SETUP.md)**: Details on API configuration and endpoints.

### Key Features to Test

1.  **Authentication**: Sign in with Google.
2.  **Trip Creation**: Use the wizard to generate a trip with AI.
3.  **Packing Lists**: Add, edit, delete, and toggle items.
4.  **Collaboration**: Use the "Nudge" feature to remind others.

## 🔧 Troubleshooting

### Common Issues

**1. "Sign in with Google" doesn't work**
*   **Cause**: Incorrect OAuth credentials or redirect URI.
*   **Fix**: Check `backend/.env`. Ensure Redirect URI in Google Cloud Console matches `http://localhost:8000/auth/callback/google`.

**2. "Failed to fetch" errors**
*   **Cause**: Backend server is not running or CORS issue.
*   **Fix**: Ensure backend is active on port 8000. Check terminal logs for errors.

**3. Packing list changes aren't saving**
*   **Cause**: Network connectivity or token expiration.
*   **Fix**: Check browser console. Try refreshing the page to renew the token.

**4. MongoDB Connection Error**
*   **Cause**: Database service not running.
*   **Fix**: Start MongoDB locally (`brew services start mongodb-community` on macOS) or check connection string.

## 📁 Project Structure

*   `/src`: React Frontend code
*   `/backend`: FastAPI Backend code
    *   `/routes`: API endpoints
    *   `/services`: Business logic (LLM, Weather, Email)
    *   `/models`: Database schemas

## Deployment

This project is configured for deployment on Ember.new (Frontend) and a Python-capable host (Backend).
