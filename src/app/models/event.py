import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PageviewEvent(Base):
    __tablename__ = "pageview_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    site_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    visitor_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    path: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    referrer: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    referrer_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(64), nullable=True)
    os: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    screen_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    utm_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_term: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_content: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )

    site = relationship("Site", back_populates="events")
