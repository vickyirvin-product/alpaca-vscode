# Phase 1 Implementation: Authentication & API Client

## Overview
Phase 1 of the frontend integration has been successfully implemented. This phase establishes the authentication foundation and enhanced API client for the Alpaca For You application.

## Files Created/Modified

### New Files Created:
1. **`src/types/auth.ts`** - Authentication TypeScript interfaces
   - `User` - User model matching backend schema
   - `AuthState` - Authentication state management
   - `AuthTokens` - JWT token structure
   - `LoginResponse` - Backend login response format
   - `UserResponse` - Backend user response (snake_case)

2. **`src/components/auth/Login.tsx`** - Login page component
   - Google OAuth "Sign in with Google" button
   - Loading states during authentication
   - Error handling and display
   - Auto-redirect to dashboard when authenticated

3. **`src/components/auth/AuthCallback.tsx`** - OAuth callback handler
   - Handles Google OAuth callback
   - Extracts and stores JWT tokens
   - Redirects to intended destination or dashboard
   - Error handling with user feedback

4. **`src/components/auth/ProtectedRoute.tsx`** - Route protection wrapper
   - Wraps routes requiring authentication
   - Shows loading state during auth check
   - Redirects to login if not authenticated
   - Stores intended destination for post-login redirect

### Modified Files:

1. **`src/lib/api.ts`** - Enhanced API client
   - **Data Transformation Utilities:**
     - `transformToCamelCase()` - Converts snake_case to camelCase
     - `transformToSnakeCase()` - Converts camelCase to snake_case
     - Recursive transformation for nested objects and arrays
   
   - **Token Management:**
     - `tokenManager.getAccessToken()` - Retrieve access token
     - `tokenManager.setAccessToken()` - Store access token
     - `tokenManager.getRefreshToken()` - Retrieve refresh token
     - `tokenManager.setRefreshToken()` - Store refresh token
     - `tokenManager.setTokens()` - Store both tokens
     - `tokenManager.clearTokens()` - Clear all tokens
     - `tokenManager.hasValidToken()` - Check token existence
   
   - **Request/Response Interceptors:**
     - Automatic token injection in Authorization header
     - 401 error handling with automatic token refresh
     - Retry failed requests after token refresh
     - Automatic logout on refresh failure
   
   - **Authentication API Methods:**
     - `authApi.loginWithGoogle()` - Initiate Google OAuth flow
     - `authApi.handleAuthCallback()` - Process OAuth callback
     - `authApi.logout()` - Clear tokens and logout
     - `authApi.getCurrentUser()` - Fetch current user info
     - `authApi.verifyToken()` - Verify token validity
     - `authApi.refreshToken()` - Manually refresh access token

2. **`src/context/AppContext.tsx`** - Enhanced with authentication
   - Added `auth` state to AppState interface
   - Added authentication methods to context:
     - `login()` - Initiate Google OAuth login
     - `logout()` - Logout and clear state
     - `checkAuth()` - Verify authentication on app load
   - Auto-initialization of auth state on mount
   - Token storage in localStorage
   - Loading states for auth operations

3. **`src/App.tsx`** - Updated routing
   - Added `/login` route (public)
   - Added `/auth/callback` route (public)
   - Wrapped `/` and `/dashboard` with `ProtectedRoute`
   - Imported authentication components

## Authentication Flow

### Login Flow:
1. User visits protected route (e.g., `/dashboard`)
2. `ProtectedRoute` checks authentication status
3. If not authenticated, redirects to `/login`
4. User clicks "Sign in with Google"
5. `authApi.loginWithGoogle()` redirects to backend `/auth/login/google`
6. Backend redirects to Google OAuth consent screen
7. User authorizes the application
8. Google redirects to backend `/auth/callback/google`
9. Backend exchanges code for tokens and returns them
10. Frontend redirects to `/auth/callback`
11. `AuthCallback` component stores tokens in localStorage
12. `checkAuth()` fetches user info from `/auth/users/me`
13. User is redirected to intended destination or dashboard

### Token Refresh Flow:
1. API request receives 401 Unauthorized response
2. Request interceptor triggers token refresh
3. Refresh token is sent to `/auth/refresh`
4. New access token is received and stored
5. Original request is retried with new token
6. If refresh fails, user is logged out and redirected to login

### Logout Flow:
1. User triggers logout action
2. `logout()` calls backend `/auth/logout` endpoint
3. Tokens are cleared from localStorage
4. Auth state is reset
5. Trip data is cleared
6. User is redirected to login page

## Backend Endpoints Used

All endpoints use the backend base URL: `http://localhost:8000`

- `GET /auth/login/google` - Initiate Google OAuth
- `GET /auth/callback/google` - Handle OAuth callback
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout (optional)
- `GET /auth/users/me` - Get current user profile

## Data Transformation

The API client automatically transforms data between frontend (camelCase) and backend (snake_case):

**Frontend → Backend (Request):**
```typescript
{ firstName: "John", lastName: "Doe" }
// Transformed to:
{ first_name: "John", last_name: "Doe" }
```

**Backend → Frontend (Response):**
```typescript
{ first_name: "John", last_name: "Doe" }
// Transformed to:
{ firstName: "John", lastName: "Doe" }
```

