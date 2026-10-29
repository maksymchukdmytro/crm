// Статистика як у LP-CRM: замовлення за днями в розрізі статусів, основний продаж і допродаж, товари.
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, qs } from "../lib/api";
import { useMeta } from "../lib/app";
import { isoDay, money } from "../lib/format";
import type { Stats } from "../lib/types";
import { Empty, Spinner } from "../components/ui";

const PRESETS: Record<string, string> = {
  today: "Сьогодні", yesterday: "Вчора", week: "Цей тиждень", lastweek: "Минулий тиждень", d7: "Останні 7 днів",
  d14: "Останні 14 днів", month: "Цей місяць", lastmonth: "Минулий місяць", d30: "Останні 30 днів", custom: "Свій період",
};

function range(p: string): [string, string] {
  const t = new Date(); const d = (x: Date) => isoDay(x);
  const add = (n: number) => { const x = new Date(t); x.setDate(x.getDate() + n); return x; };
  const monday = add(-((t.getDay() + 6) % 7));
  switch (p) {
    case "today": return [d(t), d(t)];
    case "yesterday": return [d(add(-1)), d(add(-1))];
    case "week": return [d(monday), d(t)];
    case "lastweek": { const a = new Date(monday); a.setDate(a.getDate() - 7); const b = new Date(monday); b.setDate(b.getDate() - 1); return [d(a), d(b)]; }
    case "d7": return [d(add(-6)), d(t)];
    case "d14": return [d(add(-13)), d(t)];
    case "month": return [d(new Date(t.getFullYear(), t.getMonth(), 1)), d(t)];
    case "lastmonth": return [d(new Date(t.getFullYear(), t.getMonth() - 1, 1)), d(new Date(t.getFullYear(), t.getMonth(), 0))];
    default: return [d(add(-29)), d(t)];
  }
}

