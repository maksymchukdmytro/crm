# Новий інтерфейс — технічне завдання для розробки

Цей файл доповнює `docs/UI-DESIGN.md`. Там описано, як має виглядати й працювати інтерфейс; тут — що
змінити в базі, API, сервісах і фронтенді, щоб це запрацювало. Розділи 2–12 відповідають крокам із розділу 17
`UI-DESIGN.md`.

Стан коду на момент написання: `main` = `49daee1`, міграції до `0015_documents`.

---

## 0. Загальні правила реалізації

- **Коди статусів не змінюємо** (`new`, `confirmed`, `shipped`, `delivered`, `refused`, `returned`, `cancelled`…).
  На них зав'язані сервіси (`orders.py`, `dashboard.py`, `np.py`, `marketplaces.py`, `checkbox.py`), класичний інтерфейс
  і тести. Змінюються лише назви, кольори, порядок і розділ; нові статуси додаються новими кодами.
- **Міграції** нумеруються з `0016_…`. Кожна має бути стійкою до повторного запуску й до наявних даних (`IF NOT EXISTS`,
  перевірка перед вставкою). Назви й кольори, які користувач уже змінив у налаштуваннях, міграція **не чіпає**:
  оновлює лише рядки, де значення ще дорівнює старому типовому.
- **Зміни API** (`app/api/*`, `schemas.py`) завжди супроводжуються оновленням типів:
  `python scripts/export_openapi.py && (cd frontend && npm run gen:api)`.
- **Кожен крок** — окрема гілка `wip/ui-<крок>`. У `main` — лише після зеленого `pytest` і CI. Класичний `/classic`
  і webhook прийому заявок мають працювати без змін.
- **Інтерфейс** — лише токени з `UI-DESIGN.md` §2, іконки `lucide-react`, без нових UI-бібліотек.

---

## 1. Що з функцій уже є, а що нове

| Функція з `UI-DESIGN.md` | Є зараз | Що зробити |
|---|---|---|
| Статуси Несортований, Очікує на отримання, Відмова ліда | ні | нові коди статусів (§3) |
| Перемикач розділу «Ліди» | ні (розділ є завжди) | налаштування й логіка (§4) |
| Спроби дзвінка, час передзвону, черга лідів | частково (`remind_at`) | поле `call_attempts`, ендпоінти результату й черги (§4) |
| Щільні списки, групи за днями з підсумками | ні | підсумки груп в API, налаштування колонок користувача (§5) |
| Збережені фільтри в боковій панелі | ні | таблиця `saved_filters` (§2) |
| Лічильники в меню (нові ліди, несортовані) | частково (нові ліди) | `GET /api/meta` → `counters` (§2) |
| Куди надійшла передоплата (рахунок юрособи) | ні | таблиця `legal_entity_accounts`, поля в `payments` (§6) |
| «Що лишилось» | ні | `services/checklist.py`, поле `todo` в `OrderOut` (§6) |
| Реєстр НП | **ні** | нова функція: ScanSheet API НП (§6.4) |
| Позначка «наклейку надруковано» | ні | `orders.label_printed_at` (§6) |
| Очікувана дата доставки, вартість у вікні ТТН | частково (`delivery_cost`) | `orders.delivery_eta`, ціна й дата в `ttn/preview` (§6.3) |
| Видаткові накладні як записи в базі, реєстр | ні (PDF будуються з поточних даних) | таблиці `issued_documents`, `document_counters` (§7) |
| Вікна товару й покупця, підсумки продажів товару | дані є, підсумку немає | `GET /api/products/{id}/summary`, розширення покупця (§8) |
| Прогноз залишку «закінчиться через N днів» | ні | розрахунок у `services/stock.py` (§9) |
| Головна з вибором періоду | частково (лише поточний місяць) | параметр періоду в `/api/dashboard` (§10) |
| Статистика | так, усі поля | лише новий вигляд (§11) |
| Нагадування, поля 1–4, маркетплейси, Rozetka Delivery, перевірка оплати, допродаж, друк документів, Checkbox | так | перенести в новий вигляд без змін логіки |

---

## 2. Основа фронтенду й каркас

