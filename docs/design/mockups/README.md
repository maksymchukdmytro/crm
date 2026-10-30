# Генератори макетів

Картинки-орієнтири для `docs/UI-DESIGN.md`. Це не код CRM.

- `common.py` — іконки lucide (`icons/`), шрифти, дані-приклади, функція `page()`.
- `v13_final.py` → картка замовлення (обрана схема); `v15_card.py` — та сама з компактними товарами.
- `v14_pages.py` → 10 сторінок (каркас, ТТН, товари, склад, покупці, налаштування).
- `v15_pages.py` → правки: головна, щільні списки, ліди, накладні, вікна товару й покупця, статистика.

Запуск: `python3 render.py v15_pages v15_card` → `out/<модуль>-<кадр>.png`.
Потрібні Playwright з Chromium (шлях — у `render.py`) і шрифти в `fonts/`
(Onest.ttf, Manrope.ttf, JetBrainsMono.ttf з Google Fonts; решта з `common.py` необов'язкові).
