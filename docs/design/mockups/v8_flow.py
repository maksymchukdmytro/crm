"""Варіант 8 — «Робоче місце менеджера»: інтерфейс збудований за шляхом замовлення від заявки до грошей.
Стиль — стриманий Кобальт: синій для дій, лайм лише для однієї головної кнопки екрана."""
from common import *

CSS = """
.v8{--ink:#14162B;--mut:#6B6F86;--line:#E6E8F0;--soft:#F1F2F7;--b:#2D3FE7;--b2:#EEF0FE;--lime:#C8F560;--bg:#F5F6FA;--ok:#16A34A;--warn:#D97706;--bad:#DC2626;
  font:400 13.5px/1.45 'Rubik',sans-serif;color:var(--ink);background:var(--bg);width:100%;height:100%;display:flex}
.v8 b{font-weight:500}
/* згорнуте меню — у режимі дзвінка й відправки нічого не відволікає */
.v8 .rail{width:64px;background:#fff;border-right:1px solid var(--line);display:flex;flex-direction:column;align-items:center;padding:14px 0;gap:6px}
.v8 .rail .lg{width:36px;height:36px;border-radius:10px;background:var(--b);color:#fff;display:grid;place-items:center;margin-bottom:8px}
.v8 .rail .r{width:42px;height:42px;border-radius:11px;display:grid;place-items:center;color:#8A8DA6;position:relative}
.v8 .rail .r.on{background:var(--b2);color:var(--b)}.v8 .rail .r em{position:absolute;top:3px;right:2px;font:500 10px 'Rubik';font-style:normal;background:var(--b);color:#fff;border-radius:99px;padding:0 5px}
.v8 .rail .av{margin-top:auto;width:34px;height:34px;border-radius:50%;background:#FFD7B8;display:grid;place-items:center;font-size:11.5px;font-weight:600}
/* повне меню */
.v8 .side{width:236px;background:#fff;border-right:1px solid var(--line);padding:16px 12px;display:flex;flex-direction:column;gap:4px}
.v8 .brand{display:flex;align-items:center;gap:9px;font-weight:600;font-size:17px;margin-bottom:6px}.v8 .brand .lg{width:32px;height:32px;border-radius:9px;background:var(--b);color:#fff;display:grid;place-items:center}
.v8 .ws{display:flex;align-items:center;gap:9px;padding:7px 9px;border:1px solid var(--line);border-radius:11px;margin-bottom:6px}.v8 .ws .a{width:28px;height:28px;border-radius:8px;background:var(--b2);color:var(--b);display:grid;place-items:center;font-weight:600;font-size:12px}
.v8 .ws small{display:block;font-size:11px;color:var(--mut);line-height:1.1}.v8 .ws .i:last-child{margin-left:auto;color:var(--mut)}
.v8 .lab{font-size:11.5px;color:#9A9DB2;padding:8px 8px 2px}
.v8 .it{display:flex;align-items:center;gap:10px;height:33px;padding:0 10px;border-radius:9px;color:#3D4060}.v8 .it .i{color:#8A8DA6}
.v8 .it.on{background:var(--b2);color:var(--b);font-weight:500}.v8 .it.on .i{color:var(--b)}
.v8 .it em{margin-left:auto;font-style:normal;font-size:11.5px;color:#9A9DB2}.v8 .it em.b{background:var(--b);color:#fff;border-radius:99px;padding:0 7px}.v8 .it em.w{background:#FFF1E0;color:var(--warn);border-radius:99px;padding:0 7px;font-weight:500}
.v8 .main{flex:1;min-width:0;padding:16px 20px;display:flex;flex-direction:column;gap:12px}
.v8 h1{font-size:24px;font-weight:600;letter-spacing:-.02em}.v8 .subt{color:var(--mut);font-size:13px}
.v8 .hd{display:flex;align-items:center;gap:10px}.v8 .hd .r{margin-left:auto;display:flex;gap:8px;align-items:center}
.v8 .btn{display:inline-flex;align-items:center;gap:7px;height:36px;padding:0 13px;border-radius:10px;border:1px solid var(--line);background:#fff;font-weight:500;font-size:13px;white-space:nowrap;color:var(--ink)}
.v8 .btn.b{background:var(--b);border-color:var(--b);color:#fff}.v8 .btn.l{background:var(--lime);border-color:#B5E54A;color:var(--ink)}
.v8 .btn kbd,.v8 kbd{font:500 10.5px 'Rubik';border:1px solid currentColor;border-radius:5px;padding:0 4px;opacity:.55}
.v8 .card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:14px}
.v8 .st{display:inline-flex;align-items:center;gap:5px;height:21px;padding:0 7px;border-radius:7px;font-size:11.5px;font-weight:500;white-space:nowrap;background:color-mix(in srgb,var(--c) 12%,#fff);color:color-mix(in srgb,var(--c) 72%,#000)}
.v8 .st i{width:6px;height:6px;border-radius:50%;background:var(--c)}
.v8 .chip{display:inline-flex;align-items:center;gap:5px;height:22px;padding:0 8px;border-radius:7px;font-size:12px;background:var(--soft);color:#3D4060;white-space:nowrap}
.v8 .mono{font:500 12.5px 'JB',monospace}
/* ---------- карта шляху ---------- */
.v8 .map{flex:1;display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:10px;min-height:0}
.v8 .stg{background:#fff;border:1px solid var(--line);border-radius:16px;padding:12px;display:flex;flex-direction:column;gap:9px;position:relative}
.v8 .stg:not(:last-child):after{content:"";position:absolute;right:-9px;top:30px;width:8px;height:2px;background:#C7CBEA}
.v8 .stg .n{display:flex;align-items:center;gap:8px}.v8 .stg .n span{width:26px;height:26px;border-radius:8px;background:var(--b2);color:var(--b);display:grid;place-items:center;font-weight:600;font-size:12.5px}
.v8 .stg .n b{font-size:14px;font-weight:600;line-height:1.15}
.v8 .stg .wh{font-size:11.5px;color:var(--mut);display:flex;align-items:center;gap:5px}
.v8 .stg h5{font-size:11px;font-weight:500;color:#9A9DB2;margin-top:2px}
.v8 .stg ul{list-style:none;display:flex;flex-direction:column;gap:3px;font-size:12px;line-height:1.3}
.v8 .stg ul li{display:flex;gap:6px}.v8 .stg ul li:before{content:"";flex:none;width:5px;height:5px;border-radius:2px;margin-top:5px;background:#C7CBEA}
.v8 .stg ul.auto li{color:#2A36B8}.v8 .stg ul.auto li:before{background:var(--b)}
.v8 .stg ul.see li{color:#7A4B00}.v8 .stg ul.see li:before{background:#F2B035}
.v8 .stg.hot{border-color:var(--b);box-shadow:0 0 0 3px var(--b2)}
.v8 .legend{display:flex;gap:16px;font-size:12px;color:var(--mut)}.v8 .legend span{display:flex;align-items:center;gap:6px}.v8 .legend i{width:9px;height:9px;border-radius:3px}
.v8 .deps{display:grid;grid-template-columns:repeat(2,1fr);gap:8px 18px}
.v8 .dep{display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:12.5px}.v8 .dep .chip{background:#fff;border:1px solid var(--line);height:24px}
.v8 .dep .chip.k{background:var(--ink);color:#fff;border-color:var(--ink)}.v8 .dep .ar{color:#A3A6C0}
/* ---------- режим дзвінка ---------- */
.v8 .call{flex:1;display:grid;grid-template-columns:286px 1fr 300px;min-height:0}
.v8 .q{border-right:1px solid var(--line);background:#fff;display:flex;flex-direction:column;min-height:0}
.v8 .q .qh{padding:16px 14px 10px;display:flex;flex-direction:column;gap:8px;border-bottom:1px solid var(--line)}
.v8 .q .qh .t{display:flex;align-items:center;gap:8px}.v8 .q .qh .t b{font-size:17px;font-weight:600}.v8 .q .qh .t .chip{margin-left:auto}
.v8 .seg{display:flex;gap:2px;background:var(--soft);border-radius:9px;padding:3px}.v8 .seg span{flex:1;text-align:center;padding:4px 0;border-radius:7px;font-size:12px;color:var(--mut)}.v8 .seg span.on{background:#fff;color:var(--ink);font-weight:500;box-shadow:0 1px 2px rgba(0,0,0,.08)}
.v8 .ql{padding:6px;display:flex;flex-direction:column;gap:2px;overflow:hidden}
.v8 .qi{padding:9px 10px;border-radius:11px;display:grid;grid-template-columns:1fr auto;gap:2px 8px;font-size:12.5px}
.v8 .qi b{font-size:13.5px}.v8 .qi small{color:var(--mut);font-size:12px}.v8 .qi .tm{justify-self:end;font-weight:500;font-size:12px;display:flex;align-items:center;gap:4px}
.v8 .qi.on{background:var(--b2);box-shadow:inset 3px 0 0 var(--b)}.v8 .qi .row{grid-column:1/-1;display:flex;gap:5px;align-items:center;margin-top:3px}
.v8 .sla-r{color:var(--bad)}.v8 .sla-y{color:var(--warn)}.v8 .sla-g{color:var(--ok)}
.v8 .work{display:flex;flex-direction:column;min-height:0;min-width:0}
.v8 .who{padding:14px 20px 12px;background:#fff;border-bottom:1px solid var(--line);display:flex;flex-direction:column;gap:10px}
.v8 .who .l1{display:flex;align-items:center;gap:12px}.v8 .who .ava{width:44px;height:44px;border-radius:13px;background:#FFE7D4;display:grid;place-items:center;font-weight:600;color:#9A4A12}
.v8 .who h2{font-size:21px;font-weight:600;letter-spacing:-.02em;line-height:1.15}.v8 .who .ph{font:500 15px 'Rubik';display:flex;gap:10px;align-items:center;color:#3D4060}
.v8 .who .l1 .r{margin-left:auto;display:flex;gap:8px}
.v8 .cbtn{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;border:1px solid var(--line);background:#fff;color:var(--ink)}.v8 .cbtn.g{background:#E8F7EE;border-color:#C9EBD5;color:var(--ok)}
.v8 .road{display:flex;align-items:center;gap:0;font-size:11.5px;color:#9A9DB2}
.v8 .road span{display:flex;align-items:center;gap:6px;white-space:nowrap}.v8 .road span i{width:18px;height:18px;border-radius:50%;border:1.5px solid #C7CBEA;display:grid;place-items:center;background:#fff}
.v8 .road span.d{color:var(--ink)}.v8 .road span.d i{background:var(--b);border-color:var(--b);color:#fff}.v8 .road span.c{color:var(--b);font-weight:500}.v8 .road span.c i{border-color:var(--b);box-shadow:0 0 0 3px var(--b2)}
.v8 .road em{flex:1;height:1.5px;background:#DADCEB;margin:0 8px;min-width:14px}.v8 .road em.d{background:var(--b)}
.v8 .form{flex:1;overflow:hidden;padding:14px 20px;display:flex;flex-direction:column;gap:10px}
.v8 .sec{background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px 14px}
.v8 .sec .sh{display:flex;align-items:center;gap:9px;margin-bottom:9px}.v8 .sec .sh .num{width:22px;height:22px;border-radius:50%;display:grid;place-items:center;font-size:11.5px;font-weight:600;background:var(--soft);color:var(--mut)}
.v8 .sec .sh .num.ok{background:var(--ok);color:#fff}.v8 .sec .sh .num.now{background:var(--b);color:#fff}
.v8 .sec .sh b{font-size:14px;font-weight:600}.v8 .sec .sh .hint{margin-left:auto;font-size:12px;color:var(--mut);display:flex;align-items:center;gap:5px}
.v8 .sec.now{border-color:#B9C0F7;box-shadow:0 0 0 3px var(--b2)}
.v8 .sec.done .body{opacity:.95}
.v8 .grid{display:grid;gap:8px 10px}
.v8 .fld{display:flex;flex-direction:column;gap:3px}.v8 .fld label{font-size:11px;color:var(--mut)}
.v8 .inp{height:34px;border:1px solid var(--line);border-radius:9px;padding:0 10px;display:flex;align-items:center;gap:7px;background:#fff;font-size:13px;white-space:nowrap;overflow:hidden}
.v8 .inp.f{border-color:var(--b);box-shadow:0 0 0 3px var(--b2)}.v8 .inp .i:last-child{margin-left:auto;color:#A3A6C0}.v8 .inp .ph2{color:#A3A6C0}
.v8 .from{font-size:11px;color:#2A36B8;display:flex;align-items:center;gap:4px}
.v8 .gi{display:grid;grid-template-columns:36px 1fr auto 92px 76px;gap:10px;align-items:center;padding:6px 0;border-bottom:1px solid var(--soft);font-size:13px}
.v8 .gi .im{width:36px;height:36px;border-radius:10px;background:#14162B;color:#C8F560;display:grid;place-items:center}.v8 .gi .im.lt{background:var(--soft);color:var(--mut)}
.v8 .gi small{display:block;font-size:11.5px;color:var(--mut)}.v8 .gi .sum{text-align:right;font-weight:500}
.v8 .vsel{display:flex;gap:4px}.v8 .vsel span{height:24px;padding:0 7px;border-radius:7px;border:1px solid var(--line);font-size:11.5px;display:flex;align-items:center;gap:4px}
.v8 .vsel span.on{border-color:var(--b);background:var(--b2);color:var(--b);font-weight:500}.v8 .vsel span.no{color:#B9BBCB;text-decoration:line-through}
.v8 .sw{width:10px;height:10px;border-radius:3px;background:var(--c);box-shadow:inset 0 0 0 1px rgba(0,0,0,.15)}
.v8 .stock{font-size:11.5px;display:flex;align-items:center;gap:4px}
.v8 .ups{display:flex;align-items:center;gap:8px;margin-top:8px;padding:7px 10px;border-radius:10px;background:#F6F9EC;border:1px dashed #D3E7A2;font-size:12.5px}
.v8 .ups .r{margin-left:auto;color:var(--b);font-weight:500}
.v8 .tot{display:flex;justify-content:flex-end;gap:18px;align-items:baseline;margin-top:8px;font-size:12.5px;color:var(--mut)}.v8 .tot b{font-size:17px;color:var(--ink);font-weight:600}
.v8 .pays{display:flex;gap:6px;flex-wrap:wrap}.v8 .pays span{height:30px;padding:0 10px;border:1px solid var(--line);border-radius:9px;display:flex;align-items:center;gap:6px;font-size:12.5px}
.v8 .pays span.on{border-color:var(--b);background:var(--b2);color:var(--b);font-weight:500}
.v8 .outbar{display:flex;gap:8px;align-items:center;padding:12px 20px;background:#fff;border-top:1px solid var(--line)}
.v8 .outbar .btn{height:40px}.v8 .outbar .grow{margin-left:auto}
.v8 .ctx{border-left:1px solid var(--line);background:#fff;padding:14px;display:flex;flex-direction:column;gap:12px;overflow:hidden}
.v8 .ctx h4{font-size:13px;font-weight:600;display:flex;align-items:center;gap:7px}.v8 .ctx h4 .r{margin-left:auto;font-weight:400;font-size:12px;color:var(--mut)}
.v8 .risk{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:8px}.v8 .risk div{background:var(--soft);border-radius:10px;padding:7px 8px}.v8 .risk small{display:block;font-size:11px;color:var(--mut)}.v8 .risk b{font-size:16px;font-weight:600}
.v8 .okbox{background:#E9F8EF;border-radius:10px;padding:8px 10px;font-size:12.5px;color:#14653A;display:flex;gap:7px;margin-top:8px}
.v8 .prev{display:flex;flex-direction:column;gap:6px;margin-top:8px}.v8 .prev div{display:flex;gap:8px;font-size:12.5px;align-items:flex-start}.v8 .prev .i{color:var(--b);margin-top:1px}
.v8 .prev small{display:block;color:var(--mut);font-size:11.5px}
.v8 .hist{display:flex;flex-direction:column;gap:5px;margin-top:8px}.v8 .hist div{display:flex;justify-content:space-between;font-size:12.5px}
.v8 .tip{background:#FFF8EA;border:1px solid #F7E2B6;border-radius:12px;padding:10px;font-size:12px;color:#7A4B00;display:flex;gap:7px}
/* ---------- відправка ---------- */
.v8 .ship{flex:1;display:grid;grid-template-columns:1fr 380px;gap:12px;min-height:0}
.v8 .bulk{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.v8 .prog{display:flex;align-items:center;gap:12px}.v8 .prog .bar{width:200px;height:8px;border-radius:99px;background:var(--soft);overflow:hidden;display:flex}.v8 .prog .bar i{height:100%}
.v8 table{width:100%;border-collapse:collapse}.v8 th{font-size:11.5px;font-weight:500;color:var(--mut);text-align:left;padding:8px;border-bottom:1px solid var(--line);white-space:nowrap}
.v8 td{padding:8px;border-bottom:1px solid var(--soft);font-size:13px;white-space:nowrap}.v8 tr.sel td{background:var(--b2)}
.v8 .rd{display:flex;gap:4px}.v8 .rd span{width:24px;height:24px;border-radius:7px;display:grid;place-items:center;background:var(--soft);color:#B4B7C9}
.v8 .rd span.y{background:#E7F7EE;color:var(--ok)}.v8 .rd span.n{background:#FFEDED;color:var(--bad)}.v8 .rd span.w{background:#FFF3E0;color:var(--warn)}
.v8 .cb{width:16px;height:16px;border-radius:5px;border:1.5px solid #C7CBEA;display:inline-grid;place-items:center;vertical-align:middle}.v8 .cb.on{background:var(--b);border-color:var(--b);color:#fff}
.v8 .ttn .kv{display:grid;grid-template-columns:118px 1fr;gap:7px 10px;font-size:12.5px;align-items:start;margin-top:10px}.v8 .ttn .kv span.k{color:var(--mut)}
.v8 .ttn .kv .from{margin-top:1px}
/* ---------- після відправки ---------- */
.v8 .k4{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.v8 .kp small{color:var(--mut);font-size:12px;display:flex;align-items:center;gap:6px}.v8 .kp b{display:block;font-size:28px;font-weight:600;letter-spacing:-.02em;margin-top:4px}
.v8 .kp .s{font-size:12px;color:var(--mut)}
.v8 .att{flex:1;display:grid;grid-template-columns:repeat(4,1fr) 330px;gap:10px;min-height:0}
.v8 .col{display:flex;flex-direction:column;gap:8px;min-height:0}
.v8 .col .ch{display:flex;align-items:center;gap:7px;font-weight:600;font-size:13.5px;padding:2px 2px 4px}.v8 .col .ch em{font-style:normal;font-size:11.5px;font-weight:500;border-radius:99px;padding:0 7px;background:var(--c2);color:var(--c)}
.v8 .col .ch small{display:block;font-weight:400;font-size:11.5px;color:var(--mut)}
.v8 .ex{background:#fff;border:1px solid var(--line);border-radius:13px;padding:10px;display:flex;flex-direction:column;gap:6px;font-size:12.5px}
.v8 .ex .t{display:flex;justify-content:space-between}.v8 .ex .t b{font-size:13px}.v8 .ex small{color:var(--mut);font-size:11.5px}
.v8 .ex .why{display:flex;align-items:center;gap:5px;font-size:12px}.v8 .ex .act{display:flex;gap:6px}.v8 .ex .act span{flex:1;height:28px;border-radius:8px;border:1px solid var(--line);display:flex;align-items:center;justify-content:center;gap:5px;font-size:12px;font-weight:500}
.v8 .ex .act span.p{background:var(--b);border-color:var(--b);color:#fff}
.v8 .life{display:flex;flex-direction:column;gap:0;margin-top:8px}.v8 .life div{display:grid;grid-template-columns:20px 1fr auto;gap:8px;font-size:12.5px;padding-bottom:10px;position:relative}
.v8 .life div:before{content:"";position:absolute;left:9px;top:18px;bottom:0;width:2px;background:var(--soft)}.v8 .life div:last-child:before{display:none}
.v8 .life i{width:20px;height:20px;border-radius:50%;display:grid;place-items:center;background:var(--b);color:#fff;font-style:normal}.v8 .life i.f{background:#fff;border:1.5px solid #C7CBEA;color:#A3A6C0}.v8 .life i.w{background:var(--warn)}
.v8 .life small{display:block;color:var(--mut);font-size:11.5px}.v8 .life time{color:var(--mut);font-size:11.5px}
.v8 .store{margin-top:4px;background:#FFF5E6;border-radius:12px;padding:10px;display:flex;flex-direction:column;gap:6px}.v8 .store .pb{height:6px;background:#FCE3BC;border-radius:99px}.v8 .store .pb i{display:block;height:100%;width:70%;background:var(--warn);border-radius:99px}
"""

