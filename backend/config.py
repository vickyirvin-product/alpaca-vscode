from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB Configuration
    mongo_uri: str = "mongodb+srv://product_db_user:7gMzRaDoxdE3vwgK@alpacacluster.immqteh.mongodb.net/?appName=AlpacaCluster"
    database_name: str = "alpacaforyou"
    
    # Google OAuth Configuration
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:8000/auth/callback/google"
    
    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # OpenAI Configuration
    openai_api_key: str
    
    # Weather API Configuration
    weather_api_key: str
    weather_api_base_url: str = "http://api.weatherapi.com/v1"
    
    # Weather Cache Configuration
    weather_cache_ttl_hours: int = 6  # Cache weather data for 6 hours
    weather_cache_max_size: int = 1000  # Maximum number of cached entries
    
    # Trip Generation Timeout Configuration
    trip_generation_timeout_seconds: int = 180  # 3 minutes max
    trip_generation_warning_threshold_seconds: int = 60  # warn after 1 minute
    job_cleanup_interval_seconds: int = 300  # cleanup every 5 minutes
    job_max_age_hours: int = 1  # cleanup jobs older than 1 hour
    job_max_retries: int = 2  # maximum retry attempts for transient failures
    
    # Google Maps API Configuration
    google_maps_api_key: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()