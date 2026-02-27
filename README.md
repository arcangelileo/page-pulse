# PagePulse

**Privacy-first website analytics.** A lightweight, cookie-free alternative to Google Analytics that gives website owners clear insights into their traffic without compromising visitor privacy.

No cookies. No fingerprinting. No personal data. GDPR/CCPA compliant by default — no cookie banner needed.

Add a single `<script>` tag to your website and get page views, unique visitors, referrers, top pages, devices, browsers, countries, and UTM campaign tracking in a beautiful, fast dashboard.

---

## Features

- **Privacy by design** — Cookie-free, fingerprint-free visitor counting using daily-rotating salted hashes (same approach as [Plausible Analytics](https://plausible.io/data-policy)). IP addresses are never stored.
- **Tiny tracking script** — ~700 bytes minified. Uses `navigator.sendBeacon` with XHR fallback. Handles SPA navigation out of the box.
- **Beautiful dashboard** — Pageviews, unique visitors, bounce rate, top pages, referrers, browsers, devices, countries, and UTM campaign tracking with interactive Chart.js visualizations.
- **Date range filtering** — Today, last 7 days, last 30 days, or any custom date range.
- **Public dashboards** — Toggle per-site shareable links for transparent analytics.
- **Multi-site management** — Track multiple websites from a single account.
- **Background aggregation** — Nightly rollup of raw events into optimized daily summary tables for fast queries at any scale.
- **Rate limiting** — Built-in request throttling on the event ingestion endpoint (60 req/min per IP).
- **One-line install** — A single `<script>` tag is all you need on your website.
- **GDPR/CCPA compliant** — No cookie banner required. No personal data collected.

---

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/arcangelileo/page-pulse.git && cd page-pulse
cp .env.example .env

# Generate secrets (required)
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32)); print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env

docker compose up -d
# PagePulse is running at http://localhost:8000
```

The container automatically runs database migrations on startup, creates a non-root user, and includes a health check.

### Local Development

```bash
# Clone and enter the project
git clone https://github.com/arcangelileo/page-pulse.git
cd page-pulse

# Create a virtual environment and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Set up the database
alembic upgrade head

# Start the development server (with hot reload)
uvicorn app.main:app --reload --app-dir src

# App is running at http://localhost:8000
```

### Run Tests

```bash
pytest                   # Run all 135 tests
pytest -v                # Verbose output
pytest --cov=app         # With coverage report
```

---

## Usage

### 1. Create an Account

Navigate to `http://localhost:8000/register` and create your account.

### 2. Add a Website

After logging in, click **Add site** and enter your website's name and domain (e.g., `example.com`).

### 3. Install the Tracking Script

Go to **Site Settings** and copy the tracking snippet. Paste it into the `<head>` of every page on your website:

```html
<script defer src="https://your-pagepulse-host/js/p.js" data-site="YOUR_SITE_ID"></script>
```

**What the script collects:**
- Page URL and path
- Referrer URL (external only — self-referrals are filtered)
- Screen width (for device classification: desktop/mobile/tablet)
- UTM parameters (`utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`)

**What it does NOT collect:**
- Cookies or local storage data
- IP addresses (used transiently for the daily visitor hash, then discarded)
- Browser fingerprints
- Any personal or identifiable data

### 4. View Your Analytics

Click **Dashboard** on any site to see real-time analytics:

| Widget | Description |
|--------|-------------|
| **Pageviews** | Total page loads in the selected period |
| **Unique Visitors** | Distinct visitors (daily-rotating hash) |
| **Bounce Rate** | Percentage of single-page visits |
| **Visitors Over Time** | Line chart of daily visitors and pageviews |
| **Top Pages** | Most visited pages ranked by views |
| **Top Referrers** | Traffic sources driving the most visitors |
| **Browsers** | Chrome, Firefox, Safari, Edge, etc. |
| **Devices** | Desktop, mobile, tablet breakdown |
| **Countries** | Visitor geography (from CDN geo headers) |
| **UTM Campaigns** | Campaign tracking with source/medium/campaign |

