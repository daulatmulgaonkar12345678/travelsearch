"""
CENTRALIZED CONFIGURATION HUB

This is the SINGLE SOURCE OF TRUTH for all API credentials and settings.
ALL services MUST import from here:

    from app.core.config import settings

NEVER:
- Load .env in multiple places
- Hardcode credentials
- Use fallback values for secrets
- Cache settings manually
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ======================================================
# SETTINGS
# ======================================================
class Settings(BaseSettings):
    """Single source of truth for all configuration"""

    # ==================================================
    # AMADEUS (PRIMARY & ONLY FLIGHT PROVIDER)
    # ==================================================
    amadeus_api_key: str
    amadeus_api_secret: str
    amadeus_base_url: str = "https://api.amadeus.com"
    amadeus_environment: str = "production"

    # ==================================================
    # AMADEUS COST CONTROL (CRITICAL)
    # ==================================================
    daily_search_cap: int = 70                     # per day
    flight_cache_ttl_seconds: int = 900            # 15 minutes
    search_rate_limit_per_ip: int = 5              # per minute
    amadeus_real_search_enabled: bool = True       # MASTER KILL SWITCH

    # Circuit breaker & protection
    amadeus_timeout_ms: int = 2500
    amadeus_rps: int = 3
    amadeus_rpm: int = 100
    amadeus_burst: int = 5
    amadeus_circuit_failures: int = 3
    amadeus_circuit_cooldown_seconds: int = 300

    # ==================================================
    # PROVIDER SELECTION (ENFORCED)
    # ==================================================
    flight_provider: str = "amadeus"
    hotel_provider: str = "amadeus"

    # ==================================================
    # DISABLED PROVIDERS (KEPT FOR FUTURE, OFF BY DEFAULT)
    # ==================================================
    aviasales_enabled: bool = False
    travelpayouts_api_token: Optional[str] = None
    travelpayouts_marker: Optional[str] = None
    travelpayouts_base_url: Optional[str] = None

    duffel_enabled: bool = False
    duffel_test_token: Optional[str] = None
    duffel_environment: str = "test"

    kiwi_enabled: bool = False
    kiwi_api_key: Optional[str] = None

    flightapi_enabled: bool = False
    flightapi_key: Optional[str] = None

    # ==================================================
    # DATABASE & CACHE
    # ==================================================
    mongo_url: str = "mongodb://localhost:27017"
    db_name: str = "test_database"
    mongodb_uri: Optional[str] = None
    redis_url: Optional[str] = None

    # ==================================================
    # AUTH & SECURITY
    # ==================================================
    jwt_secret: str
    admin_totp_issuer: str = "MetasearchPlatform"

    # ==================================================
    # EMAIL & CAPTCHA (OPTIONAL)
    # ==================================================
    sendgrid_api_key: Optional[str] = None
    recaptcha_site_key: Optional[str] = None
    recaptcha_secret: Optional[str] = None

    # ==================================================
    # GENERAL
    # ==================================================
    node_env: str = "development"
    cors_origins: str = "*"

    # ==================================================
    # CACHE & RATE LIMITING (GLOBAL)
    # ==================================================
    cache_ttl: int = 900
    rate_limit_per_minute: int = 100

    # ==================================================
    # SUPPLIER & COST PROTECTION
    # ==================================================
    supplier_protection: bool = True

    # ==================================================
    # ENV CONFIG
    # ==================================================
    model_config = SettingsConfigDict(
        env_file="/app/apps/backend/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# ======================================================
# SINGLETON INSTANCE (ONLY ONE ALLOWED)
# ======================================================
settings = Settings()


# ======================================================
# STARTUP VALIDATION & LOGGING
# ======================================================
def log_config_status():
    """Log configuration status on startup (masked, safe)"""
    logger.info("=" * 60)
    logger.info("🚀 CONFIGURATION STATUS (AUTHORITATIVE)")
    logger.info("=" * 60)

    # --- Amadeus ---
    masked_key = f"{settings.amadeus_api_key[:6]}...{settings.amadeus_api_key[-4:]}"
    masked_secret = f"{settings.amadeus_api_secret[:4]}...{settings.amadeus_api_secret[-4:]}"
    logger.info(f"✅ Amadeus API Key: {masked_key}")
    logger.info(f"✅ Amadeus API Secret: {masked_secret}")
    logger.info(f"✅ Amadeus Base URL: {settings.amadeus_base_url}")
    logger.info(f"✅ Amadeus Environment: {settings.amadeus_environment}")
    logger.info(f"✅ Real Search Enabled: {settings.amadeus_real_search_enabled}")
    logger.info(f"✅ Daily Search Cap: {settings.daily_search_cap}")

    # --- Provider Lock ---
    if settings.flight_provider != "amadeus":
        logger.critical("❌ INVALID PROVIDER CONFIG — FLIGHT_PROVIDER MUST BE 'amadeus'")
        raise RuntimeError("Invalid flight provider configuration")

    logger.info("🔒 Flight Provider Locked: AMADEUS ONLY")

    # --- Database ---
    logger.info(f"✅ MongoDB: {settings.mongo_url}/{settings.db_name}")

    # --- Disabled Providers ---
    logger.info("🚫 Disabled Providers: Aviasales, Duffel, Kiwi, FlightAPI")

    logger.info("=" * 60)


# Execute on startup
log_config_status()