Q = [("Дорошенко Ігор", "TikTok", "Павербанк 20000", "1 599", "щойно", "g", "1-ша спроба", "#12142B"),
     ("Коваленко Ірина", "Лендинг", "Набір кабелів USB-C", "649", "18 хв", "r", "2 спроби", "#2D3FE7"),
     ("Савчук Олена", "Instagram", "Лампа настільна LED", "899", "11 хв", "y", "повторний", "#E1306C"),
     ("Литвин Павло", "Rozetka", "Колонка Go Mini", "1 599", "7 хв", "y", "Rozetka · оплачено", "#16A34A"),
     ("Мороз Катерина", "Лендинг", "Чохол MagSafe ×2", "898", "5 хв", "g", "1-ша спроба", "#2D3FE7"),
     ("Бойко Сергій", "Instagram", "Зарядка GaN 65 Вт", "749", "о 18:00", "g", "просив передзвонити", "#E1306C"),
     ("Зінченко Аліна", "Facebook", "Павербанк 10000", "999", "2 хв", "g", "дубль? той самий тел.", "#1877F2")]


def rail(on):
    items = [("home", "house", None), ("leads", "inbox", "7"), ("orders", "receipt-text", None), ("ship", "truck", "14"), ("customers", "contact", None),
             ("products", "package", None), ("stats", "chart-column-stacked", None), ("settings", "settings", None)]
    r = "".join(f'<div class="r {"on" if k == on else ""}">{ic(i, 19)}{f"<em>{c}</em>" if c else ""}</div>' for k, i, c in items)
    return f'<aside class="rail"><span class="lg">{ic("check", 18, 2.6)}</span>{r}<span class="av">ОЛ</span></aside>'


