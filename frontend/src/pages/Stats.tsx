// Статистика: як у LP-CRM (графік статусів, основне / допродаж, товари, розширений перелік замовлень, усі фільтри)
// і більше — апрув, викуп, час підтвердження, порівняння з попереднім періодом, розрізи, цінові сегменти, CSV.
import { useMemo, useState, type ReactNode } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import {
  ArrowDown, ArrowUp, Building2, CalendarDays, ChartColumnStacked, ChevronDown, CircleDot, Download, Filter, Flag, FolderTree, Globe, Hash, Landmark, Layers,
  Megaphone, Package, PencilLine, RotateCcw, Search, ShoppingBag, Truck, User as UserIcon, Wallet,
} from "lucide-react";
import { api, qs, ROOT } from "../lib/api";
import { useMeta } from "../lib/app";
import { dt, isoDay, money, phone } from "../lib/format";
import type { Stats, StatsBreakdown, StatsOptions, StatsOrders, StatsProduct, StatsSegments, StatsSummary, Status } from "../lib/types";
import { Empty, Pill, Spinner } from "../components/ui";
import MultiSelect, { EMPTY, type MsOption } from "../components/MultiSelect";
import StatsChart, { type ChartStatus } from "../components/StatsChart";
import OrderModal from "./OrderCard";
import "./stats.css";

const PRESETS: [string, string][] = [
  ["today", "Сьогодні"], ["yesterday", "Вчора"], ["week", "Цей тиждень"], ["lastweek", "Минулий тиждень"],
  ["d7", "Останні 7 днів"], ["d14", "Останні 14 днів"], ["month", "Цей місяць"], ["lastmonth", "Минулий місяць"],
  ["d30", "Останні 30 днів"], ["d90", "Останні 90 днів"], ["year", "Цей рік"], ["all", "Весь час"], ["custom", "Свій період"],
];
const GROUPS: [string, string][] = [["auto", "Авто"], ["hour", "Години"], ["day", "Дні"], ["week", "Тижні"], ["month", "Місяці"]];

function presetRange(p: string): [string, string] {
  const t = new Date(); const d = isoDay;
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
    case "d90": return [d(add(-89)), d(t)];
    case "year": return [d(new Date(t.getFullYear(), 0, 1)), d(t)];
    default: return [d(add(-29)), d(t)];
  }
}

// фільтри-списки: ключ параметра API
const LIST_KEYS = ["product", "category", "legal_entity", "country", "status", "reason", "office", "manager", "delivery", "payment", "source", "shop",
  "site", "utm_source", "utm_medium", "utm_term", "utm_content", "utm_campaign", "extra1", "extra2", "extra3", "extra4"] as const;
type ListKey = typeof LIST_KEYS[number];
const FILTERABLE_DIMS = new Set<string>(["legal_entity", "source", "manager", "office", "payment", "delivery", "country", "reason", "shop", "site",
  "utm_source", "utm_medium", "utm_term", "utm_content", "utm_campaign", "extra1", "extra2", "extra3", "extra4"]);
const DIM_TO_FILTER: Record<string, ListKey> = { source: "source", manager: "manager", office: "office", payment: "payment", delivery: "delivery",
  country: "country", reason: "reason", shop: "shop", site: "site", legal_entity: "legal_entity", utm_source: "utm_source", utm_medium: "utm_medium", utm_term: "utm_term",
  utm_content: "utm_content", utm_campaign: "utm_campaign", extra1: "extra1", extra2: "extra2", extra3: "extra3", extra4: "extra4" };

const list = (v: string | null) => (v ? v.split(",").filter(Boolean) : []);

