// Список замовлень — щільна стрічка (UI-DESIGN §4.1–4.2, макет 05-zamovlennia.png).
// Шапка в один рядок, вкладки статусів («Несортовані» першою), фільтри-чипи в адресі сторінки, групи за днями, масові дії знизу.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AlarmClock, Ban, Bookmark, CalendarDays, Check, Copy, Download, Eye, KanbanSquare, List, Phone, Printer, Receipt, RefreshCw, Search, Truck, UserRound, X,
} from "lucide-react";
import { api, qs, ROOT } from "../lib/api";
import { errText, useDebounced, useMeta, useToast } from "../lib/app";
import { isoDay, money, phone } from "../lib/format";
import { PAY_ICONS } from "../components/payicons";
import { MarkIcon } from "../components/marks";
import type { OrderList, OrderRow } from "../lib/types";
import {
  BulkBar, Button, ChipSelect, ColumnsMenu, DenseTable, FilterChip, IconButton, MenuButton, PayCheck, Segmented, StatusPill, Tabs, Tag,
  useColumns, useOutside, type DenseCol, type TabItem,
} from "../components/ui";
import OrderModal from "./OrderCard";

const FILTERS = ["status", "q", "manager", "delivery", "src", "entity", "pm", "mark", "date_from", "date_to", "dup", "remind", "ttn"] as const;
type F = Record<(typeof FILTERS)[number], string>;
export const SOURCE_COLORS = ["#2E6BE6", "#DB2777", "#16A34A", "#D97706", "#7C3AED", "#0D9488", "#64748B", "#E11D48", "#0EA5E9", "#A16207"];
const CARRIER_SHORT: Record<string, string> = { novaposhta: "НП", ukrposhta: "Укрпошта", meest: "Meest", rozetka: "Rozetka", pickup: "Самовивіз" };
const DSTATE: Record<string, string> = { created: "var(--muted)", in_transit: "#6D5BD0", arrived: "var(--warn)", delivered: "var(--ok)", refused: "var(--bad)", returned: "var(--bad)" };

const initials = (n?: string) => (n || "").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
const hhmm = (iso?: string | null) => (iso ? new Date(iso).toLocaleTimeString("uk-UA", { hour: "2-digit", minute: "2-digit" }) : "");

// дата прямо в рядку замість рядків-груп за днями: «сьогодні 15:50», «учора 20:38», «29.10 20:38», «29.10.25 20:38»
function whenLabel(iso?: string | null) {
  if (!iso) return "—";
  const d = new Date(iso);
  const t = hhmm(iso);
  const today = isoDay(new Date());
  const y = new Date(); y.setDate(y.getDate() - 1);
  const day = isoDay(d);
  if (day === today) return `сьогодні ${t}`;
  if (day === isoDay(y)) return `учора ${t}`;
  const dd = String(d.getDate()).padStart(2, "0"), mm = String(d.getMonth() + 1).padStart(2, "0");
  return d.getFullYear() === new Date().getFullYear() ? `${dd}.${mm} ${t}` : `${dd}.${mm}.${String(d.getFullYear()).slice(2)} ${t}`;
}
const plural = (n: number, a: string, b: string, c: string) => (n % 10 === 1 && n % 100 !== 11 ? a : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? b : c);

