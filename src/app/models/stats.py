import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DailyPageStats(Base):
    __tablename__ = "daily_page_stats"
    __table_args__ = (
        UniqueConstraint("site_id", "date", "path", name="uq_daily_page"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    site_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(2048), nullable=False)
    pageviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_visitors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class DailyReferrerStats(Base):
    __tablename__ = "daily_referrer_stats"
    __table_args__ = (
        UniqueConstraint("site_id", "date", "referrer_domain", name="uq_daily_referrer"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    site_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    referrer_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    pageviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_visitors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class DailyBrowserStats(Base):
    __tablename__ = "daily_browser_stats"
    __table_args__ = (
        UniqueConstraint("site_id", "date", "browser", name="uq_daily_browser"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    site_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    browser: Mapped[str] = mapped_column(String(64), nullable=False)
    pageviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_visitors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class DailyDeviceStats(Base):
    __tablename__ = "daily_device_stats"
    __table_args__ = (
        UniqueConstraint("site_id", "date", "device_type", name="uq_daily_device"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    site_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    device_type: Mapped[str] = mapped_column(String(16), nullable=False)
    pageviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_visitors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class DailyCountryStats(Base):
    __tablename__ = "daily_country_stats"
    __table_args__ = (
        UniqueConstraint("site_id", "date", "country_code", name="uq_daily_country"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    site_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    pageviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_visitors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class DailyUTMStats(Base):
    __tablename__ = "daily_utm_stats"
    __table_args__ = (
        UniqueConstraint(
            "site_id", "date", "utm_source", "utm_medium", "utm_campaign",
            name="uq_daily_utm",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    site_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    utm_source: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    utm_medium: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    utm_campaign: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    pageviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_visitors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
