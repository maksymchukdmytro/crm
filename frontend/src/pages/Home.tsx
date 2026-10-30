// Головна (UI-DESIGN §10, макет 04-holovna): 4 плитки (сьогодні, період, покупці, нові покупці), смуга «Потребує уваги»,
// продажі по днях з пунктиром попереднього періоду, якість продажів (кільця з дельтою в пунктах), топ товарів і команда сьогодні.
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  AlarmClock, Boxes, CalendarDays, ChevronRight, CircleDot, HandCoins, Inbox, MapPin, PackageCheck, Truck, UserRound, Users, type LucideIcon,
} from "lucide-react";
import { api, qs } from "../lib/api";
import { useMeta } from "../lib/app";
import { isoDay, money } from "../lib/format";
import type { Dashboard } from "../lib/types";
import { MenuButton, Segmented, Spinner } from "../components/ui";
import "./home.css";

const WEEK = ["неділя", "понеділок", "вівторок", "середа", "четвер", "пʼятниця", "субота"];
const MONTHS = ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"];
const MONTHS_NOM = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"];

const ym = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
const dm = (iso: string) => `${Number(iso.slice(8, 10))}.${iso.slice(5, 7)}`;
const pl = (n: number, one: string, few: string, many: string) => {
  const a = n % 10, b = n % 100;
  return a === 1 && b !== 11 ? one : a >= 2 && a <= 4 && (b < 12 || b > 14) ? few : many;
};

function Delta({ v, unit = "%", hint }: { v: number | null | undefined; unit?: string; hint?: string }) {
  if (v == null) return null;
  return <span className={`hd-delta ${v >= 0 ? "up" : "down"}`} title={hint}>{v >= 0 ? "+" : "−"}{Math.abs(v)}{unit === "%" ? "%" : ` ${unit}`}</span>;
}

