from datetime import date, timedelta

import pytest

from app.services.analytics import AnalyticsService
from app.services.auth import AuthService
from app.services.event import EventService
from app.services.site import SiteService


async def _seed_data(db):
    """Create a user, site, and some events for testing."""
    user = await AuthService.create_user(db, "Test", "analytics@test.com", "pass1234")
    site = await SiteService.create_site(db, user.id, "Test Site", "test.com")
    await db.commit()

    # Record several events with different paths, referrers, browsers, etc.
    base = {
        "utm_source": None, "utm_medium": None, "utm_campaign": None,
    }
    events = [
        {
            "visitor_hash": "v1", "path": "/", "referrer_domain": "google.com",
            "browser": "Chrome", "os": "Windows", "device_type": "desktop",
            "country_code": "US",
            "utm_source": "twitter", "utm_medium": "social", "utm_campaign": "launch",
        },
        {
            **base, "visitor_hash": "v1", "path": "/about", "referrer_domain": None,
            "browser": "Chrome", "os": "Windows", "device_type": "desktop",
            "country_code": "US",
        },
        {
            **base, "visitor_hash": "v2", "path": "/", "referrer_domain": "twitter.com",
            "browser": "Firefox", "os": "Linux", "device_type": "desktop",
            "country_code": "DE",
        },
        {
            **base, "visitor_hash": "v3", "path": "/pricing",
            "referrer_domain": "google.com", "browser": "Safari", "os": "macOS",
            "device_type": "desktop", "country_code": "GB",
        },
        {
            **base, "visitor_hash": "v4", "path": "/", "referrer_domain": None,
            "browser": "Chrome", "os": "Android", "device_type": "mobile",
            "country_code": "US",
        },
    ]

    for ev in events:
        await EventService.record_event(
            db=db,
            site_id=site.id,
            visitor_hash=ev["visitor_hash"],
            url=f"https://test.com{ev['path']}",
            path=ev["path"],
            referrer=f"https://{ev['referrer_domain']}/" if ev["referrer_domain"] else None,
            referrer_domain=ev["referrer_domain"],
            browser=ev["browser"],
            os=ev["os"],
            device_type=ev["device_type"],
            screen_width=1920,
            country_code=ev["country_code"],
            utm_source=ev["utm_source"],
            utm_medium=ev["utm_medium"],
            utm_campaign=ev["utm_campaign"],
            utm_term=None,
            utm_content=None,
        )
    await db.commit()
    return user, site


@pytest.mark.asyncio
async def test_date_range_today():
    s, e = AnalyticsService._date_range("today")
    assert s == date.today()
    assert e == date.today()


@pytest.mark.asyncio
async def test_date_range_7d():
    s, e = AnalyticsService._date_range("7d")
    assert e == date.today()
    assert s == date.today() - timedelta(days=6)


@pytest.mark.asyncio
async def test_date_range_30d():
    s, e = AnalyticsService._date_range("30d")
    assert e == date.today()
    assert s == date.today() - timedelta(days=29)


@pytest.mark.asyncio
async def test_date_range_custom():
    s, e = AnalyticsService._date_range("custom", "2025-01-01", "2025-01-31")
    assert s == date(2025, 1, 1)
    assert e == date(2025, 1, 31)


@pytest.mark.asyncio
async def test_date_range_custom_invalid():
    s, e = AnalyticsService._date_range("custom", "bad", "data")
    assert e == date.today()
    assert s == date.today() - timedelta(days=6)


@pytest.mark.asyncio
async def test_date_range_custom_swapped():
    """When start > end, dates should be auto-swapped."""
    s, e = AnalyticsService._date_range("custom", "2025-01-31", "2025-01-01")
    assert s == date(2025, 1, 1)
    assert e == date(2025, 1, 31)


@pytest.mark.asyncio
async def test_get_summary(db):
    user, site = await _seed_data(db)
    today = date.today()
    result = await AnalyticsService.get_summary(db, site.id, today, today)
    assert result["pageviews"] == 5
    assert result["unique_visitors"] == 4


@pytest.mark.asyncio
async def test_get_bounce_rate(db):
    user, site = await _seed_data(db)
    today = date.today()
    bounce = await AnalyticsService.get_bounce_rate(db, site.id, today, today)
    # v1 has 2 pageviews (not a bounce), v2, v3, v4 each have 1 (bounces)
    # bounce rate = 3/4 * 100 = 75.0%
    assert bounce == 75.0


@pytest.mark.asyncio
async def test_get_bounce_rate_empty(db):
    user = await AuthService.create_user(db, "Test", "bounce@test.com", "pass1234")
    site = await SiteService.create_site(db, user.id, "Empty", "empty.com")
    await db.commit()
    bounce = await AnalyticsService.get_bounce_rate(db, site.id, date.today(), date.today())
    assert bounce == 0.0


