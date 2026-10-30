"""Крок 3 нового інтерфейсу: статуси «Несортований» / «Очікує на отримання» / «Відмова ліда», початковий статус, групи за днями."""
import importlib.util
import pathlib

from app.models import NpStatusRule, Order, Status, StatusReason
from app.services import orders as svc
from app.services import settings as st

from .test_api import api, new_order  # noqa: F401 — фікстури


def _sid(db, code):
    return db.query(Status).filter(Status.code == code).one().id


def _migration():
    path = pathlib.Path(__file__).resolve().parent.parent / "migrations/versions/0017_status_redesign.py"
    spec = importlib.util.spec_from_file_location("m0017", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_migration(db, mod):
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    conn = db.connection()
    ctx = MigrationContext.configure(conn)
    with Operations.context(ctx):
        mod.upgrade()
    db.commit()


def test_seed_has_new_statuses(db):
    names = {s.code: (s.name, s.stage, s.is_active) for s in db.query(Status)}
    assert names["unsorted"] == ("Несортований", "order", True)
    assert names["arrived"][0] == "Очікує на отримання" and names["lead_refused"][1] == "lead"
    assert names["confirmed"][0] == "Прийнятий" and names["cancelled"][0] == "Відмова" and names["packing"][2] is False


def test_migration_keeps_user_names_and_is_idempotent(db):
    # стара база: старі назви, без нових статусів; один статус користувач перейменував сам
    db.query(Status).filter(Status.code.in_(("unsorted", "arrived", "lead_refused"))).delete()
    db.query(Status).filter(Status.code == "confirmed").update({"name": "Підтверджено", "color": "#0ea5e9"})
    db.query(Status).filter(Status.code == "shipped").update({"name": "Поїхало", "color": "#123456"})
    db.add(NpStatusRule(np_code="9", status_id=_sid(db, "delivered"), except_ids=[], sort=10))
    db.commit()
    mod = _migration()
    _run_migration(db, mod)
    _run_migration(db, mod)  # повторний запуск нічого не змінює
    db.expire_all()
    s = {x.code: x for x in db.query(Status)}
    assert (s["confirmed"].name, s["confirmed"].color) == ("Прийнятий", "#2E6BE6")
    assert (s["shipped"].name, s["shipped"].color) == ("Поїхало", "#123456")   # змінене користувачем — не чіпаємо
    assert db.query(Status).filter(Status.code == "unsorted").count() == 1
    codes = sorted(r.np_code for r in db.query(NpStatusRule))
    assert codes == ["7", "8", "9"]
    assert all(r.status_id == s["arrived"].id for r in db.query(NpStatusRule).filter(NpStatusRule.np_code.in_(("7", "8"))))


def test_initial_status(db):
    assert svc.initial_status(db, "manual").code == "unsorted"
    assert svc.initial_status(db, "marketplace").code == "unsorted"
    assert svc.initial_status(db, "webhook").code == "new"
    st.set_value(db, "leads_enabled", "0")
    db.commit()
    assert svc.initial_status(db, "webhook").code == "unsorted"


def test_manual_order_goes_to_unsorted(api, db, products):
    o = new_order(api, products)
    assert db.get(Order, o["id"]).status.code == "unsorted"


def test_tracking_arrived_moves_to_waiting(db, products, api):
    from app.carriers.base import TrackResult
    from app.services import delivery
    o = db.get(Order, new_order(api, products)["id"])
    o.ttn = "20450000000000"
    o.status_id = _sid(db, "shipped")
    db.commit()
    delivery.apply_track(db, o, TrackResult(ttn="20450000000000", state="arrived", code="7", status_text="Прибув на відділення", raw={}), auto_status=True)
    db.commit()
    assert db.get(Order, o.id).status.code == "arrived"


def test_cancel_requires_reason(api, db, products):
    db.add(StatusReason(name="Передумав"))
    db.commit()
    oid = new_order(api, products)["id"]
    r = api.patch(f"/api/orders/{oid}", json={"status_id": _sid(db, "cancelled")})
    assert r.status_code == 400 and "причину" in r.text
    rid = db.query(StatusReason).first().id
    assert api.patch(f"/api/orders/{oid}", json={"status_id": _sid(db, "cancelled"), "reason_id": rid}).status_code == 200


def test_list_day_groups_and_oldest_first(api, db, products):
    ids = [new_order(api, products, phone=f"05011100{i}")["id"] for i in range(3)]
    d = api.get("/api/orders?stage=order").json()
    assert len(d["groups"]) == 1 and d["groups"][0]["count"] >= 3 and d["groups"][0]["sum"] >= 3 * 897
    old = api.get("/api/orders?stage=order&sort=old&limit=2").json()
    assert [x["id"] for x in old["items"]] == ids[:2] and old["next"] == ids[1]
    nxt = api.get(f"/api/orders?stage=order&sort=old&limit=2&after={old['next']}").json()
    assert [x["id"] for x in nxt["items"]] == ids[2:3]
    # скасовані не входять у суму групи
    db.query(Order).filter(Order.id == ids[0]).update({"status_id": _sid(db, "cancelled")})
    db.commit()
    g = api.get("/api/orders?stage=order").json()["groups"][0]
    assert g["count"] == 3 and abs(g["sum"] - 2 * 897) < 0.01
