import pytest
from datetime import date, timedelta

from sqlalchemy import select

from app.models.stats import (
    DailyBrowserStats,
    DailyCountryStats,
    DailyDeviceStats,
    DailyPageStats,
    DailyReferrerStats,
    DailyUTMStats,
)
from app.services.aggregation import AggregationService
from app.services.auth import AuthService
from app.services.event import EventService
from app.services.site import SiteService


async def _seed_events(db):
    """Create a user, site, and seed events for aggregation testing."""
    user = await AuthService.create_user(db, "Test", "agg@test.com", "pass1234")
    site = await SiteService.create_site(db, user.id, "Agg Test", "aggtest.com")
    await db.commit()

    events = [
        {
            "visitor_hash": "v1",
            "path": "/",
            "referrer_domain": "google.com",
            "browser": "Chrome",
            "os": "Windows",
            "device_type": "desktop",
            "country_code": "US",
            "utm_source": "twitter",
            "utm_medium": "social",
            "utm_campaign": "launch",
        },
        {
            "visitor_hash": "v1",
            "path": "/about",
            "referrer_domain": None,
            "browser": "Chrome",
            "os": "Windows",
            "device_type": "desktop",
            "country_code": "US",
            "utm_source": None,
            "utm_medium": None,
            "utm_campaign": None,
        },
        {
            "visitor_hash": "v2",
            "path": "/",
            "referrer_domain": "twitter.com",
            "browser": "Firefox",
            "os": "Linux",
            "device_type": "desktop",
            "country_code": "DE",
            "utm_source": None,
            "utm_medium": None,
            "utm_campaign": None,
        },
        {
            "visitor_hash": "v3",
            "path": "/pricing",
            "referrer_domain": "google.com",
            "browser": "Safari",
            "os": "macOS",
            "device_type": "desktop",
            "country_code": "GB",
            "utm_source": None,
            "utm_medium": None,
            "utm_campaign": None,
        },
        {
            "visitor_hash": "v4",
            "path": "/",
            "referrer_domain": None,
            "browser": "Chrome",
            "os": "Android",
            "device_type": "mobile",
            "country_code": "US",
            "utm_source": None,
            "utm_medium": None,
            "utm_campaign": None,
        },
    ]

    for ev in events:
        await EventService.record_event(
            db=db,
            site_id=site.id,
            visitor_hash=ev["visitor_hash"],
            url=f"https://aggtest.com{ev['path']}",
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
async def test_aggregate_day_creates_page_stats(db):
    user, site = await _seed_events(db)
    today = date.today()
    stats = await AggregationService.aggregate_day(db, today)
    assert stats["sites_processed"] == 1
    assert stats["pages"] == 3  # /, /about, /pricing

    result = await db.execute(
        select(DailyPageStats)
        .where(DailyPageStats.site_id == site.id, DailyPageStats.date == today)
        .order_by(DailyPageStats.pageviews.desc())
    )
    rows = result.scalars().all()
    assert len(rows) == 3
    assert rows[0].path == "/"
    assert rows[0].pageviews == 3
    assert rows[0].unique_visitors == 3


@pytest.mark.asyncio
async def test_aggregate_day_creates_referrer_stats(db):
    user, site = await _seed_events(db)
    today = date.today()
    stats = await AggregationService.aggregate_day(db, today)
    assert stats["referrers"] == 2  # google.com, twitter.com

    result = await db.execute(
        select(DailyReferrerStats)
        .where(DailyReferrerStats.site_id == site.id, DailyReferrerStats.date == today)
        .order_by(DailyReferrerStats.pageviews.desc())
    )
    rows = result.scalars().all()
    assert len(rows) == 2
    assert rows[0].referrer_domain == "google.com"
    assert rows[0].pageviews == 2


@pytest.mark.asyncio
async def test_aggregate_day_creates_browser_stats(db):
    user, site = await _seed_events(db)
    today = date.today()
    stats = await AggregationService.aggregate_day(db, today)
    assert stats["browsers"] == 3  # Chrome, Firefox, Safari

    result = await db.execute(
        select(DailyBrowserStats)
        .where(DailyBrowserStats.site_id == site.id, DailyBrowserStats.date == today)
        .order_by(DailyBrowserStats.pageviews.desc())
    )
    rows = result.scalars().all()
    assert len(rows) == 3
    assert rows[0].browser == "Chrome"
    assert rows[0].pageviews == 3


@pytest.mark.asyncio
async def test_aggregate_day_creates_device_stats(db):
    user, site = await _seed_events(db)
    today = date.today()
    stats = await AggregationService.aggregate_day(db, today)
    assert stats["devices"] == 2  # desktop, mobile

    result = await db.execute(
        select(DailyDeviceStats)
        .where(DailyDeviceStats.site_id == site.id, DailyDeviceStats.date == today)
        .order_by(DailyDeviceStats.pageviews.desc())
    )
    rows = result.scalars().all()
    assert len(rows) == 2
    assert rows[0].device_type == "desktop"
    assert rows[0].pageviews == 4


@pytest.mark.asyncio
async def test_aggregate_day_creates_country_stats(db):
    user, site = await _seed_events(db)
    today = date.today()
    stats = await AggregationService.aggregate_day(db, today)
    assert stats["countries"] == 3  # US, DE, GB

    result = await db.execute(
        select(DailyCountryStats)
        .where(DailyCountryStats.site_id == site.id, DailyCountryStats.date == today)
        .order_by(DailyCountryStats.pageviews.desc())
    )
    rows = result.scalars().all()
    assert len(rows) == 3
    assert rows[0].country_code == "US"
    assert rows[0].pageviews == 3


@pytest.mark.asyncio
async def test_aggregate_day_creates_utm_stats(db):
    user, site = await _seed_events(db)
    today = date.today()
    stats = await AggregationService.aggregate_day(db, today)
    assert stats["utms"] == 1

    result = await db.execute(
        select(DailyUTMStats)
        .where(DailyUTMStats.site_id == site.id, DailyUTMStats.date == today)
    )
    rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].utm_source == "twitter"
    assert rows[0].utm_medium == "social"
    assert rows[0].utm_campaign == "launch"
    assert rows[0].pageviews == 1