export default function StatsPage() {
  const meta = useMeta();
  const [preset, setPreset] = useState("d30");
  const [custom, setCustom] = useState<[string, string]>(range("d30"));
  const [f, setF] = useState({ date_field: "created", status: "", product: "", payment: "", delivery: "", office: "", source: "", manager: "", search_extra: "" });
  const [from, to] = preset === "custom" ? custom : range(preset);
  const params = { ...f, date_from: from, date_to: to };
  const { data, isFetching } = useQuery({ queryKey: ["stats", params], queryFn: () => api.get<Stats>(`/stats${qs(params)}`), placeholderData: (p) => p });
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => setF({ ...f, [k]: e.target.value });
  const statuses = useMemo(() => Object.fromEntries(meta.statuses.map((s) => [s.id, s])), [meta.statuses]);
  const pm = Object.fromEntries(meta.payment_methods.map((m) => [m.id, m.name]));

  return (
    <div className="stats">
      <div className="head"><h1>Статистика</h1>{isFetching && <span className="spinner sm" />}</div>
      <div className="filters">
        <select value={f.date_field} onChange={set("date_field")} title="За якою датою рахувати"><option value="created">Створене</option><option value="shipped">Відправлене</option><option value="changed">Змінене (статус)</option></select>
        <select value={preset} onChange={(e) => setPreset(e.target.value)}>{Object.entries(PRESETS).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select>
        {preset === "custom" && <><input type="date" value={custom[0]} onChange={(e) => setCustom([e.target.value, custom[1]])} /><input type="date" value={custom[1]} onChange={(e) => setCustom([custom[0], e.target.value])} /></>}
        <select value={f.status} onChange={set("status")}><option value="">Усі статуси</option>{meta.statuses.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
        <select value={f.product} onChange={set("product")}><option value="">Усі товари</option>{meta.products.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select>
        <select value={f.payment} onChange={set("payment")}><option value="">Усі види оплат</option>{meta.payment_methods.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</select>
        <select value={f.delivery} onChange={set("delivery")}><option value="">Будь-яка доставка</option>{Object.entries(meta.delivery_methods).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select>
        {meta.offices.length > 0 && <select value={f.office} onChange={set("office")}><option value="">Усі відділи</option>{meta.offices.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}</select>}
        <select value={f.source} onChange={set("source")}><option value="">Усі джерела</option>{meta.order_sources.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}</select>
        {meta.user.role === "admin" && <select value={f.manager} onChange={set("manager")}><option value="">Усі менеджери</option>{meta.managers.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</select>}
        <input type="search" value={f.search_extra} onChange={set("search_extra")} placeholder="Пошук у полях 1–4" />
      </div>
      {!data ? <Empty><Spinner /></Empty> : <>
        <div className="card stats-chart">
          <DayChart data={data} statuses={statuses} />
          <div className="stats-legend">
            <div className="lg-row all"><span className="lg-line" /><b>100%</b><span className="muted">({data.summary.orders})</span><span>Усі</span></div>
            {data.statuses.map((x) => (
              <div className="lg-row" key={x.status_id}><span className="lg-dot" style={{ background: statuses[x.status_id]?.color ?? "#999" }} />
                <b>{x.share}%</b><span className="muted">({x.count})</span><span>{statuses[x.status_id]?.name ?? "—"}</span></div>
            ))}
          </div>
        </div>
        <div className="stats-tiles">
          <Tile title="Замовлення" value={data.summary.orders} rows={[["Без допродажів", data.summary.orders_plain], ["Допродані", data.summary.orders_upsell], ["Частка допродажів", `${data.summary.upsell_rate}%`]]} />
          <Tile title="Товари" value={data.summary.qty} rows={[["Основні", data.summary.qty_main], ["Допродані", data.summary.qty_upsell], ["Частка допродажів", `${data.summary.qty_upsell_rate}%`]]} />
          <Tile title="Маржа" value={money(data.summary.margin)} rows={[["Основна", money(data.summary.margin_main)], ["Допродажу", money(data.summary.margin_upsell)], ["Середня", money(data.summary.margin_avg)]]} />
          <Tile title="Сума" value={money(data.summary.sum)} rows={[["Основна", money(data.summary.sum_main)], ["Допродажу", money(data.summary.sum_upsell)], ["Середній чек", money(data.summary.avg_check)]]} />
        </div>
        <div className="card flush tablewrap">
          <table className="t dense stats-products">
            <thead>
              <tr><th rowSpan={2}>Товар</th><th colSpan={3} className="num grp">Кількість</th><th colSpan={3} className="num grp">Маржа, ₴</th><th colSpan={3} className="num grp">Сума, ₴</th></tr>
              <tr><th className="num">усього</th><th className="num">осн.</th><th className="num">доп.</th><th className="num">усього</th><th className="num">осн.</th><th className="num">доп.</th><th className="num">усього</th><th className="num">осн.</th><th className="num">доп.</th></tr>
            </thead>
            <tbody>{data.products.map((p) => (
              <tr key={`${p.product_id}-${p.name}`}><td>{p.name}</td>
                <td className="num"><b>{p.qty}</b></td><td className="num">{p.qty_main}</td><td className="num muted">{p.qty_upsell || ""}</td>
                <td className={`num ${p.margin < 0 ? "lowstock" : ""}`}><b>{money(p.margin)}</b></td><td className="num">{money(p.margin_main)}</td><td className="num muted">{p.margin_upsell ? money(p.margin_upsell) : ""}</td>
                <td className="num"><b>{money(p.sum)}</b></td><td className="num">{money(p.sum_main)}</td><td className="num muted">{p.sum_upsell ? money(p.sum_upsell) : ""}</td></tr>
            ))}{!data.products.length && <tr><td colSpan={10}><Empty>За цей період замовлень немає</Empty></td></tr>}</tbody>
          </table>
        </div>
        <p className="hint">Маржа = ціна продажу − собівартість на момент продажу; знижка замовлення зменшує основну маржу й суму. {Object.keys(pm).length ? "" : ""}</p>
      </>}
    </div>
  );
}

function Tile({ title, value, rows }: { title: string; value: string | number; rows: [string, string | number][] }) {
  return (
    <div className="card stile"><div className="stile-h"><span>{title}</span><b>{value}</b></div>
      {rows.map(([k, v]) => <div className="stile-r" key={k}><span>{k}</span><span>{v}</span></div>)}</div>
  );
}

// Стовпчики за днями (сегменти — статуси їхніми кольорами) + лінія «усі»; одна вісь, підказка при наведенні.
function DayChart({ data, statuses }: { data: Stats; statuses: Record<number, { name: string; color: string }> }) {
  const [hover, setHover] = useState<number | null>(null);
  const days = data.days;
  const W = 900, H = 260, L = 34, R = 10, T = 12, B = 26;
  const max = Math.max(1, ...days.map((d) => d.total));
  const step = Math.pow(10, Math.floor(Math.log10(max))); const nice = Math.ceil(max / step) * step; const yMax = nice < max ? max : nice;
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((k) => Math.round(yMax * k));
  const bw = (W - L - R) / Math.max(days.length, 1);
  const y = (v: number) => T + (H - T - B) * (1 - v / yMax);
  const order = data.statuses.map((x) => x.status_id); // знизу — найчастіші
  const every = Math.ceil(days.length / 12);
  const pts = days.map((d, i) => `${L + bw * i + bw / 2},${y(d.total)}`).join(" ");
  const hd = hover != null ? days[hover] : null;
  return (
    <div className="daychart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Замовлення за днями в розрізі статусів" onMouseLeave={() => setHover(null)}>
        {ticks.map((t) => <g key={t}><line x1={L} x2={W - R} y1={y(t)} y2={y(t)} className="grid" /><text x={L - 6} y={y(t) + 4} className="ax" textAnchor="end">{t}</text></g>)}
        {days.map((d, i) => {
          let acc = 0;
          const x = L + bw * i + Math.max(1, bw * 0.18);
          const w = Math.max(2, bw * 0.64);
          return (
            <g key={d.day} onMouseEnter={() => setHover(i)}>
              <rect x={L + bw * i} y={T} width={bw} height={H - T - B} fill="transparent" />
              {order.map((sid) => {
                const c = d.by_status[String(sid)] ?? 0;
                if (!c) return null;
                const y0 = y(acc), y1 = y(acc + c); acc += c;
                return <rect key={sid} x={x} y={y1} width={w} height={Math.max(0, y0 - y1 - 1)} rx={2} fill={statuses[sid]?.color ?? "#999"} opacity={hover == null || hover === i ? 1 : 0.55} />;
              })}
              {i % every === 0 && <text x={L + bw * i + bw / 2} y={H - 8} className="ax" textAnchor="middle">{d.day.slice(8, 10)}.{d.day.slice(5, 7)}</text>}
            </g>
          );
        })}
        <polyline points={pts} className="tline" />
        {days.map((d, i) => <circle key={d.day} cx={L + bw * i + bw / 2} cy={y(d.total)} r={hover === i ? 4 : 2.5} className="tdot" />)}
      </svg>
      {hd && (
        <div className="dc-tip" style={{ left: `${((L + bw * (hover ?? 0) + bw / 2) / W) * 100}%` }}>
          <b>{hd.day.split("-").reverse().join(".")} · усього {hd.total}</b>
          {order.filter((sid) => hd.by_status[String(sid)]).map((sid) => (
            <div key={sid}><span className="lg-dot" style={{ background: statuses[sid]?.color }} />{statuses[sid]?.name}: {hd.by_status[String(sid)]}</div>
          ))}
        </div>
      )}
    </div>
  );
}
