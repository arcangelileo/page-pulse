import pytest


@pytest.mark.asyncio
async def test_tracking_script_served(client):
    resp = await client.get("/js/p.js")
    assert resp.status_code == 200
    assert "application/javascript" in resp.headers["content-type"]
    body = resp.text
    assert "data-site" in body
    assert "/api/v1/event" in body
    assert "sendBeacon" in body


@pytest.mark.asyncio
async def test_tracking_script_cache_headers(client):
    resp = await client.get("/js/p.js")
    assert "max-age" in resp.headers.get("cache-control", "")