def side(on):
    groups = [("Робота на сьогодні", [("leads", "Ліди · дзвінки", "inbox", '<em class="b">7</em>'), ("ship", "До відправки", "truck", "<em>14</em>"),
                                      ("watch", "Потребує уваги", "circle-alert", '<em class="w">9</em>')]),
              ("Продажі", [("home", "Головна", "house", ""), ("orders", "Усі замовлення", "receipt-text", "<em>248</em>"), ("customers", "Покупці", "contact", "")]),
              ("Склад і гроші", [("products", "Товари", "package", ""), ("warehouse", "Склад", "boxes", ""), ("payments", "Оплати", "wallet", ""),
                                 ("stats", "Статистика", "chart-column-stacked", "")]),
              ("", [("settings", "Налаштування", "settings", "")])]
    h = ""
    for g, its in groups:
        if g:
            h += f'<div class="lab">{g}</div>'
        h += "".join(f'<div class="it {"on" if k == on else ""}">{ic(i, 17)}{n}{c}</div>' for k, n, i, c in its)
    return f"""<aside class="side"><div class="brand"><span class="lg">{ic("check", 17, 2.6)}</span>mdmy</div>
<div class="ws"><span class="a">ІМ</span><span><small>Відділ</small><b>Інтернет-магазин</b></span>{ic("chevron-down", 15)}</div>{h}
<div style="margin-top:auto;display:flex;align-items:center;gap:9px;padding:6px"><span style="width:32px;height:32px;border-radius:50%;background:#FFD7B8;display:grid;place-items:center;font-size:11.5px;font-weight:600">ОЛ</span>
<span>Олена Литвин<small style="display:block;font-size:11.5px;color:var(--mut)">Менеджер · зміна до 19:00</small></span></div></aside>"""


