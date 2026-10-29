// Головна: що відбувається сьогодні й за місяць, і що потребує уваги просто зараз.
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  AlarmClock, ArrowDownRight, ArrowUpRight, Boxes, CalendarDays, CircleDollarSign, House, Inbox, MapPin, PackageCheck,
  ShoppingBag, Truck, UserPlus, Users, type LucideIcon,
} from "lucide-react";
import { api } from "../lib/api";
import { useMeta } from "../lib/app";
import { money } from "../lib/format";
import type { Dashboard } from "../lib/types";
import { Spinner } from "../components/ui";
import "./home.css";

const WEEK = ["неділя", "понеділок", "вівторок", "середа", "четвер", "пʼятниця", "субота"];
const MONTHS = ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"];
const MONTHS_NOM = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"];

function Delta({ v, hint }: { v: number | null | undefined; hint: string }) {
  if (v == null) return null;
  const up = v >= 0;
  const Icon = up ? ArrowUpRight : ArrowDownRight;
  return <span className={`delta ${up ? "up" : "down"}`} title={hint}><Icon size={13} />{up ? "+" : ""}{v}%</span>;
}

function Tile({ icon: Icon, label, value, sub, delta, hint, onClick }: {
  icon: LucideIcon; label: string; value: string; sub?: React.ReactNode; delta?: number | null; hint?: string; onClick?: () => void;
}) {
  return (
    <button type="button" className={`h-tile ${onClick ? "go" : ""}`} onClick={onClick} disabled={!onClick}>
      <span className="h-tile-l"><Icon size={16} />{label}</span>
      <span className="h-tile-v">{value}{delta !== undefined && <Delta v={delta} hint={hint ?? ""} />}</span>
      {sub && <span className="h-tile-s">{sub}</span>}
    </button>
  );
}

function Attn({ icon: Icon, n, label, tone = "", onClick }: { icon: LucideIcon; n: string | number; label: string; tone?: string; onClick?: () => void }) {
  const zero = n === 0 || n === "0";
  return (
    <button type="button" className={`attn ${tone} ${zero ? "zero" : ""}`} onClick={onClick} disabled={!onClick}>
      <Icon size={18} /><b>{n}</b><span>{label}</span>
    </button>
  );
}