### 5. Share Your Dashboard (Optional)

In **Site Settings**, toggle **Public dashboard** to create a shareable link anyone can view without logging in.

---

## Configuration

All configuration is via environment variables. Copy `.env.example` to `.env` and customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `PagePulse` | Application display name |
| `APP_ENV` | `development` | `development` or `production` |
| `DEBUG` | `true` | Enable debug mode (disable in prod) |
| `SECRET_KEY` | — | Salt for privacy-preserving visitor hashes |
| `JWT_SECRET_KEY` | — | Secret for signing JWT auth tokens |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token lifetime in minutes (default 24h) |
| `DATABASE_URL` | `sqlite+aiosqlite:///./pagepulse.db` | Database connection string |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server bind port |

### Production Checklist

- [ ] Set `APP_ENV=production` and `DEBUG=false`
- [ ] Generate cryptographically random `SECRET_KEY` and `JWT_SECRET_KEY`:
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [ ] Use a persistent volume for the SQLite database (Docker Compose handles this automatically)
- [ ] Place behind a reverse proxy (nginx, Caddy) with HTTPS for secure cookie handling

---

## API Reference

All API endpoints return JSON. Authentication uses JWT tokens stored in httponly cookies.

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/auth/register` | No | Create a new account |
| `POST` | `/api/v1/auth/login` | No | Sign in and receive JWT cookie |
| `POST` | `/api/v1/auth/logout` | Yes | Clear auth cookie |
| `GET` | `/api/v1/auth/me` | Yes | Get current user info |

**Register:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "yourpassword", "name": "Your Name"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email": "you@example.com", "password": "yourpassword"}'
```

### Sites

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/sites` | Yes | Create a new site |
| `GET` | `/api/v1/sites` | Yes | List all your sites |
| `GET` | `/api/v1/sites/{id}` | Yes | Get site details + tracking snippet |
| `PATCH` | `/api/v1/sites/{id}` | Yes | Update site settings |
| `DELETE` | `/api/v1/sites/{id}` | Yes | Delete a site and its data |

**Create a site:**
```bash
curl -X POST http://localhost:8000/api/v1/sites \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"name": "My Website", "domain": "example.com"}'
```

### Analytics

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/sites/{id}/analytics` | Yes | Dashboard data for a site |
| `GET` | `/api/v1/public/{id}/analytics` | No | Public dashboard data (if enabled) |

Query parameters: `period` (`today`, `7d`, `30d`, `custom`), `start` and `end` (`YYYY-MM-DD` format, for custom ranges).

```bash
curl http://localhost:8000/api/v1/sites/{id}/analytics?period=7d \
  -b cookies.txt
```

### Event Ingestion

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/event` | No | Record a pageview event |

This endpoint is called by the tracking script. It accepts cross-origin requests and is rate-limited to 60 requests/minute per IP.

```bash
curl -X POST http://localhost:8000/api/v1/event \
  -H "Content-Type: application/json" \
  -d '{"s": "site-uuid", "u": "https://example.com/page", "r": "https://google.com"}'
```

### Utility

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/js/p.js` | No | Serve the tracking script |
| `GET` | `/health` | No | Health check (returns `{"status": "ok"}`) |

---

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────┐
│  Website     │────▸│  POST /api/v1/   │────▸│  SQLite DB    │
│  (tracking   │     │  event           │     │               │
│   script)    │     │  (rate-limited)  │     │  Raw events   │
└─────────────┘     └──────────────────┘     │  Daily stats  │
                                              │  Users/Sites  │
┌─────────────┐     ┌──────────────────┐     │               │
│  Dashboard   │◂───│  Analytics       │◂────│               │
│  (Jinja2 +   │    │  Service         │     └───────────────┘
│   Chart.js)  │    └──────────────────┘            ▲
└─────────────┘                                     │
                    ┌──────────────────┐              │
                    │  APScheduler     │──────────────┘
                    │  (00:15 UTC)     │  Aggregates raw events
                    └──────────────────┘  into daily rollups
