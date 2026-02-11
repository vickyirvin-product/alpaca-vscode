from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from httpx import AsyncClient
from config import settings
from database import get_db
from models.user import User, UserCreate, Token, TokenData
from auth.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_token_optional,
    verify_refresh_token
)
from pydantic import BaseModel

# Initialize OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

router = APIRouter(prefix="/auth", tags=["authentication"])


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str


@router.get("/login/google")
async def login_google(request: Request):
    """
    Initiate Google OAuth login flow.
    
    Redirects the user to Google's OAuth consent screen.
    """
    redirect_uri = settings.google_redirect_uri
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback/google")
async def auth_callback_google(request: Request):
    """
    Handle Google OAuth callback.
    
    This endpoint:
    1. Exchanges the authorization code for Google tokens
    2. Fetches user info from Google
    3. Creates or updates the user in MongoDB
    4. Returns JWT access and refresh tokens
    """
    try:
        # Exchange authorization code for token
        token = await oauth.google.authorize_access_token(request)
        
        # Get user info from Google
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from Google"
            )
        
        email = user_info.get('email')
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google"
            )
        
        # Get database
        db = get_db()
        users_collection = db.users
        
        # Check if user exists
        existing_user = await users_collection.find_one({"email": email})
        
        if existing_user:
            # Update existing user
            update_data = {
                "updated_at": datetime.utcnow()
            }
            
            # Update name and avatar if provided
            if user_info.get('name'):
                update_data["full_name"] = user_info.get('name')
            if user_info.get('picture'):
                update_data["avatar_url"] = user_info.get('picture')
            
            await users_collection.update_one(
                {"email": email},
                {"$set": update_data}
            )
            user_id = str(existing_user["_id"])
        else:
            # Create new user
            new_user = {
                "email": email,
                "full_name": user_info.get('name'),
                "avatar_url": user_info.get('picture'),
                "created_at": datetime.utcnow(),
                "updated_at": None
            }
            
            result = await users_collection.insert_one(new_user)
            user_id = str(result.inserted_id)
        
        # Create JWT tokens
        access_token = create_access_token(data={"sub": email})
        refresh_token = create_refresh_token(data={"sub": email})
        
        # Redirect to frontend with tokens in URL fragment
        # Using fragment (#) instead of query params for better security
        frontend_url = "http://localhost:8081"
        redirect_url = f"{frontend_url}/auth/callback?access_token={access_token}&refresh_token={refresh_token}&token_type=bearer"
        
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_request: RefreshTokenRequest):
    """
    Refresh access token using a valid refresh token.
    
    Args:
        refresh_request: Request containing the refresh token
        
    Returns:
        New access and refresh tokens
    """
    try:
        # Verify refresh token and get user email
        email = verify_refresh_token(refresh_request.refresh_token)
        
        # Get database
        db = get_db()
        users_collection = db.users
        
        # Verify user still exists
        user = await users_collection.find_one({"email": email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new tokens
        access_token = create_access_token(data={"sub": email})
        refresh_token = create_refresh_token(data={"sub": email})
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


async def get_current_user(token_data: TokenData = Depends(verify_token)) -> User:
    """
    Dependency to get the current authenticated user.
    
    Args:
        token_data: Token data from JWT verification
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If user not found
    """
    db = get_db()
    users_collection = db.users
    
    user = await users_collection.find_one({"email": token_data.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Convert MongoDB document to User model
    return User(
        id=str(user["_id"]),
        email=user["email"],
        full_name=user.get("full_name"),
        avatar_url=user.get("avatar_url"),
        created_at=user["created_at"],
        updated_at=user.get("updated_at")
    )


async def get_current_user_optional(token_data: Optional[TokenData] = Depends(verify_token_optional)) -> Optional[User]:
    """
    Dependency to get the current authenticated user (optional).
    
    Returns None if no valid token is provided instead of raising an exception.
    Useful for endpoints that work with or without authentication.
    
    Args:
        token_data: Token data from JWT verification (optional)
        
    Returns:
        Current user object or None if not authenticated
    """
    if not token_data:
        return None
        
    try:
        db = get_db()
        users_collection = db.users
        
        user = await users_collection.find_one({"email": token_data.email})
        if not user:
            return None
        
        # Convert MongoDB document to User model
        return User(
            id=str(user["_id"]),
            email=user["email"],
            full_name=user.get("full_name"),
            avatar_url=user.get("avatar_url"),
            created_at=user["created_at"],
            updated_at=user.get("updated_at")
        )
    except Exception:
        return None


@router.get("/users/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's profile.
    
    This is a protected endpoint that requires a valid JWT access token.
    
    Returns:
        Current user's profile information
    """
    return current_user