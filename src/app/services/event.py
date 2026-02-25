import hashlib
import re
from datetime import date, timezone, datetime
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.event import PageviewEvent


class EventService:
    @staticmethod
    def compute_visitor_hash(site_id: str, ip: str, user_agent: str) -> str:
        today = date.today().isoformat()
        salt = f"{settings.secret_key}:{today}"
        raw = f"{salt}:{site_id}:{ip}:{user_agent}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def parse_user_agent(ua: str) -> dict:
        browser = "Unknown"
        os_name = "Unknown"
        device_type = "desktop"

        ua_lower = ua.lower()

        # Browser detection (order matters — check specific before generic)
        if "edg/" in ua_lower or "edge/" in ua_lower:
            browser = "Edge"
        elif "opr/" in ua_lower or "opera" in ua_lower:
            browser = "Opera"
        elif "chrome/" in ua_lower and "chromium" not in ua_lower:
            browser = "Chrome"
        elif "firefox/" in ua_lower:
            browser = "Firefox"
        elif "msie" in ua_lower or "trident/" in ua_lower:
            browser = "IE"
        elif "safari/" in ua_lower or "applewebkit/" in ua_lower:
            browser = "Safari"

        # OS detection (check iPhone/iPad BEFORE macOS since iPad UAs contain "Mac OS")
        if "iphone" in ua_lower:
            os_name = "iOS"
        elif "ipad" in ua_lower:
            os_name = "iOS"
        elif "android" in ua_lower:
            os_name = "Android"
        elif "windows" in ua_lower:
            os_name = "Windows"
        elif "macintosh" in ua_lower or "mac os" in ua_lower:
            os_name = "macOS"
        elif "linux" in ua_lower:
            os_name = "Linux"
        elif "cros" in ua_lower:
            os_name = "ChromeOS"

        # Device type detection
        if "iphone" in ua_lower:
            device_type = "mobile"
        elif "ipad" in ua_lower or "tablet" in ua_lower:
            device_type = "tablet"
        elif "mobile" in ua_lower:
            device_type = "mobile"

        return {"browser": browser, "os": os_name, "device_type": device_type}

    @staticmethod
    def extract_referrer_domain(referrer: str) -> str | None:
        if not referrer:
            return None
        try:
            parsed = urlparse(referrer)
            domain = parsed.netloc
            if domain.startswith("www."):
                domain = domain[4:]
            return domain if domain else None
        except Exception:
            return None

    @staticmethod
    def detect_country_from_headers(headers: dict) -> str | None:
        # Check common CDN/proxy headers for country code
        for header in ["cf-ipcountry", "x-country-code", "x-vercel-ip-country"]:
            value = headers.get(header)
            if value and len(value) == 2:
                return value.upper()
        return None

    @staticmethod
    def get_client_ip(request_headers: dict, client_host: str | None) -> str:
        for header in ["x-forwarded-for", "x-real-ip"]:
            value = request_headers.get(header)
            if value:
                return value.split(",")[0].strip()
        return client_host or "0.0.0.0"

    @staticmethod
    async def record_event(
        db: AsyncSession,
        site_id: str,
        visitor_hash: str,
        url: str,
        path: str,
        referrer: str | None,
        referrer_domain: str | None,
        browser: str | None,
        os: str | None,
        device_type: str | None,
        screen_width: int | None,
        country_code: str | None,
        utm_source: str | None,
        utm_medium: str | None,
        utm_campaign: str | None,
        utm_term: str | None,
        utm_content: str | None,
    ) -> PageviewEvent:
        event = PageviewEvent(
            site_id=site_id,
            visitor_hash=visitor_hash,
            url=url[:2048],
            path=path[:2048] if path else "/",
            referrer=referrer[:2048] if referrer else None,
            referrer_domain=referrer_domain,
            browser=browser,
            os=os,
            device_type=device_type,
            screen_width=screen_width if screen_width and screen_width > 0 else None,
            country_code=country_code,
            utm_source=utm_source or None,
            utm_medium=utm_medium or None,
            utm_campaign=utm_campaign or None,
            utm_term=utm_term or None,
            utm_content=utm_content or None,
        )
        db.add(event)
        await db.flush()
        return event