## Testing Instructions

### Prerequisites:
1. Backend server running on `http://localhost:8000`
2. Frontend dev server running on `http://localhost:5173`
3. Google OAuth credentials configured in `backend/.env`
4. MongoDB connection active

### Test Scenarios:

#### 1. Test Unauthenticated Access:
```bash
# Open browser to http://localhost:5173
# Expected: Redirected to /login page
# Should see: "Sign in with Google" button
```

#### 2. Test Google OAuth Login:
```bash
# Click "Sign in with Google" button
# Expected: Redirected to Google OAuth consent screen
# Authorize the application
# Expected: Redirected back to /auth/callback
# Expected: Loading screen briefly shown
# Expected: Redirected to /dashboard
# Expected: User is authenticated and can access protected routes
```

#### 3. Test Token Persistence:
```bash
# After successful login, refresh the page
# Expected: User remains authenticated (no redirect to login)
# Check localStorage for 'auth_token' and 'refresh_token'
```

#### 4. Test Protected Routes:
```bash
# While authenticated, navigate to /dashboard
# Expected: Dashboard loads successfully
# Open DevTools → Application → Local Storage
# Clear 'auth_token' and 'refresh_token'
# Refresh page
# Expected: Redirected to /login
```

#### 5. Test Logout:
```bash
# While authenticated, trigger logout (when UI is added)
# Expected: Tokens cleared from localStorage
# Expected: Redirected to /login
# Expected: Cannot access protected routes
```

#### 6. Test Token Refresh (Advanced):
```bash
# Login successfully
# Wait for access token to expire (30 minutes by default)
# Make an API request
# Expected: Token automatically refreshed
# Expected: Request succeeds with new token
# Check DevTools Network tab for /auth/refresh call
```

### Manual Testing with Browser DevTools:

```javascript
// Check authentication state
localStorage.getItem('auth_token')
localStorage.getItem('refresh_token')

// Manually clear tokens to test logout
localStorage.removeItem('auth_token')
localStorage.removeItem('refresh_token')

// Check API base URL
console.log(import.meta.env.VITE_API_BASE_URL)
```

## Known Limitations & Notes

1. **OAuth Redirect URI**: The Google OAuth redirect URI must be configured in Google Cloud Console as:
   - `http://localhost:8000/auth/callback/google`

2. **CORS Configuration**: Backend CORS is configured for:
   - `http://localhost:5173` (Vite default)
   - `http://localhost:8080`
   - `http://localhost:3000`

3. **Token Storage**: Tokens are stored in localStorage (not httpOnly cookies)
   - Consider using httpOnly cookies for production
   - Current implementation is suitable for development

4. **Session Management**: Uses JWT tokens with:
   - Access token: 30 minutes expiry
   - Refresh token: 7 days expiry

5. **Error Handling**: All authentication errors are caught and displayed to users
   - Network errors show generic error messages
   - OAuth errors redirect to login with error display

## Next Steps (Phase 2)

Phase 1 is now complete. The next phase will focus on:

1. **Trip Management Integration**
   - Connect onboarding flow to backend `/trips` endpoints
   - Implement trip creation with AI-generated packing lists
   - Fetch and display trip data from backend

2. **Data Adapters**
   - Create adapter functions for trip data transformation
   - Flatten packing lists from backend grouped format
   - Handle weather data structure differences

3. **State Management**
   - Replace mock data with real API calls
   - Implement optimistic UI updates
   - Add loading and error states

## Troubleshooting

### Issue: "Failed to get user info from Google"
- **Solution**: Check Google OAuth credentials in `backend/.env`
- Verify redirect URI matches Google Cloud Console configuration

### Issue: "Authentication callback failed"
- **Solution**: Check backend logs for detailed error
- Verify backend is running on port 8000
- Check CORS configuration

### Issue: "Token refresh failed"
- **Solution**: Check refresh token validity
- Verify `/auth/refresh` endpoint is accessible
- Check JWT secret key configuration

### Issue: Infinite redirect loop
- **Solution**: Clear localStorage tokens
- Check `ProtectedRoute` logic
- Verify auth state initialization

## Security Considerations

1. **Token Storage**: Tokens in localStorage are vulnerable to XSS attacks
   - Consider httpOnly cookies for production
   - Implement Content Security Policy (CSP)

2. **Token Expiry**: Short-lived access tokens (30 min) minimize exposure
   - Refresh tokens allow seamless re-authentication
   - Implement token rotation for enhanced security

3. **HTTPS**: Use HTTPS in production
   - Prevents token interception
   - Required for secure cookie attributes

4. **OAuth Scopes**: Currently requests minimal scopes (email, profile)
   - Review and adjust as needed
   - Follow principle of least privilege

## Conclusion

Phase 1 successfully implements:
✅ Complete authentication flow with Google OAuth
✅ JWT token management with automatic refresh
✅ Protected routes with loading states
✅ Data transformation utilities (snake_case ↔ camelCase)
✅ Request/response interceptors
✅ Error handling and user feedback
✅ Token persistence across sessions

The authentication foundation is now ready for Phase 2 integration.