# ---------------------------------------------------------------- 1. карта шляху
STAGES = [
    ("Заявка", "inbox", "сама CRM", ["нічого — дані приходять із лендингу, Instagram, Rozetka, Prom"],
     ["шукає покупця за телефоном", "позначає дубль і чорний список", "відділ — за джерелом", "запускає таймер очікування"],
     ["скільки хвилин чекає", "джерело й товар", "повторний / дубль"], False),
    ("Дзвінок", "phone", "менеджер", ["бере в роботу", "результат дзвінка одним кліком"],
     ["недодзвон → SMS і нагадування через 30 хв", "передзвонити → справа на час", "відмова → причина"],
     ["викуп і відмови покупця", "попередні замовлення", "номер спроби"], True),
    ("Уточнення", "list-checks", "менеджер, під час розмови", ["ПІБ одним рядком", "товар → варіант → кількість", "допродаж", "місто → відділення", "спосіб оплати → передоплата"],
     ["ціна й артикул — з варіанта", "вага й розміри — з товару", "сума при отриманні = разом − передоплата"],
     ["залишок саме цього варіанта", "що ще не заповнено"], True),
    ("Підтвердження", "circle-check-big", "менеджер", ["одна кнопка «Підтвердити»"],
     ["резерв на складі", "SMS «Підтверджено»", "статус у Rozetka / Prom"],
     ["що CRM зробить після кліку", "юрособа → каса й ключ НП"], False),
    ("Відправка", "truck", "склад / менеджер", ["перевірити, нічого не вводити"],
     ["ТТН із даних замовлення", "наклейка, накладна, реєстр", "чек на передоплату"],
     ["готовність кожного замовлення", "скільки лишилось до 17:00"], False),
    ("Доставка", "map-pin", "сама CRM", ["нічого — лише реагує на винятки"],
     ["статус із трекінгу НП", "«Прибуло» → SMS-нагадування", "не забирає 3 дні → справа"],
     ["термін зберігання", "посилки без руху"], False),
    ("Гроші", "wallet", "сама CRM", ["причину відмови, якщо повернення"],
     ["отримано → чек післяплати", "повернення → +склад, чек повернення", "викуп покупця оновлюється"],
     ["гроші, що не надійшли", "чеки, що не пробились"], False),
]
DEPS = [
    (["Телефон"], ["покупець", "історія й викуп", "чорний список", "дубль"]),
    (["Джерело"], ["відділ", "менеджери", "статистика"]),
    (["Товар", "Варіант"], ["ціна", "артикул", "залишок", "вага → ТТН"]),
    (["Місто"], ["відділення / поштомат", "ліміт ваги"]),
    (["Спосіб оплати"], ["передоплата", "сума при отриманні", "контроль оплати НП", "чек"]),
    (["Юрособа"], ["каса Checkbox", "ключ НП — відправник", "реквізити в документах"]),
    (["Статус"], ["резерв / списання", "SMS", "чек", "статус маркетплейсу"]),
    (["Трекінг НП"], ["статус замовлення", "нагадування", "гроші й чек"]),
]


