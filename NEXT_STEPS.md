# 🎯 Next Steps - Complete Your Setup

Great progress! You've successfully:
- ✅ Created environment configuration files
- ✅ Installed backend Python dependencies
- ✅ Installed frontend npm dependencies
- ✅ MongoDB Atlas is already configured

## 🔑 Required: Get Your API Keys

Before you can run the application, you **MUST** obtain and configure these API keys in [`backend/.env`](backend/.env):

### 1. Google OAuth Credentials (Required for Login)
**Why:** Users log in with Google
**How to get:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable "Google+ API"
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Application type: "Web application"
6. Add authorized redirect URI: `http://localhost:8000/auth/callback/google`
7. Copy Client ID and Client Secret

**Update in backend/.env:**
```env
GOOGLE_CLIENT_ID=your_actual_client_id_here
GOOGLE_CLIENT_SECRET=your_actual_client_secret_here
```

### 2. JWT Secret Key (Required for Authentication)
**Why:** Secures user sessions
**How to get:**
```bash
openssl rand -hex 32
```

**Update in backend/.env:**
```env
JWT_SECRET_KEY=paste_the_generated_key_here
```

### 3. OpenAI API Key (Required for AI Features)
**Why:** Generates smart packing lists
**How to get:**
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create new API key
3. Copy the key (starts with `sk-`)

**Update in backend/.env:**
```env
OPENAI_API_KEY=sk-your_actual_key_here
```

### 4. Weather API Key (Required for Weather-Based Suggestions)
**Why:** Provides weather-based packing recommendations
**How to get:**
1. Go to [WeatherAPI.com](https://www.weatherapi.com/signup.aspx)
2. Sign up for free account
3. Copy API key from dashboard

**Update in backend/.env:**
```env
WEATHER_API_KEY=your_actual_key_here
```

### 5. Google Maps API Key (Required for Location Features)
**Why:** Provides location search and maps
**How to get:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/google/maps-apis)
2. Enable these APIs:
   - Maps JavaScript API
   - Places API
   - Geocoding API
3. Create API key
4. Copy the key

**Update in backend/.env:**
```env
GOOGLE_MAPS_API_KEY=your_actual_key_here
```

## 🚀 Once You Have All API Keys

### Step 1: Verify Your Configuration
Open [`backend/.env`](backend/.env) and ensure all these fields are filled with real values (not placeholders):
- ✅ `GOOGLE_CLIENT_ID`
- ✅ `GOOGLE_CLIENT_SECRET`
- ✅ `JWT_SECRET_KEY`
- ✅ `OPENAI_API_KEY`
- ✅ `WEATHER_API_KEY`
- ✅ `GOOGLE_MAPS_API_KEY`

### Step 2: Start the Application

**Option A: Use the startup script (easiest)**
```bash
./start-dev.sh
```

**Option B: Manual start (two terminals)**

Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Frontend:
```bash
npm run dev
```

### Step 3: Access the Application
- **Frontend:** http://localhost:8080
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Step 4: Test Everything Works

1. **Backend Health Check:**
   - Open http://localhost:8000/healthz
   - Should see: `{"status":"ok"}`

2. **Frontend Loads:**
   - Open http://localhost:8080
   - Should see the Alpaca app homepage

3. **Test Login:**
   - Click "Login with Google"
   - Complete Google OAuth flow
   - Should redirect back to dashboard

4. **Create a Test Trip:**
   - Use the Smart Wizard
   - Enter destination, dates, travelers
   - AI should generate a packing list

## 📚 Additional Resources

- **[Quick Start Guide](QUICK_START.md)** - Quick reference for daily development
- **[Complete Setup Guide](LOCAL_SETUP_GUIDE.md)** - Detailed setup with troubleshooting
- **[Testing Guide](TESTING_GUIDE.md)** - How to test all features
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when backend is running)

## 🐛 Troubleshooting

### "Backend won't start"
- Check that all API keys in `backend/.env` are set
- Look at terminal output for specific error messages
- Verify virtual environment is activated

### "Google login doesn't work"
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct
- Check redirect URI in Google Cloud Console matches: `http://localhost:8000/auth/callback/google`
- Ensure Google+ API is enabled

### "AI features don't work"
- Verify `OPENAI_API_KEY` is correct and starts with `sk-`
- Check you have credits in your OpenAI account
- Look at backend terminal for error messages

### "CORS errors in browser"
- Ensure backend is running on port 8000
- Ensure frontend is running on port 8080
- Check both servers are actually running

## 💡 Tips

1. **Keep terminals open:** You need both backend and frontend running simultaneously
2. **Check browser console:** Press F12 to see any frontend errors
3. **Check backend logs:** Watch the backend terminal for API errors
4. **Use API docs:** Visit http://localhost:8000/docs to test endpoints directly
5. **Start simple:** Test health check and login before trying complex features

## ✅ Success Checklist

Before considering setup complete, verify:
- [ ] All API keys are configured in `backend/.env`
- [ ] Backend starts without errors on port 8000
- [ ] Frontend starts without errors on port 8080
- [ ] Health check returns `{"status":"ok"}`
- [ ] Can access frontend at http://localhost:8080
- [ ] Google login works and redirects back
- [ ] Can create a test trip with AI-generated packing list

## 🎉 You're Ready!

Once all the above is working, you're ready to develop and test your application locally!

Need help? Check the troubleshooting sections in:
- [Quick Start Guide](QUICK_START.md)
- [Complete Setup Guide](LOCAL_SETUP_GUIDE.md)