export default function OrdersPage({ stage = "order" }: { stage?: "lead" | "order" }) {
  const base = stage === "lead" ? "/leads" : "/orders";
  const meta = useMeta();
  const nav = useNavigate();
  const { id } = useParams();
  const [sp, setSp] = useSearchParams();
  const toast = useToast();
  const qc = useQueryClient();
  const statuses = useMemo(() => Object.fromEntries(meta.statuses.map((s) => [s.id, s])), [meta.statuses]);
  const byCode = useMemo(() => Object.fromEntries(meta.statuses.map((s) => [s.code, s])), [meta.statuses]);
  const pm = useMemo(() => Object.fromEntries(meta.payment_methods.map((m) => [m.id, m])), [meta.payment_methods]);
  const marks = useMemo(() => Object.fromEntries(meta.marks.map((m) => [m.id, m])), [meta.marks]);
  const managers = useMemo(() => Object.fromEntries(meta.managers.map((m) => [m.id, m])), [meta.managers]);
  const sources = useMemo(() => Object.fromEntries(meta.order_sources.map((s, i) => [s.id, { ...s, color: SOURCE_COLORS[i % SOURCE_COLORS.length] }])), [meta.order_sources]);
  const entities = useMemo(() => Object.fromEntries(meta.legal_entities.map((e) => [e.id, e])), [meta.legal_entities]);

  const f = Object.fromEntries(FILTERS.map((k) => [k, sp.get(k) ?? ""])) as F;
  const unsorted = byCode.unsorted;
  const isUnsorted = stage === "order" && !!unsorted && f.status === String(unsorted.id);
  const [search, setSearch] = useState(f.q);
  const dq = useDebounced(search, 300);
  useEffect(() => { if (dq !== f.q) setF({ q: dq }); /* eslint-disable-next-line */ }, [dq]);
  const searchRef = useRef<HTMLInputElement>(null);

  function setF(patch: Partial<F>) {
    const next = new URLSearchParams(sp);
    Object.entries(patch).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    setSp(next, { replace: true });
  }
  const list = (k: keyof F) => (f[k] ? f[k].split(",") : []);
  const setList = (k: keyof F) => (v: string[]) => setF({ [k]: v.join(",") } as Partial<F>);

  const filterKey = stage + "|" + FILTERS.map((k) => f[k]).join("|");
  const sort = isUnsorted ? "old" : "new";
  const query = useInfiniteQuery({
    queryKey: ["orders", "list", filterKey],
    queryFn: ({ pageParam }) => api.get<OrderList>(`/orders${qs({
      ...f, stage, sort, limit: 100, counts: pageParam ? 0 : 1,
      before: sort === "new" && pageParam ? pageParam : undefined, after: sort === "old" && pageParam ? pageParam : undefined,
    })}`),
    initialPageParam: 0,
    getNextPageParam: (last) => last.next ?? undefined,
  });
  const rows: OrderRow[] = useMemo(() => query.data?.pages.flatMap((p) => p.items) ?? [], [query.data]);
  const head = query.data?.pages[0];
  const endReached = useCallback(() => { if (query.hasNextPage && !query.isFetchingNextPage) query.fetchNextPage(); }, [query]);

  // ---------------- вибір і масові дії
  const [sel, setSel] = useState<Set<number>>(new Set());
  useEffect(() => setSel(new Set()), [filterKey]);
  const bulk = useMutation({
    mutationFn: (body: { action: string; value?: string | number; ids?: number[] }) =>
      api.post<{ done: number; queued: number; errors: string[] }>("/orders/bulk", { ids: body.ids ?? [...sel], action: body.action, value: body.value }),
    onSuccess: (r) => {
      toast(r.queued ? `Поставлено в чергу: ${r.queued}. Результат з'явиться автоматично.` : `Оброблено: ${r.done}`);
      r.errors.slice(0, 5).forEach((e) => toast(e, "error"));
      setSel(new Set());
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["counters"] });
    },
    onError: (e) => toast(errText(e), "error"),
  });
  const accept = (ids: number[]) => { const c = byCode.confirmed; if (c) bulk.mutate({ action: "status", value: c.id, ids }); };

  // ---------------- клавіші: «/» — пошук у списку
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (e.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(t.tagName) && !document.querySelector(".win-backdrop, .modal")) {
        e.preventDefault(); searchRef.current?.focus();
      }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);

  // ---------------- вкладки
  const stageStatuses = meta.statuses.filter((s) => s.active && (s.stage ?? "order") === stage);
  const counts = head?.counts ?? {};
  const tabs: TabItem<string>[] = [
    ...(stage === "order" && unsorted && unsorted.active ? [{ key: String(unsorted.id), label: "Несортовані", count: counts[String(unsorted.id)] ?? 0, hot: true, color: unsorted.color }] : []),
    ...stageStatuses.filter((s) => s.code !== "unsorted").map((s) => ({ key: String(s.id), label: s.name, count: counts[String(s.id)] ?? 0, color: s.color })),
    { key: "", label: "Усі", count: head?.all ?? null },
  ];
  const cnt = (code: string) => (byCode[code] ? counts[String(byCode[code].id)] ?? 0 : 0);
  const summary = stage === "order"
    ? [[cnt("unsorted"), plural(cnt("unsorted"), "несортоване", "несортовані", "несортованих")], [cnt("confirmed"), "чекають відправки"], [cnt("shipped") + cnt("arrived"), "у дорозі"]]
    : [[cnt("new"), plural(cnt("new"), "новий", "нові", "нових")], [cnt("callback"), "передзвонити"], [cnt("no_answer"), "недодзвон"]];

  // ---------------- колонки
  const COLS: DenseCol<OrderRow>[] = [
    { key: "id", label: "№", width: "56px", render: (o) => {
      const due = o.remind_at && new Date(o.remind_at) <= new Date();
      return <span className="o-id">{due && <AlarmClock size={12} className="o-bell" aria-label="Нагадування настало" />}{o.id}</span>;
    } },
    { key: "customer", label: "Покупець", width: "minmax(110px, 1.3fr)", title: (o) => o.customer_name, render: (o) => (
      <span className="o-cust">
        <span className="ell">{o.customer_name || <span className="muted">без імені</span>}</span>
        {o.customer_group && /vip/i.test(o.customer_group.name) && <Tag kind="warn">VIP</Tag>}
        {o.duplicate_of_id && <Tag kind="warn" title={`Можливий дубль №${o.duplicate_of_id}`}>Дубль?</Tag>}
        {o.blacklisted && <Tag kind="bad" title="Покупець у чорному списку" icon={<Ban size={11} />}>ЧС</Tag>}
        {isUnsorted && o.no_stock && <Tag kind="bad" title="Товару не вистачає на складі">немає товару</Tag>}
      </span>
    ) },
    { key: "phone", label: "Телефон", width: "124px", render: (o) => <span className="nowrap num">{phone(o.phone)}</span> },
    { key: "items", label: "Товар", width: "minmax(92px, 1.2fr)", title: (o) => o.items.map((i) => `${i.name} × ${i.qty}`).join(", "), render: (o) => {
      const main = o.items.filter((i) => !i.upsell);
      const first = main[0] ?? o.items[0];
      const rest = o.items.length - 1;
      return <span className="o-items"><span className="ell">{first?.name ?? "—"}</span>{rest > 0 && <span className="o-more">+{rest}</span>}</span>;
    } },
    { key: "status", label: "Статус", width: "132px", render: (o) => (
      <span className="o-st"><StatusPill status={statuses[o.status_id]} />{o.mark_id && marks[o.mark_id] && <span title={marks[o.mark_id].name}><MarkIcon icon={marks[o.mark_id].icon} color={marks[o.mark_id].color} size={13} /></span>}</span>
    ) },
    { key: "pay", label: "Оплата", width: "minmax(80px, 0.9fr)", title: (o) => pm[o.payment_method_id ?? 0]?.name, render: (o) => {
      const m = pm[o.payment_method_id ?? 0];
      if (!m) return <span className="o-dot-txt muted"><i style={{ background: "var(--line)" }} />—</span>;
      return <span className="o-dot-txt"><i style={{ background: PAY_ICONS[m.icon || ""]?.color ?? "var(--muted)" }} /><span className="ell">{m.name}</span></span>;
    } },
    { key: "delivery", label: "Доставка", width: "minmax(100px, 1fr)", title: (o) => [meta.delivery_methods[o.delivery_method], o.city_name, o.warehouse_name, o.delivery_status].filter(Boolean).join(" · "), render: (o) => {
      if (!o.city_name && !o.ttn) return <span className="muted">не вибрано</span>;
      const wh = (o.warehouse_name.match(/№\s*\d+/) || [""])[0].replace(/\s/g, "");
      return (
        <span className="o-dlv">
          <span className="ell">{CARRIER_SHORT[o.delivery_method] ?? meta.delivery_methods[o.delivery_method]} · {o.city_name}{wh && `, ${wh}`}</span>
          {o.ttn && <i className="o-ds" style={{ background: DSTATE[o.delivery_state] ?? "var(--accent-line)" }} aria-label={meta.delivery_states[o.delivery_state] ?? "ТТН створено"} />}
        </span>
      );
    } },
    { key: "source", label: "Джерело", width: "minmax(64px, 0.7fr)", title: (o) => [sources[o.source_id ?? 0]?.name, o.utm_source].filter(Boolean).join(" · "), render: (o) => {
      const s = sources[o.source_id ?? 0];
      return s ? <span className="o-dot-txt"><i style={{ background: s.color }} /><span className="ell">{s.name}</span></span>
        : o.utm_source ? <span className="ell muted">{o.utm_source}</span> : <span className="muted">—</span>;
    } },
    { key: "manager", label: "Мен.", headTitle: "Менеджер", width: "36px", align: "center", title: (o) => managers[o.manager_id ?? 0]?.name ?? "Не призначено", render: (o) => (
      o.manager_id ? <span className="o-av">{initials(managers[o.manager_id]?.name)}</span> : <span className="muted">—</span>
    ) },
    { key: "time", label: "Дата", headTitle: "Коли додано", width: "104px", render: (o) => <span className="muted num nowrap">{whenLabel(o.created_at)}</span> },
    { key: "total", label: "Сума", width: "78px", align: "right", render: (o) => <b className="num">{money(o.total)} ₴</b> },
    { key: "pay_check", label: "Опл.", headTitle: "Перевірка оплати: чи ТТН відповідає виду оплати", width: "34px", align: "center", render: (o) => <PayCheck check={o.pay_check} /> },
    { key: "ttn", label: "ТТН", width: "128px", render: (o) => (o.ttn ? <span className="mono o-ttn">{o.ttn}</span> : <span className="muted">—</span>) },
    { key: "entity", label: "Юрособа", width: "minmax(110px, 0.8fr)", render: (o) => <span className="ell">{entities[o.legal_entity_id ?? 0]?.name ?? "—"}</span> },
    { key: "utm", label: "UTM", width: "minmax(100px, 0.8fr)", render: (o) => <span className="ell muted">{[o.utm_source, o.utm_campaign].filter(Boolean).join(" · ") || "—"}</span> },
  ];
  const ALL = COLS.map((c) => ({ key: c.key, label: typeof c.label === "string" ? c.label : c.key, locked: c.key === "id" }));
  const DEFAULT = ["id", "customer", "phone", "items", "status", "pay", "delivery", "source", "manager", "time", "total", "pay_check"];
  const colPrefs = useColumns(`${stage}s.columns`, ALL, DEFAULT);
  const cols = colPrefs.visible.map((k) => COLS.find((c) => c.key === k)!).filter(Boolean);


  const anyFilter = FILTERS.some((k) => k !== "status" && k !== "q" && f[k]);
  const exportUrl = `${ROOT}/classic/orders/export.csv${qs({ status: f.status, q: f.q, manager: f.manager, date_from: f.date_from, date_to: f.date_to, delivery: f.delivery })}`;
  const selectedIds = [...sel];

  return (
    <div className="page-list">
      <div className="list-head">
        <h1>{stage === "lead" ? "Ліди" : "Замовлення"}</h1>
        <span className="list-sum">{summary.map(([n, t], i) => <span key={i}>{i > 0 && " · "}<b>{n}</b> {t}</span>)}</span>
        <div className="list-acts">
          {stage === "order" && (
            <Segmented label="Вигляд" value="list" onChange={(k) => { if (k === "board") nav("/board"); }}
              items={[{ key: "list", label: "Стрічка", icon: <List size={14} /> }, { key: "board", label: "Дошка", icon: <KanbanSquare size={14} /> }]} />
          )}
          <ColumnsMenu all={ALL} visible={colPrefs.visible} onChange={colPrefs.set} onReset={colPrefs.reset} />
          <a className="btn" href={exportUrl}><Download size={15} />Експорт</a>
        </div>
      </div>

      <Tabs items={tabs} value={f.status} onChange={(k) => setF({ status: k })} label="Статуси" className="list-tabs" />

      <div className="chips-row">
        <DateChip from={f.date_from} to={f.date_to} onChange={(a, b) => setF({ date_from: a, date_to: b })} />
        <ChipSelect label="Менеджер" value={list("manager")} onChange={setList("manager")}
          options={[{ value: "none", label: "Не призначено" }, ...meta.managers.map((m) => ({ value: String(m.id), label: m.name }))]} />
        <ChipSelect label="Джерело" value={list("src")} onChange={setList("src")}
          options={meta.order_sources.filter((s) => s.active).map((s) => ({ value: String(s.id), label: s.name, color: sources[s.id]?.color }))} />
        {meta.legal_entities.length > 0 && (
          <ChipSelect label="Юрособа" value={list("entity")} onChange={setList("entity")} options={meta.legal_entities.map((e) => ({ value: String(e.id), label: e.name }))} />
        )}
        <ChipSelect label="Доставка" single value={list("delivery")} onChange={setList("delivery")}
          options={Object.entries(meta.delivery_methods).map(([k, n]) => ({ value: k, label: n }))} />
        <ChipSelect label="Оплата" value={list("pm")} onChange={setList("pm")}
          options={meta.payment_methods.map((m) => ({ value: String(m.id), label: m.name, color: PAY_ICONS[m.icon || ""]?.color }))} />
        {meta.marks.length > 0 && (
          <ChipSelect label="Позначки" value={list("mark")} onChange={setList("mark")}
            options={meta.marks.map((m) => ({ value: String(m.id), label: m.name, icon: <MarkIcon icon={m.icon} color={m.color} size={14} /> }))} />
        )}
        {f.dup && <FilterChip label="Дублі" value="Лише дублі" onClear={() => setF({ dup: "" })} />}
        {f.remind && <FilterChip label="Нагадування" value="Нагадування настало" onClear={() => setF({ remind: "" })} />}
        {f.ttn && <FilterChip label="ТТН" value={f.ttn === "none" ? "Без ТТН" : "З ТТН"} onClear={() => setF({ ttn: "" })} />}
        {anyFilter && <button className="btn quiet sm" onClick={() => setSp(f.status ? { status: f.status } : {}, { replace: true })}><X size={14} />Скинути</button>}
        {anyFilter && <SaveFilter section={stage === "lead" ? "leads" : "orders"} query={sp.toString()} />}
        <label className="list-search">
          <Search size={15} aria-hidden />
          <input ref={searchRef} type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Пошук у списку" aria-label="Пошук у списку (/)" />
        </label>
      </div>

      <DenseTable<OrderRow>
        label={stage === "lead" ? "Ліди" : "Замовлення"}
        rows={rows} cols={cols} rowKey={(o) => o.id}
        selected={sel} onSelect={setSel} current={id ? Number(id) : null}
        onOpen={(o) => nav(`${base}/${o.id}${window.location.search}`)}
        isLoading={query.isLoading} onEndReached={endReached}
        rowClass={(o) => (o.remind_at && new Date(o.remind_at) <= new Date() ? "due" : "")}
        actions={(o) => (<>
          {isUnsorted && <Button size={30} variant="soft" icon={Check} onClick={() => accept([o.id])}>Прийняти</Button>}
          {o.phone && <a className="icon-btn s28 quiet" href={`tel:+${o.phone.replace(/\D/g, "")}`} aria-label="Подзвонити" title="Подзвонити"><Phone size={15} /></a>}
          {o.ttn && <a className="icon-btn s28 quiet" href={`${ROOT}/api/orders/${o.id}/label`} target="_blank" rel="noreferrer" aria-label="Наклейка" title="Наклейка"><Printer size={15} /></a>}
          <IconButton size={28} quiet icon={Eye} label="Перегляд" onClick={() => nav(`${base}/${o.id}${window.location.search}`)} />
        </>)}
        empty={<div className="empty-state">
          <p>{anyFilter || f.q ? "За цими фільтрами нічого немає" : isUnsorted ? "Усі замовлення розібрано" : "Замовлень поки немає"}</p>
          {(anyFilter || f.q) && <button className="btn" onClick={() => { setSearch(""); setSp(f.status ? { status: f.status } : {}, { replace: true }); }}>Скинути фільтр</button>}
        </div>}
      />

      <BulkBar count={sel.size} onClear={() => setSel(new Set())}
        primary={isUnsorted
          ? <Button variant="primary" icon={Check} onClick={() => accept(selectedIds)}>Прийняти вибрані ({sel.size})</Button>
          : <Button variant="primary" icon={Truck} onClick={() => bulk.mutate({ action: "ttn" })}>Створити {sel.size} ТТН</Button>}>
        <MenuButton align="left" className="bulk-menu" button={({ open, toggle }) => <button className="btn quiet sm" aria-expanded={open} onClick={toggle}>Статус ▾</button>}>
          {(close) => meta.statuses.filter((s) => s.active).map((s) => (
            <button key={s.id} className="pop-item" onClick={() => { close(); bulk.mutate({ action: "status", value: s.id }); }}><StatusPill status={s} /></button>
          ))}
        </MenuButton>
        {meta.user.role !== "warehouse" && (
          <MenuButton align="left" className="bulk-menu" button={({ open, toggle }) => <button className="btn quiet sm" aria-expanded={open} onClick={toggle}>Менеджер ▾</button>}>
            {(close) => (<>
              {meta.managers.map((m) => <button key={m.id} className="pop-item" onClick={() => { close(); bulk.mutate({ action: "assign", value: m.id }); }}><UserRound size={15} />{m.name}</button>)}
              <button className="pop-item" onClick={() => { close(); bulk.mutate({ action: "assign", value: 0 }); }}><X size={15} />Зняти менеджера</button>
            </>)}
          </MenuButton>
        )}
        <button className="btn quiet sm" onClick={() => bulk.mutate({ action: "track" })}><RefreshCw size={14} />Оновити трекінг</button>
        {meta.checkbox_ready && <button className="btn quiet sm" onClick={() => bulk.mutate({ action: "fiscalize" })}><Receipt size={14} />Фіскалізувати</button>}
        <button className="btn quiet sm" onClick={() => { navigator.clipboard?.writeText(selectedIds.join(", ")); toast("Номери скопійовано"); }}><Copy size={14} />Номери</button>
      </BulkBar>

      {id && <OrderModal id={id} onClose={() => nav(`${base}${window.location.search}`)} onOpen={(oid) => nav(`${base}/${oid}${window.location.search}`)}
        ids={rows.map((r) => r.id)} />}
    </div>
  );
}

