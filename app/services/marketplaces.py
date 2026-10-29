"""Маркетплейси Rozetka і Prom: імпорт замовлень у CRM і передача статусів назад.

Rozetka Seller API: https://api-seller.rozetka.com.ua — вхід POST /sites (логін + пароль у base64) → Bearer-токен;
замовлення GET /orders/search, статуси GET /orders/statuses, зміна PUT /orders/{id}.
Prom API: https://my.prom.ua/api/v1 — Bearer-токен з кабінету; GET /orders/list, POST /orders/set_status.

Відповіді маркетплейсів розбираються обережно (кілька можливих назв полів), а сирий фрагмент першого
замовлення видно в «Перевірити підключення» — щоб звірити поля до бойового імпорту.
"""
from __future__ import annotations

import base64
import logging
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

import httpx
from sqlalchemy.orm import Session

from ..models import MarketplaceShop, Order, OrderSource, PaymentMethod, Product, Status, utcnow
from . import audit, events
from . import orders as order_svc
from .names import join_name, split_full_name

log = logging.getLogger("crm.marketplaces")

ROZETKA_API = "https://api-seller.rozetka.com.ua"
PROM_API = "https://my.prom.ua/api/v1"
KINDS = {"rozetka": "Rozetka", "prom": "Prom"}

# Статуси Prom (фіксований перелік API)
PROM_STATUSES = {"pending": "Новий / в обробці", "received": "Прийнятий", "delivered": "Виконаний",
                 "canceled": "Скасований", "paid": "Оплачений"}

# Типові відповідності, якщо адміністратор не налаштував інакше
DELIVERY_GUESS = [("rozetka", "rozetka"), ("розетк", "rozetka"), ("octopus", "rozetka"), ("нова пошта", "novaposhta"), ("nova", "novaposhta"), ("укрпошт", "ukrposhta"),
                  ("meest", "meest"), ("міст", "meest"), ("самовив", "pickup"), ("кур'єр", "courier"), ("курьер", "courier")]


class MarketplaceError(Exception):
    pass


_client: httpx.Client | None = None


def http() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(timeout=30)
    return _client


def _money(v) -> Decimal:
    if v is None or v == "":
        return Decimal(0)
    if isinstance(v, (int, float, Decimal)):
        return Decimal(str(v))
    s = "".join(ch for ch in str(v).replace(",", ".") if ch.isdigit() or ch == ".")
    try:
        return Decimal(s or "0")
    except InvalidOperation:
        return Decimal(0)


def _g(d: dict | None, *keys, default=""):
    """Перше непорожнє значення з кількох можливих ключів (у т.ч. вкладених через крапку)."""
    for k in keys:
        cur = d
        for part in k.split("."):
            cur = cur.get(part) if isinstance(cur, dict) else None
        if cur not in (None, "", [], {}):
            return cur
    return default


