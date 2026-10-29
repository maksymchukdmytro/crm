from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import db as dbmod
from .api import admin as api_admin
from .api import catalog as api_catalog
from .api import core as api_core
from .api import orders as api_orders
from .config import config
from .deps import Forbidden, NotAuthenticated
from .routers import api, audit_log, auth, orders, payments, products, purchases, reports, settings, warehouse
from .services.seed import seed
from .web import BASE_DIR, CLASSIC_PREFIX, redirect, render

# Зібраний фронтенд (React): frontend/dist. У Docker і на сервері збирається під час встановлення.
SPA_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


def _spa_index() -> str | None:
    f = SPA_DIR / "index.html"
    if not f.exists():
        return None
    html = f.read_text(encoding="utf-8")
    # базова адреса для відносних шляхів збірки і префікс для роутера/API
    inject = f'<base href="{config.ROOT_PATH}/"><script>window.CRM_ROOT={config.ROOT_PATH!r};</script>'
    return html.replace("<head>", "<head>" + inject, 1)


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

    # JSON API для нового інтерфейсу
    for r in (api_core, api_orders, api_catalog, api_admin):
        app.include_router(r.router)
    # Прийом заявок (webhook) і довідники Нової Пошти
    app.include_router(api.router)
    # Класичний серверний інтерфейс — запасний, за адресою /classic
    for r in (auth, orders, products, warehouse, purchases, payments, reports, settings, audit_log):
        app.include_router(r.router, prefix=CLASSIC_PREFIX)

    @app.exception_handler(NotAuthenticated)
    async def _not_auth(request: Request, exc: NotAuthenticated):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"error": "Потрібна авторизація"}, status_code=401)
        path = request.url.path
        if path.startswith(CLASSIC_PREFIX):
            path = path[len(CLASSIC_PREFIX):] or "/"
        nxt = path + (f"?{request.url.query}" if request.url.query else "")
        return redirect(f"/login?next={nxt}")

    @app.exception_handler(Forbidden)
    async def _forbidden(request: Request, exc: Forbidden):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"error": "Недостатньо прав"}, status_code=403)
        return render(request, "error.html", {"title": "Немає доступу",
                                              "message": "У вашої ролі немає доступу до цього розділу."}, 403)

    @app.exception_handler(HTTPException)
    async def _http(request: Request, exc: HTTPException):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"error": exc.detail}, status_code=exc.status_code)
        return render(request, "error.html", {"title": f"Помилка {exc.status_code}", "message": exc.detail or ""},
                      exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        return JSONResponse({"error": "Некоректні дані запиту", "details": exc.errors()[:5]}, status_code=422)

    @app.get("/healthz", include_in_schema=False)
    def healthz():
        return {"ok": True}

    if (SPA_DIR / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=str(SPA_DIR / "assets")), name="spa-assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        """Усі інші адреси — новий інтерфейс (маршрутизацію робить сам застосунок)."""
        if path.startswith(("api/", "static/", "assets/")):
            return JSONResponse({"error": "Не знайдено"}, status_code=404)
        html = _spa_index()
        if html is None:
            # фронтенд ще не зібрано — відкриваємо класичний інтерфейс
            return redirect("/orders")
        return HTMLResponse(html, headers={"Cache-Control": "no-cache"})

    return app


app = create_app()