// ---------------------------------------------------------------- чип дат: готові відрізки й свій період
function DateChip({ from, to, onChange }: { from: string; to: string; onChange: (a: string, b: string) => void }) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLSpanElement>(null);
  useOutside(box, () => setOpen(false), open);
  const today = new Date();
  const d = (shift: number) => { const x = new Date(today); x.setDate(x.getDate() - shift); return isoDay(x); };
  const monthStart = isoDay(new Date(today.getFullYear(), today.getMonth(), 1));
  const presets: [string, string, string][] = [
    ["Сьогодні", d(0), d(0)], ["Сьогодні й учора", d(1), d(0)], ["7 днів", d(6), d(0)], ["30 днів", d(29), d(0)], ["Цей місяць", monthStart, d(0)],
  ];
  const cur = presets.find((p) => p[1] === from && p[2] === to);
  const label = cur ? cur[0] : from || to ? `${from || "…"} — ${to || "…"}` : undefined;
  return (
    <span className="chip-sel" ref={box}>
      <FilterChip label="Дата" value={label} icon={<CalendarDays size={13} />} onClick={() => setOpen((o) => !o)} onClear={() => onChange("", "")} />
      {open && (
        <div className="pop chip-pop date-pop">
          {presets.map(([n, a, b]) => (
            <button key={n} className={`pop-item${cur?.[0] === n ? " on" : ""}`} onClick={() => { onChange(a, b); setOpen(false); }}>
              <span style={{ flex: 1 }}>{n}</span>{cur?.[0] === n && <Check size={14} />}
            </button>
          ))}
          <div className="date-own">
            <span className="lbl">Свій період</span>
            <div><input type="date" value={from} onChange={(e) => onChange(e.target.value, to)} aria-label="Від" /><input type="date" value={to} onChange={(e) => onChange(from, e.target.value)} aria-label="До" /></div>
          </div>
        </div>
      )}
    </span>
  );
}