# ---------------------------------------------------------------- клієнти API
class RozetkaClient:
    def __init__(self, shop: MarketplaceShop):
        self.shop = shop

    def _token(self) -> str:
        s = self.shop
        if s.token and s.token_until and s.token_until > utcnow():
            return s.token
        if not s.login or not s.secret:
            raise MarketplaceError("Вкажіть логін і пароль кабінету продавця Rozetka")
        pw = base64.b64encode(s.secret.encode()).decode()
        try:
            r = http().post(f"{ROZETKA_API}/sites", json={"username": s.login, "password": pw})
            data = r.json()
        except (httpx.HTTPError, ValueError) as e:
            raise MarketplaceError(f"Rozetka недоступна: {e}") from e
        if not data.get("success"):
            raise MarketplaceError("Rozetka: не вдалося увійти — перевірте логін і пароль (" + _errors(data) + ")")
        s.token = (data.get("content") or {}).get("access_token", "")
        s.token_until = utcnow() + timedelta(hours=20)
        return s.token

    def call(self, method: str, path: str, **kw) -> dict:
        try:
            r = http().request(method, f"{ROZETKA_API}{path}", headers={"Authorization": f"Bearer {self._token()}",
                                                                       "Content-Language": "uk"}, **kw)
            data = r.json()
        except (httpx.HTTPError, ValueError) as e:
            raise MarketplaceError(f"Rozetka недоступна: {e}") from e
        if not data.get("success"):
            if r.status_code == 401:
                self.shop.token = ""
            raise MarketplaceError("Rozetka: " + _errors(data))
        return data.get("content") or {}

    def pdf(self, method: str, path: str, **kw) -> bytes:
        """Запит, що повертає файл (PDF); помилку Rozetka віддає JSON-ом."""
        try:
            r = http().request(method, f"{ROZETKA_API}{path}", headers={"Authorization": f"Bearer {self._token()}",
                                                                       "Content-Language": "uk"}, **kw)
        except httpx.HTTPError as e:
            raise MarketplaceError(f"Rozetka недоступна: {e}") from e
        if r.content.startswith(b"%PDF"):
            return r.content
        try:
            data = r.json()
        except ValueError:
            raise MarketplaceError(f"Rozetka не повернула PDF (код {r.status_code})")
        if r.status_code == 401:
            self.shop.token = ""
        raise MarketplaceError("Rozetka: " + _errors(data))

    def delivery_label(self, ttn: str) -> bytes:
        """Маркування (ТТН) ROZETKA Delivery — модуль Octopus: POST /delivery-rozetka/ttn-print-batch."""
        return self.pdf("POST", "/delivery-rozetka/ttn-print-batch", json={"track_numbers": [ttn]})

    def statuses(self) -> dict[str, str]:
        c = self.call("GET", "/orders/statuses")
        items = c.get("data") if isinstance(c, dict) else c
        out = {}
        for x in items or []:
            out[str(x.get("id"))] = x.get("name_uk") or x.get("name_ua") or x.get("name") or str(x.get("id"))
        return out

    def orders(self, since: datetime | None, max_pages: int = 10) -> list[dict]:
        res = []
        params = {"types": 1, "sort": "-id", "expand": "purchases,delivery,user,payment"}
        if since:
            params["created_from"] = since.strftime("%Y-%m-%d")
        for page in range(1, max_pages + 1):
            c = self.call("GET", "/orders/search", params={**params, "page": page})
            orders = c.get("orders") or c.get("data") or []
            res.extend(orders)
            meta = c.get("_meta") or {}
            if not orders or page >= int(meta.get("pageCount") or 1):
                break
        return res

    def set_status(self, external_id: str, status: str, ttn: str = ""):
        body: dict = {"status": int(status) if str(status).isdigit() else status}
        if ttn:
            body["ttn"] = ttn
        self.call("PUT", f"/orders/{external_id}", json=body)

    # --- розбір замовлення Rozetka у поля CRM
    @staticmethod
    def parse(o: dict) -> dict:
        user = o.get("recipient_title") or o.get("user_title") or {}
        if isinstance(user, str):
            last, first, middle = split_full_name(user)
        else:
            last, first, middle = (user.get("last_name") or "", user.get("first_name") or "",
                                   user.get("second_name") or user.get("middle_name") or "")
            if not (last or first) and user.get("full_name"):
                last, first, middle = split_full_name(user["full_name"])
        d = o.get("delivery") or {}
        city = d.get("city") or {}
        city_name = city.get("name_ua") or city.get("title") or city.get("name") if isinstance(city, dict) else str(city)
        place = ", ".join(str(x) for x in (_g(d, "place_number"), _g(d, "place_street"), _g(d, "place_house")) if x)
        items = []
        for p in o.get("purchases") or []:
            item = p.get("item") or {}
            items.append({"name": p.get("item_name") or item.get("name_ua") or item.get("name") or "Товар",
                          "sku": str(item.get("article") or item.get("price_offer_id") or p.get("item_id") or ""),
                          "qty": int(p.get("quantity") or 1),
                          "price": _money(p.get("price_with_discount") or p.get("price") or 0)})
        pay = o.get("payment") or {}
        return {
            "external_id": str(o.get("id")),
            "external_status": str(o.get("status") or ""),
            "last_name": last, "first_name": first, "middle_name": middle,
            "phone": o.get("recipient_phone") or o.get("user_phone") or "",
            "email": _g(o, "user.email", "email"),
            "comment": o.get("comment") or "",
            "delivery_service": str(d.get("delivery_service_name") or d.get("name_logo") or ""),
            "city_name": city_name or "",
            "warehouse_name": place or str(d.get("place_name") or ""),
            "ttn": str(o.get("ttn") or "").replace(" ", ""),
            "payment": str(pay.get("payment_method_name") or pay.get("payment_type_title") or o.get("payment_type_name")
                           or o.get("payment_type") or ""),
            "paid": str(pay.get("payment_status") or pay.get("status_payment") or "").lower() in ("paid", "success", "1", "true"),
            "total": _money(o.get("amount_with_discount") or o.get("amount") or o.get("cost_with_discount") or o.get("cost")),
            "items": items,
            "created": o.get("created") or "",
        }


