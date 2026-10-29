from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import db as dbmod
from .config import config
from .deps import Forbidden, NotAuthenticated
from .routers import api, audit_log, auth, orders, payments, products, purchases, reports, settings, warehouse
from .services.seed import seed
from .web import BASE_DIR, redirect, render


def create_app(database_url: str | None = None, run_seed: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if dbmod.engine is None or database_url:
            dbmod.init_engine(database_url)
        if run_seed:
            with dbmod.SessionLocal() as db:
                seed(db)
        yield

    app = FastAPI(title="CRM", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(
        SessionMiddleware,
        secret_key=config.SECRET_KEY,
        session_cookie="crm_session",
        max_age=14 * 24 * 3600,
        same_site="lax",
        https_only=config.HTTPS_ONLY,
        path=config.ROOT_PATH or "/",
    )
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    for r in (auth, orders, api, products, warehouse, purchases, payments, reports, settings, audit_log):
        app.include_router(r.router)

    @app.exception_handler(NotAuthenticated)
    async def _not_auth(request: Request, exc: NotAuthenticated):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"ok": False, "error": "Потрібна авторизація"}, status_code=401)
        nxt = request.url.path + (f"?{request.url.query}" if request.url.query else "")
        return redirect(f"/login?next={nxt}")

    @app.exception_handler(Forbidden)
    async def _forbidden(request: Request, exc: Forbidden):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"ok": False, "error": "Недостатньо прав"}, status_code=403)
        return render(request, "error.html", {"title": "Немає доступу",
                                              "message": "У вашої ролі немає доступу до цього розділу."}, 403)

    @app.get("/healthz", include_in_schema=False)
    def healthz():
        return {"ok": True}

    return app


app = create_app()