### 2.1 Токени й шрифт
- `frontend/src/theme.css`: замінити змінні на токени з `UI-DESIGN.md` §2.1. Старі назви змінних лишити псевдонімами, доки всі
  сторінки не переведено, щоб не зламати класичні стилі.
- **Шрифт Onest:** локальний файл (`@fontsource-variable/onest` або woff2 у `frontend/public/fonts`), `font-display: swap`.
  JetBrains Mono — для `.mono`. Commissioner прибрати після переходу.
- **Правило заокруглень** — утиліти `--r-pill: 999px; --r-field: 8px; --r-block: 14px; --r-window: 18px`. Ніде в CSS не
  писати радіус числом.

### 2.2 Компоненти (`frontend/src/components/ui.tsx` → розбити на `components/ui/*`)
| Компонент | Призначення |
|---|---|
| `Button` | `variant: primary / default / soft / quiet / danger`, `size: 30 / 36 / 44`, `icon`, `kbd` |
| `IconButton` | кругла кнопка-іконка з `aria-label` |
| `StatusPill`, `Tag` | статус із крапкою (колір з `Status.color`), позначки VIP / Дубль / Чорний список |
| `Tabs` | вкладки-пігулки з лічильниками й «Ще» для тих, що не вмістились |
| `Segmented` | перемикач вигляду: Стрічка / Дошка, періоди |
| `FilterChip` | «+ Менеджер» → випадний `MultiSelect`; активний чип — з хрестиком |
| `Field`, `MoneyInput`, `PhoneInput`, `QtyStepper`, `Select`, `SearchSelect`, `Textarea` | поля радіусом 8, підпис зверху, помилка знизу, синій підпис «звідки взялося» |
| `Toggle` | перемикач |
| `DenseTable` | рядок 31 px, групи з підсумками, вибір (клік, пробіл, Shift), дії при наведенні, закріплена шапка, заглушки, порожній стан, колонки з налаштувань користувача |
| `Block`, `SummaryBlock`, `PropertyList`, `Checklist` | блоки картки |
| `Window` | велике, середнє й мале вікно поверх сторінки з маршрутом (§2.4); `SidePanel` — 360 px |
| `BulkBar`, `Fab`, `Toast` (з «Скасувати») | |

### 2.3 Каркас (`components/Layout.tsx`)
- **Бокова панель** 236 px, групи меню з `GET /api/meta` (`meta.nav`). Якщо `leads_enabled = false`, пункт «Ліди» не
  показується. Новий пункт «Видаткові накладні» (`/invoices`) — за правом `orders`.
- **Лічильники.** `GET /api/meta` → `counters: { leads_new, orders_unsorted, reminders_due }`. Оновлюються подіями
  SSE `/api/events` (уже є): на зміну статусу публікувати `counters`.
- **Збережені фільтри.** Нова таблиця, міграція `0016`:
  ```
  saved_filters(id, user_id → users, section varchar(20) 'orders'|'leads'|…, name varchar(80),
                color varchar(9), query text /* рядок адреси ?status=…&manager=… */, sort int,
                is_shared bool default false, created_at)
  ```
  API: `GET /api/saved-filters?section=`, `POST`, `PATCH /{id}`, `DELETE /{id}`. Лічильник рахується тим самим
  запитом списку з `limit=0` (поле `total`).
- **Перемикач відділу** — вже є (відділ користувача); показувати його в боковій панелі.
- **Кнопка «+»** — `Fab` з меню швидких дій. Клавіші N, L, P, C, T — глобальні, не спрацьовують у полях вводу.
- **Пошук Ctrl K** — `CommandPalette.tsx` (вже є); додати групи результатів і «Дії».

### 2.4 Вікна поверх списку
- **Маршрути** `/orders/:id`, `/leads/:id`, `/products/:id`, `/customers/:id`, `/settings/:section` відкриваються як `Window`
  поверх попередньої сторінки. React Router «background location»: `navigate(to, { state: { background: location } })`.
  Якщо адресу відкрито напряму, вікно показується поверх відповідного списку.
- **Закриття:** Esc або «Назад» браузера. J / K — сусідній запис із поточного списку (передавати `ids` списку через
  state або кеш запиту).

