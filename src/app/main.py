from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api import health
from app.api.auth import router as auth_router, ui_router as auth_ui_router
from app.api.events import router as events_router
from app.api.sites import router as sites_router, ui_router as sites_ui_router
from app.api.tracking import router as tracking_router
from app.config import settings
from app.database import Base, engine
from app.dependencies import get_current_user, get_optional_user
from app.models.user import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


templates = Jinja2Templates(directory="src/app/templates")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="Privacy-first website analytics platform",
        version="0.1.0",
        lifespan=lifespan,
    )

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

    @app.get("/", response_class=HTMLResponse)
    async def landing(request: Request, user: User | None = Depends(get_optional_user)):
        if user:
            return RedirectResponse(url="/dashboard", status_code=302)
        return RedirectResponse(url="/login", status_code=302)

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard_redirect(
        request: Request, current_user: User = Depends(get_current_user)
    ):
        return RedirectResponse(url="/sites", status_code=302)

    return app


app = create_app()
