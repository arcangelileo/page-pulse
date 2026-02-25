from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.event import EventPayload
from app.services.event import EventService
from app.services.site import SiteService

router = APIRouter(prefix="/api/v1", tags=["events"])


@router.post("/event", status_code=status.HTTP_202_ACCEPTED)
async def ingest_event(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Parse body — support both JSON content-type and sendBeacon (text/plain)
    try:
        body = await request.json()
        payload = EventPayload(**body)
    except Exception:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    # Validate the site exists
    site = await SiteService.get_site(db, payload.s)
    if site is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # Extract metadata
    ua = request.headers.get("user-agent", "")
    client_ip = EventService.get_client_ip(
        dict(request.headers), request.client.host if request.client else None
    )
    visitor_hash = EventService.compute_visitor_hash(site.id, client_ip, ua)
    ua_info = EventService.parse_user_agent(ua)
    referrer_domain = EventService.extract_referrer_domain(payload.r)
    country = EventService.detect_country_from_headers(dict(request.headers))

    # Filter out self-referrals
    referrer = payload.r if payload.r else None
    if referrer_domain and referrer_domain == site.domain:
        referrer = None
        referrer_domain = None

    await EventService.record_event(
        db=db,
        site_id=site.id,
        visitor_hash=visitor_hash,
        url=payload.u,
        path=payload.p or "/",
        referrer=referrer,
        referrer_domain=referrer_domain,
        browser=ua_info["browser"],
        os=ua_info["os"],
        device_type=ua_info["device_type"],
        screen_width=payload.sw,
        country_code=country,
        utm_source=payload.us,
        utm_medium=payload.um,
        utm_campaign=payload.uc,
        utm_term=payload.ut,
        utm_content=payload.ux,
    )

    return Response(status_code=status.HTTP_202_ACCEPTED)