class PromClient:
    def __init__(self, shop: MarketplaceShop):
        self.shop = shop

    def call(self, method: str, path: str, **kw) -> dict:
        if not self.shop.secret:
            raise MarketplaceError("Вкажіть API-токен Prom (кабінет Prom → Налаштування → Керування API-токенами)")
        try:
            r = http().request(method, f"{PROM_API}{path}", headers={"Authorization": f"Bearer {self.shop.secret}",
                                                                     "X-LANGUAGE": "uk"}, **kw)
            data = r.json()
        except (httpx.HTTPError, ValueError) as e:
            raise MarketplaceError(f"Prom недоступний: {e}") from e
        if r.status_code >= 400 or (isinstance(data, dict) and data.get("error")):
            raise MarketplaceError("Prom: " + str(data.get("error") if isinstance(data, dict) else r.status_code))
        return data

    def statuses(self) -> dict[str, str]:
        return dict(PROM_STATUSES)

    def orders(self, since: datetime | None, max_pages: int = 10) -> list[dict]:
        res, last_id = [], None
        for _ in range(max_pages):
            params: dict = {"limit": 100}
            if since:
                params["date_from"] = since.strftime("%Y-%m-%dT%H:%M:%S")
            if last_id:
                params["last_id"] = last_id
            orders = self.call("GET", "/orders/list", params=params).get("orders") or []
            res.extend(orders)
            if len(orders) < 100:
                break
            last_id = orders[-1].get("id")
        return res

    def set_status(self, external_id: str, status: str, ttn: str = ""):
        body = {"status": status, "ids": [int(external_id) if external_id.isdigit() else external_id]}
        if status == "canceled":
            body["cancellation_reason"] = "another"
        self.call("POST", "/orders/set_status", json=body)

    @staticmethod
    def parse(o: dict) -> dict:
        dp = o.get("delivery_provider_data") or {}
        items = [{"name": p.get("name") or _g(p, "name_multilang.uk") or "Товар", "sku": str(p.get("sku") or p.get("external_id") or ""),
                  "qty": int(_money(p.get("quantity") or 1)) or 1, "price": _money(p.get("price"))}
                 for p in o.get("products") or []]
        return {
            "external_id": str(o.get("id")),
            "external_status": str(o.get("status") or ""),
            "last_name": o.get("client_last_name") or "", "first_name": o.get("client_first_name") or "",
            "middle_name": o.get("client_second_name") or "",
            "phone": o.get("phone") or "",
            "email": o.get("email") or "",
            "comment": o.get("client_notes") or "",
            "delivery_service": str(_g(o, "delivery_option.name") or dp.get("provider") or ""),
            "city_name": "",
            "warehouse_name": str(o.get("delivery_address") or ""),
            "ttn": str(dp.get("declaration_number") or "").replace(" ", ""),
            "payment": str(_g(o, "payment_option.name") or _g(o, "payment_data.type") or ""),
            "paid": str(_g(o, "payment_data.status")).lower() in ("paid", "success"),
            "total": _money(o.get("full_price") or o.get("price")),
            "items": items,
            "created": o.get("date_created") or "",
        }


def client(shop: MarketplaceShop):
    return RozetkaClient(shop) if shop.kind == "rozetka" else PromClient(shop)


def _errors(data: dict) -> str:
    e = data.get("errors") or data.get("error") or data.get("message") or "невідома помилка"
    if isinstance(e, dict):
        return "; ".join(f"{k}: {v}" for k, v in e.items()) if "message" not in e else str(e["message"])
    if isinstance(e, list):
        return "; ".join(str(x) for x in e)
    return str(e)


# ---------------------------------------------------------------- імпорт
def is_rozetka_delivery(order: Order) -> bool:
    """Відправлення ROZETKA Delivery: служба «Rozetka Delivery» або ТТН виду RMP-…"""
    return order.delivery_method == "rozetka" or (order.ttn or "").upper().startswith("RMP-")


