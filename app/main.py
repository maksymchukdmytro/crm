from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import db as dbmod
from .api import admin as api_admin
from .api import catalog as api_catalog
from .api import core as api_core
from .api import orders as api_orders
from .api import stats as api_stats
from .config import config
from .deps import Forbidden, NotAuthenticated, current_user
from .routers import api, audit_log, auth, orders, payments, products, purchases, reports, settings, warehouse
from .services import monitoring
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
    sentry = f"window.CRM_SENTRY={{dsn:{config.SENTRY_DSN_FRONTEND!r},env:{config.SENTRY_ENV!r},release:{monitoring.version().split(' ')[0]!r}}};" if config.SENTRY_DSN_FRONTEND else ""
    inject = f'<base href="{config.ROOT_PATH}/"><script>window.CRM_ROOT={config.ROOT_PATH!r};{sentry}</script>'
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

    monitoring.init_sentry("web")
    app = FastAPI(title="CRM API", version="1.0", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None,
                  description="JSON API CRM. Зміни (не GET) — із заголовком `X-CRM: 1` і cookie сесії після `/api/auth/login`.")
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

    @app.middleware("http")
    async def _metrics(request: Request, call_next):
        t = monitoring.timed()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            route = request.scope.get("route")
            path = getattr(route, "path", None) or "other"
            if path not in ("/api/events", "/api/metrics"):  # довгі з'єднання і самі метрики не рахуємо
                monitoring.observe(request.method, path, status, monitoring.timed() - t)

    # JSON API для нового інтерфейсу
    for r in (api_core, api_orders, api_catalog, api_admin, api_stats):
        app.include_router(r.router)
    # Прийом заявок (webhook) і довідники Нової Пошти
    app.include_router(api.router)
    # Класичний серверний інтерфейс — запасний, за адресою /classic (у документацію API не входить)
    for r in (auth, orders, products, warehouse, purchases, payments, reports, settings, audit_log):
        app.include_router(r.router, prefix=CLASSIC_PREFIX, include_in_schema=False)

    # Документація API — лише для тих, хто увійшов
    @app.get("/api/openapi.json", include_in_schema=False)
    def openapi_json(user=Depends(current_user)):
        return JSONResponse(app.openapi())

    @app.get("/api/docs", include_in_schema=False)
    def api_docs(user=Depends(current_user)):
        return get_swagger_ui_html(openapi_url=f"{config.ROOT_PATH}/api/openapi.json", title="CRM API")

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

    def _version() -> str:
        try:  # VERSION пише deploy/install.sh: «коміт · дата»
            return (Path(__file__).resolve().parent.parent / "VERSION").read_text(encoding="utf-8").strip()
        except OSError:
            return ""

    @app.get("/healthz", include_in_schema=False)
    def healthz():
        """Чи живий веб-процес (для systemd/Docker і скрипта встановлення) і яка версія коду працює."""
        return {"ok": True, "version": _version()}

    @app.get("/healthz/full", include_in_schema=False)
    def healthz_full():
        """Повна перевірка для зовнішнього монітора (UptimeRobot тощо): 503, якщо щось не працює."""
        with dbmod.SessionLocal() as db:
            res = monitoring.checks(db)
        ok = all(c["ok"] for c in res.values())
        return JSONResponse({"ok": ok, "checks": res}, status_code=200 if ok else 503)

    @app.get("/api/metrics", include_in_schema=False)
    def metrics_endpoint(request: Request):
        """Метрики Prometheus. Доступ: заголовок Authorization: Bearer <METRICS_TOKEN> або сесія адміністратора."""
        import hmac
        token = request.headers.get("authorization", "").removeprefix("Bearer ").strip() or request.query_params.get("token", "")
        allowed = bool(config.METRICS_TOKEN) and hmac.compare_digest(token.encode(), config.METRICS_TOKEN.encode())
        with dbmod.SessionLocal() as db:
            if not allowed:
                from .models import User
                uid = request.session.get("uid")
                u = db.get(User, uid) if uid else None
                if u is None or u.role != "admin" or not u.is_active:
                    return JSONResponse({"error": "Потрібен токен метрик"}, status_code=401)
            body = monitoring.render_metrics(db)
        return Response(body, media_type="text/plain; version=0.0.4; charset=utf-8")

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
