# Google OAuth Authentication Setup Guide

This guide will help you set up and test the Google OAuth authentication system for the Alpaca backend.

## Prerequisites

1. Python 3.8 or higher
2. MongoDB running locally or accessible via connection string
3. Google Cloud Console account

## Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Step 2: Set Up Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google+ API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:8000/auth/callback/google`
     - Add your production URL when deploying
   - Save the Client ID and Client Secret

## Step 3: Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and fill in your values:
```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=alpacaforyou

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_actual_client_id_from_google
GOOGLE_CLIENT_SECRET=your_actual_client_secret_from_google
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback/google

# JWT Configuration
JWT_SECRET_KEY=generate_a_secure_random_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

3. Generate a secure JWT secret key:
```bash
# Using Python
python -c "import secrets; print(secrets.token_hex(32))"

# Or using OpenSSL
openssl rand -hex 32
```

## Step 4: Start MongoDB

Make sure MongoDB is running:
```bash
# If using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or start your local MongoDB service
mongod
```

## Step 5: Run the Backend Server

```bash
# From the backend directory
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server should start at `http://localhost:8000`

## Step 6: Test the Authentication Flow

### Using the API Documentation (Swagger UI)

1. Open your browser and navigate to: `http://localhost:8000/docs`
2. You'll see the interactive API documentation

### Testing the OAuth Flow

1. **Initiate Login:**
   - Navigate to: `http://localhost:8000/auth/login/google`
   - You'll be redirected to Google's consent screen
   - Sign in with your Google account
   - Grant the requested permissions

2. **Callback Handling:**
   - After authorization, Google redirects back to `/auth/callback/google`
   - You'll receive a JSON response with access and refresh tokens:
   ```json
   {
     "access_token": "eyJhbGc...",
     "refresh_token": "eyJhbGc...",
     "token_type": "bearer"
   }
   ```

3. **Access Protected Endpoint:**
   - Copy the `access_token` from the response
   - In Swagger UI, click the "Authorize" button
   - Enter: `Bearer <your_access_token>`
   - Try the `/auth/users/me` endpoint to get your profile

### Testing with cURL

```bash
# 1. Get tokens (you'll need to do this in a browser first)
# Visit: http://localhost:8000/auth/login/google

# 2. Use the access token to get your profile
curl -X GET "http://localhost:8000/auth/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"

# 3. Refresh your access token
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN_HERE"}'
```

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/auth/login/google` | Initiate Google OAuth flow | No |
| GET | `/auth/callback/google` | Handle OAuth callback | No |
| POST | `/auth/refresh` | Refresh access token | No |
| GET | `/auth/users/me` | Get current user profile | Yes |

### Request/Response Examples

#### Get Current User Profile
```bash
GET /auth/users/me
Authorization: Bearer <access_token>

Response:
{
  "id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "full_name": "John Doe",
  "avatar_url": "https://lh3.googleusercontent.com/...",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": null
}
```

#### Refresh Token
```bash
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGc..."
}

Response:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

## MongoDB Collections

The authentication system creates the following collection:

### `users` Collection
```javascript
{
  "_id": ObjectId("..."),
  "email": "user@example.com",
  "full_name": "John Doe",
  "avatar_url": "https://lh3.googleusercontent.com/...",
  "created_at": ISODate("2024-01-01T00:00:00Z"),
  "updated_at": ISODate("2024-01-02T00:00:00Z")
}
```

## Security Considerations

1. **JWT Secret Key**: Use a strong, randomly generated secret key in production
2. **HTTPS**: Always use HTTPS in production for OAuth callbacks
3. **Token Storage**: Store tokens securely on the client side (HTTP-only cookies recommended)
4. **Token Expiration**: Access tokens expire in 30 minutes, refresh tokens in 7 days
5. **CORS**: Update CORS settings in `main.py` for your production frontend URL

## Troubleshooting

### Common Issues

1. **"Invalid redirect URI"**
   - Ensure the redirect URI in Google Console matches exactly: `http://localhost:8000/auth/callback/google`
   - Check that `GOOGLE_REDIRECT_URI` in `.env` matches

2. **"Could not validate credentials"**
   - Verify your JWT secret key is set correctly
   - Check that the token hasn't expired
   - Ensure you're using the access token (not refresh token) for protected endpoints

3. **MongoDB Connection Error**
   - Verify MongoDB is running
   - Check the `MONGO_URI` in your `.env` file

4. **"User not found"**
   - The user might have been deleted from the database
   - Try logging in again to recreate the user

## Next Steps

1. Integrate with frontend application
2. Implement token refresh logic in frontend
3. Add user logout functionality
4. Implement role-based access control (RBAC) if needed
5. Add email verification (optional)
6. Set up production environment with proper HTTPS

## Frontend Integration Example

```typescript
// Example frontend code to handle OAuth flow
const handleGoogleLogin = () => {
  // Redirect to backend OAuth endpoint
  window.location.href = 'http://localhost:8000/auth/login/google';
};

// After callback, store tokens
const tokens = await response.json();
localStorage.setItem('access_token', tokens.access_token);
localStorage.setItem('refresh_token', tokens.refresh_token);

// Use token in API requests
const response = await fetch('http://localhost:8000/auth/users/me', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
});
```

## Support

For issues or questions, please refer to:
- FastAPI documentation: https://fastapi.tiangolo.com/
- Authlib documentation: https://docs.authlib.org/
- Google OAuth documentation: https://developers.google.com/identity/protocols/oauth2