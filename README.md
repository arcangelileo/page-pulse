# PagePulse

Privacy-first website analytics platform. A lightweight, cookie-free alternative to Google Analytics that gives website owners clear insights into their traffic without compromising visitor privacy.

No cookies, no fingerprinting, no personal data collection — GDPR/CCPA compliant by default, no cookie banner needed.

## Features

- **Privacy-first tracking** — Cookie-free, fingerprint-free visitor counting using daily-rotating salted hashes
- **Lightweight script** — ~700 bytes, uses `sendBeacon` with XHR fallback, SPA-ready
- **Full analytics dashboard** — Pageviews, unique visitors, bounce rate, top pages, referrers, browsers, devices, countries, UTM campaigns
- **Date range picker** — Today, 7 days, 30 days, or custom date range
- **Public shareable dashboards** — Toggle per site for transparency
- **Multi-site management** — Add, edit, delete tracked websites from one account
- **Background aggregation** — Nightly rollup of raw events into daily summary tables for fast queries
- **Rate limiting** — Built-in rate limiting on event ingestion to prevent abuse
- **CORS-ready** — Event ingestion accepts cross-origin requests (tracking script runs on customer sites)

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload --app-dir src

# Run tests
pytest
```

The app will be available at `http://localhost:8000`.

### Docker

```bash
# Build and run with Docker Compose
docker compose up -d

# Or build manually
docker build -t pagepulse .
docker run -p 8000:8000 -v pagepulse-data:/data pagepulse
```

## Configuration

Environment variables (can be set in `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `change-me-...` | Secret key for visitor hash salt |
| `JWT_SECRET_KEY` | `change-me-...` | Secret for JWT token signing |
| `DATABASE_URL` | `sqlite+aiosqlite:///./pagepulse.db` | Database connection string |
| `APP_ENV` | `development` | Environment (development/production) |
| `DEBUG` | `true` | Enable debug mode |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |

## Usage

1. **Register** at `/register` and log in
2. **Add a site** — enter your website name and domain
3. **Install the tracking snippet** — copy the `<script>` tag from site settings and paste it into your website's `<head>`
4. **View analytics** — click "Dashboard" on any site to see real-time analytics
5. **Share publicly** — toggle "Public dashboard" in site settings to create a shareable link

## Tracking Script

The tracking script is served from `/js/p.js` and is ~700 bytes minified. It collects:

- Page URL and path
- Referrer URL
- Screen width
- UTM parameters (source, medium, campaign, term, content)

It does **not** collect or store:

- Cookies
- IP addresses (only used transiently for daily visitor hash, then discarded)
- Browser fingerprints
- Personal data

## Tech Stack

- **Backend**: Python 3.12+, FastAPI (async), SQLAlchemy 2.0 + aiosqlite
- **Frontend**: Jinja2 templates, Tailwind CSS (CDN), HTMX, Chart.js
- **Auth**: JWT with httponly cookies, bcrypt password hashing
- **Background jobs**: APScheduler (nightly aggregation)
- **Rate limiting**: slowapi (limits library)
- **Database**: SQLite (MVP), easily swappable to PostgreSQL
- **Migrations**: Alembic with async support

## API Endpoints

### Auth
- `POST /api/v1/auth/register` — Create account
- `POST /api/v1/auth/login` — Sign in
- `POST /api/v1/auth/logout` — Sign out
- `GET /api/v1/auth/me` — Get current user

### Sites
- `POST /api/v1/sites` — Add a site
- `GET /api/v1/sites` — List your sites
- `GET /api/v1/sites/{id}` — Get site details + tracking snippet
- `PATCH /api/v1/sites/{id}` — Update site settings
- `DELETE /api/v1/sites/{id}` — Delete a site

### Analytics
- `GET /api/v1/sites/{id}/analytics` — Get dashboard data (auth required)
- `GET /api/v1/public/{id}/analytics` — Get public dashboard data (no auth)

### Events
- `POST /api/v1/event` — Ingest a pageview event (no auth, rate limited)

### Other
- `GET /js/p.js` — Serve tracking script
- `GET /health` — Health check

## License

MIT
