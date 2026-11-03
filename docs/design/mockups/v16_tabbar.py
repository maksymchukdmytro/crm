"""Мобільна v2: 3 варіанти нижньої панелі замість чорної — на тому самому екрані «Ліди»."""
from common import *

CSS = """
.ph{width:390px;height:844px;background:#F1F2F4;font:400 14px/1.4 'Onest',sans-serif;color:#1F1F1C;position:relative;overflow:hidden;border-radius:28px}
.ph .top{display:flex;align-items:center;gap:10px;padding:26px 20px 10px}.ph h1{font-size:30px;font-weight:600;letter-spacing:-.02em;margin-right:auto}
.rb{width:46px;height:46px;border-radius:50%;background:#fff;display:grid;place-items:center;color:#1F1F1C;box-shadow:0 1px 2px rgba(0,0,0,.05)}
.tabs{display:flex;gap:8px;padding:6px 20px 14px;white-space:nowrap;overflow:hidden}
.tabs span{height:38px;padding:0 15px;border-radius:99px;display:inline-flex;align-items:center;gap:7px;font-weight:500;font-size:15px;background:color-mix(in srgb,var(--c) 12%,white);color:color-mix(in srgb,var(--c) 75%,black)}
.tabs span.on{background:#1F1F1C;color:#fff}.tabs em{font-style:normal;opacity:.7}
.cta{margin:0 20px 12px;background:linear-gradient(135deg,#2E6BE6,#2457C5);border-radius:22px;color:#fff;padding:18px 20px;display:flex;align-items:center}
.cta b{font-size:30px;font-weight:600;display:block;line-height:1}.cta small{opacity:.85;font-size:13px}.cta .go{margin-left:auto;background:#fff;color:#2E6BE6;border-radius:99px;height:46px;padding:0 18px;display:flex;align-items:center;gap:8px;font-weight:600}
.card{margin:0 20px 10px;background:#fff;border-radius:20px;padding:14px 14px 14px 12px;display:flex;align-items:center;gap:12px}
.ring{width:54px;height:54px;flex:none;position:relative;display:grid;place-items:center;text-align:center;font-size:13px;font-weight:600;line-height:1.05}
.ring svg{position:absolute;inset:0}.ring small{display:block;font-size:10px;font-weight:500}
.card .t{flex:1;min-width:0}.card .st{display:inline-flex;align-items:center;gap:5px;height:24px;padding:0 9px;border-radius:99px;font-size:12.5px;font-weight:500;background:#EAF1FD;color:#2457C5}
.card .nm{font-size:17px;font-weight:600;margin:3px 0 1px}.card .sub{font-size:13px;color:#6F6E69}
.call{width:52px;height:52px;border-radius:16px;background:#EAF1FD;color:#2E6BE6;display:grid;place-items:center;flex:none}.call.p{background:#2E6BE6;color:#fff}
.note{position:absolute;left:20px;right:20px;top:600px;background:#fff;border:1px dashed #C9DBFA;border-radius:16px;padding:12px 14px;font-size:13px;color:#4A4945}
.note b{color:#1F1F1C}
/* ---- панелі ---- */
.bar{position:absolute;left:14px;right:14px;bottom:18px;height:72px;border-radius:26px;display:grid;grid-template-columns:repeat(5,1fr);align-items:center}
.bar a{position:relative;display:flex;flex-direction:column;align-items:center;gap:4px;font-size:11.5px;font-weight:500}
.bar a i{position:absolute;top:-6px;left:calc(50% + 4px);min-width:18px;height:18px;border-radius:99px;font:600 10.5px/18px 'Onest';text-align:center;padding:0 5px;font-style:normal}
.plus{justify-self:center;width:58px;height:58px;border-radius:20px;display:grid;place-items:center}
/* 1: білий острівець з матовим склом */
.b1{background:rgba(255,255,255,.86);backdrop-filter:blur(14px);box-shadow:0 12px 30px -10px rgba(31,31,28,.25),0 0 0 1px rgba(31,31,28,.06)}
.b1 a{color:#8A8984}.b1 a.on{color:#2E6BE6}.b1 a.on .ico{background:#EAF1FD}.b1 .ico{width:44px;height:30px;border-radius:99px;display:grid;place-items:center}
.b1 a i{background:#2E6BE6;color:#fff;box-shadow:0 0 0 2px #fff}.b1 .plus{background:#2E6BE6;color:#fff;box-shadow:0 8px 18px -6px rgba(46,107,230,.7)}
/* 2: синій острівець */
.b2{background:#2E6BE6;box-shadow:0 14px 30px -10px rgba(46,107,230,.6)}
.b2 a{color:rgba(255,255,255,.72)}.b2 a.on{color:#fff}.b2 a.on .ico{background:rgba(255,255,255,.18)}.b2 .ico{width:44px;height:30px;border-radius:99px;display:grid;place-items:center}
.b2 a i{background:#fff;color:#2E6BE6;box-shadow:0 0 0 2px #2E6BE6}.b2 .plus{background:#fff;color:#2E6BE6;box-shadow:0 8px 18px -8px rgba(0,0,0,.35)}
/* 3: світло-синій острівець, активна вкладка — біла пігулка з підписом */
.b3{background:#E3ECFC;box-shadow:0 10px 26px -12px rgba(46,107,230,.45),0 0 0 1px #C9DBFA;display:flex;padding:0 10px;gap:4px}.b3 a,.b3 .plus{flex:1}.b3 a.on{flex:1.7}.b3 .plus{flex:none;margin:0 4px}
.b3 a{color:#4F6FA8}.b3 a span{display:none}.b3 a.on{flex-direction:row;gap:7px;background:#fff;color:#1F4FB8;height:48px;border-radius:18px;justify-content:center;font-size:13px;box-shadow:0 2px 6px -2px rgba(46,107,230,.35)}
.b3 a.on span{display:inline}.b3 a i{background:#2E6BE6;color:#fff;box-shadow:0 0 0 2px #E3ECFC}.b3 a.on i{top:2px;left:auto;right:6px}
.b3 .plus{background:#2E6BE6;color:#fff;width:54px;height:54px;border-radius:18px;box-shadow:0 8px 16px -6px rgba(46,107,230,.7)}
"""


