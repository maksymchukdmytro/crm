import os
import re

import httpx
import pytest
from fastapi.testclient import TestClient

TEST_DB = os.getenv("TEST_DATABASE_URL", "postgresql+psycopg://crm:crm@localhost:5432/crm_test")

from app import db as dbmod  # noqa: E402
from app.carriers.base import Carrier  # noqa: E402
from app.db import Base  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Product, User  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.services import settings as st  # noqa: E402
from app.services.seed import seed  # noqa: E402


@pytest.fixture(scope="session")
def engine():
    eng = dbmod.init_engine(TEST_DB)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    with engine.begin() as conn:
        names = ", ".join(t.name for t in reversed(Base.metadata.sorted_tables))
        conn.exec_driver_sql(f"TRUNCATE {names} RESTART IDENTITY CASCADE")
    session = dbmod.SessionLocal()
    seed(session)
    for username, role in (("manager1", "manager"), ("manager2", "manager"), ("store", "warehouse")):
        session.add(User(username=username, password_hash=hash_password("password123"), full_name=username, role=role))
    session.commit()
    yield session
    session.close()


@pytest.fixture()
def app(db):
    return create_app(TEST_DB, run_seed=False)


H = {"X-CRM": "1"}


def login(client: TestClient, username: str, password: str):
    """Клієнт JSON API під користувачем (класичного інтерфейсу більше немає — усе через /api)."""
    r = client.post("/api/auth/login", json={"username": username, "password": password}, headers=H)
    assert r.status_code == 200, r.text
    client.headers.update(H)
    return client


@pytest.fixture()
def admin(app):
    with TestClient(app) as c:
        yield login(c, "admin", "admin12345")


@pytest.fixture()
def manager(app):
    with TestClient(app) as c:
        yield login(c, "manager1", "password123")


@pytest.fixture()
def warehouse(app):
    with TestClient(app) as c:
        yield login(c, "store", "password123")


@pytest.fixture()
def anon(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def products(db):
    a = Product(sku="CREAM-1", name="Крем для рук", price=399, cost=120, stock=10, reserved=0, weight=0.3)
    b = Product(sku="SOAP-1", name="Мило ручної роботи", price=99, cost=30, stock=50, reserved=0, weight=0.1,
                is_upsell=True)
    db.add_all([a, b])
    db.commit()
    return a, b


@pytest.fixture()
def webhook_key(db):
    return st.get(db, "webhook_key")


class MockApi:
    """Підміна HTTP-клієнта перевізників: записує запити, відповідає за правилами."""

    def __init__(self):
        self.calls: list[dict] = []
        self.rules: list[tuple] = []

    def on(self, matcher, response):
        self.rules.append((matcher, response))

    def handler(self, request: httpx.Request) -> httpx.Response:
        body = request.content.decode() if request.content else ""
        import json as _j
        try:
            data = _j.loads(body) if body else {}
        except ValueError:
            data = {}
        call = {"method": request.method, "url": str(request.url), "json": data}
        self.calls.append(call)
        for matcher, response in self.rules:
            if (callable(matcher) and matcher(call)) or (isinstance(matcher, str) and re.search(matcher, call["url"] + " " + body)):
                resp = response(call) if callable(response) else response
                if isinstance(resp, httpx.Response):
                    return resp
                return httpx.Response(200, json=resp)
        return httpx.Response(404, json={"success": False, "errors": ["no mock"]})

    @property
    def client(self):
        return httpx.Client(transport=httpx.MockTransport(self.handler))


@pytest.fixture()
def mock_api(monkeypatch):
    api = MockApi()
    client = api.client
    monkeypatch.setattr(Carrier, "client", property(lambda self: client))
    return api
