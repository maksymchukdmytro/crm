import hashlib
import hmac
import secrets
import time

_ITER = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITER)
    return f"pbkdf2_sha256${_ITER}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt, digest = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iters))
        return hmac.compare_digest(dk.hex(), digest)
    except (ValueError, AttributeError):
        return False


class LoginThrottle:
    """Простий захист від підбору пароля: не більше N невдалих спроб за вікно часу."""

    def __init__(self, limit: int = 8, window: int = 600):
        self.limit, self.window = limit, window
        self._fails: dict[str, list[float]] = {}

    def _recent(self, key: str) -> list[float]:
        now = time.time()
        items = [t for t in self._fails.get(key, []) if now - t < self.window]
        self._fails[key] = items
        return items

    def blocked(self, key: str) -> bool:
        return len(self._recent(key)) >= self.limit

    def fail(self, key: str):
        self._recent(key).append(time.time())

    def reset(self, key: str):
        self._fails.pop(key, None)


throttle = LoginThrottle()