def ring(v, unit, frac, color):
    r, L = 23, 2 * 3.14159 * 23
    return f'''<span class="ring" style="color:{color}"><svg width="54" height="54" viewBox="0 0 54 54"><circle cx="27" cy="27" r="{r}" fill="none" stroke="#EEEEEA" stroke-width="4"/>
<circle cx="27" cy="27" r="{r}" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-dasharray="{L*frac:.1f} {L:.1f}" transform="rotate(-90 27 27)"/></svg>{v}<small>{unit}</small></span>'''


def screen(bar):
    leads = [("1", "дн", 1, "#DC2626", "Новий", "Петренко Іван", "Кавоварка Delonghi · 2 299 ₴", True),
             ("6", "год", .9, "#DC2626", "Новий", "Коваленко Олена", "Кавоварка Delonghi · 2 499 ₴", False),
             ("54", "хв", .6, "#D97706", "Недодзвон", "Дмитро Савчук", "Екшн-камера 4К · 5 499 ₴", False),
             ("3", "хв", .2, "#16A34A", "Новий", "Оксана Кравець", "Штатив-монопод · 2 797 ₴", False)]
    cards = "".join(f'''<div class="card">{ring(v,u,f,c)}<div class="t"><span class="st" style="{'background:#FDF1E3;color:#B45309' if s=='Недодзвон' else ''}">● {s}</span>
<div class="nm">{n}</div><div class="sub">{g}</div></div><span class="call {'p' if p else ''}">{ic('phone',20)}</span></div>''' for v,u,f,c,s,n,g,p in leads)
    return f'''<div class="ph"><div class="top"><h1>Ліди</h1><span class="rb">{ic('search',20)}</span><span class="rb">{ic('list-filter',20)}</span></div>
<div class="tabs"><span class="on">Відкриті <em>6</em></span><span style="--c:#2E6BE6">Нові <em>4</em></span><span style="--c:#D97706">Недодзвон <em>2</em></span><span style="--c:#7C3AED">Передзвонити</span></div>
<div class="cta"><div><b>6</b><small>чекають дзвінка<br>найдовше — 1 день</small></div><span class="go">{ic('phone',18)}Дзвонити</span></div>{cards}{bar}</div>'''


def bar(cls):
    def item(icon, label, on=False, n=None):
        return f'<a class="{"on" if on else ""}"><span class="ico">{ic(icon, 22)}</span><span>{label}</span>{f"<i>{n}</i>" if n else ""}</a>'
    if cls == "b3":
        def item(icon, label, on=False, n=None):  # noqa: F811
            return f'<a class="{"on" if on else ""}">{ic(icon, 22)}<span>{label}</span>{f"<i>{n}</i>" if n else ""}</a>'
        return f'<nav class="bar b3">{item("house", "Головна")}{item("receipt-text", "Замовлення", False, 16)}<span class="plus">{ic("plus", 26, 2.4)}</span>{item("inbox", "Ліди", True, 4)}<a>{ic("ellipsis", 22)}</a></nav>'
    return f'<nav class="bar {cls}">{item("house", "Головна")}{item("receipt-text", "Замовлення", False, 16)}<span class="plus">{ic("plus", 28, 2.4)}</span>{item("inbox", "Ліди", True, 4)}{item("ellipsis", "Ще")}</nav>'


def build():
    return page("Нижня панель — 3 варіанти", CSS, [
        ("1-white", "1 · Білий острівець (матове скло)", screen(bar("b1")), 390, 844),
        ("2-blue", "2 · Синій острівець", screen(bar("b2")), 390, 844),
        ("3-soft", "3 · Світло-синій, активна — біла пігулка з підписом", screen(bar("b3")), 390, 844)], cols=3, gap=40)
