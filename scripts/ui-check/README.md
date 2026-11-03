# Перевірка інтерфейсу «як користувач»

Скрипти Playwright, якими перевіряємо CRM після змін інтерфейсу (див. `docs/DESIGN-WAY.md`, розділ 1, крок 5).
Пишуть скриншоти в `/tmp/claude-0/…` — шлях можна змінити константою `O`/`OUT` на початку файлу.

## Підготовка (локально, без Docker)

```bash
service postgresql start; redis-server --daemonize yes
# бази: crm_ui — демо (python demo_data.py), crm_stress — ~2 650 замовлень для стрес-тесту
gh run download <id CI> -R maksymchukdmytro/crm -n frontend-dist -D frontend/dist   # зібраний інтерфейс з CI
scripts/ui-check/restart.sh     # сервери: 8077 — crm_ui, 8078 — crm_stress (лише для локальної перевірки)
```

Вхід у скриптах — демо-адміністратор `admin` / `admin12345` (лише локальна база).
**Не вбивайте сервери командою з `uvicorn` у тексті** (`pkill -f uvicorn` уб'є й власну оболонку) — для цього `restart.sh`.

## Скрипти

| Файл | Що робить |
|---|---|
| `walk.py [pc\|mob\|both]` | Повний прохід усіх сторінок (ПК 1440×900, телефон 390×844) на стрес-базі: скриншот кожної, помилки JS, відповіді API 4xx/5xx, прокрутка вшир, дрібні цілі дотику, обрізаний текст, час відкриття, подвійний клік «Створити». |
| `vstress.py` | Нові вигляди списку замовлень на 1024 / 1280 / 1920: швидкість, догрузка тисяч карток, «Скринька» J × 40, дозбереження, «Прийняти й далі», фільтри, «ТТН» з картки, пошук «/». |
| `views.py` | Скриншоти Таблиця / Картки / Скринька / фільтри (демо-база). |
| `restart.sh` | Перезапуск обох локальних серверів. |

## Склеїти скриншоти в аркуші (щоб переглянути 40 екранів за раз)

```python
from PIL import Image; import glob
fs = sorted(glob.glob("/tmp/claude-0/walk/mob-*.png"))
for i in range(0, len(fs), 5):
    sheet = Image.new("RGB", (5 * 402 + 12, 892), "#DADCD6")
    for k, f in enumerate(fs[i:i + 5]): sheet.paste(Image.open(f).convert("RGB"), (12 + k * 402, 40))
    sheet.save(f"/tmp/claude-0/sheet-{i // 5 + 1}.png")
```

## Баланс дужок у CSS (зайва `}` тихо вимикає наступне правило)

```bash
cd frontend/src && python3 -c "
import re,glob
for f in glob.glob('**/*.css', recursive=True):
    s = re.sub(r'/\*.*?\*/', '', open(f).read(), flags=re.S); print(f, s.count('{') - s.count('}'))"
```
Скрізь має бути 0.
