from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
from ..models import User, utcnow
from ..security import hash_password, throttle, verify_password
from ..services import audit
from ..web import flash, redirect, render, safe_next

router = APIRouter()


@router.get("/")
def index():
    return redirect("/orders")


@router.get("/login")
def login_page(request: Request, next: str = ""):
    if request.session.get("uid"):
        return redirect(safe_next(next))
    return render(request, "login.html", {"next": next})


@router.post("/login")
def login(request: Request, username: str = Form(""), password: str = Form(""), next: str = Form(""),
          db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "?"
    key = f"{ip}:{username.lower()}"
    if throttle.blocked(key):
        return render(request, "login.html", {"next": next, "error": "Забагато спроб. Спробуйте через 10 хвилин."}, 429)
    user = db.query(User).filter(User.username == username.strip()).one_or_none()
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        throttle.fail(key)
        return render(request, "login.html", {"next": next, "error": "Невірний логін або пароль"}, 401)
    throttle.reset(key)
    request.session.clear()
    request.session["uid"] = user.id
    user.last_login_at = utcnow()
    audit.log(db, user, "user", user.id, "login", {"ip": ip})
    db.commit()
    return redirect(safe_next(next))


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return redirect("/login")


@router.get("/profile")
def profile(request: Request, user: User = Depends(current_user)):
    return render(request, "profile.html", {})


@router.post("/profile")
def profile_save(request: Request, old_password: str = Form(""), new_password: str = Form(""),
                 full_name: str = Form(""), user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.full_name = full_name.strip()[:128] or user.full_name
    if new_password:
        if not verify_password(old_password, user.password_hash):
            flash(request, "Поточний пароль невірний", "error")
            return redirect("/profile")
        if len(new_password) < 8:
            flash(request, "Новий пароль має містити щонайменше 8 символів", "error")
            return redirect("/profile")
        user.password_hash = hash_password(new_password)
    db.commit()
    flash(request, "Збережено")
    return redirect("/profile")
