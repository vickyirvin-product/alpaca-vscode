# Alpaca For You - Backend API

FastAPI backend for the Alpaca For You family packing application.

## Setup

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB connection details
   ```

3. **Run the Server**
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Health Check

```bash
curl http://localhost:8000/healthz
```

Expected response:
```json
{"status": "ok"}
```

## Features

- ✅ **Google OAuth 2.0 Authentication** - Secure user login with Google
- ✅ **JWT Token Management** - Access and refresh token handling
- ✅ **MongoDB Integration** - User data persistence
- ✅ **Protected Routes** - Secure endpoints with JWT verification
- ✅ **FastAPI** - Modern, fast web framework with automatic API docs

## Authentication Setup

For detailed instructions on setting up Google OAuth authentication, see [AUTH_SETUP.md](./AUTH_SETUP.md).

Quick start:
1. Set up Google OAuth credentials in Google Cloud Console
2. Configure environment variables in `.env`
3. Run the server and test at `http://localhost:8000/auth/login/google`

## Project Structure

```
backend/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application entry point
├── config.py                # Configuration management
├── database.py              # MongoDB connection handling
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── README.md                # This file
├── AUTH_SETUP.md            # Authentication setup guide
├── auth/                    # Authentication module
│   ├── __init__.py
│   └── security.py          # JWT and security utilities
├── models/                  # Data models
│   ├── __init__.py
│   └── user.py              # User models and schemas
└── routes/                  # API routes
    ├── __init__.py
    └── auth.py              # Authentication endpoints
```

## Environment Variables

### MongoDB Configuration
- `MONGO_URI`: MongoDB connection string (default: `mongodb://localhost:27017`)
- `DATABASE_NAME`: Database name (default: `alpacaforyou`)

### Google OAuth Configuration
- `GOOGLE_CLIENT_ID`: Your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth client secret
- `GOOGLE_REDIRECT_URI`: OAuth callback URL (default: `http://localhost:8000/auth/callback/google`)

### JWT Configuration
- `JWT_SECRET_KEY`: Secret key for JWT signing (generate with `openssl rand -hex 32`)
- `JWT_ALGORITHM`: JWT algorithm (default: `HS256`)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Access token expiration (default: `30`)
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiration (default: `7`)

## Development

The server runs with auto-reload enabled during development. Any changes to Python files will automatically restart the server.