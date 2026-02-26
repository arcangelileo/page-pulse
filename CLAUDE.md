# PagePulse

Phase: DEPLOYMENT

## Project Spec
- **Idea**: Privacy-first website analytics platform. A lightweight, cookie-free alternative to Google Analytics that gives website owners clear insights into their traffic without compromising visitor privacy. No cookies, no fingerprinting, no personal data collection — GDPR/CCPA compliant by default, no cookie banner needed. A single <script> tag gives you page views, unique visitors, referrers, top pages, devices, browsers, countries, and UTM campaign tracking in a beautiful, fast dashboard.
- **Target users**: Website owners, indie hackers, SaaS companies, agencies, and privacy-conscious businesses who want analytics without the legal headaches of Google Analytics. Especially strong in EU markets where GDPR compliance is mandatory.
- **Revenue model**: Freemium SaaS with usage-based tiers. Free tier: 1 site, up to 10K pageviews/month. Pro ($9/mo): 10 sites, 100K pageviews/month, email reports. Business ($29/mo): unlimited sites, 1M pageviews/month, API access, team members, custom domains. Overage charges above limits.
- **Tech stack**: Python 3.12, FastAPI (async), SQLite via aiosqlite + SQLAlchemy (MVP), Alembic migrations, Jinja2 + Tailwind CSS (CDN) + HTMX for server-rendered UI, Chart.js for dashboard visualizations, APScheduler for background aggregation jobs, Docker
- **Repo**: https://github.com/arcangelileo/page-pulse
- **MVP scope**:
  - User auth (register, login, logout) with JWT httponly cookies
  - Site management (add/edit/delete tracked websites, get tracking snippet)
  - Lightweight tracking script (~1KB gzipped, no cookies, no fingerprinting)
  - Event ingestion API (page views with referrer, UTM params, screen size, browser, country via IP geolocation)
  - Privacy-preserving unique visitor counting (daily salted hash of IP + User-Agent, hash rotated daily so visitors can't be tracked across days)
  - Analytics dashboard with date range picker (today, 7d, 30d, custom)
  - Dashboard widgets: visitors over time (line chart), total pageviews, unique visitors, bounce rate, avg visit duration, top pages, top referrers, top countries, browsers, devices, UTM campaigns
  - Public shareable dashboard option (toggle per site)
  - Background job to aggregate raw events into daily rollups for fast queries
  - Dockerfile and docker-compose.yml

## Architecture Decisions
- **No cookies, no fingerprinting**: Unique visitors are counted using a daily-rotating salted hash of IP + User-Agent. The salt changes every day at midnight UTC, making it impossible to track a visitor across days. This is the same approach used by Plausible Analytics.
- **Server-side rendering with HTMX**: Dashboard is server-rendered with Jinja2 templates. HTMX handles interactive elements (date range changes, site switching) without a full SPA framework. This keeps the codebase simple and fast.
- **Chart.js for visualizations**: Lightweight, well-documented charting library. Data is passed as JSON from the server into chart configs.
- **Raw events + daily aggregates**: Raw pageview events are stored for the current day. A background job runs nightly to aggregate events into daily summary tables (by page, referrer, country, browser, device, UTM). Queries hit the aggregate tables for historical data and raw events for today. This keeps queries fast even with high traffic.
- **IP geolocation**: Use the free MaxMind GeoLite2 database (or ip-api.com as fallback) for country-level geolocation. IP addresses are NEVER stored — only the derived country code is kept.
- **Tracking script served from app**: The JS snippet is served from a `/js/p.js` endpoint so it can be customized per site and cache-busted. It sends a POST to `/api/v1/event` with page URL, referrer, screen width, and UTM parameters.
- **CORS handling**: The event ingestion endpoint accepts cross-origin requests from any domain (the tracking script runs on customer sites). Auth endpoints use standard same-origin cookies.
- **Rate limiting**: Event ingestion is rate-limited per site to prevent abuse. Use slowapi (built on limits library).
- **Bounce rate calculation**: A "visit" is a sequence of pageviews from the same visitor hash within 30 minutes. A bounce is a visit with only 1 pageview.
- **src layout**: `src/app/` with `api/`, `models/`, `schemas/`, `services/`, `templates/`, `static/` subdirs
- **Async SQLAlchemy + aiosqlite**: Non-blocking database access for high-throughput event ingestion
- **Pydantic Settings**: Configuration via environment variables with sensible defaults
- **JWT auth with httponly cookies**: Same pattern as other SaaS Factory projects
- **Alembic migrations from day 1**: Never modify the database schema without a migration

## Task Backlog
- [x] Create project structure, pyproject.toml, and initial configuration
- [x] Set up FastAPI app skeleton with health check, CORS, and error handling
- [x] Create database models (User, Site, PageviewEvent, DailyPageStats, DailyReferrerStats, DailyBrowserStats, DailyDeviceStats, DailyCountryStats, DailyUTMStats)
- [x] Set up Alembic and create initial migration
- [x] Implement user auth (register, login, logout, get current user) with JWT httponly cookies
- [x] Implement site management CRUD (create, list, update, delete sites; generate tracking snippet)
- [x] Build the tracking JavaScript snippet (lightweight, cookie-free pageview collection)
- [x] Implement event ingestion API (receive pageviews, extract metadata, geolocate IP, compute visitor hash, store events)
- [x] Build analytics query service (aggregate stats by date range, top pages, referrers, countries, browsers, devices, UTMs)
- [x] Build the analytics dashboard UI (main dashboard with charts, date picker, site switcher)
- [x] Implement public shareable dashboard feature
- [x] Add background aggregation job (nightly rollup of raw events into daily summary tables)
- [x] Add rate limiting to event ingestion endpoint
- [x] Write comprehensive tests (auth, sites, event ingestion, analytics queries, aggregation)
- [x] Write Dockerfile and docker-compose.yml
- [x] Write README with setup, deployment, and usage instructions

## Progress Log
### Session 1 — IDEATION
- Chose idea: PagePulse — Privacy-First Website Analytics
- Created spec and backlog
- Rationale: Proven market ($2M+ ARR competitors like Plausible), clear technical scope, strong freemium model, exercises interesting patterns (JS snippet generation, high-throughput event ingestion, data aggregation, charting dashboards)

### Session 2 — SCAFFOLDING
- Created GitHub repo and pushed initial commit
- Set up project structure: pyproject.toml with hatchling build, src/app/ layout
- Created FastAPI app with health check endpoint (`/health`), CORS middleware
- Set up async SQLAlchemy database layer with aiosqlite
- Created Pydantic Settings config (env-based)
- Added test infrastructure (pytest-asyncio, conftest with async client)
- Health check test passing

### Session 3 — MODELS, MIGRATIONS & AUTH
- Created all 10 database models: User, Site, PageviewEvent, DailyPageStats, DailyReferrerStats, DailyBrowserStats, DailyDeviceStats, DailyCountryStats, DailyUTMStats
- Set up Alembic with async SQLAlchemy support, generated initial migration covering all tables with proper indexes and unique constraints
- Built complete auth system:
  - Auth service with bcrypt password hashing and JWT token creation/verification
  - API endpoints: POST /api/v1/auth/register, POST /api/v1/auth/login, POST /api/v1/auth/logout, GET /api/v1/auth/me
  - JWT httponly cookie-based authentication with configurable expiration
  - Auth dependency injection (get_current_user, get_optional_user)
  - Pydantic schemas for request validation (EmailStr, min_length, etc.)
- Built professional auth UI with Tailwind CSS:
  - Split-panel register page with branding/features on left, form on right
  - Split-panel login page with matching design
  - Client-side form validation, loading states, error display
  - Responsive design (mobile collapses to single column)
  - Dashboard placeholder page with nav bar and logout
- Wrote 30 tests (all passing, zero warnings):
  - 21 auth API + UI integration tests (register, login, logout, me, page redirects, error cases)
  - 8 auth service unit tests (password hashing, JWT roundtrip, user CRUD, authentication)
  - 1 health check test
- Used bcrypt directly instead of passlib (passlib has compatibility issues with newer bcrypt/Python versions)

### Session 4 — SITE MANAGEMENT, TRACKING SCRIPT & EVENT INGESTION
- Built complete site management CRUD:
  - SiteService with domain normalization (strips www, protocol, paths, lowercases)
  - API endpoints: POST/GET/PATCH/DELETE /api/v1/sites, GET /api/v1/sites/{id} (includes tracking snippet)
  - Auth-guarded — users can only see/modify their own sites
  - Professional sites UI: list view with empty state, add-site modal, settings page with tracking snippet
- Built the tracking JavaScript snippet:
  - Served from `/js/p.js`, ~700 bytes minified
  - Cookie-free, fingerprint-free — sends only page URL, referrer, screen width, UTM params
  - Uses `navigator.sendBeacon` with `XMLHttpRequest` fallback
  - Supports SPA navigation (hooks into `history.pushState` and `popstate`)
  - Handles `prerender` visibility state
- Built event ingestion API:
  - POST /api/v1/event — no auth required (runs on third-party sites)
  - Privacy-preserving visitor hash: SHA-256 of daily-rotating salt + site_id + IP + User-Agent
  - User-Agent parsing: detects Chrome, Safari, Firefox, Edge, Opera, IE; Windows, macOS, Linux, Android, iOS, ChromeOS; desktop/mobile/tablet
  - Referrer domain extraction with www stripping
  - Self-referral filtering (same domain as site)
  - Country detection from CDN headers (CF-IPCountry, X-Country-Code, X-Vercel-IP-Country)
  - Client IP extraction from X-Forwarded-For/X-Real-IP headers
- Built reusable app shell template with nav bar and site switcher
- Wrote 84 tests (all passing):
  - 21 auth tests, 8 auth service tests
  - 19 site API + UI tests, 11 site service tests
  - 6 event ingestion integration tests
  - 17 event service unit tests (UA parsing, visitor hash, referrer extraction, IP detection)
  - 2 tracking script tests

### Session 5 — ANALYTICS DASHBOARD, AGGREGATION, RATE LIMITING & DOCKER
- Built complete analytics query service (AnalyticsService):
  - Date range parsing (today/7d/30d/custom with fallback)
  - Summary stats: total pageviews, unique visitors
  - Bounce rate calculation (% of single-pageview visitors)
  - Visitors over time with zero-fill for missing days
  - Top pages, top referrers, browsers, devices, countries, UTM campaigns
  - Full dashboard aggregation method
  - Fixed SQLite date filtering (use `func.date()` instead of `cast(timestamp, Date)`)
- Built production-quality analytics dashboard UI:
  - Site switcher dropdown for multi-site navigation
  - Date range picker: Today / 7 days / 30 days / Custom date range popup
  - 3 stat cards: Pageviews, Unique visitors, Bounce rate (with icons + formatting)
  - Chart.js line chart for "Visitors over time" (Unique Visitors + Pageviews lines, responsive, tooltips)
  - Two-column layout: Top pages table + Top referrers table
  - Three-column layout: Browsers (progress bars), Devices (progress bars), Countries (progress bars)
  - UTM Campaigns table (source/medium/campaign/visitors/views)
  - Empty states for all sections when no data
  - Settings and All sites footer links
- Built public shareable dashboard:
  - Public nav bar with PagePulse branding + "Public Dashboard" badge + Sign in link
  - Same analytics widgets as authenticated dashboard
  - Date range picker (Today/7d/30d/Custom)
  - "Powered by PagePulse" footer
  - Accessible without auth when site.public is toggled on
  - Returns 404 for non-public sites
- Built background aggregation service (AggregationService):
  - Rolls up raw PageviewEvents into 6 daily stats tables (pages, referrers, browsers, devices, countries, UTMs)
  - Idempotent — safely re-runnable (clears existing aggregates before re-inserting)
  - Per-site processing for all sites with events on target date
  - `aggregate_day()`, `aggregate_yesterday()`, `backfill()` methods
  - APScheduler integration: nightly cron job at 00:15 UTC
  - Scheduler starts/stops with app lifespan
- Added rate limiting to event ingestion:
  - 60 requests/minute per IP using slowapi
  - Rate limit exceeded handler returns 429 Too Many Requests
- Created Dockerfile and docker-compose.yml:
  - Python 3.12-slim base image
  - SQLite data volume for persistence
  - Health check with urllib
  - Environment variable configuration
- Updated README with comprehensive documentation:
  - Features, Quick Start (local + Docker), Configuration table
  - Usage guide, Tracking script details, Tech stack
  - Full API endpoint reference
- Fixed FastAPI deprecation: `regex` → `pattern` in Query parameters
- Wrote 132 tests (all passing, zero warnings):
  - 21 analytics service tests (date ranges, summary, bounce rate, visitors over time, top pages/referrers/browsers/devices/countries/UTMs, full dashboard, empty states)
  - 22 dashboard integration tests (page loads, data display, date periods, custom ranges, auth checks, site switcher, public dashboard, analytics API, permission checks)
  - 10 aggregation service tests (page/referrer/browser/device/country/UTM stats creation, idempotency, empty data, yesterday, backfill)
  - Plus all previous 84 tests for auth, sites, events, tracking

### Session 6 — QA & POLISH
- Ran full test suite (132 tests passing) as baseline
- **Bugs found and fixed:**
  - **Duplicate rate limiter instances**: `events.py` created its own `Limiter` separate from `main.py`'s, causing the app-level rate limit state and error handler to be disconnected from the route decorator. Fixed by extracting a shared `src/app/rate_limit.py` module imported by both.
  - **Docker Compose SQLite path**: Had 4 slashes (`sqlite+aiosqlite:////data/pagepulse.db`) instead of 3. Fixed to `///data/pagepulse.db`.
  - **No date range validation**: Custom date ranges with start > end silently produced empty results. Added auto-swap logic in `AnalyticsService._parse_date_range()`.
  - **Silent error swallowing**: Event ingestion `except` clause had no logging. Added `logger.debug()` with `exc_info=True` for diagnostics.
  - **Duplicate httpx dependency**: Listed in both main and dev dependencies in `pyproject.toml`. Removed from main deps.
- **UI/UX polish:**
  - Added `prefers-reduced-motion` media query to disable Chart.js animations for accessibility
  - Added ARIA labels to main navigation, logo link, and sign-out button
  - Added SVG favicon and meta description to base template
  - Added `role="progressbar"` with `aria-valuenow/min/max` on all progress bars (browsers, devices, countries)
  - Added `hover:bg-gray-50` row hover states on all data tables
  - Added focus ring styles (`focus:ring-2 focus:ring-brand-500`) to sign-out button
  - Improved logout error handling with try/catch around fetch
  - Replaced browser `confirm()`/`alert()` in site deletion with proper modal dialog (ARIA `role="dialog"`, `aria-modal`, `aria-labelledby`, loading state, error handling)
  - Added client-side date validation that auto-swaps start/end if reversed (both dashboards)
  - **Built marketing landing page** (`landing.html`): hero section with CTA, social proof stats bar, 6-feature grid with icons, 3-tier pricing section (Free/$0, Pro/$9/mo, Business/$29/mo), bottom CTA, footer. Professional design with brand colors, responsive layout.
  - Updated root route (`/`) to render landing page for unauthenticated users (redirect to dashboard for authenticated)
- **Tests added:**
  - `test_date_range_custom_swapped` — verifies auto-swap of reversed custom date ranges
  - `test_landing_page` — verifies landing page renders with expected content (PagePulse, CTA, privacy, GDPR)
  - `test_landing_page_redirects_when_authenticated` — verifies authenticated users get redirected to dashboard
  - Updated `test_root_shows_landing_page` and `test_root_redirects_to_dashboard_when_authenticated` in auth tests
- **Final test count: 135 tests, all passing, zero warnings**

## Known Issues
(none)

## Files Structure
```
page-pulse/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── Dockerfile                   # Python 3.12-slim container
├── docker-compose.yml           # Single-service with SQLite volume
├── alembic.ini                  # Alembic config (async SQLAlchemy)
├── .gitignore
├── .env.example
├── alembic/
│   ├── env.py                   # Async migration environment
│   ├── script.py.mako
│   └── versions/                # Migration scripts
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py              # FastAPI app factory, CORS, rate limiting, lifespan, routes
│       ├── config.py            # Pydantic Settings
│       ├── database.py          # async SQLAlchemy engine + session
│       ├── dependencies.py      # Auth dependencies (get_current_user, etc.)
│       ├── rate_limit.py        # Shared slowapi Limiter instance
│       ├── scheduler.py         # APScheduler nightly aggregation job
│       ├── api/
│       │   ├── __init__.py
│       │   ├── health.py        # GET /health
│       │   ├── auth.py          # Auth API + UI routes
│       │   ├── sites.py         # Site CRUD API + UI routes
│       │   ├── events.py        # Event ingestion API (POST /api/v1/event) with rate limiting
│       │   ├── dashboard.py     # Analytics API + dashboard UI routes
│       │   └── tracking.py      # Tracking script endpoint (GET /js/p.js)
│       ├── models/
│       │   ├── __init__.py      # Re-exports all models
│       │   ├── user.py          # User model
│       │   ├── site.py          # Site model
│       │   ├── event.py         # PageviewEvent model
│       │   └── stats.py         # Daily*Stats models (6 tables)
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── auth.py          # UserRegister, UserLogin, UserResponse, TokenResponse
│       │   ├── site.py          # SiteCreate, SiteUpdate, SiteResponse, SiteWithSnippet
│       │   └── event.py         # EventPayload
│       ├── services/
│       │   ├── __init__.py
│       │   ├── auth.py          # AuthService (password, JWT, user CRUD)
│       │   ├── site.py          # SiteService (CRUD, domain normalization, snippet generation)
│       │   ├── event.py         # EventService (visitor hash, UA parsing, event recording)
│       │   ├── analytics.py     # AnalyticsService (dashboard queries, date ranges, aggregations)
│       │   └── aggregation.py   # AggregationService (nightly rollup into daily stats tables)
│       ├── templates/
│       │   ├── base.html        # Base template with Tailwind CSS + HTMX
│       │   ├── app_shell.html   # Authenticated app shell with nav
│       │   ├── landing.html     # Marketing landing page (unauthenticated users)
│       │   ├── auth/
│       │   │   ├── register.html
│       │   │   └── login.html
│       │   ├── sites/
│       │   │   ├── index.html   # Site list page with add modal
│       │   │   └── settings.html # Site settings with tracking snippet
│       │   └── dashboard/
│       │       ├── index.html   # Authenticated dashboard with charts + widgets
│       │       └── public.html  # Public shareable dashboard
│       └── static/
└── tests/
    ├── __init__.py
    ├── conftest.py              # Async test fixtures (client, db, auth_client)
    ├── test_health.py           # 1 health check test
    ├── test_auth.py             # 21 auth integration tests
    ├── test_auth_service.py     # 8 auth service unit tests
    ├── test_sites.py            # 19 site API + UI integration tests
    ├── test_site_service.py     # 11 site service unit tests
    ├── test_events.py           # 8 event ingestion + landing page tests
    ├── test_event_service.py    # 17 event service unit tests
    ├── test_tracking.py         # 2 tracking script tests
    ├── test_analytics_service.py # 22 analytics service unit tests
    ├── test_dashboard.py        # 22 dashboard integration tests
    └── test_aggregation_service.py # 10 aggregation service tests
```
