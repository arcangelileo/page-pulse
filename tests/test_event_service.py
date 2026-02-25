import pytest

from app.services.event import EventService


def test_visitor_hash_deterministic():
    h1 = EventService.compute_visitor_hash("site1", "1.2.3.4", "Mozilla/5.0")
    h2 = EventService.compute_visitor_hash("site1", "1.2.3.4", "Mozilla/5.0")
    assert h1 == h2


def test_visitor_hash_different_ips():
    h1 = EventService.compute_visitor_hash("site1", "1.2.3.4", "Mozilla/5.0")
    h2 = EventService.compute_visitor_hash("site1", "5.6.7.8", "Mozilla/5.0")
    assert h1 != h2


def test_visitor_hash_different_sites():
    h1 = EventService.compute_visitor_hash("site1", "1.2.3.4", "Mozilla/5.0")
    h2 = EventService.compute_visitor_hash("site2", "1.2.3.4", "Mozilla/5.0")
    assert h1 != h2


def test_visitor_hash_different_ua():
    h1 = EventService.compute_visitor_hash("site1", "1.2.3.4", "Chrome/120")
    h2 = EventService.compute_visitor_hash("site1", "1.2.3.4", "Firefox/121")
    assert h1 != h2


def test_visitor_hash_is_sha256():
    h = EventService.compute_visitor_hash("site1", "1.2.3.4", "UA")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_parse_ua_chrome_windows():
    info = EventService.parse_user_agent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
    assert info["browser"] == "Chrome"
    assert info["os"] == "Windows"
    assert info["device_type"] == "desktop"


def test_parse_ua_safari_mac():
    info = EventService.parse_user_agent(
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    )
    assert info["browser"] == "Safari"
    assert info["os"] == "macOS"
    assert info["device_type"] == "desktop"


def test_parse_ua_firefox_linux():
    info = EventService.parse_user_agent(
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
    )
    assert info["browser"] == "Firefox"
    assert info["os"] == "Linux"
    assert info["device_type"] == "desktop"


def test_parse_ua_mobile_android():
    info = EventService.parse_user_agent(
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
    )
    assert info["browser"] == "Chrome"
    assert info["os"] == "Android"
    assert info["device_type"] == "mobile"


def test_parse_ua_iphone():
    info = EventService.parse_user_agent(
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148"
    )
    assert info["browser"] == "Safari"
    assert info["os"] == "iOS"
    assert info["device_type"] == "mobile"


def test_parse_ua_ipad():
    info = EventService.parse_user_agent(
        "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Safari/605.1"
    )
    assert info["browser"] == "Safari"
    assert info["os"] == "iOS"
    assert info["device_type"] == "tablet"


def test_parse_ua_edge():
    info = EventService.parse_user_agent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36 Edg/120.0"
    )
    assert info["browser"] == "Edge"


def test_parse_ua_empty():
    info = EventService.parse_user_agent("")
    assert info["browser"] == "Unknown"
    assert info["os"] == "Unknown"
    assert info["device_type"] == "desktop"


def test_extract_referrer_domain():
    assert EventService.extract_referrer_domain("https://www.google.com/search?q=test") == "google.com"
    assert EventService.extract_referrer_domain("https://t.co/abc123") == "t.co"
    assert EventService.extract_referrer_domain("") is None
    assert EventService.extract_referrer_domain("https://example.com") == "example.com"


def test_detect_country_from_headers():
    assert EventService.detect_country_from_headers({"cf-ipcountry": "US"}) == "US"
    assert EventService.detect_country_from_headers({"x-country-code": "de"}) == "DE"
    assert EventService.detect_country_from_headers({}) is None


def test_get_client_ip():
    assert EventService.get_client_ip({"x-forwarded-for": "1.2.3.4, 5.6.7.8"}, "10.0.0.1") == "1.2.3.4"
    assert EventService.get_client_ip({"x-real-ip": "9.8.7.6"}, "10.0.0.1") == "9.8.7.6"
    assert EventService.get_client_ip({}, "10.0.0.1") == "10.0.0.1"
    assert EventService.get_client_ip({}, None) == "0.0.0.0"


@pytest.mark.asyncio
async def test_record_event(db):
    from app.services.auth import AuthService
    from app.services.site import SiteService

    user = await AuthService.create_user(db, "Test", "test@test.com", "pass1234")
    site = await SiteService.create_site(db, user.id, "Test", "test.com")
    await db.commit()

    event = await EventService.record_event(
        db=db,
        site_id=site.id,
        visitor_hash="abc123",
        url="https://test.com/page",
        path="/page",
        referrer="https://google.com",
        referrer_domain="google.com",
        browser="Chrome",
        os="Windows",
        device_type="desktop",
        screen_width=1920,
        country_code="US",
        utm_source="twitter",
        utm_medium="social",
        utm_campaign="launch",
        utm_term=None,
        utm_content=None,
    )
    await db.commit()

    assert event.id is not None
    assert event.site_id == site.id
    assert event.path == "/page"
    assert event.browser == "Chrome"
    assert event.utm_source == "twitter"
