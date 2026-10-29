# Контекст для нової сесії Claude

Власна CRM для товарного бізнесу (продажі з лендингів і маркетплейсів), яку ми поетапно доводимо
до рівня LP-CRM. Працює на `https://mdmy.me/crm/`. Спілкування з власником — українською.

**План робіт і що вже зроблено — `docs/ROADMAP.md`. Прочитай його перед будь-якою задачею.**

## Правила

- **Секрети не комітити.** Ключі НП, логіни маркетплейсів, ключі й паролі Checkbox, токени SMS і
  Telegram зберігаються в базі (вводяться в «Налаштуваннях»), серверні — у `/etc/crm/crm.env`.
  У репозиторії лише `.env.example` із заглушками.
- **У LP-CRM нічого не зберігати й не змінювати.** LP-CRM — лише зразок, як має виглядати й
  працювати функція. Ми не пишемо туди даних і не ведемо в ній замовлень.
- **`main` = те, що на сервері.** Кожен коміт у `main` сервер підхоплює сам за ≤5 хв (див. нижче),
  тому незавершене — лише в гілках `wip/…`. Зливати в `main` після перевірки й зеленого `pytest`.
- Змінив API (`app/api/*`, `schemas.py`) — онови типи фронтенду, інакше впаде
  `test_openapi_snapshot_is_current`:
  `python scripts/export_openapi.py && (cd frontend && npm run gen:api)`.
- Змінив моделі — нова міграція в `migrations/versions/` (нумерація `0011_…`, `0012_…`), стійка до
  повторного запуску й до наявних даних на сервері.
- Тексти інтерфейсу, коментарі й повідомлення комітів — українською. Коміт етапу називати
  «Етап N: …».

## Інтерфейс: скіл UI/UX Pro Max
- Скіл лежить у `.claude/skills/ui-ux-pro-max` (MIT, github.com/nextlevelbuilder/ui-ux-pro-max-skill) — Claude Code
  підхоплює його сам. Перед роботою над виглядом: `python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<запит>" --domain ux`
  (або `--stack react`), перед здачею — чекліст `references/pro-rules.md`.
- Орієнтири для CRM (щільний робочий інтерфейс): пласкі поверхні без зайвих тіней, іконки лише lucide (без емодзі),
  видимий фокус з клавіатури, контраст тексту ≥ 4,5:1, на телефоні цілі дотику ≥ 44 px, без прокрутки вшир на 375 px,
  переходи 150–200 мс і `prefers-reduced-motion`.

## Як оновлюється сервер

Сервер — VPS сайту mdmy.me (nginx), CRM стоїть без Docker у підкаталозі `/crm`.
Таймер `crm-update` (скрипт `deploy/crm.sh` репозиторію `maksymchukdmytro/mdmy.me`) кожні 5 хв
перевіряє гілку `main` цього репозиторію; якщо є новий коміт — запускає `deploy/install.sh`:
копіює код у `/opt/crm`, ставить залежності, збирає React (якщо змінився), робить копію бази,
застосовує міграції й перезапускає служби `crm-web` (127.0.0.1:8020) і `crm-worker`.
Невдала версія повторюється не частіше разу на годину; журнал — `/var/log/mdmy-update.log`.

Перевірити, що викладено: `https://mdmy.me/crm/healthz` → `{"ok":true,"version":"<коміт> · <дата>"}`.
Повна перевірка (база, Redis, воркер): `/crm/healthz/full`. Доступ до сервера по SSH для звичайної
роботи не потрібен — лише якщо оновлення не застосувалось і треба читати журнали.

## CI (GitHub Actions)

`.github/workflows/ci.yml` на кожен пуш у `main` і `wip/**`: pytest на PostgreSQL + Redis, міграції з нуля
й `alembic check` (модель = міграції), збірка інтерфейсу. На гілках `wip/**` CI сам перегенеровує
`frontend/src/lib/api-schema.d.ts` з `openapi.json` і комітить його («Оновлено типи API…») — після пушу
зроби `git pull --rebase`. Зібраний інтерфейс лежить в артефакті `frontend-dist` (3 дні):
`gh run download <id> -n frontend-dist -D frontend/dist` — щоб подивитися сторінки локально.
Статус: `gh run list -R maksymchukdmytro/crm -b <гілка>`.