### 2.5 Налаштування користувача
Таблиця `user_prefs(user_id, key varchar(60), value json, PK(user_id, key))`, міграція `0016`.
API: `GET /api/me/prefs`, `PUT /api/me/prefs/{key}`. Ключі: `orders.columns`, `leads.columns`, `orders.density`, `sidebar.collapsed`.

---

## 3. Статуси замовлень (міграція `0017_status_redesign`)

Відповідність старих і нових статусів:

| Новий статус | Код | Що робить міграція |
|---|---|---|
| Несортований | `unsorted` (новий) | вставити: stage `order`, sort 5, колір `#7C7B76`, `stock_action none`, не апрув |
| Прийнятий | `confirmed` | назва «Підтверджено» → «Прийнятий», колір `#2E6BE6` |
| — | `packing` | якщо замовлень у статусі 0 — `is_active = false`; інакше лишити й показати в «⋯» |
| Відправлений | `shipped` | «Відправлено» → «Відправлений», `#6D5BD0` |
| Очікує на отримання | `arrived` (новий) | вставити: sort 65, `#D97706`, `stock_action none` (товар уже списаний при `shipped`), апрув |
| Завершений | `delivered` | «Отримано» → «Завершений», `#16A34A` |
| Відмова на пошті | `refused` | «Відмова / повертається» → «Відмова на пошті», `#E11D48` |
| Повернуто на склад | `returned` | «Повернення на складі» → «Повернуто на склад», `#64748B` |
| Відмова | `cancelled` | «Скасовано» → «Відмова», `#DC2626`; для нього вимагати причину (`reason_id`) |
| Ліди: Новий, Недодзвон, Передзвонити, Дубль | `new`, `no_answer`, `callback`, `duplicate` | stage `lead`; «Недозвон» → «Недодзвон» |
| Відмова ліда | `lead_refused` (новий) | stage `lead`, фінальний, `stock_action release` |

- **НП.** Додати в `NpStatusRule` правило коди `7`, `8` (прибув у відділення / поштомат) → `arrived`. Вставляти
  лише якщо таких кодів ще немає в правилах. Перевірити `NP_STATUSES` у `services/np.py`.
- **Початковий статус.** Нова функція `services/orders.py: initial_status(db, origin)`, яка замінить
  `status_by_code(db, "new")` у рядку 237:
  - `origin = "form"` (webhook лендингу): `new`, якщо `leads_enabled`, інакше `unsorted`;
  - `origin = "marketplace" | "site" | "manual"` → `unsorted`;
  - ручне створення менеджером з картки — `unsorted`, але кнопка «Прийняти» одразу поруч.
- **Наслідки для сервісів:**
  - `dashboard.py` (`leads_new`) рахує `new` лише коли ліди увімкнено; додати `orders_unsorted`;
  - мапи статусів маркетплейсів працюють за `status_id` — перевірити, що «нові» з маркетплейсів мапляться в `unsorted`;
  - шаблони SMS за статусами не змінюються.
- **Тести** — `tests/test_status_redesign.py`:
  - міграція на базі зі зміненими назвами їх не перезаписує;
  - повторний запуск нічого не змінює;
  - нове замовлення з маркетплейсу потрапляє в `unsorted`;
  - НП-код 7 переводить у `arrived`.

---

## 4. Ліди

### 4.1 Налаштування (ключі в `services/settings.py: DEFAULTS`)
```
"leads_enabled": "1",
"lead_wait_warn_min": "5", "lead_wait_bad_min": "15",
"lead_noanswer_remind_min": "30",
"lead_to_order_status": "confirmed",   # або "unsorted" — відповідь на відкрите питання з UI-DESIGN §18
```
- `GET /api/meta` віддає `leads_enabled` і пороги.
- Вимкнення розділу — `POST /api/settings/leads {enabled: false, move_open: true}`: усі замовлення зі статусом
  `stage='lead'` і не фінальним переводяться в `unsorted` із записом у журнал. Відповідь містить кількість перенесених
  (для вікна «12 відкритих лідів — перенести?» спершу `GET /api/settings/leads/preview` → `{open: 12}`).

### 4.2 Модель
Міграція `0018_leads`:
- `orders.call_attempts int default 0`, `orders.last_call_at timestamp null`;
- час «Передзвонити» — наявне поле `orders.remind_at`.

