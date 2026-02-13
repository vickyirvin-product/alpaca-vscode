import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from database import Database
from routes.auth import router as auth_router
from routes.trips import router as trips_router
from routes.packing import router as packing_router
from routes.collaboration import router as collaboration_router
from routes.maps import router as maps_router
from routes.weather import router as weather_router
from routes.llm import router as llm_router
from routes.trip_generation import router as trip_generation_router, cleanup_old_jobs_task
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    await Database.connect_db()
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_old_jobs_task())
    
    yield
    
    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    await Database.close_db()


# Initialize FastAPI app
app = FastAPI(
    title="Alpaca API",
    description="Backend API for the Alpaca family packing app",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:8080",  # Lovable repo frontend
        "http://localhost:8081",  # This repo frontend
        "http://localhost:3000",  # Common React dev port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware for OAuth
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret_key
)

# Register routers
app.include_router(auth_router)
app.include_router(trips_router)
app.include_router(packing_router)
app.include_router(collaboration_router)
app.include_router(maps_router)
app.include_router(weather_router)
app.include_router(llm_router)
app.include_router(trip_generation_router)


@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Alpaca API",
        "version": "1.0.0",
        "docs": "/docs"
    }