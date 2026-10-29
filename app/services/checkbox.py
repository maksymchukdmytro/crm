"""Checkbox (програмний РРО): чеки продажу, повернення, передоплати й післяплати по замовленнях.

API: https://api.checkbox.ua/api/v1 (тестовий сервер — https://dev-api.checkbox.in.ua/api/v1).
Касир входить логіном і паролем → Bearer-токен; дії з касою — із заголовком X-License-Key (ключ ліцензії каси).
Перед чеком потрібна відкрита зміна: якщо увімкнено «автозміни», CRM відкриває її сама і закриває о 23:00.
Суми в API — у копійках, кількість — у тисячних (1 шт = 1000).
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import timedelta
from decimal import Decimal

import httpx
from sqlalchemy.orm import Session

from ..models import CHECKBOX_PAYMENTS, CheckboxCashier, CheckboxReceipt, Order, utcnow
from . import audit, events
from . import settings as st

log = logging.getLogger("crm.checkbox")

PROD = "https://api.checkbox.ua/api/v1"
TEST = "https://dev-api.checkbox.in.ua/api/v1"
KINDS = {"sell": "Чек продажу", "return": "Чек повернення", "prepay": "Чек передоплати", "postpay": "Чек післяплати"}
STATUS_KEYS = {"sell": "cb_sell_status", "return": "cb_return_status", "prepay": "cb_prepay_status", "postpay": "cb_postpay_status"}


class CheckboxError(Exception):
    pass


_client: httpx.Client | None = None


def http() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(timeout=40)
    return _client


def receipt_url(r: CheckboxReceipt) -> str:
    """Публічне посилання на чек (для тестової каси посилання немає)."""
    return f"https://check.checkbox.ua/{r.checkbox_id}" if r.checkbox_id and not r.test and r.status == "done" else ""


class Api:
    def __init__(self, c: CheckboxCashier):
        self.c = c
        self.base = TEST if c.test_mode else PROD

    def _headers(self, auth: bool = True) -> dict:
        h = {"X-Client-Name": "CRM", "X-Client-Version": "1.0", "X-License-Key": self.c.license_key}
        if auth:
            h["Authorization"] = f"Bearer {self._token()}"
        return h

    def _token(self) -> str:
        c = self.c
        if c.token and c.token_until and c.token_until > utcnow():
            return c.token
        if not (c.login and c.password and c.license_key):
            raise CheckboxError("Вкажіть ключ ліцензії каси, логін і пароль касира")
        data = self._req("POST", "/cashier/signin", auth=False, json={"login": c.login, "password": c.password})
        c.token = data.get("access_token", "")
        c.token_until = utcnow() + timedelta(hours=12)
        return c.token

    def _req(self, method: str, path: str, auth: bool = True, **kw) -> dict:
        try:
            r = http().request(method, self.base + path, headers=self._headers(auth), **kw)
        except httpx.HTTPError as e:
            raise CheckboxError(f"Checkbox недоступний: {e}") from e
        try:
            data = r.json()
        except ValueError:
            data = {}
        if r.status_code >= 400:
            if r.status_code == 401 and auth:
                self.c.token = ""
            msg = data.get("message") or data.get("detail") or r.text[:200]
            if isinstance(msg, list):
                msg = "; ".join(str(m.get("msg", m)) if isinstance(m, dict) else str(m) for m in msg)
            raise CheckboxError(f"Checkbox: {msg}")
        return data if isinstance(data, dict) else {"items": data}

    def ensure_shift(self, wait: float = 15.0):
        shift = self._req("GET", "/cashier/shift")
        if shift and shift.get("status") == "OPENED":
            return shift
        if not self.c.auto_shift:
            raise CheckboxError("Зміна каси закрита — відкрийте її в Checkbox або увімкніть автозміни")
        if not shift or shift.get("status") in (None, "CLOSED"):
            shift = self._req("POST", "/shifts", json={})
        until = time.monotonic() + wait
        while shift.get("status") != "OPENED" and time.monotonic() < until:
            time.sleep(1)
            shift = self._req("GET", f"/shifts/{shift.get('id')}")
        if shift.get("status") != "OPENED":
            raise CheckboxError("Checkbox не встиг відкрити зміну — спробуйте ще раз за хвилину")
        return shift

    def close_shift(self):
        shift = self._req("GET", "/cashier/shift")
        if shift and shift.get("status") == "OPENED":
            self._req("POST", "/shifts/close", json={})

    def sell(self, body: dict) -> dict:
        self.ensure_shift()
        return self._req("POST", "/receipts/sell", json=body)

    def receipt(self, rid: str) -> dict:
        return self._req("GET", f"/receipts/{rid}")


def order_entity(db: Session, order: Order):
    """Юрособа замовлення, а якщо не вибрана — юрособа за замовчуванням."""
    from ..models import LegalEntity
    if order.legal_entity_id:
        return db.get(LegalEntity, order.legal_entity_id)
    return db.query(LegalEntity).filter(LegalEntity.is_default.is_(True), LegalEntity.is_active.is_(True)).first()


def pick_cashier(db: Session, order: Order) -> CheckboxCashier | None:
    """Каса — за юридичною особою замовлення. Якщо юросіб ще не заведено, діють старі умови вибору."""
    from ..models import LegalEntity
    if db.query(LegalEntity).count():
        entity = order_entity(db, order)
        if entity is None:
            return None
        return (db.query(CheckboxCashier).filter(CheckboxCashier.is_active.is_(True), CheckboxCashier.legal_entity_id == entity.id)
                .order_by(CheckboxCashier.sort, CheckboxCashier.id).first())
    for c in db.query(CheckboxCashier).filter(CheckboxCashier.is_active.is_(True)).order_by(CheckboxCashier.sort, CheckboxCashier.id):
        v = c.condition_value
        if c.condition == "none" \
                or (c.condition == "office" and order.office_id == v) \
                or (c.condition == "user" and order.manager_id == v) \
                or (c.condition == "np_account" and order.np_account_id == v):
            return c
    return None


def _kop(v) -> int:
    return int((Decimal(str(v or 0)) * 100).quantize(Decimal("1")))


def _payment(order: Order, amount: int) -> dict:
    key = order.payment_method.checkbox_type if order.payment_method else ""
    if key == "cash" or not key and order.payment_type == "cod":
        return {"type": "CASH", "value": amount, "label": "Готівка"}
    return {"type": "CASHLESS", "value": amount, "label": CHECKBOX_PAYMENTS.get(key, "Картка")}


def build_body(order: Order, kind: str, cashier: CheckboxCashier) -> tuple[dict, Decimal]:
    goods = []
    for i, it in enumerate(order.items, 1):
        code = (it.product.sku if it.product and it.product.sku else "") or (str(it.product_id) if it.product_id else f"item{i}")
        goods.append({"good": {"code": code[:64], "name": it.name[:256], "price": _kop(it.price)},
                      "quantity": int(it.qty) * 1000, "is_return": kind == "return"})
    if not goods:
        raise CheckboxError("У замовленні немає товарів")
    subtotal = sum((Decimal(str(it.price or 0)) * it.qty for it in order.items), Decimal(0))
    discount = min(Decimal(order.discount or 0), subtotal)
    total = subtotal - discount
    if kind == "prepay":
        total = Decimal(order.prepayment or 0)
    elif kind == "postpay":
        total = Decimal(order.cod_amount or 0)
    if total <= 0:
        raise CheckboxError("Сума чека нульова")
    body = {"id": str(uuid.uuid4()), "cashier_name": cashier.name or None, "goods": goods,
            "payments": [_payment(order, _kop(total))], "footer": f"Замовлення №{order.id}"}
    if discount > 0 and kind in ("sell", "return"):
        body["discounts"] = [{"type": "DISCOUNT", "mode": "VALUE", "value": _kop(discount), "name": "Знижка"}]
    if kind in ("prepay", "postpay"):  # частина суми: чек на всю суму товарів, оплачено лише частину — як передоплата
        body["payments"] = [_payment(order, _kop(total))]
        body["rounding"] = False
    if order.email or order.phone:
        body["delivery"] = {k: v for k, v in (("email", order.email), ("phone", order.phone)) if v}
    return body, total


def create_receipt(db: Session, order: Order, kind: str, user=None) -> CheckboxReceipt:
    if kind not in KINDS:
        raise CheckboxError("Невідомий вид чека")
    if kind == "sell" and any(r.kind == "sell" and r.status == "done" for r in receipts(db, order)):
        raise CheckboxError("Чек продажу для цього замовлення вже є")
    cashier = pick_cashier(db, order)
    if cashier is None:
        entity = order_entity(db, order)
        if entity is not None:
            raise CheckboxError(f"Для юрособи «{entity.name}» немає активної каси Checkbox (Налаштування → Checkbox)")
        raise CheckboxError("Немає каси Checkbox для цього замовлення: виберіть юрособу або задайте її за замовчуванням")
    body, total = build_body(order, kind, cashier)
    rec = CheckboxReceipt(order_id=order.id, cashier_id=cashier.id, kind=kind, total=total, test=cashier.test_mode,
                          checkbox_id=body["id"])
    db.add(rec)
    api = Api(cashier)
    try:
        data = api.sell(body)
        rec.checkbox_id = str(data.get("id") or body["id"])
        rec.fiscal_code = str(data.get("fiscal_code") or "")
        rec.status = "done" if data.get("status") in ("DONE", None) or rec.fiscal_code else "new"
        cashier.last_error = ""
    except CheckboxError as e:
        rec.status, rec.error = "error", str(e)[:1000]
        cashier.last_error = str(e)[:1000]
    audit.log(db, user, "order", order.id, "receipt", {"чек": KINDS[kind], "сума": total, "статус": rec.status,
                                                       **({"помилка": rec.error} if rec.error else {})})
    events.order_changed(db, order.id)
    db.flush()
    return rec


def receipts(db: Session, order: Order) -> list[CheckboxReceipt]:
    return db.query(CheckboxReceipt).filter(CheckboxReceipt.order_id == order.id).order_by(CheckboxReceipt.id).all()


def on_status(db: Session, order: Order):
    """Автоматичні чеки за статусом (Налаштування → Checkbox → Автоматизація)."""
    s = st.get_all(db)
    for kind, key in STATUS_KEYS.items():
        if s.get(key) and s[key] == str(order.status_id):
            if any(r.kind == kind and r.status == "done" for r in receipts(db, order)):
                continue
            from . import queue
            from .events import after_commit
            if queue.available():
                oid = order.id
                after_commit(db, f"cb:{oid}:{kind}", lambda oid=oid, k=kind: queue.enqueue("checkbox_receipt", oid, k))
            else:
                create_receipt(db, order, kind)


def close_shifts(db: Session) -> int:
    n = 0
    for c in db.query(CheckboxCashier).filter(CheckboxCashier.is_active.is_(True), CheckboxCashier.auto_shift.is_(True)):
        try:
            Api(c).close_shift()
            n += 1
        except CheckboxError as e:
            c.last_error = str(e)[:1000]
    db.commit()
    return n