def journey():
    st = ""
    for k, (t, icn, who, enter, auto, see, hot) in enumerate(STAGES, 1):
        li = lambda xs: "".join(f"<li>{x}</li>" for x in xs)
        st += f"""<div class="stg {"hot" if hot else ""}"><div class="n"><span>{k}</span><b>{t}</b><span style="margin-left:auto;background:none;color:var(--mut)">{ic(icn, 16)}</span></div>
<div class="wh">{ic("user", 12)}{who}</div><h5>Вводить людина</h5><ul>{li(enter)}</ul><h5>CRM робить сама</h5><ul class="auto">{li(auto)}</ul>
<h5>Має бути видно</h5><ul class="see">{li(see)}</ul></div>"""
    dp = ""
    for keys, outs in DEPS:
        a = '<span class="ar">→</span>'.join(f'<span class="chip k">{x}</span>' for x in keys)
        dp += f'<div class="dep">{a}<span class="ar">{ic("arrow-up-right", 13)}</span>{"".join(f"<span class=chip>{o}</span>" for o in outs)}</div>'
    body = f"""<div class="hd"><div><h1>Шлях замовлення очима менеджера</h1><div class="subt">Від заявки до грошей. Людина вводить лише те, чого CRM не може знати сама; решта підтягується з уже введеного.</div></div>
<div class="r legend"><span><i style="background:#C7CBEA"></i>вводить людина</span><span><i style="background:var(--b)"></i>CRM робить сама</span><span><i style="background:#F2B035"></i>має бути видно</span></div></div>
<div class="map">{st}</div>
<div class="card"><div style="display:flex;align-items:center;gap:8px;margin-bottom:10px"><b style="font-weight:600;font-size:14px">Що від чого залежить</b>
<span class="subt" style="font-size:12px">— тому поля в картці стоять саме в такому порядку, а залежні заповнюються самі</span></div><div class="deps">{dp}</div></div>"""
    return f'<div class="v8">{side("leads")}<main class="main">{body}</main></div>'


