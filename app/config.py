import os


class Config:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://crm:crm@localhost:5432/crm")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    # Часовий пояс для відображення дат в інтерфейсі (в БД все зберігається в UTC)
    DISPLAY_TZ: str = os.getenv("DISPLAY_TZ", "Europe/Kyiv")
    # Перший адміністратор створюється автоматично, якщо користувачів ще немає
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin12345")
    # Увімкніть, коли CRM працює за HTTPS (cookie тільки через https)
    HTTPS_ONLY: bool = os.getenv("HTTPS_ONLY", "0") == "1"
    # Префікс адреси, якщо CRM працює не в корені домену (напр. "/crm" для mdmy.me/crm).
    # Проксі (nginx) має прибирати цей префікс перед передачею запиту застосунку.
    ROOT_PATH: str = os.getenv("ROOT_PATH", "").rstrip("/")
    # Redis для черги задач (arq) і подій у реальному часі. Порожньо — без Redis:
    # усе працює, але задачі виконуються одразу в запиті, а інтерфейс оновлюється опитуванням.
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    # Моніторинг помилок Sentry (порожньо — вимкнено). Для браузера — окремий публічний DSN проєкту «Browser».
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    SENTRY_DSN_FRONTEND: str = os.getenv("SENTRY_DSN_FRONTEND", "")
    SENTRY_ENV: str = os.getenv("SENTRY_ENV", "production")
    SENTRY_TRACES_RATE: float = float(os.getenv("SENTRY_TRACES_RATE", "0") or 0)
    # Токен для /api/metrics (Prometheus). Порожньо — метрики доступні лише адміністратору в браузері.
    METRICS_TOKEN: str = os.getenv("METRICS_TOKEN", "")
    # Інтервал роботи фонового воркера, секунд
    WORKER_TICK: int = int(os.getenv("WORKER_TICK", "30"))


config = Config()