### 4.3 API
- Список: `GET /api/orders?stage=lead&tab=open|new|no_answer|callback|duplicate|refused|converted|all`. У рядку додатково
  `wait_minutes` (від `created_at` або від `remind_at`, якщо настав), `call_attempts`, `remind_at`.
  Сортування за замовчуванням — хто чекає найдовше; «Передзвонити» з настанням часу — вгору.
- Черга: `GET /api/leads/queue?filter=all|new|callback` → упорядковані `id` для вікна дзвінків.
- Результат дзвінка: `POST /api/orders/{id}/lead-result`
  `{ result: "no_answer"|"callback"|"refused"|"duplicate", at?: datetime, reason_id?: int, duplicate_of_id?: int, note?: str }`.
  Ендпоінт ставить статус і `call_attempts += 1` для no_answer, а `remind_at` — для callback (`at` або `+lead_noanswer_remind_min`).
  SMS надсилає за шаблоном статусу (як зараз). Повертає `{ order, next_id }`.
- Створення замовлення: `POST /api/orders/{id}/convert` → статус `lead_to_order_status`. Помилка 422, якщо немає товару,
  доставки чи виду оплати. Повертає `{ order, next_id }`. Після цього фронтенд показує повідомлення з «Відкрити» і «Скасувати»
  (скасування — повернення попереднього статусу через `PATCH`).

### 4.4 Фронтенд
`pages/Leads.tsx` (новий) з виглядами Стрічка, Дошка й Передзвони. Вікно ліда — `OrderCard` у режимі `lead`: черга зліва,
блоки Контакт, Запит і Дзвінки, плашка «Створити замовлення», яка розгортає блоки Товари, Оплата й Доставка. Клавіші F1, F2, F3 і Ctrl ⏎.

### 4.5 Тести
`tests/test_leads.py`:
- вимкнення розділу переносить відкриті ліди;
- `lead-result` для всіх варіантів;
- `convert` без товару повертає 422;
- `initial_status` для форми при вимкнених лідах дає `unsorted`.

---

## 5. Щільні списки

- `GET /api/orders` (і `?stage=lead`): додати `groups: [{ day: date, count, sum }]` для дат на поточній сторінці.
  Підсумки рахуються одним `GROUP BY date(created_at)` з тими самими фільтрами. Сума — без скасованих і дублів, як у
  dashboard.
- Колонки й щільність — з `user_prefs`. Порядок і видимість колонок зберігаються при зміні.
- Колонка «Перевірка оплати» — уже є (`services/pay_check.py`). Дзвіночок нагадування — з `remind_at <= now`.
- **Масові дії** — наявний `POST /api/orders/bulk`. Додати дію `create_ttn`: створює ТТН для кількох замовлень із типовими
  параметрами ключа НП і повертає звіт по кожному. Також `print_labels` — один PDF з наклейками.
- **Продуктивність:** для 1 000 замовлень на сторінку — серверна пагінація (вже є), на фронтенді віртуалізація рядків, коли
  їх понад 200.

---

## 6. Картка замовлення

### 6.1 Рахунки юрособ і передоплата (міграція `0019_payments_accounts`)
```
legal_entity_accounts(id, legal_entity_id → legal_entities ON DELETE CASCADE, name varchar(80) /* «Monobank» */,
                      kind varchar(10) 'card'|'iban'|'cash'|'service', iban varchar(34), card_mask varchar(20),
                      is_active bool, sort int)
payments: + account_id → legal_entity_accounts NULL, + confirmed_by_id → users NULL, + confirmed_at timestamp NULL
```
- Налаштування → Юрособи: список рахунків у картці юрособи. CRUD: `GET/POST/PATCH/DELETE /api/legal-entities/{id}/accounts`.
- Картка: у рядку передоплати — вибір рахунку тієї юрособи, що в замовленні. Позначка ✓ ставить `status = received`,
  `confirmed_by_id` і `confirmed_at`.

### 6.2 «Що лишилось» (`services/checklist.py`)
`build_checklist(db, order) -> list[TodoItem]`; `TodoItem = { key, label, state: done|pending|error, hint?, action? }`.
Повертається в `OrderOut.todo`. Пункти й умови — з `UI-DESIGN.md` §5.5:

