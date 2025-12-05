# Flight + Hotel Metasearch Platform

> Production-grade, SEO-first metasearch engine for flights and hotels
> Built with Next.js 14, FastAPI, MongoDB

## 🏗️ Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design and data flows.

## 📁 Monorepo Structure

```
.
├── apps/
│   ├── frontend/              # Next.js 14 frontend
│   │   ├── app/              # App Router pages
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx      # Home/Search page
│   │   │   ├── flights/
│   │   │   ├── hotels/
│   │   │   └── admin/
│   │   ├── components/       # React components
│   │   │   ├── search/
│   │   │   │   ├── SearchBar.tsx
│   │   │   │   ├── PassengerModal.tsx
│   │   │   │   ├── DateStrip.tsx
│   │   │   │   └── FilterSidebar.tsx
│   │   │   ├── results/
│   │   │   │   ├── ResultCard.tsx
│   │   │   │   └── ProviderOfferCard.tsx
│   │   │   ├── common/
│   │   │   │   └── InterstitialModal.tsx
│   │   │   └── ui/           # shadcn components
│   │   ├── lib/
│   │   ├── styles/
│   │   ├── public/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── next.config.js
│   │   └── tailwind.config.ts
│   │
│   └── backend/              # FastAPI backend
│       ├── app/
│       │   ├── main.py       # FastAPI app entry
│       │   ├── config.py     # Configuration
│       │   ├── routers/      # API routers
│       │   │   ├── search.py
│       │   │   ├── providers.py
│       │   │   ├── redirect.py
│       │   │   ├── auth.py
│       │   │   └── admin.py
│       │   ├── models/       # Pydantic models
│       │   │   ├── flight.py
│       │   │   ├── hotel.py
│       │   │   ├── user.py
│       │   │   └── click.py
│       │   ├── services/     # Business logic
│       │   │   ├── aggregator.py
│       │   │   ├── ranking.py
│       │   │   ├── cache.py
│       │   │   └── adapters/
│       │   │       ├── base.py
│       │   │       ├── amadeus_adapter.py
│       │   │       ├── lcc_adapter.py
│       │   │       └── hotel_adapter.py
│       │   ├── middleware/   # Security middleware
│       │   │   ├── rate_limit.py
│       │   │   ├── security.py
│       │   │   └── bot_detection.py
│       │   ├── db/           # Database
│       │   │   └── mongodb.py
│       │   └── utils/
│       ├── tests/
│       ├── requirements.txt
│       └── Dockerfile
│
├── packages/
│   ├── ui/                   # Shared React components
│   │   ├── package.json
│   │   └── src/
│   └── types/                # Shared types
│       ├── package.json
│       └── schemas/
│
├── scripts/
│   ├── generate_seo_pages.py # SEO page generator
│   ├── seed_data.py          # Seed mock data
│   └── deploy.sh             # Deployment script
│
├── infra/
│   ├── terraform/            # GCP Terraform configs
│   └── docker-compose.yml    # Local development
│
├── tests/
│   ├── e2e/                  # Playwright tests
│   └── load/                 # k6 load tests
│
├── .env.example
├── .gitignore
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Node.js 20+
- Python 3.11+
- MongoDB 6+ (local or Atlas)
- Redis (optional, for caching)
- Yarn package manager

### Installation

1. **Clone and install dependencies**

```bash
# Install frontend dependencies
cd apps/frontend
yarn install

# Install backend dependencies
cd ../backend
pip install -r requirements.txt
```

2. **Set up environment variables**

```bash
cp .env.example apps/frontend/.env.local
cp .env.example apps/backend/.env
```

Edit the `.env` files with your configuration (see Environment Variables section).

3. **Start MongoDB**

```bash
# Using Docker
docker run -d -p 27017:27017 --name metasearch-mongo mongo:6

# Or use existing MongoDB instance
```

4. **Start Redis (optional)**

```bash
# Using Docker
docker run -d -p 6379:6379 --name metasearch-redis redis:7-alpine
```

### Development

**Option 1: Run services separately**

```bash
# Terminal 1 - Backend
cd apps/backend
uvicorn app.main:app --reload --port 8001

# Terminal 2 - Frontend
cd apps/frontend
yarn dev
```

**Option 2: Using docker-compose**

```bash
docker-compose up
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## 🔑 Environment Variables

Create `.env.example` in the root and copy to both frontend and backend:

