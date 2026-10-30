"""Видаткові накладні (UI-DESIGN §6): кожен виданий документ — окремий запис зі знімком даних і номером, окремим для юрособи й типу.
Номер видається з document_counters під блокуванням рядка (SELECT … FOR UPDATE) і ніколи не повторюється."""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal

from sqlalchemy.orm import Session

from ..models import DELIVERY_METHODS, DocumentCounter, IssuedDocument, LegalEntity, Order, User, utcnow
from . import audit, events
from . import settings as st

KINDS = ("waybill", "invoice", "warranty")
PREFIX_KEY = {"waybill": "doc_prefix", "invoice": "invoice_prefix", "warranty": "warranty_prefix"}
DOC_SETTINGS = ("doc_prefix", "invoice_prefix", "warranty_prefix", "doc_unit", "doc_accent", "doc_site", "doc_note", "doc_logo",
                "invoice_days", "warranty_months", "warranty_terms")


class DocumentError(ValueError):
    pass


def entity_for(db: Session, order: Order) -> LegalEntity | None:
    return order.legal_entity or db.query(LegalEntity).filter(LegalEntity.is_default.is_(True)).first()


def build_data(db: Session, order: Order) -> dict:
    """Дані для PDF (видаткова, рахунок-фактура, гарантійний талон) — з поточного замовлення. Їх же зберігає знімок."""
    from ..web import today_local
    s = st.get_all(db)
    le = entity_for(db, order)
    seller = {"name": (le.name if le else "") or s.get("company_name", ""), "code": le.code if le else "",
              "code_label": (le.code_label if le else "") or "РНОКПП", "iban": le.iban if le else "",
              "address": le.address if le else "", "bank": le.bank if le else "", "phone": le.phone if le else "",
              "vat_note": (le.vat_note if le else "") or "Без ПДВ", "signer": le.signer if le else ""}
    where = ", ".join(x for x in (order.city_name, order.warehouse_name) if x)
    delivery_name = DELIVERY_METHODS.get(order.delivery_method, order.delivery_method or "")
    items = [{"name": i.name, "sku": (i.product.sku if i.product else "") or "", "qty": i.qty, "price": float(i.price or 0),
              "warranty_months": (i.product.warranty_months if i.product else 0) or 0, "upsell": i.is_upsell} for i in order.items]
    return {
        "order": {"id": order.id, "date": today_local().isoformat(), "created": order.created_at.isoformat() if order.created_at else None,
                  "buyer": order.customer_name or "", "phone": order.phone or "", "email": order.email or "",
                  "delivery": delivery_name + (f" · {where}" if where else ""), "address": order.address or "",
                  "ttn": order.ttn or "", "items": items, "discount": float(order.discount or 0),
                  "total": float(order.total or 0), "prepayment": float(order.prepayment or 0),
                  "cod_amount": float(order.cod_amount or 0),
                  "payment": order.payment_method.name if order.payment_method else ""},
        "seller": seller,
        "docs": {k: s.get(k, "") for k in DOC_SETTINGS},
    }


def payload_hash(order: Order) -> str:
    """Відбиток того, що потрапляє в документ: товари, ціни, знижка, покупець, юрособа. Змінився — «змінилось» у реєстрі."""
    data = {"items": [[i.name, i.qty, str(Decimal(i.price or 0))] for i in order.items], "discount": str(Decimal(order.discount or 0)),
            "total": str(Decimal(order.total or 0)), "buyer": order.customer_name or "", "phone": order.phone or "",
            "entity": order.legal_entity_id}
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def is_changed(doc: IssuedDocument, order: Order | None) -> bool:
    return bool(order is not None and doc.state == "active" and doc.payload_hash and doc.payload_hash != payload_hash(order))


def _prefix(db: Session, le: LegalEntity | None, kind: str) -> str:
    own = getattr(le, f"{kind}_prefix", None) if le else None
    if own:
        return own
    return st.get(db, PREFIX_KEY[kind]) or {"waybill": "РН-", "invoice": "СФ-", "warranty": "ГТ-"}[kind]


