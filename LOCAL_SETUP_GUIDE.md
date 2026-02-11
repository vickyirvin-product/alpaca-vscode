# Local Development Setup Guide

This guide will help you set up and run the Alpaca application on your local machine.

## Prerequisites

- **Python 3.9+** installed
- **Node.js 18+** and npm installed
- **MongoDB Atlas account** (already configured in your backend)
- API keys for external services (see below)

## Step 1: Get Required API Keys

You'll need to obtain the following API keys:

### 1.1 Google OAuth Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Set application type to "Web application"
6. Add authorized redirect URI: `http://localhost:8000/auth/callback/google`
7. Copy the Client ID and Client Secret

### 1.2 OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key (starts with `sk-`)

### 1.3 Weather API Key
1. Go to [WeatherAPI.com](https://www.weatherapi.com/signup.aspx)
2. Sign up for a free account
3. Copy your API key from the dashboard

### 1.4 Google Maps API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/google/maps-apis)
2. Enable the following APIs:
   - Maps JavaScript API
   - Places API
   - Geocoding API
3. Create an API key
4. Copy the key

### 1.5 Generate JWT Secret Key
Run this command in your terminal:
```bash
openssl rand -hex 32
```
Copy the output - this will be your JWT_SECRET_KEY

## Step 2: Configure Backend Environment

1. Open `backend/.env` file (already created)
2. Replace the placeholder values with your actual API keys:
   - `GOOGLE_CLIENT_ID` - Your Google OAuth Client ID
   - `GOOGLE_CLIENT_SECRET` - Your Google OAuth Client Secret
   - `JWT_SECRET_KEY` - The key you generated with openssl
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `WEATHER_API_KEY` - Your WeatherAPI.com key
   - `GOOGLE_MAPS_API_KEY` - Your Google Maps API key

**Note:** MongoDB is already configured to use your Atlas cluster, so you don't need to change `MONGO_URI`.

## Step 3: Install Backend Dependencies

Open a terminal and run:

```bash
cd backend
pip install -r requirements.txt
```

Or if you prefer using a virtual environment (recommended):

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 4: Install Frontend Dependencies

Open a new terminal (keep the backend terminal open) and run:

```bash
npm install
```

## Step 5: Start the Backend Server

In the backend terminal:

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Test the backend:** Open http://localhost:8000 in your browser. You should see:
```json
{
  "message": "Welcome to Alpaca API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

## Step 6: Start the Frontend Development Server

In the frontend terminal:

```bash
npm run dev
```

You should see output like:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:8080/
➜  Network: use --host to expose
```

**Access the app:** Open http://localhost:8080 in your browser

## Step 7: Test the Connection

### 7.1 Health Check
1. Open http://localhost:8000/healthz in your browser
2. You should see: `{"status":"ok"}`

### 7.2 API Documentation
1. Open http://localhost:8000/docs in your browser
2. You should see the FastAPI interactive documentation (Swagger UI)
3. This is useful for testing API endpoints directly

### 7.3 Frontend Connection
1. Open http://localhost:8080 in your browser
2. The app should load without errors
3. Check the browser console (F12) for any connection errors

## Step 8: Test Authentication Flow

1. Click "Login with Google" on the frontend
2. You should be redirected to Google's login page
3. After logging in, you should be redirected back to the app
4. You should see your user profile/dashboard

## Common Issues and Solutions

### Issue: Backend won't start
**Solution:** Make sure all required environment variables are set in `backend/.env`

### Issue: "Module not found" errors
**Solution:** 
- Backend: Make sure you're in the `backend` directory and have activated your virtual environment
- Frontend: Run `npm install` again

### Issue: CORS errors in browser console
**Solution:** The backend is already configured for CORS. Make sure:
- Backend is running on port 8000
- Frontend is running on port 8080
- Both servers are running

### Issue: MongoDB connection errors
**Solution:** Your MongoDB Atlas cluster is already configured. Make sure:
- The connection string in `backend/.env` is correct
- Your IP address is whitelisted in MongoDB Atlas (or use 0.0.0.0/0 for development)

### Issue: Google OAuth not working
**Solution:** 
- Verify your Google OAuth credentials are correct
- Make sure the redirect URI in Google Cloud Console matches: `http://localhost:8000/auth/callback/google`
- Check that Google+ API is enabled

## Development Workflow

### Running Both Servers
You'll need two terminal windows:

**Terminal 1 (Backend):**
```bash
cd backend
source venv/bin/activate  # If using virtual environment
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
npm run dev
```

### Making Changes
- **Frontend changes:** Vite will hot-reload automatically
- **Backend changes:** Uvicorn will auto-reload with the `--reload` flag

### Stopping the Servers
Press `Ctrl+C` in each terminal to stop the servers

## Next Steps

Once everything is running:

1. **Create a test trip** - Use the Smart Wizard to create your first trip with comprehensive AI-generated packing lists
2. **Test packing lists** - Verify comprehensive items across 9 categories, age-appropriate recommendations, and weather-based suggestions
3. **Test collaboration** - Send nudges, share trips
4. **Verify AI quality** - Check that packing lists include realistic quantities, essential item marking, and activity-specific gear
4. **Explore the API** - Visit http://localhost:8000/docs to see all available endpoints

## Useful Commands

### Backend
```bash
# Run tests
cd backend
pytest

# Run specific test file
pytest test_auth.py

# Check code style
flake8 .
```

### Frontend
```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Environment Variables Reference

### Backend (.env)
- `MONGO_URI` - MongoDB connection string (already configured)
- `DATABASE_NAME` - Database name (already set to "alpacaforyou")
- `GOOGLE_CLIENT_ID` - Google OAuth Client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth Client Secret
- `GOOGLE_REDIRECT_URI` - OAuth redirect URI (already set)
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- `JWT_ALGORITHM` - JWT algorithm (already set to HS256)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Access token expiration (30 minutes)
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token expiration (7 days)
- `OPENAI_API_KEY` - OpenAI API key for AI features
- `WEATHER_API_KEY` - WeatherAPI.com key
- `WEATHER_API_BASE_URL` - Weather API base URL (already set)
- `GOOGLE_MAPS_API_KEY` - Google Maps API key

### Frontend (.env.local)
- `VITE_API_BASE_URL` - Backend API URL (already set to http://localhost:8000)

## Support

If you encounter any issues not covered in this guide:
1. Check the browser console for errors (F12)
2. Check the backend terminal for error messages
3. Review the API documentation at http://localhost:8000/docs
4. Check the existing documentation files in the project

Happy coding! 🦙