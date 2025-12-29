from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.routers import (
    search,
    providers,
    redirect,
    auth,
    admin,
    pricing,
    airports,
    cities,
    hotels_autocomplete,
    internal_health,
    hybrid_health,
    health_amadeus,
    service_status,
)
from app.routers import health_aviasales
from app.routers import internal_stats
from app.routers import saved_searches
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.db.mongodb import connect_db, close_db
from app.exceptions.service_unavailable import (
    ServiceUnavailableException,
    service_unavailable_exception_handler,
)

logger = logging.getLogger(__name__)

# ============================================================
# FastAPI App
# ============================================================

app = FastAPI(
    title="Metasearch API",
    description="Flight + Hotel Metasearch Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ============================================================
# ✅ CORS — REQUIRED FOR CUSTOM DOMAIN (FIXED)
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Local development
        "http://localhost:3000",
        "http://localhost:8001",

        # Vercel (preview and production)
        "https://travelsearch.vercel.app",
        "https://travelsearch-*.vercel.app",  # Preview deployments

        # Custom domains (IMPORTANT)
        "https://travelsearch.in",
        "https://www.travelsearch.in",
        
        # Render backend (for health checks)
        "https://travelsearch-backend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,  # Cache preflight for 24 hours
)

# ============================================================
# Security & Rate Limiting
# ============================================================

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# ============================================================
# Startup / Shutdown
# ============================================================

@app.on_event("startup")
async def startup():
    logger.info("=" * 60)
    logger.info("STARTING BACKEND APPLICATION")
    logger.info("=" * 60)

    from app.core.config import log_config_status
    log_config_status()

    await connect_db()

    # Hybrid supplier protection (MongoDB-backed)
    try:
        from app.services.supplier_protection_controller import get_controller
        controller = await get_controller()
        logger.info("✅ Hybrid supplier protection initialized")
    except Exception as e:
        logger.warning(f"⚠️ Hybrid protection init failed: {e}")

    # Redis protected orchestrator (optional)
    if getattr(settings, "supplier_protection", False) and getattr(settings, "redis_url", None):
        try:
            from app.services.protected_orchestrator import protected_orchestrator
            await protected_orchestrator.initialize()
            logger.info("✅ Protected orchestrator initialized")
        except Exception as e:
            logger.warning(f"⚠️ Protected orchestrator init failed: {e}")

    logger.info("=" * 60)
    logger.info("BACKEND STARTUP COMPLETE")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown():
    await close_db()

    try:
        from app.services.redis_client import redis_client
        await redis_client.disconnect()
    except Exception:
        pass

# ============================================================
# Exception Handlers
# ============================================================

app.add_exception_handler(
    ServiceUnavailableException,
    service_unavailable_exception_handler
)

# ============================================================
# Health
# ============================================================

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

# ============================================================
# Routers
# ============================================================

app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(service_status.router, tags=["service-status"])
app.include_router(providers.router, prefix="/api", tags=["providers"])
app.include_router(redirect.router, prefix="/api", tags=["redirect"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(pricing.router, prefix="/api", tags=["pricing"])
app.include_router(airports.router, prefix="/api", tags=["airports"])
app.include_router(cities.router, prefix="/api", tags=["cities"])
app.include_router(hotels_autocomplete.router, prefix="/api", tags=["hotels"])

# Webhooks
from app.routers import webhooks_reconcile
app.include_router(webhooks_reconcile.router, prefix="/api", tags=["webhooks", "admin"])

# Internal health
app.include_router(internal_health.router, tags=["internal-health"])
app.include_router(hybrid_health.router, tags=["hybrid-protection"])
app.include_router(health_amadeus.router, prefix="/api", tags=["health"])
app.include_router(health_aviasales.router, prefix="/api", tags=["health", "aviasales"])
app.include_router(internal_stats.router, prefix="/api", tags=["internal", "monitoring"])
app.include_router(saved_searches.router, prefix="/api", tags=["saved-searches"])

# Track Price - Price drop alerts
from app.routers import track_price
app.include_router(track_price.router, prefix="/api", tags=["track-price"])

# Train & Bus Search
from app.routers import train as train_router
from app.routers import bus as bus_router
app.include_router(train_router.router, prefix="/api", tags=["trains"])
app.include_router(bus_router.router, prefix="/api", tags=["buses"])

# MSRTC Maharashtra State Bus Services
from app.routers import msrtc as msrtc_router
app.include_router(msrtc_router.router, prefix="/api", tags=["msrtc"])

# Bus Autocomplete (cascading search with state bias)
from app.routers import bus_autocomplete
app.include_router(bus_autocomplete.router, prefix="/api", tags=["bus-autocomplete"])

# Route Stops - Likely Stops on Route feature
from app.routers import route_stops
app.include_router(route_stops.router, prefix="/api", tags=["routes"])

# Feeder Routes - Tourist Destination Connectivity
from app.routers import feeder_routes
app.include_router(feeder_routes.router, prefix="/api", tags=["feeder-routes"])

# Train Connectivity - Hub-based routing for Indian Railways
from app.routers import train_connectivity
app.include_router(train_connectivity.router, prefix="/api", tags=["train-connectivity"])

# ============================================================
# Local Run
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001)
