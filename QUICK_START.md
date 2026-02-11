# 🦙 Alpaca - Quick Start Guide

## First Time Setup (Do Once)

### 1. Get API Keys
You need these API keys (see [`LOCAL_SETUP_GUIDE.md`](LOCAL_SETUP_GUIDE.md) for detailed instructions):
- ✅ Google OAuth credentials (Client ID & Secret)
- ✅ OpenAI API key
- ✅ WeatherAPI.com key
- ✅ Google Maps API key
- ✅ JWT secret (generate with: `openssl rand -hex 32`)

### 2. Configure Backend
Edit [`backend/.env`](backend/.env) and replace all placeholder values with your actual API keys.

### 3. Install Dependencies

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

**Frontend:**
```bash
npm install
```

## Daily Development

### Option 1: Use the Startup Script (Easiest)
```bash
./start-dev.sh
```
This starts both frontend and backend servers automatically.

### Option 2: Manual Start (Two Terminals)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

## Access the Application

- **Frontend:** http://localhost:8080
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/healthz

## Testing the Setup

1. **Backend Health Check:**
   ```bash
   curl http://localhost:8000/healthz
   ```
   Should return: `{"status":"ok"}`

2. **Frontend Connection:**
   - Open http://localhost:8080
   - Check browser console (F12) for errors

3. **Authentication:**
   - Click "Login with Google"
   - Complete Google OAuth flow
   - Should redirect back to dashboard

## Common Commands

### Backend
```bash
# Run all tests
cd backend && pytest

# Run specific test
cd backend && pytest test_auth.py

# Check API docs
open http://localhost:8000/docs
```

### Frontend
```bash
# Run tests
npm test

# Build for production
npm run build

# Lint code
npm run lint
```

## Troubleshooting

### Backend won't start?
- Check that all API keys are set in `backend/.env`
- Verify virtual environment is activated
- Check terminal for error messages

### Frontend won't connect?
- Ensure backend is running on port 8000
- Check `.env.local` has `VITE_API_BASE_URL=http://localhost:8000`
- Clear browser cache and reload

### CORS errors?
- Verify backend is running on port 8000
- Verify frontend is running on port 8080
- Check backend terminal for CORS-related errors

### MongoDB connection issues?
- Your MongoDB Atlas cluster is already configured
- Ensure your IP is whitelisted in MongoDB Atlas
- Check the `MONGO_URI` in `backend/.env`

## Project Structure

```
alpaca-vscode/
├── backend/              # FastAPI backend
│   ├── main.py          # Main application entry
│   ├── routes/          # API endpoints
│   ├── models/          # Database models
│   ├── services/        # Business logic
│   └── .env             # Backend configuration
├── src/                 # React frontend
│   ├── components/      # React components
│   ├── lib/            # Utilities (including api.ts)
│   └── pages/          # Page components
├── .env.local          # Frontend configuration
└── start-dev.sh        # Development startup script
```

## Need More Help?

- 📖 Full setup guide: [`LOCAL_SETUP_GUIDE.md`](LOCAL_SETUP_GUIDE.md)
- 🔧 API documentation: http://localhost:8000/docs (when backend is running)
- 🐛 Check browser console (F12) for frontend errors
- 📝 Check terminal output for backend errors

## Stop the Servers

Press `Ctrl+C` in each terminal (or once if using `start-dev.sh`)