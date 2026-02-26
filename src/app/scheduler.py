"""Background scheduler for nightly aggregation jobs."""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import async_session
from app.services.aggregation import AggregationService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def nightly_aggregation():
    """Nightly job: aggregate yesterday's raw events into daily summary tables."""
    logger.info("Starting nightly aggregation job...")
    try:
        async with async_session() as db:
            stats = await AggregationService.aggregate_yesterday(db)
            logger.info(
                "Nightly aggregation complete: %d sites, %d page stats, "
                "%d referrer stats, %d browser stats, %d device stats, "
                "%d country stats, %d utm stats",
                stats["sites_processed"],
                stats["pages"],
                stats["referrers"],
                stats["browsers"],
                stats["devices"],
                stats["countries"],
                stats["utms"],
            )
    except Exception:
        logger.exception("Error during nightly aggregation")


def start_scheduler():
    """Start the background scheduler with nightly aggregation at 00:15 UTC."""
    scheduler.add_job(
        nightly_aggregation,
        CronTrigger(hour=0, minute=15, timezone="UTC"),
        id="nightly_aggregation",
        name="Nightly event aggregation",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Background scheduler started — nightly aggregation at 00:15 UTC")


def stop_scheduler():
    """Gracefully stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Background scheduler stopped")