def _next_number(db: Session, le_id: int | None, kind: str) -> int:
    key = le_id or 0
    c = db.query(DocumentCounter).filter(DocumentCounter.legal_entity_id == key, DocumentCounter.kind == kind).with_for_update().one_or_none()
    if c is None:
        # перший документ: продовжуємо після найбільшого наявного номера (на випадок ручного втручання)
        top = db.query(IssuedDocument.number).filter(IssuedDocument.legal_entity_id.is_(le_id) if le_id is None else IssuedDocument.legal_entity_id == le_id,
                                                     IssuedDocument.kind == kind).order_by(IssuedDocument.number.desc()).first()
        c = DocumentCounter(legal_entity_id=key, kind=kind, next_number=(top[0] + 1) if top else 1)
        db.add(c)
        db.flush()
        c = db.query(DocumentCounter).filter(DocumentCounter.legal_entity_id == key, DocumentCounter.kind == kind).with_for_update().one()
    n = c.next_number
    c.next_number = n + 1
    return n


def active_for(db: Session, order_id: int, kind: str) -> IssuedDocument | None:
    return (db.query(IssuedDocument).filter(IssuedDocument.order_id == order_id, IssuedDocument.kind == kind, IssuedDocument.state == "active")
            .order_by(IssuedDocument.id.desc()).first())


def _create(db: Session, order: Order, kind: str, user: User | None) -> IssuedDocument:
    if kind not in KINDS:
        raise DocumentError("Невідомий тип документа")
    if not order.items:
        raise DocumentError("У замовленні немає товарів")
    le = entity_for(db, order)
    n = _next_number(db, le.id if le else None, kind)
    number_text = f"{_prefix(db, le, kind)}{n:04d}"
    snap = build_data(db, order)
    snap["number_text"] = number_text
    snap["kind"] = kind
    doc = IssuedDocument(kind=kind, legal_entity_id=le.id if le else None, order_id=order.id, customer_id=order.customer_id,
                         number=n, number_text=number_text, issued_at=utcnow(), total=Decimal(order.total or 0), snapshot=snap,
                         payload_hash=payload_hash(order), state="active", created_by_id=user.id if user else None)
    db.add(doc)
    db.flush()
    audit.log(db, user, "order", order.id, "document", {"документ": f"{IssuedDocumentKinds[kind]} {number_text}"})
    events.order_changed(db, order.id)
    return doc


IssuedDocumentKinds = {"waybill": "Видаткова накладна", "invoice": "Рахунок-фактура", "warranty": "Гарантійний талон"}


def issue(db: Session, order: Order, kind: str, user: User | None) -> IssuedDocument:
    """Чинний документ цього типу для замовлення або новий."""
    return active_for(db, order.id, kind) or _create(db, order, kind, user)


def reissue(db: Session, doc: IssuedDocument, user: User | None) -> IssuedDocument:
    """Новий документ з новим номером; старий — анульований з посиланням на нову версію."""
    order = db.get(Order, doc.order_id) if doc.order_id else None
    if order is None:
        raise DocumentError("Замовлення документа видалено — перевипустити неможливо")
    doc.state = "void"
    db.flush()
    new = _create(db, order, doc.kind, user)
    doc.replaced_by_id = new.id
    audit.log(db, user, "order", order.id, "document", {"перевипущено": f"{doc.number_text} → {new.number_text}"})
    return new


def void(db: Session, doc: IssuedDocument, user: User | None) -> None:
    doc.state = "void"
    if doc.order_id:
        audit.log(db, user, "order", doc.order_id, "document", {"анульовано": doc.number_text})
        events.order_changed(db, doc.order_id)


def printed(db: Session, doc: IssuedDocument) -> None:
    doc.print_count = (doc.print_count or 0) + 1
    doc.last_printed_at = utcnow()
    if doc.order_id:
        events.order_changed(db, doc.order_id)


def auto_issue(db: Session, order: Order, user: User | None) -> None:
    """Хук на «Відправлений»: видаткова й гарантійний талон, якщо doc_auto_issue = shipped (за замовчуванням)."""
    if (st.get(db, "doc_auto_issue") or "shipped") != "shipped" or not order.items:
        return
    for kind in ("waybill", "warranty"):
        try:
            issue(db, order, kind, user)
        except DocumentError:
            pass