# ---------------------------------------------------------------- 2. режим дзвінка
def call():
    ql = ""
    for n, (nm, src, prod, s, tm, sla, note, c) in enumerate(Q):
        on = n == 0
        ql += f"""<div class="qi {"on" if on else ""}"><b>{nm}</b><span class="tm sla-{sla}">{ic("clock", 12)}{tm}</span><small>{prod}</small><small style="justify-self:end">{s} ₴</small>
<div class="row"><span class="chip" style="height:20px;font-size:11px"><i class="sw" style="--c:{c};width:7px;height:7px;border-radius:2px"></i>{src}</span><small>{note}</small></div></div>"""
    road = [("d", "Заявка"), ("c", "Дзвінок"), ("", "Підтверджено"), ("", "Відправлено"), ("", "У відділенні"), ("", "Отримано")]
    rd = ""
    for k, (cl, t) in enumerate(road):
        if k:
            rd += f'<em class="{"d" if cl in ("d", "c") else ""}"></em>'
        rd += f'<span class="{cl}"><i>{ic("check", 11, 3) if cl == "d" else ""}</i>{t}</span>'
    form = f"""
<div class="sec done"><div class="sh"><span class="num ok">{ic("check", 12, 3)}</span><b>Покупець</b><span class="hint">{ic("sparkles", 13)}ім'я й по батькові розпізнано з одного рядка</span></div>
<div class="grid" style="grid-template-columns:2fr 1.3fr 1fr"><div class="fld"><label>ПІБ — одним рядком</label><div class="inp">Дорошенко Ігор Петрович</div></div>
<div class="fld"><label>Телефон</label><div class="inp">+380 67 455 21 90{ic("copy", 14)}</div></div><div class="fld"><label>Джерело → відділ</label><div class="inp">TikTok → Інтернет-магазин</div></div></div></div>
<div class="sec now"><div class="sh"><span class="num now">2</span><b>Товари</b><span class="hint">ціна, артикул і залишок — з варіанта</span></div>
<div class="gi"><span class="im">{ic("zap", 18)}</span><span><b>Павербанк Volt 20 000 мА·год</b><small>PB-20-BLK · 0,42 кг</small></span>
<span class="vsel"><span class="on"><i class="sw" style="--c:#151515"></i>Чорний</span><span><i class="sw" style="--c:#F4F4F2"></i>Білий</span><span class="no"><i class="sw" style="--c:#2F5BEA"></i>Синій</span></span>
<span class="inp" style="height:30px;justify-content:center;gap:12px">−<b>1</b>+</span><span class="sum">1 599 ₴</span></div>
<div style="display:flex;gap:14px;align-items:center;margin-top:6px"><span class="stock sla-g">{ic("boxes", 13)}Чорний: 18 шт на складі, 3 в резерві</span><span class="stock" style="color:var(--mut)">Синій закінчився — прийде 4.11</span></div>
<div class="ups">{ic("sparkles", 15)}<span>З павербанком часто беруть <b>кабель USB-C 1 м</b> · 198 ₴ (42% замовлень)</span><span class="r">+ Додати</span></div>
<div class="tot"><span>Товарів: 1</span><span>Знижка: 0 ₴</span><span>Разом <b>1 599 ₴</b></span></div></div>
<div class="sec"><div class="sh"><span class="num">3</span><b>Доставка</b><span class="hint">відділення — лише в обраному місті</span></div>
<div class="grid" style="grid-template-columns:1fr 1fr 1.6fr 1fr"><div class="fld"><label>Служба</label><div class="inp">{ic("truck", 14)}Нова Пошта{ic("chevron-down", 14)}</div></div>
<div class="fld"><label>Місто</label><div class="inp"><span class="ph2">Почніть вводити…</span></div></div><div class="fld"><label>Відділення / поштомат</label><div class="inp"><span class="ph2">Спершу місто</span></div></div>
<div class="fld"><label>Отримувач</label><div class="inp">як покупець{ic("chevron-down", 14)}</div></div></div></div>
<div class="sec"><div class="sh"><span class="num">4</span><b>Оплата</b><span class="hint">від способу залежить сума при отриманні й чек</span></div>
<div class="pays"><span>{ic("banknote", 14)}Накладений платіж</span><span>{ic("shield-check", 14)}Контроль оплати НП</span><span>{ic("credit-card", 14)}Передоплата на карту</span><span>{ic("wallet", 14)}NovaPay</span></div></div>"""
    ctx = f"""<div><h4>{ic("contact", 15)}Покупець<span class="r">новий</span></h4><div class="risk"><div><small>Замовлень</small><b>0</b></div><div><small>Викуп</small><b>—</b></div><div><small>Відмов</small><b>0</b></div></div>
<div class="okbox">{ic("shield-check", 15)}Не в чорному списку · дублів за 30 днів немає</div></div>
<div><h4>{ic("zap", 15)}Після «Підтвердити» CRM сама</h4><div class="prev">
<div>{ic("boxes", 14)}<span>Зарезервує 1 шт · Чорний 20 000<small>на складі лишиться 17</small></span></div>
<div>{ic("message-square", 14)}<span>Надішле SMS «Підтвердження»<small>з номером замовлення і сумою</small></span></div>
<div>{ic("landmark", 14)}<span>Каса й відправник — ФОП Максимчук<small>юрособа за замовчуванням, можна змінити</small></span></div>
<div>{ic("truck", 14)}<span>Поставить у «До відправки» на сьогодні<small>відправка до 17:00</small></span></div></div></div>
<div><h4>{ic("clock", 15)}Скрипт дзвінка<span class="r">Павербанк</span></h4><div class="hist" style="font-size:12.5px;color:#3D4060">
<div>1. Привітатись, назвати магазин</div><div>2. Уточнити колір — чорний чи білий</div><div>3. Запропонувати кабель USB-C</div><div>4. Місто й відділення, спосіб оплати</div></div></div>
<div class="tip">{ic("circle-alert", 15)}<span>Ще не заповнено: місто, відділення, спосіб оплати. «Підтвердити» стане активною, коли все буде готово.</span></div>"""
    body = f"""<div class="call"><div class="q"><div class="qh"><div class="t"><b>Черга дзвінків</b><span class="chip">7</span></div>
<div class="seg"><span class="on">Усі 7</span><span>Нові 4</span><span>Пізніше 3</span></div><div class="subt" style="font-size:12px">Спершу ті, хто чекає найдовше. Червоний — понад 15 хв.</div></div><div class="ql">{ql}</div></div>
<div class="work"><div class="who"><div class="l1"><span class="ava">ДІ</span><div><h2>Дорошенко Ігор</h2><div class="ph">+380 67 455 21 90 <span class="st" style="--c:#16A34A"><i></i>Іде дзвінок · 01:24</span></div></div>
<div class="r"><span class="cbtn g">{ic("phone", 18)}</span><span class="cbtn">{ic("message-circle", 18)}</span><span class="cbtn">{ic("send", 18)}</span></div></div><div class="road">{rd}</div></div>
<div class="form">{form}</div>
<div class="outbar"><span class="btn">{ic("phone", 15)}Недодзвон <kbd>F1</kbd></span><span class="btn">{ic("clock", 15)}Передзвонити… <kbd>F2</kbd></span><span class="btn" style="color:var(--bad)">{ic("x", 15)}Відмова <kbd>F3</kbd></span>
<span class="btn grow">{ic("copy", 15)}Дубль</span><span class="btn l" style="opacity:.55">{ic("circle-check-big", 16)}Підтвердити <kbd>Ctrl ⏎</kbd></span></div></div>
<div class="ctx">{ctx}</div></div>"""
    return f'<div class="v8">{rail("leads")}{body}</div>'


