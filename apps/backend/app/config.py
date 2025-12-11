from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Provider API Keys (Production)
    # SECURITY: Never hardcode credentials - always load from .env
    amadeus_api_key: str = "REPLACE_ME"
    amadeus_api_secret: str = "REPLACE_ME"
    amadeus_base_url: str = "https://api.amadeus.com"  # Production URL
    amadeus_environment: str = "production"
    amadeus_rate_limit_rps: int = 3  # Requests per second
    amadeus_rate_limit_rpm: int = 100  # Requests per minute
    
    # Duffel (optional secondary flight provider)
    duffel_test_token: Optional[str] = "REPLACE_ME"
    duffel_environment: str = "test"
    
    # Travelpayouts / Aviasales (affiliate redirect)
    travelpayouts_aviasales_base_url: str = "REPLACE_ME"
    travelpayouts_marker: str = "REPLACE_ME"
    
    # Legacy providers (keeping for backward compatibility)
    lcc_api_key: str = "REPLACE_ME"
    trip_api_key: str = "REPLACE_ME"
    agoda_api_key: str = "REPLACE_ME"
    kiwi_api_key: str = "REPLACE_ME"
    
    # Provider selection
    flight_provider: str = "amadeus+duffel"  # amadeus, duffel, amadeus+duffel - Using both for better coverage like Skyscanner!
    hotel_provider: str = "amadeus"   # amadeus
    
    # Email & Captcha
    sendgrid_api_key: str = "REPLACE_ME"
    recaptcha_site_key: str = "REPLACE_ME"
    recaptcha_secret: str = "REPLACE_ME"
    
    # Database & Cache
    mongodb_uri: str = "mongodb://localhost:27017/metasearch"
    redis_url: Optional[str] = "redis://localhost:6379"
    
    # Auth & JWT
    jwt_secret: str = "your-secret-key-change-in-production"
    admin_totp_issuer: str = "MetasearchPlatform"
    
    # Misc
    node_env: str = "development"
    
    # Cache settings
    cache_ttl: int = 900  # 15 minutes
    
    # Rate limiting
    rate_limit_per_minute: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

settings = Settings()

# Check if using mock mode
def is_mock_mode(provider: str) -> bool:
    """Check if a provider is in mock mode (API key not set)"""
    key_map = {
        "amadeus": settings.amadeus_api_key,
        "lcc": settings.lcc_api_key,
        "trip": settings.trip_api_key,
        "agoda": settings.agoda_api_key,
        "kiwi": settings.kiwi_api_key,
    }
    return key_map.get(provider, "REPLACE_ME") == "REPLACE_ME"
