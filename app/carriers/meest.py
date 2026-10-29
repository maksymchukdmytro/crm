"""Meest Express, OpenAPI v3.0.

Увага: інтеграцію написано за публічними описами API і не перевірено на
бойовому акаунті. Перед роботою зробіть тестове відправлення. Якщо назви
полів у вашій версії API відрізняються, правки вносяться лише в цьому файлі.
"""
from decimal import Decimal

import httpx

from ..models import Order
from .base import Carrier, CarrierError, ShipmentResult, TrackResult, order_weight

BASE = "https://api.meest.com/v3.0/openAPI"
_token_cache: dict[str, str] = {}


def meest_state(text: str) -> str:
    t = (text or "").lower()
    if "відмов" in t or "поверн" in t:
        return "refused"
    if "видано" in t or "отримано" in t or "вручено" in t:
        return "delivered"
    if "прибул" in t or "у відділенні" in t or "очікує" in t:
        return "arrived"
    if "створено" in t or "оформлено" in t:
        return "created"
    return "in_transit" if t else "unknown"


class Meest(Carrier):
    code = "meest"
    name = "Meest"
    beta = True

    def configured(self) -> bool:
        return bool(self.s.get("meest_username") and self.s.get("meest_password"))

    def _auth(self, force: bool = False) -> str:
        user = self.s.get("meest_username", "")
        if not force and _token_cache.get(user):
            return _token_cache[user]
        if not self.configured():
            raise CarrierError("Не вказано логін/пароль Meest (Налаштування → Доставка)")
        try:
            r = self.client.post(f"{BASE}/auth", json={"username": user, "password": self.s.get("meest_password")})
            data = r.json()
        except (httpx.HTTPError, ValueError) as e:
            raise CarrierError(f"Meest недоступний: {e}") from e
        token = ((data.get("result") or {}).get("token")) if isinstance(data, dict) else None
        if not token:
            raise CarrierError("Meest: не вдалося авторизуватися, перевірте логін і пароль")
        _token_cache[user] = token
        return token

    def _req(self, method: str, path: str, json: dict | None = None, raw: bool = False, retry: bool = True):
        token = self._auth()
        try:
            r = self.client.request(method, f"{BASE}/{path}", json=json, headers={"token": token})
        except httpx.HTTPError as e:
            raise CarrierError(f"Meest недоступний: {e}") from e
        if r.status_code == 401 and retry:
            self._auth(force=True)
            return self._req(method, path, json, raw, retry=False)
        if raw:
            if r.status_code >= 400:
                raise CarrierError(f"Meest ({r.status_code})")
            return r.content
        try:
            data = r.json()
        except ValueError as e:
            raise CarrierError(f"Meest ({r.status_code}): некоректна відповідь") from e
        status = data.get("status") if isinstance(data, dict) else None
        if r.status_code >= 400 or (status and str(status).upper() not in ("OK", "SUCCESS")):
            info = data.get("info") if isinstance(data, dict) else None
            msg = (info or {}).get("message") if isinstance(info, dict) else None
            raise CarrierError(f"Meest: {msg or data}"[:300])
        return data.get("result", data)

    def create_shipment(self, order: Order, opts: dict | None = None) -> ShipmentResult:
        if not self.s.get("meest_sender_branch_id"):
            raise CarrierError("Вкажіть ID відділення відправника Meest у налаштуваннях")
        if not order.warehouse_ref:
            raise CarrierError("Вкажіть ID відділення Meest отримувача (поле «ID відділення»)")
        cod = Decimal(order.cod_amount or 0)
        body = {
            "parcelNumber": "",
            "payType": "cash",
            "receiverPay": True,
            "notation": f"Замовлення {order.id}",
            "sender": {
                "name": self.s.get("meest_sender_name", ""), "phone": self.s.get("meest_sender_phone", ""),
                "service": "Branch", "branchID": self.s["meest_sender_branch_id"],
            },
            "receiver": {
                "name": order.customer_name, "phone": order.phone,
                "service": "Branch", "branchID": order.warehouse_ref,
            },
            "placesItems": [{"quantity": 1, "weight": float(order_weight(order, Decimal("0.5"))),
                             "insurance": float(max(Decimal(order.total or 0), Decimal(1)))}],
        }
        if cod > 0:
            body["COD"] = float(cod)
        res = self._req("POST", "parcel", body) or {}
        number = res.get("parcelNumber") or res.get("barCode") or ""
        if not number:
            raise CarrierError("Meest не повернув номер відправлення")
        return ShipmentResult(ttn=str(number), ref=str(res.get("parcelID", "")))

    def delete_shipment(self, order: Order):
        if not order.carrier_ref:
            raise CarrierError("Відправлення створене не через CRM — видаліть його в кабінеті Meest")
        self._req("DELETE", f"parcel/{order.carrier_ref}")

    def label_pdf(self, order: Order) -> bytes:
        if not order.carrier_ref:
            raise CarrierError("Наклейка доступна лише для відправлень, створених через CRM")
        content = self._req("GET", f"print/sticker100/{order.carrier_ref}", raw=True)
        if not content.startswith(b"%PDF"):
            raise CarrierError("Meest не повернув PDF наклейки")
        return content

    def track(self, orders: list[Order]) -> list[TrackResult]:
        results = []
        for o in orders:
            try:
                res = self._req("GET", f"tracking/{o.ttn}")
            except CarrierError:
                continue
            events = res if isinstance(res, list) else [res]
            last = events[-1] if events else {}
            text = str(last.get("eventName") or last.get("status") or last.get("statusName") or "")
            results.append(TrackResult(ttn=o.ttn, state=meest_state(text), status_text=text,
                                       code=str(last.get("eventCode", "")), raw=last if isinstance(last, dict) else {}))
        return results