export default function HomePage() {
  const meta = useMeta();
  const nav = useNavigate();
  const now = new Date();
  const cur = ym(now);
  const prevM = ym(new Date(now.getFullYear(), now.getMonth() - 1, 1));
  const [period, setPeriod] = useState(cur);
  const [custom, setCustom] = useState({ from: isoDay(new Date(now.getFullYear(), now.getMonth(), 1)), to: isoDay(now) });
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", period], queryFn: () => api.get<Dashboard>(`/dashboard${qs({ period })}`), refetchInterval: 60_000, placeholderData: (p) => p,
  });
  const st = (code: string) => meta.statuses.find((s) => s.code === code)?.id;
  const title = `${WEEK[now.getDay()]}, ${now.getDate()} ${MONTHS[now.getMonth()]}`.replace(/^./, (c) => c.toUpperCase());

  if (isLoading || !data) return <div className="empty big"><Spinner /></div>;
  const { today, month, customers: c, attention: a, quality: q, period: p } = data;
  const isMonth = /^\d{4}-\d{2}$/.test(period);
  const periodName = isMonth ? MONTHS_NOM[Number(period.slice(5, 7)) - 1] : `${dm(p.date_from)} – ${dm(p.date_to)}`;
  const prevName = `${dm(p.prev_from)} – ${dm(p.prev_to)}`;
  const avgToday = today.orders ? today.sum / today.orders : 0;
  const leadsOn = meta.leads_enabled !== false && meta.nav.includes("leads");

  const attention: { icon: LucideIcon; n: string | number; label: string; tone: "" | "hot" | "warn"; go?: () => void }[] = [
    ...(leadsOn ? [{ icon: Inbox, n: a.leads_new, label: pl(a.leads_new, "новий лід", "нові ліди", "нових лідів"), tone: "hot" as const,
      go: () => nav(st("new") ? `/leads?tab=new` : "/leads") }] : []),
    ...(a.orders_unsorted || !leadsOn ? [{ icon: CircleDot, n: a.orders_unsorted, label: "несортованих", tone: "hot" as const,
      go: () => nav(st("unsorted") ? `/orders?status=${st("unsorted")}` : "/orders") }] : []),
    { icon: PackageCheck, n: a.to_ship, label: "чекають відправки", tone: "warn", go: () => nav(st("confirmed") ? `/orders?status=${st("confirmed")}` : "/orders") },
    { icon: MapPin, n: a.arrived, label: "чекають на пошті", tone: "warn", go: () => nav(st("arrived") ? `/orders?status=${st("arrived")}` : "/orders") },
    { icon: AlarmClock, n: a.reminders, label: "нагадування зараз", tone: "hot", go: () => nav("/orders") },
    { icon: Truck, n: a.on_way, label: "у дорозі", tone: "", go: () => nav(st("shipped") ? `/orders?status=${st("shipped")}` : "/orders") },
    { icon: HandCoins, n: `${money(a.cod_expected)} ₴`, label: "очікуємо післяплату", tone: "", go: meta.nav.includes("payments") ? () => nav("/payments") : undefined },
    { icon: Boxes, n: a.low_stock, label: "товарів закінчуються", tone: "hot", go: meta.nav.includes("warehouse") ? () => nav("/warehouse") : undefined },
  ];

  return (
    <div className="home2">
      <div className="hd-head">
        <h1>Головна</h1><span className="hd-sub">{title}</span>
        <div className="hd-acts">
          <Segmented label="Період" value={isMonth && (period === cur || period === prevM) ? period : "custom"}
            onChange={(k) => { if (k !== "custom") setPeriod(k); }}
            items={[{ key: cur, label: MONTHS_NOM[now.getMonth()] }, { key: prevM, label: MONTHS_NOM[(now.getMonth() + 11) % 12] },
              { key: "custom", label: isMonth && (period === cur || period === prevM) ? "Свій період" : periodName }]} />
          <MenuButton button={({ open, toggle }) => <button className="icon-btn" aria-label="Обрати свій період" aria-expanded={open} onClick={toggle}><CalendarDays size={16} /></button>}>
            {(close) => (
              <form className="hd-range" onSubmit={(e) => { e.preventDefault(); setPeriod(`${custom.from}..${custom.to}`); close(); }}>
                <label>З<input type="date" value={custom.from} max={custom.to} onChange={(e) => setCustom({ ...custom, from: e.target.value })} /></label>
                <label>По<input type="date" value={custom.to} min={custom.from} max={isoDay(now)} onChange={(e) => setCustom({ ...custom, to: e.target.value })} /></label>
                <button className="btn primary sm">Показати</button>
              </form>
            )}
          </MenuButton>
        </div>
      </div>

      <div className="hd-tiles">
        <button type="button" className="hd-tile" onClick={() => nav(`/orders?date_from=${today.date}&date_to=${today.date}`)}>
          <small><CircleDot size={14} />Сьогодні</small>
          <span className="hd-big">{money(today.sum)} ₴<Delta v={today.sum_delta} hint="До вчора" /></span>
          <span className="hd-row"><span>{today.orders} {pl(today.orders, "замовлення", "замовлення", "замовлень")} · сер. чек</span><b>{money(avgToday)} ₴</b></span>
          <span className="hd-row"><span>Учора</span><b>{money(today.yesterday_sum)} ₴</b></span>
        </button>
        <button type="button" className="hd-tile" onClick={() => nav("/stats")}>
          <small><CalendarDays size={14} />{periodName}</small>
          <span className="hd-big">{money(month.sum)} ₴<Delta v={month.sum_delta} hint={`До ${prevName}`} /></span>
          <span className="hd-row"><span>{month.orders} {pl(month.orders, "замовлення", "замовлення", "замовлень")} · сер. чек</span><b>{money(month.avg_check)} ₴</b></span>
          <span className="hd-row"><span>{prevName}</span><b>{money(month.prev_sum)} ₴</b></span>
        </button>
        <button type="button" className="hd-tile" onClick={() => nav("/customers")}>
          <small><Users size={14} />Покупці</small>
          <span className="hd-big">{money(c.total)}</span>
          <span className="hd-row"><span>Повторні</span><b>{c.repeat_share}%</b></span>
          <span className="hd-row"><span>У чорному списку</span><b>{c.blacklisted}</b></span>
        </button>
        <button type="button" className="hd-tile" onClick={() => nav("/customers")}>
          <small><UserRound size={14} />Нові покупці</small>
          <span className="hd-big">+{c.new}<Delta v={c.new_delta} hint={`До ${prevName}`} /></span>
          <span className="hd-row"><span>сьогодні</span><b>+{c.new_today}</b></span>
          <span className="hd-row"><span>{prevName}</span><b>+{c.new_prev}</b></span>
        </button>
      </div>

      <div>
        <div className="hd-cap">Потребує уваги — клік відкриває відфільтрований список</div>
        <div className="hd-attn" style={{ gridTemplateColumns: `repeat(${attention.length}, minmax(0, 1fr))` }}>
          {attention.map((x) => {
            const zero = x.n === 0 || x.n === "0 ₴";
            return (
              <button key={x.label} type="button" className={`${zero ? "zero" : x.tone}`} onClick={x.go} disabled={!x.go}>
                <span className="ic"><x.icon size={16} />{x.go && <ChevronRight size={14} />}</span>
                <b>{x.n}</b><small>{x.label}</small>
              </button>
            );
          })}
        </div>
      </div>

      <div className="hd-mid">
        <section className="hd-card">
          <h2>Продажі · {periodName.toLowerCase()}<small>сума по днях · пунктир — {prevName} · без скасованих і дублів</small></h2>
          <DayChart days={data.days} prev={data.prev_days ?? []} />
        </section>
        <section className="hd-card">
          <h2>Якість продажів<small>{periodName.toLowerCase()}</small></h2>
          <Ring label="Апрув" v={q.approve_rate} d={q.approve_delta} color="var(--accent)" hint="Частка підтверджених замовлень" />
          <Ring label="Викуп" v={q.buyout_rate} d={q.buyout_delta} color="var(--ok)" hint="Отримані серед отриманих і відмов" />
          <Ring label="Допродаж" v={q.upsell_rate} d={q.upsell_delta} color="#7C3AED" hint="Замовлення з допродажем" />
          <p className="hd-note">Зміна — до {prevName}, у пунктах</p>
        </section>
      </div>

      <div className={`hd-bottom${(data.team ?? []).length ? "" : " one"}`}>
        <section className="hd-card flush">
          <h2>Топ товарів · {periodName.toLowerCase()}<button type="button" className="link-btn" onClick={() => nav("/stats")}>Статистика<ChevronRight size={14} /></button></h2>
          {data.top.length === 0 ? <p className="hint pad">Продажів за цей період ще немає.</p> : (
            <div className="hd-tbl">
              <div className="hd-tr h"><span>Товар</span><span /><span className="r">Шт</span><span className="r">Сума, ₴</span></div>
              {data.top.map((t, i) => (
                <div key={`${t.product_id}-${i}`} className="hd-tr"><span className="ell">{t.name}</span>
                  <span className="hd-bar"><i style={{ width: `${(t.qty / Math.max(1, data.top[0].qty)) * 100}%` }} /></span>
                  <span className="r num">{t.qty}</span><b className="r num">{money(t.sum)}</b></div>
              ))}
            </div>
          )}
        </section>
        {(data.team ?? []).length > 0 && (
          <section className="hd-card flush">
            <h2>Команда сьогодні<small>видно адміністратору</small></h2>
            <div className="hd-tbl team">
              <div className="hd-tr h"><span>Менеджер</span><span className="r">Лідів</span><span className="r">Замовлень</span><span className="r">Апрув</span><span className="r">Сума, ₴</span></div>
              {(data.team ?? []).map((u) => (
                <div key={u.id} className="hd-tr"><span className="ell hd-mgr"><span className="o-av">{u.name.split(/\s+/).map((x) => x[0]).slice(0, 2).join("").toUpperCase()}</span>{u.name}</span>
                  <span className="r num">{u.leads}</span><span className="r num">{u.confirmed}</span>
                  <span className="r num">{u.approve_rate == null ? "—" : `${u.approve_rate}%`}</span><b className="r num">{money(u.sum)}</b></div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

function Ring({ label, v, d, color, hint }: { label: string; v: number; d: number | null | undefined; color: string; hint: string }) {
  const r = 16, L = 2 * Math.PI * r;
  return (
    <div className="hd-ring" title={hint}>
      <svg width="42" height="42" viewBox="0 0 42 42" aria-hidden>
        <circle cx="21" cy="21" r={r} fill="none" stroke="var(--line-2)" strokeWidth="5" />
        <circle cx="21" cy="21" r={r} fill="none" stroke={color} strokeWidth="5" strokeLinecap="round"
          strokeDasharray={`${(L * Math.min(100, Math.max(0, v))) / 100} ${L}`} transform="rotate(-90 21 21)" />
      </svg>
      <span className="l">{label}</span><b>{v}%</b><Delta v={d} unit="п." />
    </div>
  );
}

// Сума по днях стовпцями; попередній період — пунктиром день у день; підказка при наведенні.
function DayChart({ days, prev }: { days: Dashboard["days"]; prev: Dashboard["days"] }) {
  const [hover, setHover] = useState<number | null>(null);
  const W = 720, H = 190, L = 44, R = 8, T = 10, B = 22;
  const max = Math.max(1, ...days.map((d) => d.sum), ...prev.map((d) => d.sum));
  const step = useMemo(() => { const raw = max / 3; const p = Math.pow(10, Math.floor(Math.log10(raw))); return [1, 2, 2.5, 5, 10].map((m) => m * p).find((s) => s >= raw) ?? raw; }, [max]);
  const top = step * 3;
  const n = Math.max(days.length, 1);
  const bw = (W - L - R) / n;
  const y = (v: number) => T + (H - T - B) * (1 - v / top);
  const every = n > 20 ? 5 : n > 10 ? 2 : 1;
  const short = (v: number) => (v >= 1000 ? `${Math.round(v / 100) / 10}к` : String(v));
  const line = prev.slice(0, n).map((d, i) => `${L + bw * i + bw / 2},${y(d.sum)}`).join(" ");
  const hd = hover != null ? days[hover] : null;
  const hp = hover != null ? prev[hover] : null;
  return (
    <div className="hd-chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Сума замовлень по днях" onMouseLeave={() => setHover(null)}>
        {[0, 1, 2, 3].map((k) => <g key={k}><line x1={L} x2={W - R} y1={y(step * k)} y2={y(step * k)} className="grid" />
          <text x={L - 6} y={y(step * k) + 4} textAnchor="end" className="ax">{short(step * k)}</text></g>)}
        {days.map((d, i) => {
          const x = L + bw * i, w = Math.max(3, bw - 4), h = H - B - y(d.sum);
          const last = i === days.length - 1;
          return (
            <g key={d.day} onMouseEnter={() => setHover(i)}>
              <rect x={x} y={T} width={bw} height={H - T - B} fill="transparent" />
              {d.sum > 0 && <rect className={`bar${last || hover === i ? " on" : ""}`} x={x + 2} y={y(d.sum)} width={w} height={h} rx={Math.min(3, w / 2)} />}
              {(i % every === 0 || last) && <text x={x + bw / 2} y={H - 6} textAnchor="middle" className="ax">{Number(d.day.slice(8))}</text>}
            </g>
          );
        })}
        {prev.length > 1 && <polyline points={line} className="prev" />}
      </svg>
      {hd && (
        <div className="hd-tip" style={{ left: `${((L + bw * (hover ?? 0) + bw / 2) / W) * 100}%` }}>
          <b>{Number(hd.day.slice(8))} {MONTHS[Number(hd.day.slice(5, 7)) - 1]} · {money(hd.sum)} ₴</b>
          <span>{hd.orders} {pl(hd.orders, "замовлення", "замовлення", "замовлень")}{hp ? ` · раніше ${money(hp.sum)} ₴` : ""}</span>
        </div>
      )}
    </div>
  );
}
