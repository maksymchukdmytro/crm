from dataclasses import dataclass, field
from decimal import Decimal

import httpx

from ..models import Order


class CarrierError(Exception):
    """Помилка служби доставки з текстом, зрозумілим менеджеру."""


@dataclass
class TrackResult:
    ttn: str
    state: str  # одне з DELIVERY_STATES
    status_text: str = ""
    code: str = ""
    raw: dict = field(default_factory=dict)


@dataclass
class ShipmentResult:
    ttn: str
    ref: str = ""
    cost: Decimal = Decimal(0)


class Carrier:
    code = ""
    name = ""
    beta = False  # інтеграція не перевірена на бойовому акаунті
    can_create = True

    def __init__(self, settings: dict[str, str], client: httpx.Client | None = None):
        self.s = settings
        self._client = client

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=25)
        return self._client

    def configured(self) -> bool:  # pragma: no cover - перевизначається
        return False

    def create_shipment(self, order: Order) -> ShipmentResult:  # pragma: no cover
        raise CarrierError("Створення ТТН для цієї служби не підтримується")

    def delete_shipment(self, order: Order):  # pragma: no cover
        raise CarrierError("Видалення ТТН для цієї служби не підтримується")

    def track(self, orders: list[Order]) -> list[TrackResult]:  # pragma: no cover
        return []

    def label_pdf(self, order: Order) -> bytes:  # pragma: no cover
        raise CarrierError("Друк наклейки для цієї служби не підтримується")


def split_name(full: str) -> tuple[str, str, str]:
    """'Прізвище Ім'я По батькові' -> (прізвище, ім'я, по батькові)."""
    parts = (full or "").split()
    last = parts[0] if parts else ""
    first = parts[1] if len(parts) > 1 else ""
    middle = " ".join(parts[2:]) if len(parts) > 2 else ""
    if not first:  # вказано лише одне слово — вважаємо його ім'ям
        first, last = last, ""
    return last, first, middle


def order_weight(order: Order, default: Decimal) -> Decimal:
    w = Decimal(0)
    for it in order.items:
        if it.product is not None and it.product.weight:
            w += Decimal(it.product.weight) * it.qty
    return w if w > 0 else default