```bash
# ==========================================
# PROVIDER API KEYS (use REPLACE_ME for mocks)
# ==========================================

# Amadeus Flight API (primary)
AMADEUS_API_KEY=REPLACE_ME
AMADEUS_API_SECRET=REPLACE_ME

# Low-Cost Carrier API
LCC_API_KEY=REPLACE_ME

# Hotel APIs
TRIP_API_KEY=REPLACE_ME
AGODA_API_KEY=REPLACE_ME
KIWI_API_KEY=REPLACE_ME

# ==========================================
# EMAIL & CAPTCHA
# ==========================================

SENDGRID_API_KEY=REPLACE_ME
RECAPTCHA_SITE_KEY=REPLACE_ME
RECAPTCHA_SECRET=REPLACE_ME

# ==========================================
# DATABASE & CACHE
# ==========================================

MONGODB_URI=mongodb://localhost:27017/metasearch
REDIS_URL=redis://localhost:6379

# ==========================================
# AUTH & JWT
# ==========================================

JWT_SECRET=your-secret-key-change-in-production
ADMIN_TOTP_ISSUER=MetasearchPlatform

# ==========================================
# MISC
# ==========================================

NODE_ENV=development
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### 🔌 Plugging Real API Keys

**Mock Mode (Default)**
If API keys are set to `REPLACE_ME` or empty, the platform uses realistic mock adapters.

**Real Provider Integration**

1. **Amadeus Flight API**
   - Sign up: https://developers.amadeus.com/
   - Get API Key & Secret
   - Set `AMADEUS_API_KEY` and `AMADEUS_API_SECRET`
   - Adapter: `apps/backend/app/services/adapters/amadeus_adapter.py`
   - Scopes needed: `flight-offers-search`, `flight-offers-price`

2. **LCC API** (e.g., Ryanair, EasyJet via aggregator)
   - Example: FlightStats, AviationStack
   - Set `LCC_API_KEY`
   - Adapter: `apps/backend/app/services/adapters/lcc_adapter.py`

3. **Hotel APIs**
   - Trip.com: https://www.trip.com/affiliate/
   - Agoda: https://partners.agoda.com/
   - Kiwi: https://tequila.kiwi.com/
   - Set respective `*_API_KEY` variables
   - Adapter: `apps/backend/app/services/adapters/hotel_adapter.py`

4. **SendGrid (Email Alerts)**
   - Sign up: https://sendgrid.com/
   - Create API key with Mail Send permissions
   - Set `SENDGRID_API_KEY`

5. **reCAPTCHA v3**
   - Register: https://www.google.com/recaptcha/admin
   - Get Site Key and Secret Key
   - Set `RECAPTCHA_SITE_KEY` and `RECAPTCHA_SECRET`

## 🧪 Testing

### Unit Tests

```bash
# Backend tests
cd apps/backend
pytest tests/ -v

# Frontend tests
cd apps/frontend
yarn test
```

### E2E Tests (Playwright)

```bash
cd tests/e2e
pnpm install
pnpm playwright test
```

### Load Tests (k6)

```bash
cd tests/load
k6 run search_load_test.js
```

## 📊 Performance Targets

- **Search API**: p95 < 800ms (cached), p95 < 2000ms (uncached)
- **SEO Pages**: Lighthouse Performance > 90
- **Throughput**: 100 RPS sustained
- **Cache Hit Rate**: > 60%

## 🔒 Security

- Rate limiting: 100 req/min per IP
- Bot detection with device fingerprinting
- RBAC with 4 roles: superadmin, ops, seo, content
- Mandatory 2FA for admin
- CSP, HSTS, secure cookies
- Secret management ready
- Immutable audit logs

## 🚢 Deployment

### Emergent Platform (Current)

```bash
# Deploy via Emergent CLI or UI
# Follow platform-specific instructions
```

### GCP Migration (Future)

See `infra/terraform/` for Cloud Run + Firestore setup.

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

## 📈 Monitoring

- Backend logs: `/var/log/supervisor/backend.*.log`
- Frontend logs: Browser console + Next.js logs
- MongoDB: Monitor via MongoDB Atlas or Compass
- Redis: Use `redis-cli` or RedisInsight

## 🤝 Contributing

See CONTRIBUTING.md for development guidelines.

## 📄 License

MIT License - see LICENSE file

## 🔗 Links

- [Architecture Documentation](./ARCHITECTURE.md)
- [API Documentation](http://localhost:8001/docs) (when running)
- [Component Storybook](http://localhost:6006) (when running)

---

**Built with ❤️ using Next.js, FastAPI, and MongoDB**