def rozetka_label(db: Session, order: Order) -> bytes:
    """PDF-маркування Rozetka для замовлення (через API магазину, з якого прийшло замовлення, або перший магазин Rozetka)."""
    if not order.ttn:
        raise MarketplaceError("У замовлення ще немає ТТН Rozetka")
    shop = db.get(MarketplaceShop, order.shop_id) if order.shop_id else None
    if shop is None or shop.kind != "rozetka":
        shop = (db.query(MarketplaceShop).filter(MarketplaceShop.kind == "rozetka", MarketplaceShop.is_active.is_(True))
                .order_by(MarketplaceShop.id).first())
    if shop is None:
        raise MarketplaceError("Додайте магазин Rozetka в «Налаштування → Маркетплейси», щоб друкувати маркування")
    pdf = RozetkaClient(shop).delivery_label(order.ttn)
    db.commit()  # зберегти свіжий токен
    return pdf


def _guess_delivery(shop: MarketplaceShop, name: str, ttn: str = "") -> str:
    if ttn.upper().startswith("RMP-"):
        return "rozetka"
    m = (shop.delivery_map or {}).get(name)
    if m:
        return m
    low = name.lower()
    for needle, code in DELIVERY_GUESS:
        if needle in low:
            return code
    return "novaposhta"


def _guess_payment(db: Session, shop: MarketplaceShop, name: str, paid: bool) -> int | None:
    m = (shop.payment_map or {}).get(name)
    if m:
        return int(m)
    ids = {pm.id for pm in db.query(PaymentMethod.id).all()}
    # типово як у LP-CRM: Rozetka — RozetkaPay (14) / Післяплата Rozetka (15); Prom — Пром-оплата (10) / Післяплата NovaPay (16)
    if shop.kind == "rozetka":
        pid = 14 if paid else 15
    else:
        pid = 10 if paid or "пром" in name.lower() or "prom" in name.lower() else 16
    return pid if pid in ids else None


def _match_product(db: Session, sku: str, name: str) -> Product | None:
    if sku:
        p = db.query(Product).filter(Product.sku == sku).one_or_none()
        if p:
            return p
    if name:  # як у LP-CRM: товари маркетплейсу зіставляються за назвою
        return db.query(Product).filter(Product.name.ilike(name.strip())).first()
    return None


def import_order(db: Session, shop: MarketplaceShop, data: dict) -> tuple[Order, bool]:
    """Створює замовлення з даних маркетплейсу або оновлює наявне (ТТН, статус маркетплейсу). → (замовлення, нове?)"""
    order = db.query(Order).filter(Order.shop_id == shop.id, Order.external_id == data["external_id"]).one_or_none()
    if order is not None:
        changed = {}
        if data["ttn"] and not order.ttn:
            order.ttn = data["ttn"]
            changed["ТТН"] = data["ttn"]
            if data["ttn"].upper().startswith("RMP-"):
                order.delivery_method = "rozetka"
        if data["external_status"] and order.external_status != data["external_status"]:
            changed["статус маркетплейсу"] = [order.external_status, data["external_status"]]
            order.external_status = data["external_status"]
        if changed:
            audit.log(db, None, "order", order.id, "update", {"маркетплейс": KINDS.get(shop.kind), **changed})
            events.order_changed(db, order.id)
        return order, False

    src = shop.source_id or (db.query(OrderSource.id).filter(OrderSource.name == "Маркетплейси").scalar())
    fields = {
        "last_name": data["last_name"], "first_name": data["first_name"], "middle_name": data["middle_name"],
        "phone": data["phone"], "email": data["email"], "comment": data["comment"],
        "delivery_method": _guess_delivery(shop, data["delivery_service"], data["ttn"]),
        "city_name": data["city_name"], "warehouse_name": data["warehouse_name"], "ttn": data["ttn"],
        "payment_method_id": _guess_payment(db, shop, data["payment"], data["paid"]),
        "office_id": shop.office_id, "source_id": src, "site": f"{KINDS.get(shop.kind)} · {shop.name}".strip(" ·"),
    }
    if shop.extra_field in (1, 2, 3, 4):
        fields[f"extra{shop.extra_field}"] = f"{KINDS.get(shop.kind)}({shop.name})" if shop.name else KINDS.get(shop.kind, "")
    items = []
    for it in data["items"]:
        p = _match_product(db, it["sku"], it["name"])
        items.append({"product_id": p.id if p else "", "name": p.name if p else it["name"], "qty": it["qty"], "price": it["price"]})
    order = order_svc.create_order(db, fields, items, user=None, source="marketplace")
    order.shop_id, order.external_id, order.external_status = shop.id, data["external_id"], data["external_status"]
    if shop.import_status_id:
        st = db.get(Status, shop.import_status_id)
        if st is not None and st.id != order.status_id:
            order_svc.change_status(db, order, st, None, auto=True, reason=f"імпорт з {KINDS.get(shop.kind)}")
    audit.log(db, None, "order", order.id, "import", {"маркетплейс": KINDS.get(shop.kind), "магазин": shop.name,
                                                       "номер": data["external_id"]})
    return order, True


