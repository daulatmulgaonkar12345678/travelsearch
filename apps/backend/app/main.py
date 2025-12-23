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
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.db.mongodb import connect_db, close_db
from app.exceptions.service_unavailable import (
    ServiceUnavailableException,
    service_unavailable_exception_handler,
    generic_exception_handler,
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Metasearch API",
    description="Flight + Hotel Metasearch Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ============================================================
# ✅ CORS — THIS FIXES FRONTEND ↔ BACKEND CONNECTION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8001",
        "https://travelsearch.vercel.app",
        "https://travelsearch-backend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Security + Rate limit middleware
# ============================================================

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# ============================================================
# Application lifecycle
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

    # Redis protected orchestrator (optional / deprecated)
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
# Health
# ============================================================

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

# ============================================================
# Routers
# ============================================================

app.include_router(search.router, prefix="/api", tags=["search"])
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

# ============================================================
# Local run
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001)
