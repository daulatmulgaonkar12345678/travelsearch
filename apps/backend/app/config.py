from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Provider API Keys
    amadeus_api_key: str = "REPLACE_ME"
    amadeus_api_secret: str = "REPLACE_ME"
    lcc_api_key: str = "REPLACE_ME"
    trip_api_key: str = "REPLACE_ME"
    agoda_api_key: str = "REPLACE_ME"
    kiwi_api_key: str = "REPLACE_ME"
    
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
