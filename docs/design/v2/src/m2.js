// Мобільна CRM, варіант 2: картки-блоки, іконки в кружечках, кольорові вкладки статусів (рішення власника).
document.head.insertAdjacentHTML("beforeend", `<style>
.phone { background: #F2F3F5; }
.hdr { display: flex; align-items: center; gap: 10px; padding: 14px 16px 8px; }
.hdr h1 { margin: 0; flex: 1; font-size: 26px; font-weight: 650; letter-spacing: -.025em; }
.cb { width: 42px; height: 42px; border-radius: 99px; background: #fff; display: grid; place-items: center; color: var(--ink); position: relative; flex: none; box-shadow: 0 1px 2px rgba(16,24,40,.05); }
.cb svg.i { width: 20px; height: 20px; }
.cb .badge { top: -2px; right: -2px; border-color: #F2F3F5; }
.body { flex: 1; min-height: 0; overflow: hidden; padding: 4px 16px 110px; display: flex; flex-direction: column; gap: 14px; }
.blk { background: #fff; border-radius: 22px; padding: 16px; box-shadow: 0 1px 2px rgba(16,24,40,.04); }
.sh { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.sh .ttl { font-size: 16px; font-weight: 650; flex: 1; }
.sh .all { font-size: 13.5px; color: var(--accent-ink); font-weight: 600; }
.ic { width: 38px; height: 38px; border-radius: 12px; display: grid; place-items: center; flex: none; }
.ic svg.i { width: 19px; height: 19px; }
.ic.blue { background: #EAF1FE; color: #2458C4; } .ic.green { background: #E6F5EC; color: #17663D; } .ic.orange { background: #FDF0DF; color: #9A5205; }
.ic.red { background: #FCE9E8; color: #B42318; } .ic.violet { background: #F0ECFC; color: #5A3FB8; } .ic.gray { background: #F1F1EE; color: #4A4945; }
.chipsx { display: flex; gap: 8px; overflow: hidden; white-space: nowrap; padding: 0 16px; }
.st { display: inline-flex; align-items: center; gap: 7px; height: 36px; padding: 0 14px; border-radius: 99px; font-size: 14px; font-weight: 600; flex: none; }
.st .n { font-weight: 600; opacity: .7; }
.cnt { min-width: 22px; height: 22px; padding: 0 7px; border-radius: 99px; font-size: 12px; font-weight: 700; display: inline-grid; place-items: center; }
.dock { position: absolute; left: 12px; right: 12px; bottom: 14px; height: 66px; border-radius: 24px; background: #1C1C1A; display: grid; grid-template-columns: repeat(5, 1fr); align-items: center; box-shadow: 0 10px 30px rgba(0,0,0,.25); }
.dk { display: flex; flex-direction: column; align-items: center; gap: 3px; color: rgba(255,255,255,.55); font-size: 11px; position: relative; }
.dk svg.i { width: 22px; height: 22px; stroke-width: 1.8; }
.dk.on { color: #fff; font-weight: 600; }
.dk .badge { top: -6px; right: calc(50% - 20px); border-color: #1C1C1A; }
.dfab { width: 50px; height: 50px; margin: 0 auto; border-radius: 18px; background: var(--accent); color: #fff; display: grid; place-items: center; }
.dfab svg.i { width: 24px; height: 24px; stroke-width: 2.4; }
.thumb { border-radius: 12px; background: linear-gradient(140deg, #ECEDEF, #DADCE0); display: grid; place-items: center; color: #9A9DA3; flex: none; }
</style>`);
window.dock = (on) => `<nav class="dock">
  <span class="dk ${on === "home" ? "on" : ""}">${icon("home")}Головна</span>
  <span class="dk ${on === "orders" ? "on" : ""}">${icon("orders")}<span class="badge">16</span>Замовлення</span>
  <span class="dfab">${icon("plus")}</span>
  <span class="dk ${on === "leads" ? "on" : ""}">${icon("inbox")}<span class="badge">4</span>Ліди</span>
  <span class="dk ${on === "more" ? "on" : ""}">${icon("menu")}Ще</span></nav>`;
// кольори статусів як у CRM; вкладка: світлий фон + колір, вибрана — насичений фон
window.ST = { u: ["Несортований", "#7A7973"], n: ["Новий", "#2F6BE8"], c: ["Прийнятий", "#1F8FD6"], s: ["Відправлений", "#6D4FD1"], w: ["Очікує на пошті", "#D9820B"], d: ["Завершений", "#1E8A52"], r: ["Відмова на пошті", "#D93025"], x: ["Відмова", "#B42318"] };
window.stTab = (k, label, n, on) => { const c = ST[k][1]; return on
  ? `<span class="st" style="background:${c};color:#fff">${label}<span class="n">${n}</span></span>`
  : `<span class="st" style="background:color-mix(in srgb, ${c} 12%, white);color:color-mix(in srgb, ${c} 80%, black)">${label}<span class="n">${n}</span></span>`; };
window.stPill = (k) => { const c = ST[k][1]; return `<span style="display:inline-flex;align-items:center;gap:6px;height:24px;padding:0 9px;border-radius:99px;font-size:12.5px;font-weight:600;background:color-mix(in srgb, ${c} 12%, white);color:color-mix(in srgb, ${c} 82%, black)"><span style="width:6px;height:6px;border-radius:9px;background:${c}"></span>${ST[k][0]}</span>`; };