@pytest.mark.asyncio
async def test_get_visitors_over_time(db):
    user, site = await _seed_data(db)
    today = date.today()
    result = await AnalyticsService.get_visitors_over_time(db, site.id, today, today)
    assert len(result) == 1
    assert result[0]["date"] == today.isoformat()
    assert result[0]["pageviews"] == 5
    assert result[0]["unique_visitors"] == 4


@pytest.mark.asyncio
async def test_get_visitors_over_time_fills_missing_days(db):
    user, site = await _seed_data(db)
    today = date.today()
    start = today - timedelta(days=2)
    result = await AnalyticsService.get_visitors_over_time(db, site.id, start, today)
    assert len(result) == 3
    # First two days should have zero data
    assert result[0]["pageviews"] == 0
    assert result[1]["pageviews"] == 0
    assert result[2]["pageviews"] == 5


@pytest.mark.asyncio
async def test_get_top_pages(db):
    user, site = await _seed_data(db)
    today = date.today()
    result = await AnalyticsService.get_top_pages(db, site.id, today, today)
    assert len(result) == 3
    # "/" has 3 pageviews (most), should be first
    assert result[0]["path"] == "/"
    assert result[0]["pageviews"] == 3


@pytest.mark.asyncio
async def test_get_top_referrers(db):
    user, site = await _seed_data(db)
    today = date.today()
    result = await AnalyticsService.get_top_referrers(db, site.id, today, today)
    assert len(result) == 2
    assert result[0]["referrer_domain"] == "google.com"
    assert result[0]["pageviews"] == 2


@pytest.mark.asyncio
async def test_get_browsers(db):
    user, site = await _seed_data(db)
    today = date.today()
    result = await AnalyticsService.get_browsers(db, site.id, today, today)
    assert len(result) == 3
    # Chrome has 3 pageviews (most), should be first
    assert result[0]["browser"] == "Chrome"
    assert result[0]["pageviews"] == 3


@pytest.mark.asyncio
async def test_get_devices(db):
    user, site = await _seed_data(db)
    today = date.today()
    result = await AnalyticsService.get_devices(db, site.id, today, today)
    assert len(result) == 2
    assert result[0]["device_type"] == "desktop"
    assert result[0]["pageviews"] == 4
    assert result[1]["device_type"] == "mobile"


@pytest.mark.asyncio
async def test_get_countries(db):
    user, site = await _seed_data(db)
    today = date.today()
    result = await AnalyticsService.get_countries(db, site.id, today, today)
    assert len(result) == 3
    # US has 3 pageviews (most)
    assert result[0]["country_code"] == "US"
    assert result[0]["pageviews"] == 3


@pytest.mark.asyncio
async def test_get_utm_campaigns(db):
    user, site = await _seed_data(db)
    today = date.today()
    result = await AnalyticsService.get_utm_campaigns(db, site.id, today, today)
    assert len(result) == 1
    assert result[0]["utm_source"] == "twitter"
    assert result[0]["utm_medium"] == "social"
    assert result[0]["utm_campaign"] == "launch"


@pytest.mark.asyncio
async def test_get_full_dashboard(db):
    user, site = await _seed_data(db)
    result = await AnalyticsService.get_full_dashboard(db, site.id, "today")
    assert result["period"] == "today"
    assert result["start_date"] == date.today().isoformat()
    assert result["end_date"] == date.today().isoformat()
    assert result["summary"]["pageviews"] == 5
    assert result["summary"]["unique_visitors"] == 4
    assert result["summary"]["bounce_rate"] == 75.0
    assert len(result["visitors_over_time"]) == 1
    assert len(result["top_pages"]) == 3
    assert len(result["top_referrers"]) == 2
    assert len(result["browsers"]) == 3
    assert len(result["devices"]) == 2
    assert len(result["countries"]) == 3
    assert len(result["utm_campaigns"]) == 1


@pytest.mark.asyncio
async def test_get_full_dashboard_empty(db):
    user = await AuthService.create_user(db, "Test", "empty@test.com", "pass1234")
    site = await SiteService.create_site(db, user.id, "Empty", "empty.com")
    await db.commit()
    result = await AnalyticsService.get_full_dashboard(db, site.id, "7d")
    assert result["summary"]["pageviews"] == 0
    assert result["summary"]["unique_visitors"] == 0
    assert result["summary"]["bounce_rate"] == 0.0
    assert len(result["visitors_over_time"]) == 7
    assert all(d["pageviews"] == 0 for d in result["visitors_over_time"])