# ---------------------------------------------------------------- 3. відправка
SHIP = [(1482, "Шевченко Тарас", "НП · Київ, №12", "Контроль оплати", "1 597", "yyyyn", False),
        (1484, "Дорошенко Ігор", "НП · Львів, поштомат 3112", "Накладений", "1 797", "ynnnn", True),
        (1472, "Гнатюк Роман", "НП · Київ, №201", "Передоплата", "0", "yyyyy", False),
        (1479, "Ткаченко Марія", "Укрпошта · Вінниця", "Накладений", "1 048", "ynnnn", False),
        (1474, "Поліщук Віктор", "НП · Харків, №52", "Rozetka · оплачено", "0", "yyyyy", False),
        (1469, "Петренко Сергій", "НП · Одеса, №31", "Контроль оплати", "2 199", "ynnnn", False),
        (1466, "Руденко Ганна", "Meest · Київ", "Накладений", "1 599", "ynnnn", False),
        (1462, "Захарченко Ольга", "НП · Тульчин, №1", "Передоплата", "0", "wnnnn", False),
        (1460, "Іваненко Петро", "НП · Дніпро, №7", "Контроль оплати", "999", "yyyyy", False)]
RD = [("boxes", "Резерв"), ("truck", "ТТН"), ("tag", "Наклейка"), ("receipt", "Чек"), ("list-checks", "Реєстр")]


def shipping():
    rows = ""
    for oid, nm, dl, pay, cod, rd, sel in SHIP:
        r = "".join(f'<span class="{ {"y": "y", "n": "", "w": "w"}[s] }" title="{t}">{ic(i, 13)}</span>' for (i, t), s in zip(RD, rd))
        if rd[0] == "w":
            r = r.replace('class="w"', 'class="n"', 1)
        rows += f"""<tr class="{"sel" if sel else ""}"><td><span class="cb {"on" if rd[:2] == "yn" else ""}">{ic("check", 10, 3) if rd[:2] == "yn" else ""}</span></td><td><b>№{oid}</b></td><td>{nm}</td><td>{dl}</td><td>{pay}</td>
<td style="text-align:right">{cod} ₴</td><td><span class="rd">{r}</span></td></tr>"""
    ttn = f"""<div class="card ttn" style="display:flex;flex-direction:column"><div style="display:flex;align-items:center;gap:8px"><b style="font-size:15px;font-weight:600">ТТН для №1484</b><span class="st" style="--c:#2D3FE7"><i></i>Чернетка</span>
<span style="margin-left:auto;color:var(--mut)">{ic("x", 16)}</span></div><div class="subt" style="font-size:12px;margin-top:2px">Усе заповнено з замовлення — перевірте й створіть</div>
<div class="kv"><span class="k">Відправник</span><span>ФОП Максимчук О. В.<div class="from">{ic("landmark", 11)}з юрособи замовлення</div></span>
<span class="k">Отримувач</span><span>Дорошенко Ігор · +380 67 455 21 90</span>
<span class="k">Куди</span><span>Львів, поштомат №3112<div class="from" style="color:var(--warn)">{ic("circle-alert", 11)}поштомат: до 20 кг, 40×30×60 см — вміщається</div></span>
<span class="k">Вага · розміри</span><span>0,55 кг · 18×10×4 см<div class="from">{ic("package", 11)}сума ваги товарів + пакування</div></span>
<span class="k">Оголошена вартість</span><span>1 797 ₴<div class="from">{ic("receipt-text", 11)}разом за замовленням</div></span>
<span class="k">Післяплата</span><span><b>1 797 ₴ · грошовий переказ</b><div class="from">{ic("banknote", 11)}спосіб оплати «Накладений платіж»</div></span>
<span class="k">Платник доставки</span><span>Отримувач<div class="from">{ic("key-round", 11)}типово для ключа НП «Тульчин»</div></span>
<span class="k">Опис</span><span>Павербанк, кабель<div class="from">{ic("package", 11)}з назв товарів</div></span></div>
<div style="margin-top:auto;display:flex;flex-direction:column;gap:8px"><div class="okbox" style="background:#EEF0FE;color:#2A36B8">{ic("zap", 15)}Після створення: статус «Відправлено», списання зі складу, SMS із ТТН, наклейка в чергу друку</div>
<div style="display:flex;gap:8px"><span class="btn" style="flex:1;justify-content:center">{ic("printer", 15)}Накладна</span><span class="btn l" style="flex:2;justify-content:center">{ic("truck", 16)}Створити ТТН <kbd>Ctrl ⏎</kbd></span></div></div></div>"""
    body = f"""<div class="hd"><div><h1>До відправки сьогодні</h1><div class="subt">Четвер, 29 жовтня · забір кур'єром о 17:00 · лишилось 2 год 40 хв</div></div>
<div class="r prog"><span class="subt"><b style="color:var(--ink)">5 з 14</b> повністю готові</span><span class="bar"><i style="width:36%;background:var(--ok)"></i><i style="width:28%;background:#9AA4F5"></i></span></div></div>
<div class="bulk"><span class="chip" style="height:30px;background:var(--b2);color:var(--b);font-weight:500">Вибрано 4</span><span class="btn b">{ic("truck", 15)}Створити 4 ТТН</span><span class="btn">{ic("tag", 15)}Друк наклейок</span>
<span class="btn">{ic("printer", 15)}Накладні</span><span class="btn">{ic("list-checks", 15)}Реєстр НП</span><span class="btn">{ic("receipt", 15)}Пробити чеки</span>
<span style="margin-left:auto" class="subt">Готовність:</span>{"".join(f'<span class="chip">{ic(i, 13)}{t}</span>' for i, t in RD)}</div>
<div class="ship"><div class="card" style="padding:4px 8px;overflow:hidden"><table><tr><th></th><th>№</th><th>Покупець</th><th>Доставка</th><th>Оплата</th><th style="text-align:right">При отриманні</th><th>Готовність</th></tr>{rows}</table>
<div class="tip" style="margin:10px 6px"><span>{ic("circle-alert", 15)}</span><span>№1462: товар не зарезервовано — на складі 0 шт білого павербанка 20 000. Замініть варіант або перенесіть відправку.</span></div></div>{ttn}</div>"""
    return f'<div class="v8">{rail("ship")}<main class="main">{body}</main></div>'


