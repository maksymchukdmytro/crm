// Спільна бічна панель і верхній рядок для макетів комп'ютера.
window.sidebar = (active) => {
  const items = [
    ["Продажі"], ["home", "Головна", "home"], ["inbox", "Ліди", "leads", "4", 1], ["orders", "Замовлення", "orders", "17", 1],
    ["doc", "Видаткові накладні", "inv"], ["board", "Дошка", "board"], ["users", "Покупці", "cust"],
    ["Склад"], ["box", "Товари", "prod", "13"], ["boxes", "Склад", "stock"], ["cart", "Закупівлі", "purch"],
    ["Гроші й аналітика"], ["wallet", "Оплати", "pay"], ["chart", "Статистика", "stats"], ["report", "Звіти", "rep"],
    ["Збережені фільтри"], ["#2F6BE6", "Чекають ТТН", "s1", "14"], ["#7C4DDB", "Передзвонити сьогодні", "s2", "5"],
    ["Керування"], ["history", "Журнал дій", "audit"], ["gear", "Налаштування", "set"], ["pulse", "Система", "sys"],
  ];
  const nav = items.map(([ic, label, key, n, hot]) => {
    if (!label) return `<div class="sb-t">${ic}</div>`;
    const lead = ic.startsWith("#") ? `<span class="sb-sq" style="background:${ic}"></span>` : icon(ic);
    const cnt = n ? `<span class="count ${hot ? "" : "plain"}">${n}</span>` : "";
    return `<div class="sb-i ${key === active ? "on" : ""}">${lead}<span class="sp ell">${label}</span>${cnt}</div>`;
  }).join("");
  return `<aside class="sb">
    <div class="sb-top"><span class="logo">m</span><b style="font-size:15.5px;font-weight:600;flex:1">mdmy</b><span style="width:7px;height:7px;border-radius:9px;background:var(--ok)"></span></div>
    <div class="sb-office">${icon("building")}<span style="flex:1">Відділ: усі</span>${icon("down")}</div>
    <nav class="sb-nav">${nav}</nav>
    <div class="sb-me"><span class="av">А</span><span style="display:flex;flex-direction:column;line-height:1.25"><span style="font-size:13.5px">Адміністратор</span><span style="font-size:12px;color:var(--muted)">Адміністратор</span></span></div>
  </aside>`;
};
window.topbar = () => `<div class="topbar">
  <div class="search">${icon("search")}<span>Шукати замовлення, телефон, ТТН або товар…</span><kbd>Ctrl K</kbd></div>
  <span style="flex:1"></span>
  <button class="ibtn">${icon("chat")}</button>
  <button class="ibtn">${icon("bell")}<span class="badge">1</span></button>
</div>`;