| key | Умова появи | done, коли |
|---|---|---|
| `reserve` | статус з `stock_action` reserve або далі | `stock_reserved` (error, якщо не вистачає залишку) |
| `prepay` | вид оплати `partial` / `prepaid` | є `payments` з `status=received` |
| `prepay_receipt` | є передоплата і каса юрособи | є `CheckboxReceipt` типу передоплата зі `status=done` |
| `ttn` | доставка не самовивіз | `orders.ttn` |
| `label` | є ТТН | `orders.label_printed_at` |
| `waybill` | `doc_in_parcel = 1` у налаштуваннях | є `issued_documents` waybill з `print_count > 0` |
| `registry` | ТТН НП | `orders.np_registry_ref` |
| `sms_ttn` | є ТТН і шаблон SMS для статусу | є `sms_messages` з цим шаблоном |
| після відправки: `received`, `money`, `cod_receipt` | статус `shipped` або далі | трекінг: `delivered`, `payments` cod received, чек післяплати |

Міграція `0019` (та сама): `orders.label_printed_at timestamp`, `orders.np_registry_ref varchar(40)`,
`orders.delivery_eta date`. `label_printed_at` ставить `GET /api/orders/{id}/label`.

### 6.3 Вікно ТТН
- `GET /api/orders/{id}/ttn/preview` (уже є) — додати `price` (НП `InternetDocument.getDocumentPrice`), `eta`
  (`getDocumentDeliveryDate`), `cod_commission` (якщо контроль оплати).
- **Пошук.** Відділення й поштомати — наявний пошук міст і відділень. До кожного пункту додати `max_weight`, щоб показати
  обмеження.
- `POST /api/orders/{id}/ttn` — додати `after: { print_label, add_registry, send_sms, set_shipped }`. Дії виконуються після
  створення (друк — повертається посилання на PDF наклейки).
- **Трекінг** заповнює `delivery_eta` з `ScheduledDeliveryDate`.

### 6.4 Реєстр НП (нова функція)
- `carriers/novaposhta.py`: `ScanSheet.insertDocuments` (створити або доповнити реєстр на сьогодні для ключа НП),
  `ScanSheet.getScanSheetList`, `ScanSheet.removeDocuments`, друк реєстру.
- Сервіс `services/np.py: add_to_registry(order_ids)` зберігає `np_registry_ref`. Масова дія «Реєстр НП» і пункт у «⋯» доставки.
- Тести з моком НП: два замовлення одного ключа потрапляють в один реєстр за день.

### 6.5 Інші поля картки
- `OrderOut.items[].catalog_price` — для підпису «ціна в каталозі», коли ціну змінено в замовленні.
- `OrderOut.customer_summary` — плитки (замовлень, викуп, відмов, сума) та інші замовлення (останні 5). Це є в сервісі
  покупців, треба лише віддати в картку.
- **Історія:** `GET /api/orders/{id}/history?kind=all|status|sms|comments` — об'єднання `audit_log`, `order_comments`,
  `sms_messages`, сортування за часом.
- **«Хтось редагує».** Подія SSE `order_open {order_id, user}` раз на 30 с, поки вікно відкрите; у картці — смуга
  «Олена зараз редагує це замовлення». Необов'язково для першого кроку.
- **Автозбереження** — наявний `PATCH /api/orders/{id}` з затримкою 0,8 с; на фронтенді — черга змін, щоб не губити
  швидке введення.

---

## 7. Видаткові накладні (міграція `0020_issued_documents`)

### 7.1 Таблиці
```
issued_documents(
  id, kind varchar(10) 'waybill'|'invoice'|'warranty',
  legal_entity_id → legal_entities, order_id → orders ON DELETE SET NULL, customer_id → customers NULL,
  number int, number_text varchar(30) /* 'РН-0168' */, issued_at timestamp, total numeric(12,2),
  snapshot json /* усе, що потрібно для PDF: реквізити, покупець, товари, ціни, гарантія, налаштування документа */,
  payload_hash varchar(64) /* хеш даних замовлення на момент видачі — для «змінилось» */,
  state varchar(10) 'active'|'void', replaced_by_id → issued_documents NULL,
  created_by_id → users NULL, print_count int default 0, last_printed_at timestamp NULL,
  UNIQUE(legal_entity_id, kind, number)
)
document_counters(legal_entity_id, kind, next_number int, PK(legal_entity_id, kind))
legal_entities: + waybill_prefix, invoice_prefix, warranty_prefix varchar(10) NULL  -- якщо NULL — глобальні з налаштувань
```

