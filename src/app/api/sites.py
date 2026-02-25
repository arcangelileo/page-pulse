from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.site import SiteCreate, SiteResponse, SiteUpdate, SiteWithSnippet
from app.services.site import SiteService

router = APIRouter(prefix="/api/v1/sites", tags=["sites"])
ui_router = APIRouter(tags=["sites-ui"])
templates = Jinja2Templates(directory="src/app/templates")


# --- API Endpoints ---


@router.post("", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_site(
    data: SiteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = await SiteService.create_site(
        db, user_id=current_user.id, name=data.name, domain=data.domain
    )
    return SiteResponse.model_validate(site)


@router.get("", response_model=list[SiteResponse])
async def list_sites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sites = await SiteService.list_sites(db, current_user.id)
    return [SiteResponse.model_validate(s) for s in sites]


@router.get("/{site_id}", response_model=SiteWithSnippet)
async def get_site(
    site_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = await SiteService.get_site(db, site_id)
    if site is None or site.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    snippet = SiteService.generate_tracking_snippet(site.id)
    return SiteWithSnippet(
        **SiteResponse.model_validate(site).model_dump(),
        tracking_snippet=snippet,
    )


@router.patch("/{site_id}", response_model=SiteResponse)
async def update_site(
    site_id: str,
    data: SiteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = await SiteService.get_site(db, site_id)
    if site is None or site.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    site = await SiteService.update_site(
        db, site, name=data.name, domain=data.domain, public=data.public
    )
    return SiteResponse.model_validate(site)


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(
    site_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = await SiteService.get_site(db, site_id)
    if site is None or site.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    await SiteService.delete_site(db, site)


# --- UI Routes ---


@ui_router.get("/sites", response_class=HTMLResponse)
async def sites_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sites = await SiteService.list_sites(db, current_user.id)
    return templates.TemplateResponse(
        request, "sites/index.html", {"user": current_user, "sites": sites}
    )


@ui_router.get("/sites/{site_id}/settings", response_class=HTMLResponse)
async def site_settings_page(
    request: Request,
    site_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = await SiteService.get_site(db, site_id)
    if site is None or site.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    snippet = SiteService.generate_tracking_snippet(site.id)
    return templates.TemplateResponse(
        request, "sites/settings.html",
        {"user": current_user, "site": site, "tracking_snippet": snippet},
    )
