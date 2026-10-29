"""Нова Пошта, API 2.0: https://developers.novaposhta.ua/"""
import re
from datetime import datetime
from decimal import Decimal

import httpx

from ..models import Order
from .base import Carrier, CarrierError, ShipmentResult, TrackResult, name_parts, order_weight

API_URL = "https://api.novaposhta.ua/v2.0/json/"


def np_state(code: str) -> str:
    c = str(code)
    if c == "1":
        return "created"
    if c in ("2", "3"):
        return "deleted" if c == "2" else "unknown"
    if c in ("7", "8"):
        return "arrived"
    if c in ("9", "10", "11", "106"):
        return "delivered"
    if c in ("102", "103", "105", "108"):
        return "refused"
    if c in ("4", "41", "5", "6", "101", "104", "111", "112", "14"):
        return "in_transit"
    return "in_transit" if c else "unknown"


def _num(d: Decimal) -> str:
    """30.0 → «30», 12.5 → «12.5» (без наукового запису)."""
    t = f"{d:f}"
    return t.rstrip("0").rstrip(".") if "." in t else t


def seat_size(raw: str | None) -> tuple[int, int, int]:
    """«20x15x10», «20*15*10», «20 15 10» → (20, 15, 10); некоректне — 20×15×10."""
    nums = [int(n) for n in re.findall(r"\d+", raw or "")][:3]
    if len(nums) != 3 or min(nums) <= 0:
        return 20, 15, 10
    return nums[0], nums[1], nums[2]