// ---------------------------------------------------------------- зберегти поточний фільтр у бокову панель
function SaveFilter({ section, query }: { section: string; query: string }) {
  const qc = useQueryClient();
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [color, setColor] = useState(SOURCE_COLORS[0]);
  const box = useRef<HTMLSpanElement>(null);
  useOutside(box, () => setOpen(false), open);
  const save = useMutation({
    mutationFn: () => api.post("/saved-filters", { name, color, section, query }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["saved-filters"] }); qc.invalidateQueries({ queryKey: ["counters"] }); setOpen(false); setName(""); toast("Фільтр збережено в меню"); },
    onError: (e) => toast(errText(e), "error"),
  });
  return (
    <span className="chip-sel" ref={box}>
      <button className="btn quiet sm" onClick={() => setOpen((o) => !o)}><Bookmark size={14} />Зберегти</button>
      {open && (
        <form className="pop chip-pop save-pop" onSubmit={(e) => { e.preventDefault(); if (name.trim()) save.mutate(); }}>
          <label className="lbl" htmlFor="sf-name">Назва фільтра</label>
          <input id="sf-name" autoFocus value={name} onChange={(e) => setName(e.target.value)} placeholder="Напр., Чекають ТТН" maxLength={80} />
          <div className="sf-colors" role="radiogroup" aria-label="Колір мітки">
            {SOURCE_COLORS.slice(0, 7).map((c) => (
              <button key={c} type="button" role="radio" aria-checked={c === color} className={c === color ? "on" : ""} style={{ background: c }} onClick={() => setColor(c)} aria-label={c} />
            ))}
          </div>
          <Button type="submit" variant="primary" size={30} disabled={!name.trim() || save.isPending}>Зберегти в меню</Button>
        </form>
      )}
    </span>
  );
}
