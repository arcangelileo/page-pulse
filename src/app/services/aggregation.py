"""Background aggregation service — rolls up raw PageviewEvents into daily summary tables."""

import logging
from datetime import date, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import PageviewEvent
from app.models.site import Site
from app.models.stats import (
    DailyBrowserStats,
    DailyCountryStats,
    DailyDeviceStats,
    DailyPageStats,
    DailyReferrerStats,
    DailyUTMStats,
)

logger = logging.getLogger(__name__)


class AggregationService:
    """Aggregates raw pageview events into daily summary tables for fast queries."""

    @staticmethod
    async def aggregate_day(db: AsyncSession, target_date: date) -> dict:
        """Aggregate all events for a specific date into daily stats tables.

        Returns a dict with counts of rows inserted per table.
        """
        stats = {
            "pages": 0,
            "referrers": 0,
            "browsers": 0,
            "devices": 0,
            "countries": 0,
            "utms": 0,
            "sites_processed": 0,
        }

        # Find all sites that have events on target_date
        site_ids_result = await db.execute(
            select(PageviewEvent.site_id.distinct()).where(
                func.date(PageviewEvent.timestamp) == target_date.isoformat()
            )
        )
        site_ids = [row[0] for row in site_ids_result.all()]

        for site_id in site_ids:
            counts = await AggregationService._aggregate_site_day(db, site_id, target_date)
            stats["pages"] += counts["pages"]
            stats["referrers"] += counts["referrers"]
            stats["browsers"] += counts["browsers"]
            stats["devices"] += counts["devices"]
            stats["countries"] += counts["countries"]
            stats["utms"] += counts["utms"]
            stats["sites_processed"] += 1

        await db.commit()
        logger.info(
            "Aggregated %d sites for %s: %d pages, %d referrers, %d browsers, "
            "%d devices, %d countries, %d utms",
            stats["sites_processed"],
            target_date.isoformat(),
            stats["pages"],
            stats["referrers"],
            stats["browsers"],
            stats["devices"],
            stats["countries"],
            stats["utms"],
        )
        return stats

    @staticmethod
    async def _aggregate_site_day(db: AsyncSession, site_id: str, target_date: date) -> dict:
        """Aggregate events for a single site on a single day."""
        date_filter = func.date(PageviewEvent.timestamp) == target_date.isoformat()
        site_filter = PageviewEvent.site_id == site_id

        # Clear existing aggregates for this site+date (idempotent)
        for model in [
            DailyPageStats,
            DailyReferrerStats,
            DailyBrowserStats,
            DailyDeviceStats,
            DailyCountryStats,
            DailyUTMStats,
        ]:
            await db.execute(
                delete(model).where(model.site_id == site_id, model.date == target_date)
            )

        counts = {}

        # Pages
        result = await db.execute(
            select(
                PageviewEvent.path,
                func.count().label("pageviews"),
                func.count(func.distinct(PageviewEvent.visitor_hash)).label("unique_visitors"),
            )
            .where(site_filter, date_filter)
            .group_by(PageviewEvent.path)
        )
        rows = result.all()
        for row in rows:
            db.add(
                DailyPageStats(
                    site_id=site_id,
                    date=target_date,
                    path=row.path,
                    pageviews=row.pageviews,
                    unique_visitors=row.unique_visitors,
                )
            )
        counts["pages"] = len(rows)

        # Referrers
        result = await db.execute(
            select(
                PageviewEvent.referrer_domain,
                func.count().label("pageviews"),
                func.count(func.distinct(PageviewEvent.visitor_hash)).label("unique_visitors"),
            )
            .where(
                site_filter,
                date_filter,
                PageviewEvent.referrer_domain.isnot(None),
                PageviewEvent.referrer_domain != "",
            )
            .group_by(PageviewEvent.referrer_domain)
        )
        rows = result.all()
        for row in rows:
            db.add(
                DailyReferrerStats(
                    site_id=site_id,
                    date=target_date,
                    referrer_domain=row.referrer_domain,
                    pageviews=row.pageviews,
                    unique_visitors=row.unique_visitors,
                )
            )
        counts["referrers"] = len(rows)

        # Browsers
        result = await db.execute(
            select(
                PageviewEvent.browser,
                func.count().label("pageviews"),
                func.count(func.distinct(PageviewEvent.visitor_hash)).label("unique_visitors"),
            )
            .where(site_filter, date_filter, PageviewEvent.browser.isnot(None))
            .group_by(PageviewEvent.browser)
        )
        rows = result.all()
        for row in rows:
            db.add(
                DailyBrowserStats(
                    site_id=site_id,
                    date=target_date,
                    browser=row.browser,
                    pageviews=row.pageviews,
                    unique_visitors=row.unique_visitors,
                )
            )
        counts["browsers"] = len(rows)

        # Devices
        result = await db.execute(
            select(
                PageviewEvent.device_type,
                func.count().label("pageviews"),
                func.count(func.distinct(PageviewEvent.visitor_hash)).label("unique_visitors"),
            )
            .where(site_filter, date_filter, PageviewEvent.device_type.isnot(None))
            .group_by(PageviewEvent.device_type)
        )
        rows = result.all()
        for row in rows:
            db.add(
                DailyDeviceStats(
                    site_id=site_id,
                    date=target_date,
                    device_type=row.device_type,
                    pageviews=row.pageviews,
                    unique_visitors=row.unique_visitors,
                )
            )
        counts["devices"] = len(rows)

        # Countries
        result = await db.execute(
            select(
                PageviewEvent.country_code,
                func.count().label("pageviews"),
                func.count(func.distinct(PageviewEvent.visitor_hash)).label("unique_visitors"),
            )
            .where(site_filter, date_filter, PageviewEvent.country_code.isnot(None))
            .group_by(PageviewEvent.country_code)
        )
        rows = result.all()
        for row in rows:
            db.add(
                DailyCountryStats(
                    site_id=site_id,
                    date=target_date,
                    country_code=row.country_code,
                    pageviews=row.pageviews,
                    unique_visitors=row.unique_visitors,
                )
            )
        counts["countries"] = len(rows)

        # UTMs
        result = await db.execute(
            select(
                PageviewEvent.utm_source,
                PageviewEvent.utm_medium,
                PageviewEvent.utm_campaign,
                func.count().label("pageviews"),
                func.count(func.distinct(PageviewEvent.visitor_hash)).label("unique_visitors"),
            )
            .where(site_filter, date_filter, PageviewEvent.utm_source.isnot(None))
            .group_by(
                PageviewEvent.utm_source,
                PageviewEvent.utm_medium,
                PageviewEvent.utm_campaign,
            )
        )
        rows = result.all()
        for row in rows:
            db.add(
                DailyUTMStats(
                    site_id=site_id,
                    date=target_date,
                    utm_source=row.utm_source or "",
                    utm_medium=row.utm_medium or "",
                    utm_campaign=row.utm_campaign or "",
                    pageviews=row.pageviews,
                    unique_visitors=row.unique_visitors,
                )
            )
        counts["utms"] = len(rows)

        await db.flush()
        return counts

    @staticmethod
    async def aggregate_yesterday(db: AsyncSession) -> dict:
        """Convenience method to aggregate yesterday's data (typical nightly job)."""
        yesterday = date.today() - timedelta(days=1)
        return await AggregationService.aggregate_day(db, yesterday)

    @staticmethod
    async def backfill(db: AsyncSession, start_date: date, end_date: date) -> dict:
        """Aggregate data for a range of dates (for backfilling historical data)."""
        total = {
            "pages": 0,
            "referrers": 0,
            "browsers": 0,
            "devices": 0,
            "countries": 0,
            "utms": 0,
            "sites_processed": 0,
            "days_processed": 0,
        }
        current = start_date
        while current <= end_date:
            stats = await AggregationService.aggregate_day(db, current)
            for key in ["pages", "referrers", "browsers", "devices", "countries", "utms", "sites_processed"]:
                total[key] += stats[key]
            total["days_processed"] += 1
            current += timedelta(days=1)
        return total
