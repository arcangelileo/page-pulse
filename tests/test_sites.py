import pytest


# --- Create Site ---


@pytest.mark.asyncio
async def test_create_site(auth_client):
    resp = await auth_client.post(
        "/api/v1/sites",
        json={"name": "My Blog", "domain": "myblog.com"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Blog"
    assert data["domain"] == "myblog.com"
    assert data["public"] is False
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_site_normalizes_domain(auth_client):
    resp = await auth_client.post(
        "/api/v1/sites",
        json={"name": "My Site", "domain": "https://www.Example.COM/page"},
    )
    assert resp.status_code == 201
    assert resp.json()["domain"] == "example.com"


@pytest.mark.asyncio
async def test_create_site_unauthenticated(client):
    resp = await client.post(
        "/api/v1/sites",
        json={"name": "My Blog", "domain": "myblog.com"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_site_missing_fields(auth_client):
    resp = await auth_client.post("/api/v1/sites", json={"name": "My Blog"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_site_empty_name(auth_client):
    resp = await auth_client.post(
        "/api/v1/sites", json={"name": "", "domain": "example.com"}
    )
    assert resp.status_code == 422


# --- List Sites ---


@pytest.mark.asyncio
async def test_list_sites_empty(auth_client):
    resp = await auth_client.get("/api/v1/sites")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_sites_returns_owned(auth_client):
    await auth_client.post(
        "/api/v1/sites", json={"name": "Site A", "domain": "a.com"}
    )
    await auth_client.post(
        "/api/v1/sites", json={"name": "Site B", "domain": "b.com"}
    )
    resp = await auth_client.get("/api/v1/sites")
    assert resp.status_code == 200
    sites = resp.json()
    assert len(sites) == 2
    names = {s["name"] for s in sites}
    assert names == {"Site A", "Site B"}


# --- Get Site ---


@pytest.mark.asyncio
async def test_get_site_with_snippet(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/sites", json={"name": "My Site", "domain": "mysite.com"}
    )
    site_id = create_resp.json()["id"]

    resp = await auth_client.get(f"/api/v1/sites/{site_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "My Site"
    assert data["domain"] == "mysite.com"
    assert "tracking_snippet" in data
    assert site_id in data["tracking_snippet"]
    assert "p.js" in data["tracking_snippet"]


@pytest.mark.asyncio
async def test_get_site_not_found(auth_client):
    resp = await auth_client.get("/api/v1/sites/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_site_other_user(auth_client, client):
    # Create site as auth_client user
    create_resp = await auth_client.post(
        "/api/v1/sites", json={"name": "Private", "domain": "private.com"}
    )
    site_id = create_resp.json()["id"]

    # Register a second user
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"name": "Other", "email": "other@example.com", "password": "otherpass123"},
    )
    client.cookies.set("access_token", reg_resp.cookies.get("access_token"))

    # Second user should NOT see first user's site
    resp = await client.get(f"/api/v1/sites/{site_id}")
    assert resp.status_code == 404


# --- Update Site ---


@pytest.mark.asyncio
async def test_update_site(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/sites", json={"name": "Old Name", "domain": "old.com"}
    )
    site_id = create_resp.json()["id"]

    resp = await auth_client.patch(
        f"/api/v1/sites/{site_id}",
        json={"name": "New Name", "domain": "new.com", "public": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "New Name"
    assert data["domain"] == "new.com"
    assert data["public"] is True


@pytest.mark.asyncio
async def test_update_site_partial(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/sites", json={"name": "My Site", "domain": "site.com"}
    )
    site_id = create_resp.json()["id"]

    resp = await auth_client.patch(
        f"/api/v1/sites/{site_id}", json={"public": True}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "My Site"
    assert resp.json()["public"] is True


@pytest.mark.asyncio
async def test_update_site_not_found(auth_client):
    resp = await auth_client.patch(
        "/api/v1/sites/nonexistent", json={"name": "New"}
    )
    assert resp.status_code == 404


# --- Delete Site ---


@pytest.mark.asyncio
async def test_delete_site(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/sites", json={"name": "To Delete", "domain": "delete.com"}
    )
    site_id = create_resp.json()["id"]

    resp = await auth_client.delete(f"/api/v1/sites/{site_id}")
    assert resp.status_code == 204

    # Verify it's gone
    get_resp = await auth_client.get(f"/api/v1/sites/{site_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_site_not_found(auth_client):
    resp = await auth_client.delete("/api/v1/sites/nonexistent")
    assert resp.status_code == 404


# --- UI Routes ---


@pytest.mark.asyncio
async def test_sites_page(auth_client):
    resp = await auth_client.get("/sites")
    assert resp.status_code == 200
    assert "Your Sites" in resp.text


@pytest.mark.asyncio
async def test_sites_page_unauthenticated(client):
    resp = await client.get("/sites", follow_redirects=False)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_site_settings_page(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/sites", json={"name": "Config Site", "domain": "config.com"}
    )
    site_id = create_resp.json()["id"]

    resp = await auth_client.get(f"/sites/{site_id}/settings")
    assert resp.status_code == 200
    assert "Tracking snippet" in resp.text
    assert "config.com" in resp.text
