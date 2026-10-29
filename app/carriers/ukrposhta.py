"""Укрпошта: eCom API 0.0.1 та Status Tracking API.

Документація: https://dev.ukrposhta.ua/documentation
Схема створення відправлення: адреса (індекс) → клієнт-отримувач → відправлення.
"""
from decimal import Decimal

import httpx

from ..models import Order
from .base import Carrier, CarrierError, ShipmentResult, TrackResult, name_parts, order_weight


def up_state(event_name: str, code: str = "") -> str:
    t = (event_name or "").lower()
    if "відправник" in t and ("вручено" in t or "повернуто" in t):
        return "returned"
    if "вручено" in t or "вручене" in t or code in ("41000", "41002"):
        return "delivered"
    if "поверн" in t or "відмов" in t:
        return "refused"
    if "надійшло" in t or "прибуло" in t or "очікує" in t:
        return "arrived"
    if "створено" in t or "прийнято" in t or "зареєстровано" in t:
        return "created" if "створено" in t else "in_transit"
    return "in_transit" if t else "unknown"


class Ukrposhta(Carrier):
    code = "ukrposhta"
    name = "Укрпошта"
    beta = True

    @property
    def host(self) -> str:
        return "https://dev.ukrposhta.ua" if self.s.get("up_sandbox") == "1" else "https://www.ukrposhta.ua"

    def configured(self) -> bool:
        return bool(self.s.get("up_bearer") and self.s.get("up_token"))

    def _req(self, method: str, path: str, json: dict | None = None, *, bearer: str | None = None,
             base: str = "ecom/0.0.1", token: bool = True, raw: bool = False):
        bearer = bearer or self.s.get("up_bearer")
        if not bearer:
            raise CarrierError("Не вказано bearer-токен Укрпошти (Налаштування → Доставка)")
        params = {"token": self.s.get("up_token", "")} if token else {}
        url = f"{self.host}/{base}/{path.lstrip('/')}"
        try:
            r = self.client.request(method, url, json=json, params=params,
                                    headers={"Authorization": f"Bearer {bearer}"})
        except httpx.HTTPError as e:
            raise CarrierError(f"Укрпошта недоступна: {e}") from e
        if r.status_code >= 400:
            try:
                msg = r.json().get("message") or r.text
            except ValueError:
                msg = r.text
            raise CarrierError(f"Укрпошта ({r.status_code}): {str(msg)[:300]}")
        if raw:
            return r.content
        return r.json() if r.content else {}

    def create_shipment(self, order: Order, opts: dict | None = None) -> ShipmentResult:
        if not self.s.get("up_sender_uuid"):
            raise CarrierError("Вкажіть UUID клієнта-відправника Укрпошти в налаштуваннях")
        postcode = (order.postcode or "").strip()
        if len(postcode) != 5 or not postcode.isdigit():
            raise CarrierError("Для Укрпошти вкажіть 5-значний індекс відділення отримувача")
        last, first, middle = name_parts(order)
        if not first or not last:
            raise CarrierError("Для Укрпошти потрібні прізвище та ім'я отримувача")
        address = self._req("POST", "addresses", {"postcode": postcode, "city": order.city_name or None},
                            token=False)
        client = self._req("POST", "clients", {
            "type": "INDIVIDUAL", "firstName": first, "lastName": last, "middleName": middle,
            "addressId": address.get("id"), "phoneNumber": order.phone,
        })
        grams = int(order_weight(order, Decimal("0.5")) * 1000)
        cod = Decimal(order.cod_amount or 0)
        declared = max(Decimal(order.total or 0), cod)
        body = {
            "sender": {"uuid": self.s["up_sender_uuid"]},
            "recipient": {"uuid": client.get("uuid")},
            "deliveryType": "W2W",
            "type": self.s.get("up_type") or "STANDARD",
            "paidByRecipient": True,
            "parcels": [{"weight": grams, "length": 30, "declaredPrice": float(declared)}],
            "externalId": str(order.id),
        }
        if cod > 0:
            body["postPay"] = float(cod)
        sh = self._req("POST", "shipments", body)
        if not sh.get("barcode"):
            raise CarrierError("Укрпошта не повернула номер відправлення")
        return ShipmentResult(ttn=sh["barcode"], ref=sh.get("uuid", ""),
                              cost=Decimal(str(sh.get("deliveryPrice") or 0)))

    def delete_shipment(self, order: Order):
        if not order.carrier_ref:
            raise CarrierError("Відправлення створене не через CRM — видаліть його в кабінеті Укрпошти")
        self._req("DELETE", f"shipments/{order.carrier_ref}")

    def label_pdf(self, order: Order) -> bytes:
        if not order.carrier_ref:
            raise CarrierError("Наклейка доступна лише для відправлень, створених через CRM")
        content = self._req("GET", f"shipments/{order.carrier_ref}/sticker", base="forms/ecom/0.0.1", raw=True)
        if not content.startswith(b"%PDF"):
            raise CarrierError("Укрпошта не повернула PDF наклейки")
        return content

    def track(self, orders: list[Order]) -> list[TrackResult]:
        bearer = self.s.get("up_tracking_bearer") or self.s.get("up_bearer")
        results = []
        for o in orders:
            try:
                d = self._req("GET", f"statuses/last?barcode={o.ttn}&lang=UA", bearer=bearer,
                              base="status-tracking/0.0.1", token=False)
            except CarrierError:
                continue
            name, code = str(d.get("eventName", "")), str(d.get("event", ""))
            results.append(TrackResult(ttn=o.ttn, state=up_state(name, code), status_text=name, code=code, raw=d))
        return results