## Як запускати тести

Потрібні PostgreSQL з базою `crm_test` і (для тестів черги й подій) Redis на localhost.
```bash
pip install -r requirements.txt pytest
TEST_DATABASE_URL=postgresql+psycopg://crm:crm@localhost:5432/crm_test pytest -q
```
Фронтенд: `cd frontend && npm ci && npm run build` (перевірка TypeScript + збірка).

Якщо в сесії закриті PyPI / npm: залежності Python можна взяти з GitHub (`git clone --depth 1 --branch <тег>`
fastapi, sqlalchemy, psycopg, alembic, mako, python-multipart, httpx, httpcore, redis-py, arq, sentry-python,
client_python, annotated-doc) і підключити через `.pth`-файл у site-packages + мінімальні `*.dist-info/METADATA`
(psycopg і SQLAlchemy перевіряють версію). TypeScript перевіряє CI. Скриншоти: Playwright + Chromium з
`/opt/pw-browsers`, локальний сервер `uvicorn app.main:app --port 8077` на базі з `python demo_data.py`.

## Будова

```
app/models.py        усі таблиці
app/services/        бізнес-логіка (orders, stock, payments, delivery, np, marketplaces, checkbox, sms, reports, monitoring)
app/api/             JSON API для React: core, orders, catalog, admin, schemas (Pydantic → OpenAPI)
app/carriers/        перевізники: novaposhta, ukrposhta, meest (спільний інтерфейс base.py)
app/tasks.py         задачі воркера arq: SMS, ТТН, трекінг, маркетплейси, чеки, сповіщення
app/routers/, templates/  класичний інтерфейс /classic (запасний) і webhook прийому заявок
frontend/src/pages/  React-сторінки: Home (головна), Orders (ліди й замовлення), OrderCard, TtnDialog, Board, Products, Customers,
                     Catalog (склад), Stats, Finance, Settings, System
migrations/versions/ 0001…0015
```
Стек: Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL 16, Redis + arq, Alembic; React 19, TypeScript, Vite.

## Ключові модулі (етапи 2–4)

- **Нова Пошта — кілька ключів.** `NpAccount` = один API-ключ НП = один ФОП, зі своїм
  відправником, містом/відділенням і типовими параметрами ТТН (платник, тип вантажу, післяплата
  «грошовий переказ» або «контроль оплати», опис, розміри). Один ключ позначено `is_default`;
  у замовленні — `np_account_id`. Старі налаштування НП мігрували в ключ «Основний ключ».
  `NpStatusRule`: код статусу ТТН → статус замовлення, крім статусів-винятків. Логіка — `services/np.py`,
  `carriers/novaposhta.py`; вікно ТТН — `frontend/src/pages/TtnDialog.tsx`.
- **Checkbox — каса на кожен ФОП.** `CheckboxCashier` (ключ ліцензії, логін, пароль, тестовий режим,
  автовідкриття зміни й закриття о 23:00). Каса вибирається `pick_cashier()` згори вниз за умовою:
  `none` / `office` (відділ) / `user` (менеджер) / `np_account` (ключ НП). Чеки `CheckboxReceipt`:
  продаж, повернення, передоплата, післяплата; автоматично за статусами або кнопками в картці.
- **Маркетплейси.** `MarketplaceShop` (`kind` = `rozetka` / `prom`): імпорт замовлень кожні 5 хв
  задачею воркера, мапи статусів / оплат / доставок, передача статусу з CRM назад (`push_status`).
  У замовленні — `shop_id`, `external_id`, `external_status`. Логіка — `services/marketplaces.py`.
- **Довідники (етап 1).** 47 видів оплат (`PaymentMethod`, id як у LP-CRM), відділи `Office` з
  доступом менеджерів, причини, позначки, джерела, країна, додаткові поля 1–4 (`extra1…4`).