export default function StatsPage() {
  const meta = useMeta();
  const [sp, setSp] = useSearchParams();
  const [tab, setTab] = useState(sp.get("tab") || "products");
  const [showFilters, setShowFilters] = useState(false);
  const [openOrder, setOpenOrder] = useState<number | null>(null);
  const [hidden, setHidden] = useState<Set<number>>(new Set());
  const [showTotal, setShowTotal] = useState(true);

  const preset = sp.get("p") || "d30";
  const dateField = sp.get("date_field") || "created";
  const group = sp.get("group") || "auto";
  const upsell = sp.get("upsell") || "";
  const search = sp.get("search") || "";
  const [from, to] = preset === "custom" ? [sp.get("from") || presetRange("d30")[0], sp.get("to") || presetRange("d30")[1]] : presetRange(preset);
  const lists = Object.fromEntries(LIST_KEYS.map((k) => [k, list(sp.get(k))])) as Record<ListKey, string[]>;

  const set = (patch: Record<string, string | string[] | null>) => {
    const next = new URLSearchParams(sp);
    for (const [k, v] of Object.entries(patch)) {
      const s = Array.isArray(v) ? v.join(",") : v;
      if (s) next.set(k, s); else next.delete(k);
    }
    setSp(next, { replace: true });
  };

  const params: Record<string, string> = {
    date_field: dateField, group, upsell, search,
    ...(preset === "all" ? { all_time: "true" } : { date_from: from, date_to: to }),
    ...Object.fromEntries(LIST_KEYS.map((k) => [k, lists[k].join(",")])),
  };
  const key = JSON.stringify(params);
  const opts = useQuery({ queryKey: ["stats-options"], queryFn: () => api.get<StatsOptions>("/stats/options"), staleTime: 5 * 60_000 });
  const main = useQuery({ queryKey: ["stats", key], queryFn: () => api.get<Stats>(`/stats${qs(params)}`), placeholderData: (p) => p });
  const data = main.data;

  const statusMap = useMemo(() => Object.fromEntries(meta.statuses.map((s) => [s.id, s])), [meta.statuses]);
  const chartStatuses: ChartStatus[] = useMemo(
    () => (data?.statuses ?? []).map((x) => ({ id: x.status_id, name: statusMap[x.status_id]?.name ?? `Статус ${x.status_id}`, color: statusMap[x.status_id]?.color ?? "#999" })),
    [data?.statuses, statusMap],
  );
  const activeCount = LIST_KEYS.reduce((n, k) => n + (lists[k].length ? 1 : 0), 0) + (upsell ? 1 : 0) + (search ? 1 : 0);

  // варіанти для фільтрів
  const strOpts = (name: string): MsOption[] => (opts.data?.values[name] ?? []).map((x) => ({ value: x.value, label: x.value, hint: x.count }));
  const extraName = (i: number) => meta.extra_fields[i - 1] || `Додаткове поле ${i}`;
  const filters: { key: ListKey; label: string; icon: ReactNode; options: MsOption[]; empty?: boolean; hide?: boolean }[] = [
    { key: "category", label: "Категорія", icon: <FolderTree size={15} />, hide: !meta.categories.length,
      options: meta.categories.filter((c) => !c.parent_id).flatMap((r) => [{ value: String(r.id), label: r.name },
        ...meta.categories.filter((c) => c.parent_id === r.id).map((c) => ({ value: String(c.id), label: c.name, depth: 1 }))]) },
    { key: "product", label: "Товар", icon: <Package size={15} />, options: meta.products.map((p) => ({ value: String(p.id), label: p.name })) },
    { key: "legal_entity", label: "Юрособа", icon: <Landmark size={15} />, options: meta.legal_entities.map((x) => ({ value: String(x.id), label: x.name })), empty: true, hide: !meta.legal_entities.length },
    { key: "country", label: "Країна", icon: <Globe size={15} />, options: Object.entries(meta.countries).map(([k, v]) => ({ value: k, label: v })), hide: Object.keys(meta.countries).length < 2 },
    { key: "status", label: "Статус", icon: <CircleDot size={15} />, options: meta.statuses.map((s) => ({ value: String(s.id), label: s.name, color: s.color })) },
    { key: "reason", label: "Причина", icon: <Flag size={15} />, options: meta.reasons.map((r) => ({ value: String(r.id), label: r.name })), empty: true, hide: !meta.reasons.length },
    { key: "office", label: "Відділ", icon: <Building2 size={15} />, options: meta.offices.map((o) => ({ value: String(o.id), label: o.name })), empty: true, hide: !meta.offices.length },
    { key: "manager", label: "Менеджер", icon: <UserIcon size={15} />, options: meta.managers.map((m) => ({ value: String(m.id), label: m.name || m.username })), empty: true, hide: meta.user.role !== "admin" },
    { key: "delivery", label: "Доставка", icon: <Truck size={15} />, options: Object.entries(meta.delivery_methods).map(([k, v]) => ({ value: k, label: v })), empty: true },
    { key: "payment", label: "Оплата", icon: <Wallet size={15} />, options: meta.payment_methods.map((m) => ({ value: String(m.id), label: m.name })), empty: true },
    { key: "source", label: "Джерело", icon: <Megaphone size={15} />, options: meta.order_sources.map((x) => ({ value: String(x.id), label: x.name })), empty: true },
    { key: "shop", label: "Магазин", icon: <ShoppingBag size={15} />, options: Object.entries(meta.shops).map(([k, v]) => ({ value: k, label: v })), empty: true, hide: !Object.keys(meta.shops).length },
    { key: "site", label: "Сайт", icon: <Globe size={15} />, options: strOpts("site"), empty: true },
    { key: "utm_source", label: "utm_source", icon: <Hash size={15} />, options: strOpts("utm_source"), empty: true },
    { key: "utm_medium", label: "utm_medium", icon: <Hash size={15} />, options: strOpts("utm_medium"), empty: true },
    { key: "utm_term", label: "utm_term", icon: <Hash size={15} />, options: strOpts("utm_term"), empty: true },
    { key: "utm_content", label: "utm_content", icon: <Hash size={15} />, options: strOpts("utm_content"), empty: true },
    { key: "utm_campaign", label: "utm_campaign", icon: <Hash size={15} />, options: strOpts("utm_campaign"), empty: true },
    ...[1, 2, 3, 4].filter((i) => meta.extra_on?.[i - 1] ?? true).map((i) => ({ key: `extra${i}` as ListKey, label: extraName(i), icon: <PencilLine size={15} />, options: strOpts(`extra${i}`), empty: true })),
  ];

  const exportHref = (kind: string, extra: Record<string, string> = {}) => `${ROOT}/api/stats/export.csv${qs({ ...params, kind, ...extra })}`;
  const addFilter = (k: ListKey, v: string) => set({ [k]: lists[k].includes(v) ? lists[k] : [...lists[k], v] });

  return (
    <div className="stats">
      <div className="head">
        <h1><span className="h-ico"><ChartColumnStacked size={18} /></span>Статистика {main.isFetching && <span className="spinner sm" />}</h1>
        <div className="actions">
          <button className="btn sm ghost st-filters-toggle" onClick={() => setShowFilters((x) => !x)}><Filter size={15} />Фільтри{activeCount ? ` · ${activeCount}` : ""}</button>
          {activeCount > 0 && <button className="btn sm ghost" onClick={() => set(Object.fromEntries([...LIST_KEYS, "upsell", "search"].map((k) => [k, null])))}><RotateCcw size={14} />Скинути фільтри</button>}
        </div>
      </div>

      <div className="st-bar">
        <label className="st-sel" title="За якою датою рахувати замовлення"><CalendarDays size={15} />
          <select value={dateField} onChange={(e) => set({ date_field: e.target.value })}>
            {Object.entries(opts.data?.date_fields ?? { created: "Додане" }).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select><ChevronDown size={14} /></label>
        <label className="st-sel"><select value={preset} onChange={(e) => set({ p: e.target.value === "d30" ? null : e.target.value, ...(e.target.value === "custom" ? { from, to } : { from: null, to: null }) })}>
          {PRESETS.map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select><ChevronDown size={14} /></label>
        {preset === "custom" ? (
          <span className="st-dates"><input type="date" value={from} max={to} onChange={(e) => set({ from: e.target.value })} /><span>—</span>
            <input type="date" value={to} min={from} onChange={(e) => set({ to: e.target.value })} /></span>
        ) : data && <span className="st-period">{data.date_from.split("-").reverse().join(".")} — {data.date_to.split("-").reverse().join(".")}</span>}
        <span className="st-seg" role="group" aria-label="Групування">
          {GROUPS.map(([k, v]) => <button key={k} className={group === k ? "on" : ""} onClick={() => set({ group: k === "auto" ? null : k })}>{v}</button>)}
        </span>
      </div>

      <div className={`st-body ${showFilters ? "filters-open" : ""}`}>
        <aside className="st-filters">
          <div className="st-search"><Search size={15} /><input type="search" placeholder="Пошук у полях 1–4 і коментарі" defaultValue={search}
            onKeyDown={(e) => { if (e.key === "Enter") set({ search: (e.target as HTMLInputElement).value.trim() }); }}
            onBlur={(e) => { if (e.target.value.trim() !== search) set({ search: e.target.value.trim() }); }} /></div>
          {filters.filter((f) => !f.hide).map((f) => (
            <MultiSelect key={f.key} label={f.label} placeholder={f.label} icon={f.icon} options={f.options} allowEmpty={f.empty}
              value={lists[f.key]} onChange={(v) => set({ [f.key]: v })} />
          ))}
          <MultiSelect single label="Допродаж" placeholder="Допродаж: усі" icon={<Layers size={15} />}
            options={[{ value: "with", label: "Лише з допродажем" }, { value: "without", label: "Без допродажу" }]}
            value={upsell ? [upsell] : []} onChange={(v) => set({ upsell: v[0] ?? null })} />
        </aside>

        <section className="st-main">
          {!data ? <div className="card"><Empty><Spinner /></Empty></div> : <>
            <div className="card st-chart">
              {data.summary.orders === 0
                ? <Empty>За вибраний період і фільтри замовлень немає</Empty>
                : <div className="st-chart-in">
                  <StatsChart points={data.series} statuses={chartStatuses} hidden={hidden} showTotal={showTotal} group={data.group} />
                  <div className="st-legend">
                    <button className={`st-lg ${showTotal ? "" : "off"}`} onClick={() => setShowTotal((x) => !x)}>
                      <span className="st-lg-line" /><b>100%</b><span className="st-lg-n">({data.summary.orders})</span><span className="st-lg-name">Усі</span></button>
                    {data.statuses.map((x) => {
                      const s = statusMap[x.status_id];
                      const off = hidden.has(x.status_id);
                      return (
                        <button key={x.status_id} className={`st-lg ${off ? "off" : ""}`} title={off ? "Показати" : "Сховати на графіку"}
                          onClick={() => setHidden((h) => { const n = new Set(h); if (n.has(x.status_id)) n.delete(x.status_id); else n.add(x.status_id); return n; })}>
                          <span className="st-lg-dot" style={{ background: s?.color ?? "#999" }} /><b>{x.share}%</b><span className="st-lg-n">({x.count})</span><span className="st-lg-name" title={s?.name}>{s?.name ?? "—"}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>}
            </div>

            <div className="st-tiles">
              <Tile title="Замовлення" value={data.summary.orders} delta={delta(data, "orders")}
                rows={[["Без допродажів", data.summary.orders_plain], ["Допродані", data.summary.orders_upsell], ["% допродажів", `${data.summary.upsell_rate}%`]]} />
              <Tile title="Товари" value={data.summary.qty} delta={delta(data, "qty")}
                rows={[["Основні", data.summary.qty_main], ["Допродані", data.summary.qty_upsell], ["% допроданих", `${data.summary.qty_upsell_rate}%`]]} />
              <Tile title="Маржа" value={money(data.summary.margin)} delta={delta(data, "margin")}
                rows={[["Основна", money(data.summary.margin_main)], ["Допродажу", money(data.summary.margin_upsell)], ["Середня", money(data.summary.margin_avg)]]} />
              <Tile title="Сума" value={money(data.summary.sum)} delta={delta(data, "sum")}
                rows={[["Основна", money(data.summary.sum_main)], ["Допродажу", money(data.summary.sum_upsell)], ["Середній чек", money(data.summary.avg_check)]]} />
            </div>
            <div className="st-kpis">
              <Kpi label="Апрув" value={`${data.summary.approve_rate}%`} sub={`${data.summary.approved} підтверджено`} d={pp(data, "approve_rate")} />
              <Kpi label="Викуп" value={data.summary.delivered + data.summary.refused ? `${data.summary.buyout_rate}%` : "—"} sub={`${data.summary.delivered} отримано · ${data.summary.refused} відмов`} d={data.summary.delivered + data.summary.refused ? pp(data, "buyout_rate") : null} />
              <Kpi label="Відправлено" value={data.summary.shipped} sub={data.summary.orders ? `${Math.round(data.summary.shipped * 100 / data.summary.orders)}% від замовлень` : ""} d={delta(data, "shipped")} />
              <Kpi label="Середній чек" value={`${money(data.summary.avg_check)} ₴`} sub={`маржа ${money(data.summary.margin_avg)} ₴`} d={delta(data, "avg_check")} />
              <Kpi label="Час підтвердження" value={data.summary.confirm_avg_min == null ? "—" : minutes(data.summary.confirm_avg_min)} sub="від додавання до апруву"
                d={data.prev && data.prev.orders >= MIN_PREV_ORDERS && data.prev.confirm_avg_min && data.summary.confirm_avg_min != null ? { v: pct(data.summary.confirm_avg_min, data.prev.confirm_avg_min), good: data.summary.confirm_avg_min <= data.prev.confirm_avg_min, unit: "%" } : null} />
              {data.summary.duplicates > 0 && <Kpi label="Дублі" value={data.summary.duplicates} sub="не псують апрув, якщо не підтверджені" d={null} />}
            </div>
            {data.prev && <p className="hint st-prev">Порівняння з попереднім періодом {data.prev.date_from.split("-").reverse().join(".")} — {data.prev.date_to.split("-").reverse().join(".")}: {data.prev.orders} замовлень, {money(data.prev.sum)} ₴.</p>}

            <div className="tabs st-tabs">
              {[["products", "Товари"], ["breakdown", "Розрізи"], ["orders", "Замовлення"], ["segments", "Цінові сегменти"]].map(([k, v]) => (
                <a key={k} className={tab === k ? "on" : ""} onClick={() => { setTab(k); set({ tab: k === "products" ? null : k }); }}>{v}</a>
              ))}
            </div>
            {tab === "products" && <ProductsTab qkey={key} params={params} exportHref={exportHref("products")} onPick={(id) => id && addFilter("product", String(id))} />}
            {tab === "breakdown" && <BreakdownTab qkey={key} params={params} dims={opts.data?.dimensions ?? {}} extraName={extraName}
              exportHref={(dim) => exportHref("breakdown", { dim })} onPick={(dim, v) => DIM_TO_FILTER[dim] && addFilter(DIM_TO_FILTER[dim], v)} />}
            {tab === "orders" && <OrdersTab qkey={key} params={params} statusMap={statusMap} extraName={extraName} exportHref={exportHref("orders")} onOpen={setOpenOrder} />}
            {tab === "segments" && <SegmentsTab qkey={key} params={params} metrics={opts.data?.segment_metrics ?? {}} />}
            <p className="hint">Маржа = ціна продажу − собівартість на момент продажу. Знижка замовлення зменшує основну суму й маржу.
              Апрув — частка підтверджених (дублі без підтвердження не враховуються). Викуп — отримані з-поміж отриманих і відмов.</p>
          </>}
        </section>
      </div>
      {openOrder != null && <OrderModal id={String(openOrder)} onClose={() => setOpenOrder(null)} onOpen={(id) => setOpenOrder(id)} />}
    </div>
  );
}

// ---------------------------------------------------------------- плитки й показники
type D = { v: number; good: boolean; unit: string } | null;

function pct(cur: number, prev: number): number {
  return prev ? Math.round(((cur - prev) / Math.abs(prev)) * 1000) / 10 : 0;
}
// порівняння має сенс, лише коли в попередньому періоді було з чим порівнювати
const MIN_PREV_ORDERS = 5;
function delta(s: Stats, k: keyof StatsSummary): D {
  const p = s.prev?.[k], c = s.summary[k];
  if (!s.prev || s.prev.orders < MIN_PREV_ORDERS || typeof p !== "number" || typeof c !== "number" || !p) return null;
  return { v: pct(c, p), good: c >= p, unit: "%" };
}
function pp(s: Stats, k: "approve_rate" | "buyout_rate"): D {
  if (!s.prev || s.prev.orders < MIN_PREV_ORDERS) return null;
  const v = Math.round((s.summary[k] - s.prev[k]) * 10) / 10;
  return { v, good: v >= 0, unit: " п.п." };
}
function minutes(m: number): string {
  if (m < 60) return `${Math.round(m)} хв`;
  const h = m / 60;
  return h < 48 ? `${Math.floor(h)} год ${Math.round(m % 60)} хв` : `${Math.round(h / 24)} дн`;
}

function Delta({ d }: { d: D }) {
  if (!d || !isFinite(d.v)) return null;
  if (d.v === 0) return <span className="dl zero">0{d.unit}</span>;
  return <span className={`dl ${d.good ? "up" : "down"}`} title="Порівняно з попереднім періодом">
    {d.v > 0 ? <ArrowUp size={12} /> : <ArrowDown size={12} />}{Math.abs(d.v)}{d.unit}</span>;
}

function Tile({ title, value, rows, delta: d }: { title: string; value: ReactNode; rows: [string, ReactNode][]; delta: D }) {
  return (
    <div className="card st-tile">
      <div className="st-tile-h"><span>{title}</span><Delta d={d} /></div>
      <div className="st-tile-v">{value}</div>
      {rows.map(([k, v]) => <div className="st-tile-r" key={k}><span>{k}</span><b>{v}</b></div>)}
    </div>
  );
}

function Kpi({ label, value, sub, d }: { label: string; value: ReactNode; sub?: ReactNode; d: D }) {
  return <div className="st-kpi"><div className="st-kpi-l">{label}<Delta d={d} /></div><div className="st-kpi-v">{value}</div>{sub && <div className="st-kpi-s">{sub}</div>}</div>;
}

// ---------------------------------------------------------------- таблиці
function useSort<T>(rows: T[], init: keyof T, dir: 1 | -1 = -1) {
  const [s, setS] = useState<{ k: keyof T; d: 1 | -1 }>({ k: init, d: dir });
  const sorted = useMemo(() => [...rows].sort((a, b) => {
    const x = a[s.k], y = b[s.k];
    if (typeof x === "number" && typeof y === "number") return (x - y) * s.d;
    return String(x ?? "").localeCompare(String(y ?? ""), "uk") * s.d;
  }), [rows, s]);
  const th = (k: keyof T, label: ReactNode, cls = "num") => (
    <th className={`${cls} sortable ${s.k === k ? "on" : ""}`} onClick={() => setS((p) => ({ k, d: p.k === k ? (p.d === 1 ? -1 : 1) : -1 }))}>
      {label}{s.k === k && (s.d === 1 ? <ArrowUp size={11} /> : <ArrowDown size={11} />)}</th>
  );
  return { sorted, th };
}

function TabHead({ children, exportHref }: { children?: ReactNode; exportHref: string }) {
  return <div className="st-tabhead">{children}<a className="btn sm" href={exportHref} download><Download size={14} />CSV для Excel</a></div>;
}

function ProductsTab({ qkey, params, exportHref, onPick }: { qkey: string; params: Record<string, string>; exportHref: string; onPick: (id: number | null) => void }) {
  const [q, setQ] = useState("");
  const { data } = useQuery({ queryKey: ["stats-products", qkey], queryFn: () => api.get<{ rows: StatsProduct[] }>(`/stats/products${qs(params)}`), placeholderData: (p) => p });
  const rows = useMemo(() => (data?.rows ?? []).filter((r) => !q || `${r.name} ${r.sku}`.toLowerCase().includes(q.toLowerCase())), [data, q]);
  const { sorted, th } = useSort(rows, "qty");
  const tot = rows.reduce((a, r) => ({ qty: a.qty + r.qty, qm: a.qm + r.qty_main, qu: a.qu + r.qty_upsell, s: a.s + r.sum, sm: a.sm + r.sum_main, su: a.su + r.sum_upsell, m: a.m + r.margin, mm: a.mm + r.margin_main, mu: a.mu + r.margin_upsell }),
    { qty: 0, qm: 0, qu: 0, s: 0, sm: 0, su: 0, m: 0, mm: 0, mu: 0 });
  if (!data) return <div className="card"><Empty><Spinner /></Empty></div>;
  return (
    <div className="card flush">
      <TabHead exportHref={exportHref}><input type="search" className="st-tsearch" placeholder="Пошук товару" value={q} onChange={(e) => setQ(e.target.value)} /><span className="muted">{rows.length} товарів</span></TabHead>
      <div className="tablewrap">
        <table className="t dense st-table">
          <thead>
            <tr><th rowSpan={2}>Товар</th><th rowSpan={2} className="num">Замовл.</th><th colSpan={3} className="num grp">Кількість</th><th colSpan={3} className="num grp">Маржа, ₴</th><th colSpan={3} className="num grp">Сума, ₴</th></tr>
            <tr>{th("qty", "усього")}{th("qty_main", "осн.")}{th("qty_upsell", "доп.")}{th("margin", "усього")}{th("margin_main", "осн.")}{th("margin_upsell", "доп.")}{th("sum", "усього")}{th("sum_main", "осн.")}{th("sum_upsell", "доп.")}</tr>
          </thead>
          <tbody>{sorted.map((p) => (
            <tr key={`${p.product_id}-${p.name}`} className={p.product_id ? "clickable" : ""} onClick={() => onPick(p.product_id ?? null)} title={p.product_id ? "Відфільтрувати статистику за цим товаром" : undefined}>
              <td><div className="st-pname">{p.name}</div>{(p.sku || p.category) && <span className="sub">{[p.sku, p.category].filter(Boolean).join(" · ")}</span>}</td>
              <td className="num muted">{p.orders}</td>
              <td className="num"><b>{p.qty}</b></td><td className="num">{p.qty_main || ""}</td><td className="num up-c">{p.qty_upsell || ""}</td>
              <td className={`num ${p.margin < 0 ? "neg" : ""}`}><b>{money(p.margin)}</b></td><td className="num">{p.margin_main ? money(p.margin_main) : ""}</td><td className="num up-c">{p.margin_upsell ? money(p.margin_upsell) : ""}</td>
              <td className="num"><b>{money(p.sum)}</b></td><td className="num">{p.sum_main ? money(p.sum_main) : ""}</td><td className="num up-c">{p.sum_upsell ? money(p.sum_upsell) : ""}</td>
            </tr>
          ))}{!sorted.length && <tr><td colSpan={11}><Empty>Немає товарів за цими фільтрами</Empty></td></tr>}</tbody>
          {sorted.length > 1 && <tfoot><tr><td>Разом</td><td /><td className="num">{tot.qty}</td><td className="num">{tot.qm}</td><td className="num">{tot.qu}</td>
            <td className="num">{money(tot.m)}</td><td className="num">{money(tot.mm)}</td><td className="num">{money(tot.mu)}</td>
            <td className="num">{money(tot.s)}</td><td className="num">{money(tot.sm)}</td><td className="num">{money(tot.su)}</td></tr></tfoot>}
        </table>
      </div>
    </div>
  );
}

function BreakdownTab({ qkey, params, dims, extraName, exportHref, onPick }: {
  qkey: string; params: Record<string, string>; dims: Record<string, string>; extraName: (i: number) => string;
  exportHref: (dim: string) => string; onPick: (dim: string, v: string) => void;
}) {
  const [dim, setDim] = useState("utm_source");
  const { data, isFetching } = useQuery({ queryKey: ["stats-breakdown", qkey, dim], queryFn: () => api.get<StatsBreakdown>(`/stats/breakdown${qs({ ...params, dim })}`), placeholderData: (p) => p });
  const rows = data?.rows ?? [];
  const { sorted, th } = useSort(rows, dim === "hour" || dim === "weekday" ? "key" : "orders", dim === "hour" || dim === "weekday" ? 1 : -1);
  const maxOrders = Math.max(1, ...rows.map((r) => r.orders));
  const dimName = (k: string, v: string) => (k.startsWith("extra") ? extraName(Number(k.slice(5))) : v);
  return (
    <div className="card flush">
      <TabHead exportHref={exportHref(dim)}>
        <label className="st-sel"><select value={dim} onChange={(e) => setDim(e.target.value)}>
          {Object.entries(dims).map(([k, v]) => <option key={k} value={k}>{dimName(k, v)}</option>)}
        </select><ChevronDown size={14} /></label>
        {isFetching && <span className="spinner sm" />}
        {FILTERABLE_DIMS.has(dim) && <span className="muted">Клік по рядку — додати у фільтр</span>}
      </TabHead>
      <div className="tablewrap">
        <table className="t dense st-table">
          <thead><tr>{th("label", dimName(dim, dims[dim] ?? "Значення"), "")}{th("orders", "Замовлення")}{th("approve_rate", "Апрув")}{th("shipped", "Відправл.")}
            {th("delivered", "Отримано")}{th("refused", "Відмови")}{th("buyout_rate", "Викуп")}{th("sum", "Сума, ₴")}{th("margin", "Маржа, ₴")}{th("avg_check", "Сер. чек")}{th("upsell_rate", "Допродажі")}</tr></thead>
          <tbody>{sorted.map((r) => (
            <tr key={r.key} className={FILTERABLE_DIMS.has(dim) ? "clickable" : ""} onClick={() => FILTERABLE_DIMS.has(dim) && onPick(dim, r.key)}>
              <td className={r.key === EMPTY ? "muted" : ""}>{r.label}</td>
              <td className="num st-barcell"><span className="st-bar-bg" style={{ width: `${(r.orders / maxOrders) * 100}%` }} /><b>{r.orders}</b></td>
              <td className="num"><Rate v={r.approve_rate} /></td><td className="num">{r.shipped}</td><td className="num">{r.delivered}</td><td className="num">{r.refused}</td>
              <td className="num"><Rate v={r.buyout_rate} empty={!r.delivered && !r.refused} /></td>
              <td className="num">{money(r.sum)}</td><td className={`num ${r.margin < 0 ? "neg" : ""}`}>{money(r.margin)}</td><td className="num">{money(r.avg_check)}</td><td className="num">{r.upsell_rate}%</td>
            </tr>
          ))}{!sorted.length && <tr><td colSpan={11}><Empty>Немає даних</Empty></td></tr>}</tbody>
        </table>
      </div>
    </div>
  );
}

function Rate({ v, empty = false }: { v: number; empty?: boolean }) {
  if (empty) return <span className="muted">—</span>;
  return <span className={`rate ${v >= 70 ? "hi" : v >= 40 ? "mid" : "lo"}`}>{v}%</span>;
}

function OrdersTab({ qkey, params, statusMap, extraName, exportHref, onOpen }: {
  qkey: string; params: Record<string, string>; statusMap: Record<number, Status>;
  extraName: (i: number) => string; exportHref: string; onOpen: (id: number) => void;
}) {
  const q = useInfiniteQuery({
    queryKey: ["stats-orders", qkey], initialPageParam: 0,
    queryFn: ({ pageParam }) => api.get<StatsOrders>(`/stats/orders${qs({ ...params, offset: pageParam, limit: 100 })}`),
    getNextPageParam: (last) => (last.offset + last.rows.length < last.total ? last.offset + last.rows.length : undefined),
  });
  const rows = q.data?.pages.flatMap((p) => p.rows) ?? [];
  const total = q.data?.pages[0]?.total ?? 0;
  const has = (k: keyof StatsOrders["rows"][number]) => rows.some((r) => r[k]);
  const extras = [1, 2, 3, 4].filter((i) => has(`extra${i}` as "extra1"));
  const utm = has("utm_source") || has("utm_medium") || has("utm_campaign") || has("utm_content") || has("utm_term");
  if (q.isLoading) return <div className="card"><Empty><Spinner /></Empty></div>;
  return (
    <div className="card flush">
      <TabHead exportHref={exportHref}><span className="muted">Знайдено {total} замовлень</span></TabHead>
      <div className="tablewrap">
        <table className="t dense st-table st-orders">
          <thead><tr><th>№</th><th>Статус</th><th>Покупець</th><th>Товари</th><th className="num">Сума</th><th className="num">Маржа</th><th>Оплата</th><th>Доставка</th>
            <th>Додане</th><th className="num" title="Від додавання до першого підтвердження">Підтв.</th><th>Відправлене</th><th>Менеджер</th>{has("office") && <th>Відділ</th>}
            {has("site") && <th>Сайт</th>}{utm && <th>UTM</th>}{extras.map((i) => <th key={i}>{extraName(i)}</th>)}</tr></thead>
          <tbody>{rows.map((r) => (
            <tr key={r.id} className="clickable" onClick={() => onOpen(r.id)}>
              <td className="mono">{r.id}{r.external_id && <span className="sub">{r.external_id}</span>}</td>
              <td><Pill status={statusMap[r.status_id]} /></td>
              <td><div>{r.customer_name || "—"}</div><span className="sub">{phone(r.phone)}</span></td>
              <td className="st-items">{r.items.map((i, k) => (
                <div key={k} className={i.is_upsell ? "up" : ""}>{i.name} <span className="muted">×{i.qty} = {money(i.price * i.qty)}</span>{i.is_upsell && <span className="badge info">допродаж</span>}</div>
              ))}</td>
              <td className="num"><b>{money(r.total)}</b></td><td className={`num ${r.margin < 0 ? "neg" : ""}`}>{money(r.margin)}</td>
              <td>{r.payment}</td><td>{r.delivery}{r.ttn && <span className="sub mono">{r.ttn}</span>}</td>
              <td className="nowrap">{dt(r.created_at, true)}</td><td className="num">{r.confirm_secs == null ? "" : minutes(r.confirm_secs / 60)}</td>
              <td className="nowrap">{dt(r.shipped_at, true)}</td><td>{r.manager}</td>{has("office") && <td>{r.office}</td>}
              {has("site") && <td>{r.site}</td>}
              {utm && <td className="st-utm">{[r.utm_source, r.utm_medium, r.utm_campaign, r.utm_content, r.utm_term].filter(Boolean).join(" / ")}</td>}
              {extras.map((i) => <td key={i}>{r[`extra${i}` as "extra1"]}</td>)}
            </tr>
          ))}{!rows.length && <tr><td colSpan={14}><Empty>Немає замовлень</Empty></td></tr>}</tbody>
        </table>
      </div>
      {q.hasNextPage && <div className="st-more"><button className="btn" disabled={q.isFetchingNextPage} onClick={() => q.fetchNextPage()}>
        {q.isFetchingNextPage ? "Завантаження…" : `Показати ще (${rows.length} з ${total})`}</button></div>}
    </div>
  );
}

function SegmentsTab({ qkey, params, metrics }: { qkey: string; params: Record<string, string>; metrics: Record<string, string> }) {
  const [metric, setMetric] = useState("orders_total");
  const { data } = useQuery({ queryKey: ["stats-segments", qkey, metric], queryFn: () => api.get<StatsSegments>(`/stats/segments${qs({ ...params, metric })}`), placeholderData: (p) => p });
  const [hover, setHover] = useState<number | null>(null);
  const rate = metric === "upsell_rate" || metric === "return_rate";
  const buckets = data?.buckets ?? [];
  const val = (b: StatsSegments["buckets"][number]) => (metric === "upsell_rate" ? b.upsell_rate : metric === "return_rate" ? b.return_rate : b.orders);
  const max = Math.max(rate ? 10 : 1, ...buckets.map(val));
  const name = (b: StatsSegments["buckets"][number]) => (b.to == null ? `від ${money(b.from)}` : `${money(b.from)}–${money(b.to)}`);
  return (
    <div className="card">
      <div className="st-tabhead flat">
        <label className="st-sel"><select value={metric} onChange={(e) => setMetric(e.target.value)}>
          {Object.entries(metrics).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select><ChevronDown size={14} /></label>
        <span className="muted">Розподіл ваших замовлень за ціною — на який чек і офер покупці реагують найкраще{data?.step ? `, крок ${money(data.step)} ₴` : ""}</span>
      </div>
      {!data ? <Empty><Spinner /></Empty> : !buckets.length ? <Empty>Немає даних</Empty> : <>
        <div className="seg-chart" onMouseLeave={() => setHover(null)}>
          {buckets.map((b, i) => (
            <div key={i} className={`seg-col ${hover === i ? "hl" : ""}`} onMouseEnter={() => setHover(i)}>
              <div className="seg-bar" style={{ height: `${(val(b) / max) * 100}%` }} />
              <div className="seg-x">{b.to == null ? `${money(b.from)}+` : money(b.from)}</div>
            </div>
          ))}
          {hover != null && buckets[hover] && (
            <div className="seg-tip" style={{ left: `${((hover + 0.5) / buckets.length) * 100}%` }}>
              <b>{name(buckets[hover])} ₴</b><div>Замовлень: {buckets[hover].orders}</div>
              <div>З допродажем: {buckets[hover].upsell_rate}%</div><div>Відмов і повернень: {buckets[hover].return_rate}%</div>
            </div>
          )}
        </div>
        <div className="tablewrap"><table className="t dense st-table"><thead><tr><th>Діапазон, ₴</th><th className="num">Замовлень</th><th className="num">З допродажем</th>
          <th className="num">Отримано</th><th className="num">Відмови</th><th className="num">Відмов, %</th></tr></thead>
          <tbody>{buckets.filter((b) => b.orders).map((b, i) => <tr key={i}><td>{name(b)}</td><td className="num"><b>{b.orders}</b></td><td className="num">{b.upsell} <span className="muted">({b.upsell_rate}%)</span></td>
            <td className="num">{b.delivered}</td><td className="num">{b.refused}</td><td className="num">{b.delivered + b.refused ? `${b.return_rate}%` : "—"}</td></tr>)}</tbody></table></div>
      </>}
    </div>
  );
}

