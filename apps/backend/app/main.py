from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import search, providers, redirect, auth, admin, pricing, airports, cities, hotels_autocomplete
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.db.mongodb import connect_db, close_db

app = FastAPI(
    title="Metasearch API",
    description="Flight + Hotel Metasearch Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# Database lifecycle
@app.on_event("startup")
async def startup():
    await connect_db()

@app.on_event("shutdown")
async def shutdown():
    await close_db()

# Health check
@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

# Include routers
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(providers.router, prefix="/api", tags=["providers"])
app.include_router(redirect.router, prefix="/api", tags=["redirect"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(pricing.router, prefix="/api", tags=["pricing"])
app.include_router(airports.router, prefix="/api", tags=["airports"])
app.include_router(cities.router, prefix="/api", tags=["cities"])
app.include_router(hotels_autocomplete.router, prefix="/api", tags=["hotels"])

# Import and include reconciliation routes
from app.routers import webhooks_reconcile
app.include_router(webhooks_reconcile.router, prefix="/api", tags=["webhooks", "admin"])

# Import and include airports routes
from app.routers import airports
app.include_router(airports.router, prefix="/api", tags=["airports"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