```

### How Privacy-Preserving Visitor Counting Works

PagePulse counts unique visitors without cookies or fingerprinting:

1. A **daily salt** is derived from `SECRET_KEY` + today's date (changes every 24 hours at midnight UTC).
2. When a pageview arrives, a **visitor hash** is computed: `SHA-256(salt + site_id + IP + User-Agent)`.
3. The hash is stored with the event — the raw IP address is **never** persisted.
4. Because the salt changes daily, the same visitor produces a **different hash** each day, making cross-day tracking impossible.

This is the same approach used by [Plausible Analytics](https://plausible.io/data-policy).

### Data Flow

- **Real-time**: Raw `PageviewEvent` records are written to the database on every request.
- **Nightly**: APScheduler runs at 00:15 UTC and aggregates the previous day's raw events into 6 summary tables (`DailyPageStats`, `DailyReferrerStats`, `DailyBrowserStats`, `DailyDeviceStats`, `DailyCountryStats`, `DailyUTMStats`).
- **Queries**: Dashboard queries read from raw events for the selected date range. Aggregate tables provide fast historical lookups for high-traffic deployments.

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Python 3.12, FastAPI (async) |
| Database | SQLite via aiosqlite + SQLAlchemy 2.0 |
| Migrations | Alembic (async, auto-run on container start) |
| Templates | Jinja2 + Tailwind CSS (CDN) + HTMX |
| Charts | Chart.js |
| Auth | JWT (httponly cookies) + bcrypt |
| Background Jobs | APScheduler (async) |
| Rate Limiting | slowapi |
| Container | Docker (multi-stage build, non-root user) |

---

## Project Structure

```
page-pulse/
├── Dockerfile                    # Multi-stage production build
├── docker-entrypoint.sh          # Runs migrations then starts uvicorn
├── docker-compose.yml            # Single-service with SQLite volume
├── pyproject.toml                # Dependencies and build config
├── alembic.ini                   # Migration configuration
├── .env.example                  # Environment variable template
├── alembic/
│   ├── env.py                    # Async migration environment
│   └── versions/                 # Migration scripts
├── src/app/
│   ├── main.py                   # App factory, middleware, lifespan
│   ├── config.py                 # Pydantic Settings
│   ├── database.py               # Async SQLAlchemy engine + session
│   ├── dependencies.py           # Auth dependency injection
│   ├── rate_limit.py             # Shared rate limiter instance
│   ├── scheduler.py              # APScheduler nightly cron
│   ├── api/
│   │   ├── auth.py               # Auth API + UI routes
│   │   ├── sites.py              # Site CRUD API + UI routes
│   │   ├── events.py             # Event ingestion (POST /api/v1/event)
│   │   ├── dashboard.py          # Analytics API + dashboard UI
│   │   ├── tracking.py           # Tracking script endpoint
│   │   └── health.py             # Health check
│   ├── models/                   # SQLAlchemy models (10 tables)
│   ├── schemas/                  # Pydantic request/response schemas
│   ├── services/
│   │   ├── auth.py               # Password hashing, JWT, user CRUD
│   │   ├── site.py               # Site CRUD, domain normalization
│   │   ├── event.py              # Visitor hash, UA parsing, ingestion
│   │   ├── analytics.py          # Dashboard queries, date ranges
│   │   └── aggregation.py        # Nightly rollup into daily stats
│   └── templates/                # Jinja2 HTML templates
└── tests/                        # 135 tests (pytest-asyncio)
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Make your changes
5. Run tests: `pytest`
6. Run linter: `ruff check src/ tests/`
7. Commit and push: `git push origin feature/my-feature`
8. Open a Pull Request

---

## License

MIT
