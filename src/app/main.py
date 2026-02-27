from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import health
from app.api.auth import router as auth_router
from app.api.auth import ui_router as auth_ui_router
from app.api.dashboard import router as dashboard_router
from app.api.dashboard import ui_router as dashboard_ui_router
from app.api.events import router as events_router
from app.api.sites import router as sites_router
from app.api.sites import ui_router as sites_ui_router
from app.api.tracking import router as tracking_router
from app.config import settings
from app.database import Base, engine
from app.dependencies import get_current_user, get_optional_user
from app.models.user import User
from app.rate_limit import limiter
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    start_scheduler()
    yield
    stop_scheduler()


templates = Jinja2Templates(directory="src/app/templates")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="Privacy-first website analytics platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth_router)
    app.include_router(auth_ui_router)
    app.include_router(sites_router)
    app.include_router(sites_ui_router)
    app.include_router(tracking_router)
    app.include_router(events_router)
    app.include_router(dashboard_router)
    app.include_router(dashboard_ui_router)

    @app.get("/", response_class=HTMLResponse)
    async def landing(request: Request, user: User | None = Depends(get_optional_user)):
        if user:
            return RedirectResponse(url="/dashboard", status_code=302)
        return templates.TemplateResponse(request, "landing.html")

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard_redirect(
        request: Request, current_user: User = Depends(get_current_user)
    ):
        return RedirectResponse(url="/sites", status_code=302)

    return app


app = create_app()
