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
    
    # Google Maps API Configuration
    google_maps_api_key: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()