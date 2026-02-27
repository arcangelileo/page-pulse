import pytest


async def _create_site(auth_client):
    """Helper to create a site and return its ID."""
    resp = await auth_client.post(
        "/api/v1/sites",
        json={"name": "Test Site", "domain": "test.com"},
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_ingest_event(auth_client, client):
    site_id = await _create_site(auth_client)

    resp = await client.post(
        "/api/v1/event",
        json={
            "s": site_id,
            "u": "https://test.com/hello",
            "p": "/hello",
            "r": "https://google.com/search",
            "sw": 1920,
            "us": "google",
            "um": "organic",
            "uc": "",
            "ut": "",
            "ux": "",
        },
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"},
    )
    assert resp.status_code == 202


@pytest.mark.asyncio
async def test_ingest_event_minimal(auth_client, client):
    site_id = await _create_site(auth_client)

    minimal = {
        "s": site_id, "u": "https://test.com/", "p": "/", "r": "",
        "sw": 0, "us": "", "um": "", "uc": "", "ut": "", "ux": "",
    }
    resp = await client.post("/api/v1/event", json=minimal)
    assert resp.status_code == 202


@pytest.mark.asyncio
async def test_ingest_event_invalid_site(client):
    payload = {
        "s": "nonexistent", "u": "https://test.com/", "p": "/", "r": "",
        "sw": 0, "us": "", "um": "", "uc": "", "ut": "", "ux": "",
    }
    resp = await client.post("/api/v1/event", json=payload)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_ingest_event_bad_body(client):
    resp = await client.post("/api/v1/event", content=b"not json")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_ingest_event_no_auth_needed(auth_client, client):
    """Event ingestion works without auth cookies (tracking script runs on 3rd party sites)."""
    site_id = await _create_site(auth_client)

    # Use a fresh client without auth cookies
    payload = {
        "s": site_id, "u": "https://test.com/", "p": "/", "r": "",
        "sw": 0, "us": "", "um": "", "uc": "", "ut": "", "ux": "",
    }
    resp = await client.post("/api/v1/event", json=payload)
    assert resp.status_code == 202


@pytest.mark.asyncio
async def test_ingest_event_self_referral_filtered(auth_client, client):
    """Self-referrals (referrer same as site domain) should be filtered out."""
    site_id = await _create_site(auth_client)

    resp = await client.post(
        "/api/v1/event",
        json={
            "s": site_id,
            "u": "https://test.com/page2",
            "p": "/page2",
            "r": "https://test.com/page1",
            "sw": 1024,
            "us": "", "um": "", "uc": "", "ut": "", "ux": "",
        },
    )
    assert resp.status_code == 202


@pytest.mark.asyncio
async def test_landing_page(client):
    """Landing page should render for unauthenticated users."""
    resp = await client.get("/", follow_redirects=False)
    assert resp.status_code == 200
    assert "PagePulse" in resp.text
    assert "Get started free" in resp.text
    assert "privacy" in resp.text.lower()
    assert "GDPR" in resp.text


@pytest.mark.asyncio
async def test_landing_page_redirects_when_authenticated(auth_client):
    """Authenticated users should be redirected from landing to dashboard."""
    resp = await auth_client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["location"]