# ---------------------------------------------------------------- 4. потребує уваги
EXC = [("Не забирають", "#D97706", "#FFF1E0", "у відділенні 3+ дні", [
           ("№1476 Мельник Денис", "НП Тульчин, №1 · 4-й день", "зберігання до 02.11", "phone", "Подзвонити"),
           ("№1458 Кузьменко Віра", "НП Київ, №88 · 3-й день", "SMS-нагадування вже було", "phone", "Подзвонити"),
           ("№1451 Остапчук Ліна", "Укрпошта Житомир · 5-й день", "повернеться 01.11", "phone", "Подзвонити")]),
       ("Повертаються", "#DC2626", "#FFEDED", "відмова, посилка в дорозі назад", [
           ("№1477 Олійник Світлана", "НП Дніпро → Тульчин", "причина не вказана", "pencil", "Вказати причину"),
           ("№1449 Лук'яненко Ден", "НП Львів → Тульчин", "прибуде 31.10", "boxes", "Чекаю на склад")]),
       ("Гроші не надійшли", "#2D3FE7", "#EEF0FE", "отримано, а переказу немає", [
           ("№1441 Сидоренко Ольга", "отримано 26.10 · 1 299 ₴", "контроль оплати НП", "refresh-cw", "Перевірити")]),
       ("Без руху", "#64748B", "#EEF0F4", "ТТН не змінюється 2+ дні", [
           ("№1470 Федоренко Іван", "створена 27.10 · не передана", "кур'єр не забрав?", "truck", "У реєстр"),
           ("№1468 Гончар Оксана", "у дорозі 3 дні", "Укрпошта", "eye", "Відстежити")])]


def attention():
    cols = ""
    for t, c, c2, sub, items in EXC:
        ex = "".join(f"""<div class="ex"><div class="t"><b>{a}</b></div><small>{b}</small><div class="why" style="color:{c}">{ic("circle-alert", 13)}{w}</div>
<div class="act"><span class="p">{ic(i, 13)}{btn}</span><span style="flex:none;width:30px">{ic("ellipsis", 14)}</span></div></div>""" for a, b, w, i, btn in items)
        cols += f'<div class="col" style="--c:{c};--c2:{c2}"><div class="ch"><span>{t}<small>{sub}</small></span><em style="margin-left:auto">{len(items)}</em></div>{ex}</div>'
    life = [("Заявка з Instagram", "TikTok-реклама «Fit 3»", "26.10 11:30", ""), ("Підтверджено · Андрій", "резерв, SMS", "26.10 11:41", ""),
            ("ТТН 20451128843021", "наклейка, реєстр №34", "26.10 16:10", ""), ("Прибуло у відділення", "SMS-нагадування надіслано", "28.10 09:02", "w"),
            ("Отримано", "чек післяплати пробиється сам", "", "f"), ("Гроші на рахунку", "контроль оплати НП", "", "f")]
    lf = "".join(f'<div><i class="{k}">{ic("check", 11, 3) if k == "" else ""}</i><span>{a}<small>{b}</small></span><time>{d}</time></div>' for a, b, d, k in life)
    body = f"""<div class="hd"><div><h1>Потребує уваги</h1><div class="subt">Після відправки CRM веде замовлення сама. Тут лише ті, де треба втрутитись людині.</div></div>
<div class="r"><span class="btn">{ic("funnel", 15)}Мої</span><span class="btn">{ic("refresh-cw", 15)}Оновлено 2 хв тому</span></div></div>
<div class="k4"><div class="card kp"><small>{ic("truck", 14)}В дорозі</small><b>57</b><span class="s">48 300 ₴ післяплати</span></div>
<div class="card kp"><small>{ic("map-pin", 14)}У відділенні</small><b>22</b><span class="s">з них 3 — понад 3 дні</span></div>
<div class="card kp"><small>{ic("circle-check-big", 14)}Отримано за тиждень</small><b>96</b><span class="s"><span class="sla-g">викуп 81%</span> · 128 400 ₴</span></div>
<div class="card kp"><small>{ic("undo-2", 14)}Повернення за тиждень</small><b>9</b><span class="s"><span class="sla-r">−3 297 ₴</span> на доставці</span></div></div>
<div class="att">{cols}<div class="card" style="display:flex;flex-direction:column"><div style="display:flex;align-items:center;gap:8px"><b style="font-size:15px;font-weight:600">№1476 · Мельник Денис</b>
<span class="st" style="--c:#F97316;margin-left:auto"><i></i>У відділенні</span></div><div class="subt" style="font-size:12px">Смарт-годинник Fit 3 · 2 398 ₴ при отриманні</div>
<div class="store"><div style="display:flex;justify-content:space-between;font-size:12.5px"><b>Зберігання до 02.11</b><span style="color:var(--warn)">лишилось 2 дні</span></div><div class="pb"><i></i></div>
<div style="font-size:12px;color:#7A4B00">Після цього посилка поїде назад — доставка в обидва боки за наш рахунок.</div></div>
<div class="life">{lf}</div><div style="margin-top:auto;display:flex;gap:8px"><span class="btn" style="flex:1;justify-content:center">{ic("message-circle", 15)}Viber</span>
<span class="btn b" style="flex:2;justify-content:center">{ic("phone", 15)}Подзвонити</span></div></div></div>"""
    return f'<div class="v8">{side("watch")}<main class="main">{body}</main></div>'


def build():
    return page("Варіант 8 — Робоче місце менеджера", CSS, [
        ("1-journey", "Шлях замовлення: хто що вводить, що CRM робить сама, що має бути видно", journey(), None, None),
        ("2-call", "Режим дзвінка: черга зліва, картка в порядку розмови, результат дзвінка внизу", call(), None, None),
        ("3-ship", "До відправки: готовність кожного замовлення, ТТН заповнена з даних", shipping(), None, None),
        ("4-watch", "Після відправки: лише винятки, де треба втрутитись", attention(), None, None)])