def sync_shop(db: Session, shop: MarketplaceShop) -> dict:
    stats = {"new": 0, "updated": 0, "seen": 0, "error": ""}
    # нові й оновлені замовлення за останні 14 днів (не раніше дати старту магазину)
    border = utcnow() - timedelta(days=14)
    since = max(datetime.combine(shop.since, datetime.min.time()) if shop.since and not isinstance(shop.since, datetime)
                else (shop.since or border), border)
    try:
        c = client(shop)
        raw = c.orders(since)
        seen_pay, seen_del = set((shop.directory or {}).get("payments", [])), set((shop.directory or {}).get("deliveries", []))
        for o in raw:
            data = c.parse(o)
            if not data["external_id"] or data["external_id"] == "None":
                continue
            stats["seen"] += 1
            seen_pay.add(data["payment"]) if data["payment"] else None
            seen_del.add(data["delivery_service"]) if data["delivery_service"] else None
            with db.begin_nested():
                _, new = import_order(db, shop, data)
            stats["new" if new else "updated"] += 1
        shop.directory = {**(shop.directory or {}), "payments": sorted(seen_pay), "deliveries": sorted(seen_del)}
        shop.last_error = ""
        shop.imported = (shop.imported or 0) + stats["new"]
    except MarketplaceError as e:
        shop.last_error = str(e)[:1000]
        stats["error"] = str(e)
    shop.last_sync_at = utcnow()
    db.commit()
    return stats


def sync_all(db: Session) -> dict:
    out = {}
    for shop in db.query(MarketplaceShop).filter(MarketplaceShop.is_active.is_(True)).all():
        out[shop.id] = sync_shop(db, shop)
    return out


def check(db: Session, shop: MarketplaceShop) -> dict:
    """Перевірка підключення: статуси маркетплейсу + перше замовлення (сирі поля й як CRM їх розібрала)."""
    c = client(shop)
    statuses = c.statuses()
    shop.directory = {**(shop.directory or {}), "statuses": statuses}
    raw = c.orders(utcnow() - timedelta(days=30), max_pages=1)
    sample = raw[0] if raw else None
    parsed = c.parse(sample) if sample else None
    db.commit()
    if parsed:
        parsed = {**parsed, "total": float(parsed["total"]), "items": [{**i, "price": float(i["price"])} for i in parsed["items"]]}
    return {"statuses": statuses, "orders_30d": len(raw), "sample_parsed": parsed,
            "sample_keys": sorted(sample.keys()) if isinstance(sample, dict) else []}


def push_status(db: Session, order: Order) -> str | None:
    """Передати статус замовлення на маркетплейс за відповідністю статусів магазину. → помилка або None."""
    if not order.shop_id or not order.external_id:
        return None
    shop = db.get(MarketplaceShop, order.shop_id)
    if shop is None or not shop.is_active:
        return None
    target = (shop.status_map or {}).get(str(order.status_id))
    if not target or target == order.external_status:
        return None
    try:
        client(shop).set_status(order.external_id, str(target), order.ttn or "")
        order.external_status = str(target)
        audit.log(db, None, "order", order.id, "update", {"маркетплейс": KINDS.get(shop.kind), "статус передано": target})
        return None
    except MarketplaceError as e:
        log.warning("Статус замовлення %s не передано на %s: %s", order.id, shop.kind, e)
        audit.log(db, None, "order", order.id, "update", {"маркетплейс": KINDS.get(shop.kind), "помилка": str(e)[:200]})
        return str(e)
