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
    # Інтервал роботи фонового воркера, секунд
    WORKER_TICK: int = int(os.getenv("WORKER_TICK", "30"))


config = Config()