### 7.2 Сервіс `services/documents.py`
- `issue(db, order, kind, user)` — повертає чинний документ цього типу для замовлення або створює новий. Номер видається
  `SELECT … FOR UPDATE` з `document_counters` і ніколи не повторюється. `snapshot` будується тим самим кодом, що зараз
  віддає `GET /api/orders/{id}/documents`.
- `reissue(db, doc, user)` — новий документ з новим номером. Старий отримує `state=void` і `replaced_by_id`.
- `void(db, doc, user)`.
- `is_changed(doc, order)` — порівняння `payload_hash` з хешем поточних даних.
- **Автовидача.** Хук на зміну статусу на `shipped` видає `waybill` і `warranty`, якщо налаштування
  `doc_auto_issue = "shipped"` (інші варіанти: `"print"` — при першому друці, `"off"`). `invoice` — лише кнопкою.
- **Наявні замовлення** не переносяться: документи з'являються з моменту запуску. Опція «Видати для відправлених за період» —
  у Системі.

### 7.3 API
- `GET /api/documents?entity=&period=&q=&has_invoice=&status=&page=`. Рядок відповіді: видаткова накладна + стан
  рахунку й гарантії того ж замовлення: `{ id, number_text, issued_at, order_id, customer, entity, total, state, changed,
  docs: { waybill: id, invoice: id|null, warranty: id|null } }`. Плюс підсумок за період і лічильники за юрособами для вкладок.
- `POST /api/orders/{id}/documents/{kind}` — видати або повернути чинний (кнопки в «Друк ▾» картки).
- `GET /api/documents/{id}` → `snapshot` для побудови PDF у браузері (`lib/docs.ts` бере дані зі snapshot, а не з поточного замовлення).
- `POST /api/documents/{id}/printed` — `print_count += 1`. `POST /api/documents/{id}/reissue`, `POST /api/documents/{id}/void`.
- `GET /api/documents/export?format=csv|xlsx&…` — реєстр для бухгалтера.
- Архів PDF для масової дії — у браузері (pdfmake + JSZip у `lib/vendor`), щоб не тягнути pdfmake на сервер.

### 7.4 Тести (`tests/test_issued_documents.py`)
- Нумерація окрема для юрособи й типу, без повторів при паралельних запитах.
- Snapshot не змінюється після зміни ціни товару.
- Перевипуск дає новий номер, а старий стає `void`.
- Автовидача при `shipped`.
- `changed` стає true після зміни товарів замовлення.

---

## 8. Вікна товару й покупця

- **Товар.** Наявні `GET/PATCH /api/products/{id}` (catalog). Новий `GET /api/products/{id}/summary?days=30` →
  `{ qty, sum, margin, buyout_rate, upsell_share, sold_total }` — з `services/stats.py` (фільтр за товаром). Генератор
  варіантів — наявна логіка атрибутів. Кнопка «Скласти варіанти» робить декартовий добуток значень, артикули пропонуються
  за шаблоном `{SKU}-{значення}`.
- **Покупець.** `GET /api/customers/{id}` розширити:
  - `orders` (усі, з оплатою й доставкою);
  - `communications` — `sms_messages` за телефоном і записи журналу про дзвінки;
  - `addresses` — групування доставок з `orders`: служба, місто, відділення, кількість;
  - `tiles` — замовлень, викуп, відмов, сума.
  
  Поле «Додатковий телефон» у макеті — `customers.phone2 varchar(20)` (міграція `0021`), пошук покупця за обома номерами.

## 9. Склад

`services/stock.py: forecast(db, variant_ids)`:
- `daily = продано за 30 днів / 30`;
- `days_left = available / daily`;
- `None`, якщо `daily = 0`.

Ендпоінт `GET /api/stock?filter=all|low|out|dead` — рядки по варіантах із прогнозом. `dead` — без продажів 60 днів при залишку > 0.
Рухи за день — наявний `StockMovement`.

