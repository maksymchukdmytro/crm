import pytest

ADMIN_PAGES = [
    "/orders", "/orders/new", "/products", "/products/new", "/warehouse", "/purchases", "/purchases/new",
    "/suppliers", "/payments", "/reports", "/audit", "/profile",
    "/settings?tab=general", "/settings?tab=webhook", "/settings?tab=delivery", "/settings?tab=sms",
    "/settings?tab=statuses", "/settings?tab=users",
]


def test_login_required(anon):
    r = anon.get("/orders", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/classic/login")


def test_wrong_password(anon):
    r = anon.post("/login", data={"username": "admin", "password": "nope"})
    assert r.status_code == 401
    assert "Невірний логін" in r.text


@pytest.mark.parametrize("url", ADMIN_PAGES)
def test_admin_pages_render(admin, products, url):
    r = admin.get(url)
    assert r.status_code == 200, r.text[:2000]


def test_order_card_renders(admin, products, webhook_key):
    r = admin.post(f"http://testserver/api/v1/orders?key={webhook_key}", json={"name": "Іван Петренко", "phone": "0671234567",
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
    from app import web
    monkeypatch.setattr(web, "CLASSIC_ROOT", "/crm/classic")
    monkeypatch.setitem(web.templates.env.globals, "R", "/crm/classic")
    monkeypatch.setitem(web.templates.env.globals, "RA", "/crm")
    page = admin.get("/orders").text
    assert 'href="/crm/static/app.css' in page and 'href="/crm/classic/orders/new"' in page
    assert 'href="/orders' not in page and 'href="/crm/orders' not in page
    r = admin.post("/orders/new", data={"phone": "0671234567", "customer_name": "Тест"}, follow_redirects=False)
    assert r.headers["location"].startswith("/crm/classic/orders/")
    admin.post("/logout", follow_redirects=False)
    r = admin.get("/orders", follow_redirects=False)
    assert r.headers["location"] == "/crm/classic/login?next=/orders"
