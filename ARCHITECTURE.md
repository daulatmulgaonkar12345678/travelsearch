# Metasearch Platform Architecture

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
        Mobile[Mobile Browser]
    end

    subgraph "Frontend - Next.js 14"
        NextApp[Next.js App Router]
        SSR[SSR Pages]
        SSG[SSG Pages]
        ISR[ISR SEO Pages]
        Components[React Components]
    end

    subgraph "Backend - FastAPI"
        API[FastAPI Server]
        
        subgraph "Routers"
            SearchRouter[/api/search]
            ProviderRouter[/api/providers]
            RedirectRouter[/api/redirect]
            AuthRouter[/api/auth]
            AdminRouter[/api/admin]
        end
        
        subgraph "Services"
            Aggregator[Search Aggregator]
            RankingEngine[Ranking Engine]
            CacheService[Cache Service]
        end
        
        subgraph "Provider Adapters"
            AmadeusAdapter[Amadeus Adapter]
            LCCAdapter[LCC Adapter]
            HotelAdapter[Hotel Adapter]
            AdapterInterface[Provider Interface]
        end
        
        subgraph "Security"
            RateLimiter[Rate Limiter]
            BotDetection[Bot Detection]
            RBAC[RBAC Guard]
            JWT[JWT Auth]
        end
    end

    subgraph "Data Layer"
        MongoDB[(MongoDB)]
        Redis[(Redis Cache)]
        
        subgraph "Collections"
            Users[users]
            SEOPages[seo_pages]
            Clicks[clicks]
            Providers[providers]
            AdminAudit[admin_audit]
            Alerts[price_alerts]
        end
    end

    subgraph "External Services"
        AmadeusAPI[Amadeus API]
        LCCAPI[LCC APIs]
        HotelAPIs[Hotel APIs]
        SendGrid[SendGrid]
        reCAPTCHA[reCAPTCHA]
    end

    subgraph "Infrastructure"
        Scheduler[Cloud Scheduler]
        SecretMgr[Secret Manager]
        CDN[CDN/Edge]
    end

    subgraph "CI/CD"
        GitHub[GitHub Actions]
        Docker[Docker Build]
        Deploy[Emergent Deploy]
    end

    Browser --> CDN
    Mobile --> CDN
    CDN --> NextApp
    NextApp --> SSR
    NextApp --> SSG
    NextApp --> ISR
    NextApp --> Components
    
    Components --> API
    API --> SearchRouter
    API --> ProviderRouter
    API --> RedirectRouter
    API --> AuthRouter
    API --> AdminRouter
    
    SearchRouter --> Aggregator
    Aggregator --> RankingEngine
    Aggregator --> CacheService
    
    Aggregator --> AmadeusAdapter
    Aggregator --> LCCAdapter
    Aggregator --> HotelAdapter
    
    AmadeusAdapter --> AdapterInterface
    LCCAdapter --> AdapterInterface
    HotelAdapter --> AdapterInterface
    
    AdapterInterface -.->|Mock Mode| AmadeusAPI
    AdapterInterface -.->|Mock Mode| LCCAPI
    AdapterInterface -.->|Mock Mode| HotelAPIs
    
    API --> RateLimiter
    API --> BotDetection
    AdminRouter --> RBAC
    AuthRouter --> JWT
    
    CacheService --> Redis
    API --> MongoDB
    MongoDB --> Users
    MongoDB --> SEOPages
    MongoDB --> Clicks
    MongoDB --> Providers
    MongoDB --> AdminAudit
    MongoDB --> Alerts
    
    Scheduler -.-> API
    AuthRouter -.-> reCAPTCHA
    API -.-> SendGrid
    API --> SecretMgr
    
    GitHub --> Docker
    Docker --> Deploy
    Deploy --> API
    Deploy --> NextApp

    style NextApp fill:#3b82f6
    style API fill:#10b981
    style MongoDB fill:#22c55e
    style Redis fill:#ef4444
    style AmadeusAdapter fill:#f59e0b
    style LCCAdapter fill:#f59e0b
    style HotelAdapter fill:#f59e0b
