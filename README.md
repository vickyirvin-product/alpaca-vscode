# Alpaca For You 🦙

Alpaca For You is an intelligent packing list assistant that helps families prepare for trips. It uses AI to generate personalized packing lists based on destination weather, duration, and traveler needs.

## 🚀 Local Development

To run the application locally, you need to start both the backend (FastAPI) and frontend (React/Vite) servers.

### Prerequisites

*   Node.js & npm
*   Python 3.8+
*   MongoDB (running locally or accessible URI)
*   Google OAuth Credentials (configured in `backend/.env`)

### 1. Start the Backend

The backend runs on port `8000`.

```bash
cd backend
# Create virtual environment (if not exists)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Verify backend is running: [http://localhost:8000/healthz](http://localhost:8000/healthz)

### 2. Start the Frontend

The frontend runs on port `5173` (or `8080` depending on availability).

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Access the app: [http://localhost:5173](http://localhost:5173)

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

This project is configured for deployment on Lovable/Vercel (Frontend) and a Python-capable host (Backend).
