from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.analytics import AnalyticsService
from app.services.site import SiteService

router = APIRouter(prefix="/api/v1", tags=["analytics"])
ui_router = APIRouter(tags=["dashboard-ui"])
templates = Jinja2Templates(directory="src/app/templates")


# --- API Endpoint ---


@router.get("/sites/{site_id}/analytics")
async def get_analytics(
    site_id: str,
    period: str = Query("7d", pattern="^(today|7d|30d|custom)$"),
    start: str | None = None,
    end: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = await SiteService.get_site(db, site_id)
    if site is None or site.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    data = await AnalyticsService.get_full_dashboard(db, site_id, period, start, end)
    data["site"] = {"id": site.id, "name": site.name, "domain": site.domain}
    return data


# --- Public API Endpoint ---


@router.get("/public/{site_id}/analytics")
async def get_public_analytics(
    site_id: str,
    period: str = Query("7d", pattern="^(today|7d|30d|custom)$"),
    start: str | None = None,
    end: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    site = await SiteService.get_site(db, site_id)
    if site is None or not site.public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")

    data = await AnalyticsService.get_full_dashboard(db, site_id, period, start, end)
    data["site"] = {"id": site.id, "name": site.name, "domain": site.domain}
    return data


# --- Dashboard UI Route ---


@ui_router.get("/dashboard/{site_id}", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    site_id: str,
    period: str = "7d",
    start: str | None = None,
    end: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = await SiteService.get_site(db, site_id)
    if site is None or site.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    # Get all user's sites for the site switcher
    user_sites = await SiteService.list_sites(db, current_user.id)
    analytics = await AnalyticsService.get_full_dashboard(db, site_id, period, start, end)

    return templates.TemplateResponse(
        request, "dashboard/index.html",
        {
            "user": current_user,
            "site": site,
            "sites": user_sites,
            "analytics": analytics,
            "period": period,
            "start_date": start or analytics["start_date"],
            "end_date": end or analytics["end_date"],
        },
    )


# --- Public Dashboard UI Route ---


@ui_router.get("/share/{site_id}", response_class=HTMLResponse)
async def public_dashboard_page(
    request: Request,
    site_id: str,
    period: str = "7d",
    start: str | None = None,
    end: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    site = await SiteService.get_site(db, site_id)
    if site is None or not site.public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")

    analytics = await AnalyticsService.get_full_dashboard(db, site_id, period, start, end)

    return templates.TemplateResponse(
        request, "dashboard/public.html",
        {
            "site": site,
            "analytics": analytics,
            "period": period,
            "start_date": start or analytics["start_date"],
            "end_date": end or analytics["end_date"],
        },
    )