```

## Architecture Overview

### Frontend (Next.js 14)
- **App Router**: Modern Next.js routing with React Server Components
- **SSR**: Server-side rendering for dynamic search results
- **SSG**: Static generation for SEO landing pages
- **ISR**: Incremental Static Regeneration for route/city pages
- **Components**: shadcn/ui based accessible components

### Backend (FastAPI)
- **Modular Router Design**: Separate routers for search, providers, redirect, auth, admin
- **Provider Adapters**: Normalized interface for multiple flight/hotel APIs
- **Search Aggregator**: Merges results from multiple providers
- **Ranking Engine**: Composite scoring (price 60%, duration 25%, stops 15%)
- **Cache Layer**: Redis for 15-minute result caching
- **Security**: Rate limiting, bot detection, RBAC, JWT authentication

### Data Layer (MongoDB)
- **users**: User accounts, preferences, saved searches
- **seo_pages**: Programmatically generated SEO content
- **clicks**: Affiliate click tracking with fraud detection
- **providers**: Provider configurations and status
- **admin_audit**: Immutable audit logs for admin actions
- **price_alerts**: User price alert subscriptions

### External Integrations
- **Flight APIs**: Amadeus (primary), LCC providers (secondary)
- **Hotel APIs**: Trip.com, Agoda, Booking.com
- **Email**: SendGrid for price alerts
- **Security**: reCAPTCHA v3 for bot protection

### Security Features
- Rate limiting per IP and per API key
- Device fingerprinting and bot detection
- RBAC with roles: superadmin, ops, seo, content
- Mandatory 2FA for admin accounts
- CSP, HSTS, secure cookies
- Secret management integration
- Immutable audit logs

### Deployment
- **Development**: Local Next.js + FastAPI + MongoDB
- **Production**: Emergent platform deployment
- **Future Migration**: GCP Cloud Run + Firestore (Terraform stubs provided)

## Data Flow

### Search Flow
1. User enters search criteria (origin, destination, date)
2. Next.js frontend sends request to `/api/search`
3. FastAPI search aggregator queries provider adapters in parallel
4. Each adapter normalizes provider-specific responses
5. Aggregator merges duplicates, ranks results
6. Results cached in Redis (15min TTL)
7. Results returned to frontend with provider offers

### Redirect Flow
1. User clicks provider offer card
2. Frontend shows interstitial modal
3. Frontend calls `/api/redirect` with provider + route data
4. Backend generates unique click_id
5. Click logged to MongoDB (hashed fingerprint, masked IP)
6. Backend returns 302 redirect to provider deep link
7. Provider processes booking
8. Provider sends webhook with click_id for reconciliation

### Admin Flow
1. Admin logs in with email + password
2. 2FA TOTP challenge
3. JWT token issued with role claims
4. RBAC guard checks permissions on protected routes
5. All admin actions logged to admin_audit collection

## Performance Targets

- **Search Response**: p95 < 800ms (with cache), p95 < 2000ms (cache miss)
- **SEO Pages**: LCP < 2.5s, FID < 100ms, CLS < 0.1
- **Throughput**: 100 RPS sustained on read-only search
- **Cache Hit Rate**: > 60% for popular routes

## Migration Path to GCP

1. **MongoDB → Firestore**: Change adapter, update queries to Firestore SDK
2. **Redis → Memorystore**: Update connection string
3. **FastAPI → Cloud Run**: Use provided Dockerfile
4. **Next.js → Firebase Hosting + Cloud Run**: SSR via Cloud Run, static assets via Firebase
5. **Secrets → Secret Manager**: Update config to fetch from GCP Secret Manager
6. **Scheduler**: Cloud Scheduler for price alerts

## Folder Structure

See detailed folder tree in README.md
