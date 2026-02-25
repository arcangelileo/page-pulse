# PagePulse

Phase: DEVELOPMENT

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
- [ ] Create database models (User, Site, PageviewEvent, DailyPageStats, DailyReferrerStats, DailyBrowserStats, DailyDeviceStats, DailyCountryStats, DailyUTMStats)
- [ ] Set up Alembic and create initial migration
- [ ] Implement user auth (register, login, logout, get current user) with JWT httponly cookies
- [ ] Implement site management CRUD (create, list, update, delete sites; generate tracking snippet)
- [ ] Build the tracking JavaScript snippet (lightweight, cookie-free pageview collection)
- [ ] Implement event ingestion API (receive pageviews, extract metadata, geolocate IP, compute visitor hash, store events)
- [ ] Build analytics query service (aggregate stats by date range, top pages, referrers, countries, browsers, devices, UTMs)
- [ ] Build the analytics dashboard UI (main dashboard with charts, date picker, site switcher)
- [ ] Implement public shareable dashboard feature
- [ ] Add background aggregation job (nightly rollup of raw events into daily summary tables)
- [ ] Add rate limiting to event ingestion endpoint
- [ ] Write comprehensive tests (auth, sites, event ingestion, analytics queries, aggregation)
- [ ] Write Dockerfile and docker-compose.yml
- [ ] Write README with setup, deployment, and usage instructions

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

## Known Issues
(none yet)

## Files Structure
```
page-pulse/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── .gitignore
├── .env.example
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py              # FastAPI app factory, CORS, lifespan
│       ├── config.py            # Pydantic Settings
│       ├── database.py          # async SQLAlchemy engine + session
│       ├── api/
│       │   ├── __init__.py
│       │   └── health.py        # GET /health
│       ├── models/
│       │   └── __init__.py
│       ├── schemas/
│       │   └── __init__.py
│       ├── services/
│       │   └── __init__.py
│       ├── templates/
│       └── static/
└── tests/
    ├── __init__.py
    ├── conftest.py              # async test client fixture
    └── test_health.py           # health check test
```
