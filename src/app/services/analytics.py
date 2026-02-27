from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import PageviewEvent


class AnalyticsService:
    """Queries analytics data from both raw events (today) and daily aggregates (historical)."""

    @staticmethod
    def _date_range(period: str, start: str | None = None, end: str | None = None):
        today = date.today()
        if period == "today":
            return today, today
        elif period == "7d":
            return today - timedelta(days=6), today
        elif period == "30d":
            return today - timedelta(days=29), today
        elif period == "custom" and start and end:
            try:
                s, e = date.fromisoformat(start), date.fromisoformat(end)
                if s > e:
                    s, e = e, s
                return s, e
            except ValueError:
                return today - timedelta(days=6), today
        return today - timedelta(days=6), today

    @staticmethod
    async def get_summary(db: AsyncSession, site_id: str, start_date: date, end_date: date) -> dict:
        """Total pageviews and unique visitors for the period."""
        result = await db.execute(
            select(
                func.count().label("pageviews"),
                func.count(func.distinct(PageviewEvent.visitor_hash)).label("unique_visitors"),
            ).where(
                PageviewEvent.site_id == site_id,
                func.date(PageviewEvent.timestamp) >= start_date,
                func.date(PageviewEvent.timestamp) <= end_date,
            )
        )
        row = result.one()
        return {
            "pageviews": row.pageviews or 0,
            "unique_visitors": row.unique_visitors or 0,
        }

    @staticmethod
    async def get_bounce_rate(
        db: AsyncSession, site_id: str, start_date: date, end_date: date
    ) -> float:
        """Bounce rate: % of visitors with only 1 pageview in the period."""
        result = await db.execute(
            select(
                PageviewEvent.visitor_hash,
                func.count().label("pv_count"),
            ).where(
                PageviewEvent.site_id == site_id,
                func.date(PageviewEvent.timestamp) >= start_date,
                func.date(PageviewEvent.timestamp) <= end_date,
            ).group_by(PageviewEvent.visitor_hash)
        )
        rows = result.all()
        if not rows:
            return 0.0
        bounces = sum(1 for r in rows if r.pv_count == 1)
        return round(bounces / len(rows) * 100, 1)

    @staticmethod
    async def get_visitors_over_time(
        db: AsyncSession, site_id: str, start_date: date, end_date: date
    ) -> list[dict]:
        """Pageviews and unique visitors per day."""
        result = await db.execute(
            select(
                func.date(PageviewEvent.timestamp).label("day"),
                func.count().label("pageviews"),
                func.count(func.distinct(PageviewEvent.visitor_hash)).label("unique_visitors"),
            ).where(
                PageviewEvent.site_id == site_id,
                func.date(PageviewEvent.timestamp) >= start_date,
                func.date(PageviewEvent.timestamp) <= end_date,
            ).group_by("day").order_by("day")
        )
        data_map = {
            str(r.day): {"pageviews": r.pageviews, "unique_visitors": r.unique_visitors}
            for r in result.all()
        }

        # Fill in missing days with zeros
        days = []
        current = start_date
        while current <= end_date:
            key = current.isoformat()
            entry = data_map.get(key, {"pageviews": 0, "unique_visitors": 0})
            days.append({"date": key, **entry})
            current += timedelta(days=1)
        return days

    @staticmethod
    async def get_top_pages(
        db: AsyncSession, site_id: str, start_date: date, end_date: date, limit: int = 10
    ) -> list[dict]:
        result = await db.execute(
            select(
                PageviewEvent.path,
                func.count().label("pageviews"),
                func.count(func.distinct(PageviewEvent.visitor_hash)).label("unique_visitors"),
            ).where(
                PageviewEvent.site_id == site_id,
                func.date(PageviewEvent.timestamp) >= start_date,
                func.date(PageviewEvent.timestamp) <= end_date,
            ).group_by(PageviewEvent.path)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return [
            {"path": r.path, "pageviews": r.pageviews, "unique_visitors": r.unique_visitors}
            for r in result.all()
        ]

    @staticmethod
    async def get_top_referrers(
        db: AsyncSession, site_id: str, start_date: date, end_date: date, limit: int = 10
    ) -> list[dict]:
        result = await db.execute(
            select(
                PageviewEvent.referrer_domain,
                func.count().label("pageviews"),
                func.count(func.distinct(PageviewEvent.visitor_hash)).label("unique_visitors"),
            ).where(
                PageviewEvent.site_id == site_id,
                PageviewEvent.referrer_domain.isnot(None),
                PageviewEvent.referrer_domain != "",
                func.date(PageviewEvent.timestamp) >= start_date,
                func.date(PageviewEvent.timestamp) <= end_date,
            ).group_by(PageviewEvent.referrer_domain)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return [
            {
                "referrer_domain": r.referrer_domain,
                "pageviews": r.pageviews,
                "unique_visitors": r.unique_visitors,
            }
            for r in result.all()
        ]

    @staticmethod
    async def get_browsers(
        db: AsyncSession, site_id: str, start_date: date, end_date: date, limit: int = 10
    ) -> list[dict]:
        result = await db.execute(
            select(
                PageviewEvent.browser,
                func.count().label("pageviews"),
                func.count(func.distinct(PageviewEvent.visitor_hash)).label("unique_visitors"),
            ).where(
                PageviewEvent.site_id == site_id,
                PageviewEvent.browser.isnot(None),
                func.date(PageviewEvent.timestamp) >= start_date,
                func.date(PageviewEvent.timestamp) <= end_date,
            ).group_by(PageviewEvent.browser)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return [
            {"browser": r.browser, "pageviews": r.pageviews, "unique_visitors": r.unique_visitors}
            for r in result.all()
        ]

    @staticmethod
    async def get_devices(
        db: AsyncSession, site_id: str, start_date: date, end_date: date, limit: int = 10
    ) -> list[dict]:
        result = await db.execute(
            select(
                PageviewEvent.device_type,
                func.count().label("pageviews"),
                func.count(func.distinct(PageviewEvent.visitor_hash)).label("unique_visitors"),
            ).where(
                PageviewEvent.site_id == site_id,
                PageviewEvent.device_type.isnot(None),
                func.date(PageviewEvent.timestamp) >= start_date,
                func.date(PageviewEvent.timestamp) <= end_date,
            ).group_by(PageviewEvent.device_type)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return [
            {
                "device_type": r.device_type,
                "pageviews": r.pageviews,
                "unique_visitors": r.unique_visitors,
            }
            for r in result.all()
        ]

    @staticmethod
    async def get_countries(
        db: AsyncSession, site_id: str, start_date: date, end_date: date, limit: int = 10
    ) -> list[dict]:
        result = await db.execute(
            select(
                PageviewEvent.country_code,
                func.count().label("pageviews"),
                func.count(func.distinct(PageviewEvent.visitor_hash)).label("unique_visitors"),
            ).where(
                PageviewEvent.site_id == site_id,
                PageviewEvent.country_code.isnot(None),
                func.date(PageviewEvent.timestamp) >= start_date,
                func.date(PageviewEvent.timestamp) <= end_date,
            ).group_by(PageviewEvent.country_code)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return [
            {
                "country_code": r.country_code,
                "pageviews": r.pageviews,
                "unique_visitors": r.unique_visitors,
            }
            for r in result.all()
        ]

    @staticmethod
    async def get_utm_campaigns(
        db: AsyncSession, site_id: str, start_date: date, end_date: date, limit: int = 10
    ) -> list[dict]:
        result = await db.execute(
            select(
                PageviewEvent.utm_source,
                PageviewEvent.utm_medium,
                PageviewEvent.utm_campaign,
                func.count().label("pageviews"),
                func.count(func.distinct(PageviewEvent.visitor_hash)).label("unique_visitors"),
            ).where(
                PageviewEvent.site_id == site_id,
                PageviewEvent.utm_source.isnot(None),
                func.date(PageviewEvent.timestamp) >= start_date,
                func.date(PageviewEvent.timestamp) <= end_date,
            ).group_by(
                PageviewEvent.utm_source,
                PageviewEvent.utm_medium,
                PageviewEvent.utm_campaign,
            )
            .order_by(func.count().desc())
            .limit(limit)
        )
        return [
            {
                "utm_source": r.utm_source,
                "utm_medium": r.utm_medium,
                "utm_campaign": r.utm_campaign or "",
                "pageviews": r.pageviews,
                "unique_visitors": r.unique_visitors,
            }
            for r in result.all()
        ]

    @staticmethod
    async def get_full_dashboard(
        db: AsyncSession, site_id: str, period: str = "7d",
        start: str | None = None, end: str | None = None,
    ) -> dict:
        """Get all dashboard data in one call."""
        start_date, end_date = AnalyticsService._date_range(period, start, end)

        summary = await AnalyticsService.get_summary(db, site_id, start_date, end_date)
        bounce_rate = await AnalyticsService.get_bounce_rate(db, site_id, start_date, end_date)
        visitors_over_time = await AnalyticsService.get_visitors_over_time(
            db, site_id, start_date, end_date
        )
        top_pages = await AnalyticsService.get_top_pages(db, site_id, start_date, end_date)
        top_referrers = await AnalyticsService.get_top_referrers(db, site_id, start_date, end_date)
        browsers = await AnalyticsService.get_browsers(db, site_id, start_date, end_date)
        devices = await AnalyticsService.get_devices(db, site_id, start_date, end_date)
        countries = await AnalyticsService.get_countries(db, site_id, start_date, end_date)
        utm_campaigns = await AnalyticsService.get_utm_campaigns(db, site_id, start_date, end_date)

        return {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "summary": {
                **summary,
                "bounce_rate": bounce_rate,
            },
            "visitors_over_time": visitors_over_time,
            "top_pages": top_pages,
            "top_referrers": top_referrers,
            "browsers": browsers,
            "devices": devices,
            "countries": countries,
            "utm_campaigns": utm_campaigns,
        }
