import pytest

ADMIN_PAGES = [
    "/orders", "/orders/new", "/products", "/products/new", "/warehouse", "/purchases", "/purchases/new",
    "/suppliers", "/payments", "/reports", "/audit", "/profile",
    "/settings?tab=general", "/settings?tab=webhook", "/settings?tab=delivery", "/settings?tab=sms",
    "/settings?tab=statuses", "/settings?tab=users",
]


def test_login_required(anon):
    r = anon.get("/orders", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/login")


def test_wrong_password(anon):
    r = anon.post("/login", data={"username": "admin", "password": "nope"})
    assert r.status_code == 401
    assert "Невірний логін" in r.text


@pytest.mark.parametrize("url", ADMIN_PAGES)
def test_admin_pages_render(admin, products, url):
    r = admin.get(url)
    assert r.status_code == 200, r.text[:2000]


def test_order_card_renders(admin, products, webhook_key):
    r = admin.post(f"/api/v1/orders?key={webhook_key}", json={"name": "Іван Петренко", "phone": "0671234567",
                                                               "sku": "CREAM-1"})
    oid = r.json()["order_id"]
    for url in (f"/orders/{oid}", f"/orders/{oid}/print"):
        assert admin.get(url).status_code == 200


def test_role_restrictions(manager, warehouse):
    assert manager.get("/settings").status_code == 403
    assert manager.get("/payments").status_code == 403
    assert manager.get("/warehouse").status_code == 403
    assert manager.get("/reports").status_code == 200
    assert warehouse.get("/warehouse").status_code == 200
    assert warehouse.get("/reports").status_code == 403
    assert warehouse.get("/orders").status_code == 200


def test_logout(admin):
    admin.post("/logout")
    assert admin.get("/orders", follow_redirects=False).status_code == 303


def test_root_path_prefix(monkeypatch, admin, products):
    """CRM за адресою /crm: посилання й редиректи з префіксом (nginx прибирає його перед застосунком)."""
    from app.config import config
    from app.web import templates
    monkeypatch.setattr(config, "ROOT_PATH", "/crm")
    monkeypatch.setitem(templates.env.globals, "R", "/crm")
    page = admin.get("/orders").text
    assert 'href="/crm/static/app.css' in page and 'href="/crm/orders/new"' in page
    assert 'href="/orders' not in page
    r = admin.post("/orders/new", data={"phone": "0671234567", "customer_name": "Тест"}, follow_redirects=False)
    assert r.headers["location"].startswith("/crm/orders/")
    admin.post("/logout")
    r = admin.get("/orders", follow_redirects=False)
    assert r.headers["location"] == "/crm/login?next=/orders"