export default function HomePage() {
  const meta = useMeta();
  const nav = useNavigate();
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: () => api.get<Dashboard>("/dashboard"), refetchInterval: 60_000 });
  const st = (code: string) => meta.statuses.find((s) => s.code === code)?.id;
  const now = new Date();
  const title = `${WEEK[now.getDay()]}, ${now.getDate()} ${MONTHS[now.getMonth()]}`;

  if (isLoading || !data) return <div className="empty big"><Spinner /></div>;
  const { today, month, customers, attention: a } = data;
  const monthName = MONTHS_NOM[now.getMonth()];

  return (
    <div className="home">
      <div className="head">
        <h1><span className="h-ico"><House size={18} /></span>Головна <span className="h-date">{title}</span></h1>
      </div>

      <div className="h-tiles">
        <Tile icon={CircleDollarSign} label="Сьогодні" value={`${money(today.sum)} ₴`} delta={today.sum_delta} hint={`Учора: ${money(today.yesterday_sum)} ₴`}
          sub={<>{today.orders} {pl(today.orders, "замовлення", "замовлення", "замовлень")} · учора {money(today.yesterday_sum)} ₴</>}
          onClick={() => nav(`/orders?date_from=${today.date}&date_to=${today.date}`)} />
        <Tile icon={CalendarDays} label={`${monthName}`} value={`${money(month.sum)} ₴`} delta={month.sum_delta}
          hint={`Той самий відрізок минулого місяця: ${money(month.prev_sum)} ₴`}
          sub={<>{month.orders} {pl(month.orders, "замовлення", "замовлення", "замовлень")} · середній чек {money(month.avg_check)} ₴</>}
          onClick={() => nav("/stats")} />
        <Tile icon={Users} label="Покупці" value={money(customers.total)}
          sub={<>усього в базі</>} onClick={() => nav("/customers")} />
        <Tile icon={UserPlus} label="Нові покупці" value={`+${customers.new}`} delta={customers.new_delta} hint="До того самого відрізка минулого місяця"
          sub={<>за {monthName.toLowerCase()}</>} onClick={() => nav("/customers")} />
      </div>

      <section className="h-card">
        <h2>Потребує уваги</h2>
        <div className="attn-row">
          <Attn icon={Inbox} n={a.leads_new} label="нових лідів" tone="hot" onClick={() => nav(st("new") ? `/leads?status=${st("new")}` : "/leads")} />
          <Attn icon={PackageCheck} n={a.to_ship} label="чекають відправки" tone="warn" onClick={() => nav(st("confirmed") ? `/orders?status=${st("confirmed")}` : "/orders")} />
          <Attn icon={MapPin} n={a.arrived} label="чекають на пошті" tone="warn" onClick={() => nav("/orders")} />
          <Attn icon={AlarmClock} n={a.reminders} label="нагадувань зараз" tone="hot" onClick={() => nav("/orders")} />
          <Attn icon={Truck} n={a.on_way} label="у дорозі" />
          <Attn icon={CircleDollarSign} n={`${money(a.cod_expected)} ₴`} label="очікуємо післяплату" onClick={meta.nav.includes("payments") ? () => nav("/payments") : undefined} />
          {a.low_stock > 0 && <Attn icon={Boxes} n={a.low_stock} label="товарів закінчуються" tone="hot" onClick={meta.nav.includes("warehouse") ? () => nav("/warehouse") : undefined} />}
        </div>
      </section>

      <div className="h-grid">
        <section className="h-card">
          <div className="h-card-head"><h2>Продажі за {monthName.toLowerCase()}</h2><span className="muted">без скасованих і дублів</span></div>
          <DayBars days={data.days} />
        </section>
        <section className="h-card">
          <h2>Якість продажів за місяць</h2>
          <div className="h-rates">
            <Rate label="Апрув" v={month.approve_rate} hint="Частка підтверджених замовлень" />
            <Rate label="Викуп" v={month.buyout_rate} hint="Отримані серед отриманих і відмов" />
            <Rate label="Допродаж" v={month.upsell_rate} hint="Замовлення з допродажем" />
          </div>
          <div className="h-kv"><span>Маржа</span><b>{money(month.margin)} ₴</b></div>
          <div className="h-kv"><span>Замовлень</span><b>{month.orders} <Delta v={month.orders_delta} hint={`Минулого місяця за ті самі дні: ${month.prev_orders}`} /></b></div>
          <div className="h-kv"><span>Ліди в роботі</span><b>{a.leads_open}</b></div>
        </section>
      </div>

      <div className="h-grid">
        <section className="h-card">
          <h2><ShoppingBag size={16} /> Топ товарів місяця</h2>
          {data.top.length === 0 ? <p className="hint">Продажів цього місяця ще немає.</p> : (
            <table className="t dense">
              <thead><tr><th>Товар</th><th className="num">Продано, шт</th><th className="num">Сума, ₴</th></tr></thead>
              <tbody>{data.top.map((p, i) => <tr key={`${p.product_id}-${i}`}><td>{p.name}</td><td className="num">{p.qty}</td><td className="num"><b>{money(p.sum)}</b></td></tr>)}</tbody>
            </table>
          )}
        </section>
        {(data.team ?? []).length > 0 && (
          <section className="h-card">
            <h2><Users size={16} /> Команда сьогодні</h2>
            <table className="t dense">
              <thead><tr><th>Менеджер</th><th className="num">Нових</th><th className="num">Підтвердив</th><th>Заходив</th></tr></thead>
              <tbody>{(data.team ?? []).map((u) => <tr key={u.id}><td>{u.name}</td><td className="num">{u.new}</td><td className="num"><b>{u.confirmed}</b></td>
                <td className="muted">{u.last_login ? ago(u.last_login) : "—"}</td></tr>)}</tbody>
            </table>
          </section>
        )}
      </div>
    </div>
  );
}

