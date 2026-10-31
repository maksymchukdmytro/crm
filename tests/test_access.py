"""Вхід, ролі й службові сторінки після видалення класичного інтерфейсу: усе — JSON API + React."""

def test_login_required(anon):
    r = anon.get("/api/orders")
    assert r.status_code == 401 and r.json()["error"] == "Потрібна авторизація"


def test_wrong_password(anon):
    r = anon.post("/api/auth/login", json={"username": "admin", "password": "nope"}, headers={"X-CRM": "1"})
    assert r.status_code == 401


def test_classic_interface_is_gone(admin):
    """/classic більше не віддає серверних сторінок — лише застосунок (або 503, якщо фронтенд не зібрано)."""
    for url in ("/classic/orders", "/classic/login", "/static/app.css"):
        r = admin.get(url, follow_redirects=False)
        assert r.status_code in (200, 404, 503) and "<form" not in r.text


def test_order_print_and_export(admin, products, webhook_key):
    r = admin.post(f"/api/v1/orders?key={webhook_key}", json={"name": "Іван Петренко", "phone": "0671234567", "sku": "CREAM-1"})
    oid = r.json()["order_id"]
    page = admin.get(f"/api/orders/{oid}/print")
    assert page.status_code == 200 and "Петренко" in page.text and "До сплати при отриманні" in page.text
    assert f"№{oid}" in page.text and "399" in page.text
    csv = admin.get("/api/orders/export.csv")
    assert csv.status_code == 200 and csv.headers["content-type"].startswith("text/csv") and "Петренко" in csv.text


def test_role_restrictions(manager, warehouse):
    assert manager.get("/api/settings").status_code == 403
    assert manager.get("/api/payments").status_code == 403
    assert manager.get("/api/orders").status_code == 200
    assert warehouse.get("/api/orders").status_code == 200
    assert warehouse.get("/api/settings").status_code == 403


def test_logout(admin):
    assert admin.post("/api/auth/logout").status_code == 200
    assert admin.get("/api/orders").status_code == 401


def test_html_paths_without_session_open_the_app(anon):
    """Без входу будь-яка адреса інтерфейсу віддає застосунок (вхід показує React), а не серверну форму."""
    r = anon.get("/orders", follow_redirects=False)
    assert r.status_code in (200, 503)
