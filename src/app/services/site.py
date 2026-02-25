from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.site import Site


class SiteService:
    @staticmethod
    def normalize_domain(domain: str) -> str:
        domain = domain.strip().lower()
        if domain.startswith("http://") or domain.startswith("https://"):
            parsed = urlparse(domain)
            domain = parsed.netloc or parsed.path
        domain = domain.split("/")[0]
        if domain.startswith("www."):
            domain = domain[4:]
        return domain

    @staticmethod
    def generate_tracking_snippet(site_id: str) -> str:
        base_url = f"http{'s' if settings.app_env == 'production' else ''}://{settings.host}"
        if settings.port != 443 and settings.port != 80:
            base_url += f":{settings.port}"
        return (
            f'<script defer data-site="{site_id}" '
            f'src="{base_url}/js/p.js"></script>'
        )

    @staticmethod
    async def create_site(
        db: AsyncSession, user_id: str, name: str, domain: str
    ) -> Site:
        normalized = SiteService.normalize_domain(domain)
        site = Site(user_id=user_id, name=name, domain=normalized)
        db.add(site)
        await db.flush()
        await db.refresh(site)
        return site

    @staticmethod
    async def list_sites(db: AsyncSession, user_id: str) -> list[Site]:
        result = await db.execute(
            select(Site).where(Site.user_id == user_id).order_by(Site.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_site(db: AsyncSession, site_id: str) -> Site | None:
        result = await db.execute(select(Site).where(Site.id == site_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_site_by_domain(db: AsyncSession, domain: str) -> Site | None:
        normalized = SiteService.normalize_domain(domain)
        result = await db.execute(select(Site).where(Site.domain == normalized))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_site(
        db: AsyncSession, site: Site, name: str | None = None,
        domain: str | None = None, public: bool | None = None
    ) -> Site:
        if name is not None:
            site.name = name
        if domain is not None:
            site.domain = SiteService.normalize_domain(domain)
        if public is not None:
            site.public = public
        await db.flush()
        await db.refresh(site)
        return site

    @staticmethod
    async def delete_site(db: AsyncSession, site: Site) -> None:
        await db.delete(site)
        await db.flush()