function Rate({ label, v, hint }: { label: string; v: number; hint: string }) {
  return (
    <div className="rate" title={hint}>
      <span>{label}</span><b>{v}%</b>
      <span className="rate-bar" aria-hidden><span style={{ width: `${Math.min(100, Math.max(0, v))}%` }} /></span>
    </div>
  );
}

// Стовпчики: сума замовлень за кожен день місяця; одна серія, одна вісь, підказка при наведенні.
function DayBars({ days }: { days: Dashboard["days"] }) {
  const [hover, setHover] = useState<number | null>(null);
  const W = 640, H = 200, L = 46, R = 6, T = 10, B = 24;
  const max = Math.max(1, ...days.map((d) => d.sum));
  const step = useMemo(() => { const raw = max / 4; const p = Math.pow(10, Math.floor(Math.log10(raw))); return [1, 2, 2.5, 5, 10].map((m) => m * p).find((s) => s >= raw) ?? raw; }, [max]);
  const top = step * 4;
  const bw = (W - L - R) / Math.max(days.length, 1);
  const y = (v: number) => T + (H - T - B) * (1 - v / top);
  const every = days.length > 16 ? 5 : days.length > 8 ? 2 : 1;
  const hd = hover != null ? days[hover] : null;
  const short = (v: number) => (v >= 1000 ? `${Math.round(v / 100) / 10}k` : String(v));
  return (
    <div className="daybars">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Сума замовлень по днях місяця" onMouseLeave={() => setHover(null)}>
        {[0, 1, 2, 3, 4].map((k) => <g key={k}><line x1={L} x2={W - R} y1={y(step * k)} y2={y(step * k)} className="grid" />
          <text x={L - 6} y={y(step * k) + 4} textAnchor="end" className="ax">{short(step * k)}</text></g>)}
        {days.map((d, i) => {
          const x = L + bw * i, w = Math.max(3, bw - 2), h = H - B - y(d.sum);
          return (
            <g key={d.day} onMouseEnter={() => setHover(i)}>
              <rect x={x} y={T} width={bw} height={H - T - B} fill="transparent" />
              {d.sum > 0 && <path className={`bar ${hover === i ? "on" : ""}`} d={roundTop(x + 1, y(d.sum), w, h, Math.min(4, w / 2))} />}
              {(i % every === 0 || i === days.length - 1) && <text x={x + bw / 2} y={H - 7} textAnchor="middle" className="ax">{Number(d.day.slice(8))}</text>}
            </g>
          );
        })}
      </svg>
      {hd && (
        <div className="db-tip" style={{ left: `${((L + bw * (hover ?? 0) + bw / 2) / W) * 100}%` }}>
          <b>{Number(hd.day.slice(8))} {MONTHS[Number(hd.day.slice(5, 7)) - 1]}</b>
          <span>{money(hd.sum)} ₴ · {hd.orders} {pl(hd.orders, "замовлення", "замовлення", "замовлень")}</span>
        </div>
      )}
    </div>
  );
}

function roundTop(x: number, y: number, w: number, h: number, r: number) {
  if (h <= r) return `M${x},${y + h}V${y}H${x + w}V${y + h}Z`;
  return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`;
}

function pl(n: number, one: string, few: string, many: string) {
  const a = n % 10, b = n % 100;
  return a === 1 && b !== 11 ? one : a >= 2 && a <= 4 && (b < 12 || b > 14) ? few : many;
}

function ago(iso: string) {
  const m = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (m < 2) return "щойно";
  if (m < 60) return `${m} хв тому`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h} год тому`;
  return `${Math.round(h / 24)} дн тому`;
}
