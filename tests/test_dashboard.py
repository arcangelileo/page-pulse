import pytest


async def _create_site(auth_client, name="Test Site", domain="test.com"):
    """Helper to create a site and return its ID."""
    resp = await auth_client.post(
        "/api/v1/sites",
        json={"name": name, "domain": domain},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _make_site_public(auth_client, site_id):
    """Toggle a site to public."""
    resp = await auth_client.patch(
        f"/api/v1/sites/{site_id}",
        json={"public": True},
    )
    assert resp.status_code == 200


async def _ingest_event(client, site_id, path="/", referrer=""):
    """Ingest a pageview event for a site."""
    resp = await client.post(
        "/api/v1/event",
        json={"s": site_id, "u": f"https://test.com{path}", "p": path, "r": referrer, "sw": 1920, "us": "", "um": "", "uc": "", "ut": "", "ux": ""},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"},
    )
    assert resp.status_code == 202


# --- Dashboard UI Tests ---


@pytest.mark.asyncio
async def test_dashboard_page_loads(auth_client):
    site_id = await _create_site(auth_client)
    resp = await auth_client.get(f"/dashboard/{site_id}")
    assert resp.status_code == 200
    body = resp.text
    assert "Test Site" in body
    assert "Pageviews" in body
    assert "Unique visitors" in body
    assert "Bounce rate" in body
    assert "visitors-chart" in body


@pytest.mark.asyncio
async def test_dashboard_page_with_data(auth_client, client):
    site_id = await _create_site(auth_client)
    await _ingest_event(client, site_id, "/")
    await _ingest_event(client, site_id, "/about")
    await _ingest_event(client, site_id, "/pricing")

    resp = await auth_client.get(f"/dashboard/{site_id}?period=today")
    assert resp.status_code == 200
    body = resp.text
    assert "Top pages" in body
    # Chart data should be present
    assert "visitors_over_time" in body or "chartData" in body


@pytest.mark.asyncio
async def test_dashboard_page_date_periods(auth_client):
    site_id = await _create_site(auth_client)

    for period in ["today", "7d", "30d"]:
        resp = await auth_client.get(f"/dashboard/{site_id}?period={period}")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_page_custom_period(auth_client):
    site_id = await _create_site(auth_client)
    resp = await auth_client.get(
        f"/dashboard/{site_id}?period=custom&start=2025-01-01&end=2025-01-31"
    )
    assert resp.status_code == 200
    assert "2025-01-01" in resp.text
    assert "2025-01-31" in resp.text


@pytest.mark.asyncio
async def test_dashboard_page_requires_auth(client):
    resp = await client.get("/dashboard/some-id", follow_redirects=False)
    # Should redirect to login
    assert resp.status_code in (302, 401, 403)


@pytest.mark.asyncio
async def test_dashboard_page_wrong_user(auth_client, app):
    site_id = await _create_site(auth_client)

    # Create a second user
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client2:
        resp = await client2.post(
            "/api/v1/auth/register",
            json={"name": "Other", "email": "other@test.com", "password": "pass1234"},
        )
        assert resp.status_code == 201
        client2.cookies.set("access_token", resp.cookies.get("access_token"))

        resp = await client2.get(f"/dashboard/{site_id}")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_page_not_found(auth_client):
    resp = await auth_client.get("/dashboard/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_site_switcher(auth_client):
    """Dashboard should show all user's sites in the site switcher."""
    site1_id = await _create_site(auth_client, "Site Alpha", "alpha.com")
    site2_id = await _create_site(auth_client, "Site Beta", "beta.com")

    resp = await auth_client.get(f"/dashboard/{site1_id}")
    assert resp.status_code == 200
    body = resp.text
    assert "Site Alpha" in body
    assert "Site Beta" in body


# --- Public Dashboard UI Tests ---


@pytest.mark.asyncio
async def test_public_dashboard_page_loads(auth_client, client):
    site_id = await _create_site(auth_client)
    await _make_site_public(auth_client, site_id)

    resp = await client.get(f"/share/{site_id}")
    assert resp.status_code == 200
    body = resp.text
    assert "Test Site" in body
    assert "Public Dashboard" in body
    assert "Pageviews" in body
    assert "visitors-chart" in body


@pytest.mark.asyncio
async def test_public_dashboard_with_data(auth_client, client):
    site_id = await _create_site(auth_client)
    await _make_site_public(auth_client, site_id)
    await _ingest_event(client, site_id, "/")
    await _ingest_event(client, site_id, "/about")

    resp = await client.get(f"/share/{site_id}?period=today")
    assert resp.status_code == 200
    body = resp.text
    assert "Top pages" in body


@pytest.mark.asyncio
async def test_public_dashboard_not_public(auth_client, client):
    """A non-public site should return 404."""
    site_id = await _create_site(auth_client)
    resp = await client.get(f"/share/{site_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_public_dashboard_not_found(client):
    resp = await client.get("/share/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_public_dashboard_date_periods(auth_client, client):
    site_id = await _create_site(auth_client)
    await _make_site_public(auth_client, site_id)

    for period in ["today", "7d", "30d"]:
        resp = await client.get(f"/share/{site_id}?period={period}")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_public_dashboard_no_auth_needed(auth_client, client):
    """Public dashboard should be accessible without any auth."""
    site_id = await _create_site(auth_client)
    await _make_site_public(auth_client, site_id)

    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=client._transport.app)
    async with AsyncClient(transport=transport, base_url="http://test") as fresh_client:
        resp = await fresh_client.get(f"/share/{site_id}")
        assert resp.status_code == 200
        assert "Test Site" in resp.text


# --- Analytics API Tests ---


@pytest.mark.asyncio
async def test_analytics_api_endpoint(auth_client, client):
    site_id = await _create_site(auth_client)
    await _ingest_event(client, site_id, "/")

    resp = await auth_client.get(f"/api/v1/sites/{site_id}/analytics?period=today")
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "visitors_over_time" in data
    assert "top_pages" in data
    assert "site" in data
    assert data["site"]["id"] == site_id
    assert data["summary"]["pageviews"] >= 1


@pytest.mark.asyncio
async def test_analytics_api_requires_auth(client):
    resp = await client.get("/api/v1/sites/someid/analytics")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_analytics_api_wrong_site(auth_client):
    resp = await auth_client.get("/api/v1/sites/nonexistent/analytics")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_public_analytics_api_endpoint(auth_client, client):
    site_id = await _create_site(auth_client)
    await _make_site_public(auth_client, site_id)
    await _ingest_event(client, site_id, "/hello")

    resp = await client.get(f"/api/v1/public/{site_id}/analytics?period=today")
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert data["site"]["id"] == site_id


@pytest.mark.asyncio
async def test_public_analytics_api_not_public(auth_client, client):
    site_id = await _create_site(auth_client)
    resp = await client.get(f"/api/v1/public/{site_id}/analytics")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_public_analytics_api_not_found(client):
    resp = await client.get("/api/v1/public/nonexistent/analytics")
    assert resp.status_code == 404