@pytest.mark.asyncio
async def test_aggregate_day_is_idempotent(db):
    """Running aggregation twice for the same day should not duplicate data."""
    user, site = await _seed_events(db)
    today = date.today()

    stats1 = await AggregationService.aggregate_day(db, today)
    stats2 = await AggregationService.aggregate_day(db, today)

    # Counts should be the same both times
    assert stats1["pages"] == stats2["pages"]

    # Should not have duplicated rows
    result = await db.execute(
        select(DailyPageStats).where(
            DailyPageStats.site_id == site.id, DailyPageStats.date == today
        )
    )
    assert len(result.scalars().all()) == 3


@pytest.mark.asyncio
async def test_aggregate_day_no_events(db):
    """Aggregation should handle a day with no events gracefully."""
    user = await AuthService.create_user(db, "Test", "noevents@test.com", "pass1234")
    site = await SiteService.create_site(db, user.id, "Empty", "empty.com")
    await db.commit()

    stats = await AggregationService.aggregate_day(db, date.today())
    assert stats["sites_processed"] == 0
    assert stats["pages"] == 0


@pytest.mark.asyncio
async def test_aggregate_yesterday(db):
    """aggregate_yesterday should target yesterday's date."""
    # No events exist for yesterday, so should process 0 sites
    stats = await AggregationService.aggregate_yesterday(db)
    assert stats["sites_processed"] == 0


@pytest.mark.asyncio
async def test_backfill(db):
    """Backfill should process a range of dates."""
    today = date.today()
    stats = await AggregationService.backfill(db, today - timedelta(days=2), today)
    assert stats["days_processed"] == 3
