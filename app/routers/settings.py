import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.datastructures import FormData

from ..carriers import CarrierError
from ..config import config
from ..carriers.novaposhta import NovaPoshta
from ..db import get_db
from ..deps import admin_only
from ..models import ROLES, STOCK_ACTIONS, Order, SmsMessage, SmsTemplate, Status, User
from ..security import hash_password
from ..services import audit, sms as sms_svc
from ..services import settings as st
from ..services.orders import to_int
from ..web import flash, redirect, render
from .orders import form_data

router = APIRouter()

TABS = {
    "general": "Загальні",
    "webhook": "Прийом заявок",
    "delivery": "Доставка",
    "sms": "SMS / Viber",
    "statuses": "Статуси",
    "users": "Користувачі",
}

SECTION_KEYS = {
    "fields": ["extra1_name", "extra2_name", "extra3_name", "extra4_name", "extra1_on", "extra2_on", "extra3_on", "extra4_on"],
    "checkbox": ["cb_sell_status", "cb_return_status", "cb_prepay_status", "cb_postpay_status"],
    "general": ["company_name", "duplicate_days", "auto_assign", "managers_see_own_only",
                "auto_status_from_tracking", "tracking_interval_min"],
    "np": ["np_api_key", "np_city_name", "np_city_ref", "np_warehouse_name", "np_warehouse_ref", "np_sender_phone",
           "np_cod_mode", "np_payer", "np_default_weight", "np_seat_size", "np_description", "np_sender_ref", "np_contact_ref"],
    "up": ["up_bearer", "up_token", "up_tracking_bearer", "up_sender_uuid", "up_sandbox", "up_type"],
    "meest": ["meest_username", "meest_password", "meest_sender_branch_id", "meest_sender_name", "meest_sender_phone"],
    "sms": ["sms_enabled", "sms_token", "sms_sender", "viber_sender"],
    "alerts": ["alert_tg_token", "alert_tg_chat", "alert_no_leads_hours"],
}
CHECKBOXES = {"managers_see_own_only", "auto_status_from_tracking", "up_sandbox", "sms_enabled"}


@router.get("/settings")
def settings_page(request: Request, tab: str = "general", db: Session = Depends(get_db),
                  user: User = Depends(admin_only)):
    if tab not in TABS:
        tab = "general"
    ctx = {"tab": tab, "tabs": TABS, "s": st.get_all(db), "secret_keys": st.SECRET_KEYS}
    if tab == "statuses":
        ctx["statuses"] = db.query(Status).order_by(Status.sort, Status.id).all()
        ctx["stock_actions"] = STOCK_ACTIONS
    if tab == "users":
        ctx["users"] = db.query(User).order_by(User.is_active.desc(), User.role, User.username).all()
        ctx["roles"] = ROLES
    if tab == "sms":
        ctx["templates"] = db.query(SmsTemplate).order_by(SmsTemplate.id).all()
        ctx["statuses"] = db.query(Status).order_by(Status.sort).all()
        ctx["placeholders"] = sms_svc.PLACEHOLDERS
        ctx["sms_log"] = db.query(SmsMessage).order_by(SmsMessage.id.desc()).limit(30).all()
    if tab == "webhook":
        ctx["base_url"] = str(request.base_url).rstrip("/") + config.ROOT_PATH
    return render(request, "settings/index.html", ctx, active="settings")


@router.post("/settings/save/{section}")
def settings_save(section: str, request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
                  user: User = Depends(admin_only)):
    keys = SECTION_KEYS.get(section)
    if not keys:
        raise HTTPException(404)
    changed = []
    for k in keys:
        if k in CHECKBOXES:
            val = "1" if form.get(k) == "1" else "0"
        elif k in form:
            val = (form.get(k) or "").strip()
            if k in st.SECRET_KEYS and val == "********":
                continue  # секрет не змінювали
        else:
            continue
        if st.get(db, k) != val:
            st.set_value(db, k, val)
            changed.append(k)
    if changed:
        audit.log(db, user, "settings", None, "update", {"поля": changed})
    db.commit()
    flash(request, "Налаштування збережено")
    tab = {"np": "delivery", "up": "delivery", "meest": "delivery"}.get(section, section)
    return redirect(f"/settings?tab={tab}")


