# PagePulse

Privacy-first website analytics platform. A lightweight, cookie-free alternative to Google Analytics.

## Quick Start

```bash
# Install dependencies
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Run the server
uvicorn app.main:app --reload --app-dir src

# Run tests
pytest
```

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy (async), SQLite
- **Frontend**: Jinja2, Tailwind CSS, HTMX, Chart.js
- **Auth**: JWT with httponly cookies