## 10. Головна

`GET /api/dashboard?period=YYYY-MM|from..to` (зараз завжди поточний місяць). Додати:
- `customers.repeat_share`, `customers.blacklisted`;
- `quality` з дельтами до попереднього періоду;
- `attention.reminders_due` (вже є як `reminders`).

Фронтенд — новий `pages/Home.tsx` за макетом.

## 11. Статистика

API не змінюється. `pages/Stats.tsx`:
- **Шапка:** тип дати, період і групування. Фільтри — частина чипами, решта під «Ще N фільтрів і пошук».
- **Показники:** 4 плитки й смуга з 6 показників.
- **Графік:** легенда праворуч, повзунок лишається.
- **Вкладки** — `Tabs`, таблиці — `DenseTable`.

## 12. Налаштування

- Вікно `/settings/:section`, нижня смуга «Зберегти зміни». Кнопка активна, лише коли форма змінена; без автозбереження.
- **Загальні:** `leads_enabled` і пороги (§4.1); `doc_auto_issue`, `doc_in_parcel` — у «Документах».
- **Юрособи:** рахунки (§6.1) і префікси документів (§7.1).

## 13. Мобільна версія

- Точки зламу: `≤ 768` — телефон, `769–1279` — згорнута бокова панель.
- Нижня панель вкладок і центральна «+»; вікна — на весь екран; `DenseTable` перетворюється на картки.
- Перевірка: Playwright на 390 і 375 px — без прокрутки вшир, цілі дотику ≥ 44 px.

## 14. Перевірка кожного кроку

1. `pytest -q` зелений (нові тести з розділів вище), `alembic check`, міграції з нуля й на копії бази з даними.
2. `npm run build` без помилок TypeScript; `test_openapi_snapshot_is_current`.
3. Скриншоти Playwright змінених сторінок на 1440 і 390 px (`uvicorn app.main:app` + `python demo_data.py`). Порівняння з
   `docs/design/screens/*`, без помилок у консолі.
4. Звірка з чеклістом `UI-DESIGN.md` §16 і переліком §19 (нічого з наявних функцій не загублено).
5. Запис у `docs/ROADMAP.md`, розділ «Новий інтерфейс»: що зроблено, номери міграцій, тести.

## 15. Порядок і обсяг

| Крок | Гілка | Міграції | Обсяг |
|---|---|---|---|
| 1. Токени, шрифт, компоненти | `wip/ui-1-tokens` | — | M |
| 2. Каркас, збережені фільтри, налаштування користувача | `wip/ui-2-shell` | 0016 | M |
| 3. Статуси й «Несортовані», щільний список замовлень | `wip/ui-3-orders` | 0017 | M |
| 4. Ліди (перемикач, стрічка, дошка, вікно дзвінка) | `wip/ui-4-leads` | 0018 | L |
| 5. Картка замовлення, рахунки юрособ, «Що лишилось», вікно ТТН, реєстр НП | `wip/ui-5-card` | 0019 | L |
| 6. Видаткові накладні | `wip/ui-6-invoices` | 0020 | L |
| 7. Вікна товару й покупця, склад | `wip/ui-7-catalog` | 0021 | M |
| 8. Головна, статистика, налаштування | `wip/ui-8-home-stats` | — | M |
| 9. Мобільна версія | `wip/ui-9-mobile` | — | M |

Номери міграцій орієнтовні: якщо паралельно з'явиться інша міграція, зсунути нумерацію.

## 16. Ризики

- **Перейменування статусів** змінює тексти в SMS-шаблонах, якщо там підставляється назва статусу. Перевірити шаблони після
  міграції.
- **Rozetka / Prom:** мапи статусів за `status_id` не ламаються, але нові `unsorted` і `arrived` треба додати в мапи, інакше
  замовлення з маркетплейсу не отримає правильний статус.
- **Реєстр НП** — нова інтеграція: перевірити на тестовому ключі, реєстр не можна змінювати після передачі кур'єру.
- **Документи зі snapshot:** старі PDF до запуску не мають запису. Не видавати номери «заднім числом» без явної команди.
- **Ліди вимкнено при наявних лідах:** перенесення незворотне масово — тільки з підтвердженням і записом у журнал.