@router.post("/settings/np/load-sender")
def np_load_sender(request: Request, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    try:
        data = NovaPoshta(st.get_all(db)).load_sender()
    except CarrierError as e:
        flash(request, str(e), "error")
        return redirect("/settings?tab=delivery")
    for k in ("np_sender_ref", "np_contact_ref", "np_sender_phone"):
        st.set_value(db, k, data[k])
    db.commit()
    flash(request, f"Відправника завантажено: {data['sender_name']}, контакт {data['contact_name']}, {data['np_sender_phone']}")
    return redirect("/settings?tab=delivery")


@router.post("/settings/webhook/regenerate")
def webhook_regenerate(request: Request, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    st.set_value(db, "webhook_key", secrets.token_urlsafe(24))
    audit.log(db, user, "settings", None, "update", {"поля": ["webhook_key"]})
    db.commit()
    flash(request, "Новий ключ створено. Оновіть його на всіх лендингах!", "warn")
    return redirect("/settings?tab=webhook")


# ------------------------------------------------------------------ статуси
@router.post("/settings/statuses")
def statuses_save(request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
                  user: User = Depends(admin_only)):
    for s in db.query(Status).all():
        p = f"s{s.id}_"
        if p + "name" not in form:
            continue
        s.name = (form.get(p + "name") or s.name).strip()[:80]
        s.color = (form.get(p + "color") or s.color)[:9]
        s.sort = to_int(form.get(p + "sort"), s.sort)
        action = form.get(p + "stock_action") or s.stock_action
        s.stock_action = action if action in STOCK_ACTIONS else s.stock_action
        s.counts_as_approved = form.get(p + "approved") == "1"
        s.is_final = form.get(p + "final") == "1"
        s.is_active = form.get(p + "active") == "1" or s.code == "new"
    new_name = (form.get("new_name") or "").strip()
    if new_name:
        code = "custom_" + secrets.token_hex(3)
        db.add(Status(code=code, name=new_name[:80], color=form.get("new_color") or "#64748b",
                      sort=to_int(form.get("new_sort"), 200),
                      stock_action=form.get("new_stock_action") if form.get("new_stock_action") in STOCK_ACTIONS else "none"))
    audit.log(db, user, "settings", None, "update", {"поля": ["statuses"]})
    db.commit()
    flash(request, "Статуси збережено")
    return redirect("/settings?tab=statuses")


@router.post("/settings/statuses/{sid}/delete")
def status_delete(sid: int, request: Request, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    s = db.get(Status, sid)
    if s is None:
        raise HTTPException(404)
    if s.is_system:
        flash(request, "Системний статус не можна видалити, але його можна вимкнути", "error")
    elif db.query(Order).filter(Order.status_id == sid).count():
        flash(request, "У цьому статусі є замовлення. Перенесіть їх або вимкніть статус.", "error")
    else:
        db.query(SmsTemplate).filter(SmsTemplate.status_id == sid).delete()
        db.delete(s)
        db.commit()
        flash(request, "Статус видалено")
    return redirect("/settings?tab=statuses")


# ------------------------------------------------------------ SMS-шаблони
@router.post("/settings/sms-templates")
def sms_templates_save(request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
                       user: User = Depends(admin_only)):
    tid = to_int(form.get("id"))
    if form.get("delete") == "1" and tid:
        t = db.get(SmsTemplate, tid)
        if t:
            db.delete(t)
        db.commit()
        flash(request, "Шаблон видалено")
        return redirect("/settings?tab=sms")
    t = db.get(SmsTemplate, tid) if tid else SmsTemplate()
    t.status_id = to_int(form.get("status_id"))
    t.channel = form.get("channel") if form.get("channel") in ("sms", "viber", "hybrid") else "sms"
    t.text = (form.get("text") or "").strip()
    t.is_active = form.get("is_active") == "1"
    if not t.text or not db.get(Status, t.status_id):
        flash(request, "Вкажіть статус і текст шаблону", "error")
        return redirect("/settings?tab=sms")
    if not tid:
        db.add(t)
    db.commit()
    flash(request, "Шаблон збережено")
    return redirect("/settings?tab=sms")


@router.post("/settings/sms-test")
def sms_test(request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
             user: User = Depends(admin_only)):
    from ..services.orders import normalize_phone
    phone = normalize_phone(form.get("phone"))
    s = st.get_all(db)
    if not s.get("sms_token"):
        flash(request, "Спочатку вкажіть токен TurboSMS", "error")
        return redirect("/settings?tab=sms")
    ok, info = sms_svc.send_turbosms(s["sms_token"], phone, "Тестове повідомлення CRM", form.get("channel", "sms"),
                                     s.get("sms_sender", ""), s.get("viber_sender", ""))
    flash(request, "Тестове повідомлення відправлено" if ok else f"Помилка: {info}", "ok" if ok else "error")
    return redirect("/settings?tab=sms")


# -------------------------------------------------------------- користувачі
@router.post("/settings/users")
def users_save(request: Request, form: FormData = Depends(form_data), db: Session = Depends(get_db),
               user: User = Depends(admin_only)):
    uid = to_int(form.get("id"))
    u = db.get(User, uid) if uid else User()
    username = (form.get("username") or "").strip()
    if not uid:
        if not username or not form.get("password"):
            flash(request, "Вкажіть логін і пароль", "error")
            return redirect("/settings?tab=users")
        u.username = username[:64]
    u.full_name = (form.get("full_name") or "").strip()[:128]
    role = form.get("role")
    if role in ROLES:
        if u.id == user.id and role != "admin":
            flash(request, "Не можна забрати права адміністратора в самого себе", "error")
            return redirect("/settings?tab=users")
        u.role = role
    if uid:
        active = form.get("is_active") == "1"
        if u.id == user.id and not active:
            flash(request, "Не можна вимкнути власний обліковий запис", "error")
            return redirect("/settings?tab=users")
        u.is_active = active
    pw = form.get("password") or ""
    if pw:
        if len(pw) < 8:
            flash(request, "Пароль має містити щонайменше 8 символів", "error")
            return redirect("/settings?tab=users")
        u.password_hash = hash_password(pw)
    if not uid:
        db.add(u)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        flash(request, "Такий логін уже зайнятий", "error")
        return redirect("/settings?tab=users")
    audit.log(db, user, "user", u.id, "create" if not uid else "update",
              {"логін": u.username, "роль": u.role, "активний": u.is_active, "пароль змінено": bool(pw)})
    db.commit()
    flash(request, "Користувача збережено")
    return redirect("/settings?tab=users")
