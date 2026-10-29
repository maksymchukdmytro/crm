from fastapi import Depends, Request
from sqlalchemy.orm import Session

from .db import get_db
from .models import User
from .services import settings as st


class NotAuthenticated(Exception):
    pass


class Forbidden(Exception):
    pass


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    uid = request.session.get("uid")
    user = db.get(User, uid) if uid else None
    if user is None or not user.is_active:
        request.session.pop("uid", None)
        raise NotAuthenticated()
    request.state.user = user
    request.state.company = st.get(db, "company_name")
    return user


def require(*roles: str):
    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise Forbidden()
        return user

    return dep


admin_only = require("admin")
staff = require("admin", "manager", "warehouse")
sales = require("admin", "manager")
stock_team = require("admin", "warehouse")