class NovaPoshta(Carrier):
    code = "novaposhta"
    name = "Нова Пошта"

    @property
    def key(self) -> str:
        return self.s.get("np_api_key", "")

    def configured(self) -> bool:
        return bool(self.key)

    def call(self, model: str, method: str, props: dict) -> list:
        if not self.key:
            raise CarrierError("Не вказано API-ключ Нової Пошти (Налаштування → Доставка)")
        payload = {"apiKey": self.key, "modelName": model, "calledMethod": method, "methodProperties": props}
        try:
            r = self.client.post(API_URL, json=payload)
            data = r.json()
        except (httpx.HTTPError, ValueError) as e:
            raise CarrierError(f"Нова Пошта недоступна: {e}") from e
        if not data.get("success"):
            errors = data.get("errors") or data.get("warnings") or ["невідома помилка"]
            if isinstance(errors, dict):
                errors = list(errors.values())
            raise CarrierError("Нова Пошта: " + "; ".join(str(e) for e in errors))
        return data.get("data") or []

    # --- Довідники ---------------------------------------------------------
    def search_cities(self, query: str) -> list[dict]:
        data = self.call("Address", "getCities", {"FindByString": query, "Limit": "20", "Page": "1"})
        res = []
        for c in data:
            area = c.get("AreaDescription") or ""
            kind = c.get("SettlementTypeDescription") or ""
            label = c.get("Description", "")
            extra = ", ".join(x for x in (kind, f"{area} обл." if area else "") if x)
            res.append({"ref": c.get("Ref"), "name": label, "label": f"{label} ({extra})" if extra else label})
        return res

    def search_warehouses(self, city_ref: str, query: str = "") -> list[dict]:
        props = {"CityRef": city_ref, "Limit": "50", "Page": "1"}
        if query:
            props["FindByString"] = query
        data = self.call("Address", "getWarehouses", props)
        return [{"ref": w.get("Ref"), "name": w.get("Description"), "label": w.get("Description")} for w in data]

    def load_directory(self) -> dict:
        """Контрагенти-відправники і їхні контактні особи з кабінету НП — для вибору в налаштуваннях ключа."""
        cps = self.call("Counterparty", "getCounterparties", {"CounterpartyProperty": "Sender", "Page": "1"})
        if not cps:
            raise CarrierError("У кабінеті Нової Пошти не знайдено відправника")
        senders = []
        for c in cps:
            contacts = self.call("Counterparty", "getCounterpartyContactPersons", {"Ref": c["Ref"], "Page": "1"})
            senders.append({"ref": c["Ref"], "name": c.get("Description", ""),
                            "contacts": [{"ref": x["Ref"], "name": x.get("Description", ""), "phone": x.get("Phones", "")}
                                         for x in contacts]})
        return {"senders": senders}

    def load_sender(self) -> dict:
        """Отримує контрагента-відправника і контактну особу з кабінету НП."""
        cps = self.call("Counterparty", "getCounterparties", {"CounterpartyProperty": "Sender", "Page": "1"})
        if not cps:
            raise CarrierError("У кабінеті Нової Пошти не знайдено відправника")
        sender = cps[0]
        contacts = self.call("Counterparty", "getCounterpartyContactPersons", {"Ref": sender["Ref"], "Page": "1"})
        if not contacts:
            raise CarrierError("Не знайдено контактну особу відправника")
        c = contacts[0]
        return {
            "np_sender_ref": sender["Ref"],
            "np_contact_ref": c["Ref"],
            "np_sender_phone": c.get("Phones", ""),
            "sender_name": sender.get("Description", ""),
            "contact_name": c.get("Description", ""),
        }

    # --- ТТН ---------------------------------------------------------------
    def _recipient(self, order: Order) -> tuple[str, str]:
        last, first, middle = name_parts(order)
        if not first or not last:
            raise CarrierError("Для Нової Пошти потрібні прізвище та ім'я отримувача (кирилицею)")
        data = self.call("Counterparty", "save", {
            "FirstName": first, "MiddleName": middle, "LastName": last,
            "Phone": order.phone, "Email": "",
            "CounterpartyType": "PrivatePerson", "CounterpartyProperty": "Recipient",
        })
        rec = data[0]
        contact = ((rec.get("ContactPerson") or {}).get("data") or [{}])[0].get("Ref", "")
        return rec["Ref"], contact

    # Параметри ТТН за замовчуванням: показуються у вікні «Створення накладної», менеджер може змінити
    def shipment_defaults(self, order: Order) -> dict:
        s = self.s
        default_w = Decimal(s.get("np_default_weight") or "0.5")
        weight = order_weight(order, default_w)
        # розміри: з товарів (найбільша довжина й ширина, висоти складаються), інакше — з налаштувань ключа
        dims = []
        for it in order.items:
            p = it.product
            if p is None or not (p.length and p.width and p.height):
                dims = []
                break
            dims.append((Decimal(p.length), Decimal(p.width), Decimal(p.height) * it.qty))
        if dims:
            length, width, height = max(d[0] for d in dims), max(d[1] for d in dims), sum(d[2] for d in dims)
        else:
            length, width, height = (Decimal(x) for x in seat_size(s.get("np_seat_size")))
        descr = ", ".join(dict.fromkeys(it.product.ship_description for it in order.items
                                         if it.product is not None and it.product.ship_description))
        cod = Decimal(order.cod_amount or 0)
        info = []
        if s.get("np_info_items", "1") == "1":
            info.append("; ".join(f"{it.name} ×{it.qty}" for it in order.items))
        if s.get("np_info_item_ids") == "1":
            info.append("ID: " + ", ".join(str(it.product_id) for it in order.items if it.product_id))
        if s.get("np_info_comment") == "1" and order.comment:
            info.append(order.comment.strip())
        return {
            "payer": s.get("np_payer") or "Recipient",
            "cargo_type": s.get("np_cargo_type") or "Parcel",
            "service_type": s.get("np_service_type") or "WarehouseWarehouse",
            "weight": float(weight),
            "seats": [{"length": float(length), "width": float(width), "height": float(height), "weight": float(weight)}],
            "description": (descr or s.get("np_description") or "Товар")[:100],
            "declared_cost": max(int(Decimal(order.total or 0)), 1),
            "cod_mode": (s.get("np_cod_mode") or "backward") if cod > 0 else "none",
            "cod_amount": float(cod),
            "cod_payer": s.get("np_cod_payer") or "Recipient",
            "additional_info": " | ".join(x for x in info if x)[:100],
        }

    def create_shipment(self, order: Order, opts: dict | None = None) -> ShipmentResult:
        s = self.s
        missing = [n for k, n in [
            ("np_sender_ref", "відправник"), ("np_contact_ref", "контактна особа"),
            ("np_city_ref", "місто відправки"), ("np_warehouse_ref", "відділення відправки"),
            ("np_sender_phone", "телефон відправника"),
        ] if not s.get(k)]
        if missing:
            raise CarrierError("Не заповнені дані відправника НП: " + ", ".join(missing))
        if not order.city_ref or not order.warehouse_ref:
            raise CarrierError("Оберіть місто і відділення Нової Пошти зі списку")
        if not order.phone:
            raise CarrierError("Не вказано телефон отримувача")
        p = self.shipment_defaults(order)
        p.update({k: v for k, v in (opts or {}).items() if v is not None and k in p})
        seats = p["seats"] or [{"length": 20, "width": 15, "height": 10, "weight": p["weight"]}]
        options, volume, total_w = [], Decimal(0), Decimal(0)
        for x in seats:
            ln, wd, ht = (Decimal(str(x.get(k) or 0)) for k in ("length", "width", "height"))
            w = Decimal(str(x.get("weight") or 0))
            if min(ln, wd, ht) <= 0 or w <= 0:
                raise CarrierError("Вкажіть розміри й вагу кожного місця відправлення")
            options.append({  # НП вимагає опис кожного місця: розміри (см), об'ємна вага = Д×Ш×В / 4000, вага
                "volumetricLength": _num(ln), "volumetricWidth": _num(wd), "volumetricHeight": _num(ht),
                "volumetricVolume": str((ln * wd * ht / 4000).quantize(Decimal("0.001"))), "weight": str(w),
            })
            volume += ln * wd * ht / 1_000_000
            total_w += w
        recipient, contact = self._recipient(order)
        props = {
            "PayerType": p["payer"],
            "PaymentMethod": "Cash",
            "DateTime": datetime.now().strftime("%d.%m.%Y"),
            "CargoType": p["cargo_type"],
            "Weight": str(total_w),
            "ServiceType": p["service_type"],
            "SeatsAmount": str(len(options)),
            "OptionsSeat": options,
            "VolumeGeneral": str(volume.quantize(Decimal("0.0001"))),
            "Description": str(p["description"] or "Товар")[:100],
            "Cost": str(max(int(Decimal(str(p["declared_cost"] or 1))), 1)),
            "CitySender": s["np_city_ref"],
            "Sender": s["np_sender_ref"],
            "SenderAddress": s["np_warehouse_ref"],
            "ContactSender": s["np_contact_ref"],
            "SendersPhone": s["np_sender_phone"],
            "CityRecipient": order.city_ref,
            "Recipient": recipient,
            "RecipientAddress": order.warehouse_ref,
            "ContactRecipient": contact,
            "RecipientsPhone": order.phone,
            "InfoRegClientBarcodes": str(order.id),
        }
        if p.get("additional_info"):
            props["AdditionalInformation"] = str(p["additional_info"])[:100]
        cod = Decimal(str(p.get("cod_amount") or 0)).quantize(Decimal("0.01"))
        cod_kind = "none"
        if cod > 0 and p["cod_mode"] != "none":
            cod_kind = "control" if p["cod_mode"] == "afterpayment" else "backward"
            if p["cod_mode"] == "afterpayment":
                props["AfterpaymentOnGoodsCost"] = str(cod)
            else:
                props["BackwardDeliveryData"] = [
                    {"PayerType": p.get("cod_payer") or "Recipient", "CargoType": "Money", "RedeliveryString": str(cod)}
                ]
        d = self.call("InternetDocument", "save", props)[0]
        return ShipmentResult(ttn=str(d.get("IntDocNumber", "")), ref=d.get("Ref", ""),
                              cost=Decimal(str(d.get("CostOnSite") or 0)),
                              cod_kind=cod_kind, cod_sum=cod if cod_kind != "none" else Decimal(0))

    def delete_shipment(self, order: Order):
        if not order.carrier_ref:
            raise CarrierError("ТТН створена не через CRM — видаліть її в кабінеті Нової Пошти")
        self.call("InternetDocument", "delete", {"DocumentRefs": order.carrier_ref})

    def label_pdf(self, order: Order) -> bytes:
        url = (f"https://my.novaposhta.ua/orders/printMarking100x100/orders[]/{order.ttn}"
               f"/type/pdf/apiKey/{self.key}")
        try:
            r = self.client.get(url)
        except httpx.HTTPError as e:
            raise CarrierError(f"Не вдалося отримати наклейку: {e}") from e
        if r.status_code != 200 or not r.content.startswith(b"%PDF"):
            raise CarrierError("Нова Пошта не повернула PDF наклейки")
        return r.content

    def track(self, orders: list[Order]) -> list[TrackResult]:
        results = []
        for i in range(0, len(orders), 100):
            chunk = orders[i:i + 100]
            docs = [{"DocumentNumber": o.ttn, "Phone": o.phone} for o in chunk]
            for d in self.call("TrackingDocument", "getStatusDocuments", {"Documents": docs}):
                code = str(d.get("StatusCode", ""))
                results.append(TrackResult(ttn=str(d.get("Number", "")), state=np_state(code),
                                           status_text=d.get("Status", ""), code=code, raw=d))
        return results
