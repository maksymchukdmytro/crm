// Список замовлень (макети v20, рішення власника 03.11): три вигляди на ПК — «Таблиця», «Картки» (щільніші за макет) і «Скринька»
// (вузький список ліворуч + картка праворуч без вікна); «Дошка» — окрема сторінка. Шапка: назва з підсумком, пошук, фільтри,
// вигляд і «+ Замовлення»; під нею вкладки статусів, а праворуч — лише ввімкнені фільтри (усі — під кнопкою фільтрів).
import { memo, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlarmClock, Ban, Bookmark, CalendarDays, Check, ChevronDown, CircleAlert, Copy, Crown, Download, Eye, Inbox, KanbanSquare, LayoutGrid, List, ListFilter, MessageCircle, MessageSquare, Package, PackageX, Phone, Plus, Printer, Receipt, ReceiptText, RefreshCw, Search, Send, Trash2, Truck, UserRound, Wallet, X,
} from "lucide-react";
import { api, qs, ROOT } from "../lib/api";
import { errText, useDebounced, useMeta, useToast } from "../lib/app";
import { isoDay, money, phone } from "../lib/format";
import { PAY_ICONS, PayIcon } from "../components/payicons";
import { MarkIcon } from "../components/marks";
import type { Order, OrderList, OrderRow, Status } from "../lib/types";
import {
  BulkBar, Button, ChipSelect, ColumnsMenu, DenseTable, FilterChip, IconButton, MenuButton, MobileActs, PayCheck, RoundButton, Segmented, Sheet, StatusPill, Tabs,
  useColumns, useMobile, useOutside, type DenseCol, type TabItem, EmptyState, Floating, HoverCard } from "../components/ui";
import OrderModal, { openTtnOnLoad } from "./OrderCard";

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
// коротко для таблиці, карток і скриньки: «17:10» сьогодні, «учора», «28.10», «28.10.25»
function shortWhen(iso?: string | null) {
  if (!iso) return "—";
  const d = new Date(iso);
  const y = new Date(); y.setDate(y.getDate() - 1);
  const day = isoDay(d);
  if (day === isoDay(new Date())) return hhmm(iso);
  if (day === isoDay(y)) return "учора";
  const dd = String(d.getDate()).padStart(2, "0"), mm = String(d.getMonth() + 1).padStart(2, "0");
  return d.getFullYear() === new Date().getFullYear() ? `${dd}.${mm}` : `${dd}.${mm}.${String(d.getFullYear()).slice(2)}`;
}
type View = "table" | "cards" | "inbox";
const VIEW_KEY = "crm-orders-view";
const readView = (): View => { try { const v = localStorage.getItem(VIEW_KEY); return v === "cards" || v === "inbox" ? v : "table"; } catch { return "table"; } };

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
  // статус прямо з таблиці: той самий захист складу, що в картці; для відмови з причинами — причина
  const setStatus = async (o: OrderRow, sid: number, reasonId?: number) => {
    const s = meta.statuses.find((x) => x.id === sid);
    if (!s || sid === o.status_id) return;
    const STOCK: Record<string, string> = { reserve: "товар буде зарезервовано", ship: "товар буде списано зі складу", return: "товар повернеться на залишок", release: "резерв буде знято" };
    const warn = STOCK[s.stock_action ?? ""];
    if (warn && !window.confirm(`№${o.id} → «${s.name}»: ${warn}. Продовжити?`)) return;
    try {
      if (reasonId) {
        const full = await api.get<Order>(`/orders/${o.id}`);
        await api.patch(`/orders/${o.id}`, { status_id: sid, reason_id: reasonId, version: full.version });
        toast(`№${o.id}: ${s.name}`);
        qc.invalidateQueries({ queryKey: ["orders"] }); qc.invalidateQueries({ queryKey: ["counters"] });
      } else bulk.mutate({ action: "status", value: sid, ids: [o.id] });
    } catch (e) { toast(errText(e), "error"); }
  };
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

  // ---------------- колонки (макет v26): текстом — №, покупець, товар, статус, дата, сума; решта — значками з підказкою
  const COLS: DenseCol<OrderRow>[] = [
    { key: "id", label: "№", width: "48px", render: (o) => <span className="o-id">{o.id}</span> },
    { key: "customer", label: "Покупець", width: "minmax(130px, 1.3fr)", title: (o) => o.customer_name, render: (o) => {
      const due = !!o.remind_at && new Date(o.remind_at) <= new Date();
      return (
        <span className="o-cust">
          <span className="ell">{o.customer_name || <span className="muted">без імені</span>}</span>
          <Signals o={o} due={due} unsorted={isUnsorted} />
        </span>
      );
    } },
    { key: "items", label: "Товар", width: "minmax(130px, 1.4fr)", title: (o) => o.items.map((i) => `${i.name} × ${i.qty}`).join(", "), render: (o) => {
      const main = o.items.filter((i) => !i.upsell);
      const first = main[0] ?? o.items[0];
      const rest = o.items.length - 1;
      return (
        <span className="o-items"><span className="ell">{first?.name ?? "—"}</span>
          {rest > 0 && <HoverCard label={`Усі товари замовлення №${o.id}`} triggerClass="o-more" width={300} trigger={`+${rest}`}>
            <GoodsCard o={o} />
          </HoverCard>}
        </span>
      );
    } },
    { key: "status", label: "Статус", width: "minmax(110px, 136px)", render: (o) => (
      <span className="o-st"><StatusMenu o={o} statuses={stageStatuses} current={statuses[o.status_id]} onPick={(sid) => setStatus(o, sid)} />
        {o.mark_id && marks[o.mark_id] && <span title={marks[o.mark_id].name}><MarkIcon icon={marks[o.mark_id].icon} color={marks[o.mark_id].color} size={13} /></span>}</span>
    ) },
    { key: "pay", mobile: "hide", label: <Wallet size={14} aria-label="Оплата" />, headTitle: "Оплата", width: "34px", align: "center", render: (o) => {
      const m = pm[o.payment_method_id ?? 0];
      const bad = o.pay_check?.state === "bad";
      return (
        <HoverCard label={`Оплата: ${m?.name ?? "не вибрано"}`} triggerClass={`o-ic${bad ? " bad" : ""}`} width={270}
          trigger={m ? <PayIcon icon={m.icon} image={m.image} size={20} /> : <span className="o-none" aria-hidden>—</span>}>
          <div className="hc-t1">Оплата</div>
          <div className="hc-row">{m ? <PayIcon icon={m.icon} image={m.image} size={22} /> : null}<b>{m?.name ?? "Вид оплати не вибрано"}</b></div>
          <div className="hc-kv"><span>Сума</span><b className="num">{money(o.total)} ₴</b></div>
          <div className="hc-kv"><span>При отриманні</span><b className="num">{money(o.cod_amount)} ₴</b></div>
          {o.pay_check && <div className={`hc-note ${o.pay_check.state}`}>{o.pay_check.text}</div>}
        </HoverCard>
      );
    } },
    { key: "delivery", label: <Truck size={14} aria-label="Доставка" />, headTitle: "Доставка", width: "56px", render: (o) => {
      if (!o.city_name && !o.ttn) return <span className="o-none" title={o.delivery_method === "pickup" ? "Самовивіз" : "Доставку не вибрано"}>{o.delivery_method === "pickup" ? "Сам." : "—"}</span>;
      return (
        <HoverCard label={`Доставка: ${[o.city_name, o.warehouse_name].filter(Boolean).join(", ")}`} triggerClass="o-dlv-t" width={300}
          trigger={<><CarrierBadge method={o.delivery_method} />{<i className="o-ds" style={{ background: o.ttn ? DSTATE[o.delivery_state] ?? "var(--accent-line)" : "var(--line)" }} />}</>}>
          <DeliveryCard o={o} name={meta.delivery_methods[o.delivery_method] ?? o.delivery_method} state={meta.delivery_states[o.delivery_state]} />
        </HoverCard>
      );
    } },
    { key: "source", mobile: "hide", label: "Дж.", headTitle: "Джерело", width: "26px", align: "center", title: (o) => [sources[o.source_id ?? 0]?.name, o.utm_source].filter(Boolean).join(" · ") || "Джерело не вказано", render: (o) => {
      const s = sources[o.source_id ?? 0];
      return <i className="o-src" style={{ background: s?.color ?? (o.utm_source ? "var(--faint)" : "var(--line)") }} />;
    } },
    { key: "manager", mobile: "hide", label: "М.", headTitle: "Менеджер", width: "28px", align: "center", title: (o) => managers[o.manager_id ?? 0]?.name ?? "Не призначено", render: (o) => (
      o.manager_id ? <span className="o-av">{initials(managers[o.manager_id]?.name)}</span> : <span className="muted">—</span>
    ) },
    { key: "time", label: "Дата", headTitle: "Коли додано", width: "50px", title: (o) => whenLabel(o.created_at), render: (o) => <span className="muted num nowrap">{shortWhen(o.created_at)}</span> },
    { key: "total", mobile: "end", label: "Сума", width: "78px", align: "right", render: (o) => <b className="num">{money(o.total)} ₴</b> },
    { key: "call", mobile: "hide", label: <Phone size={13} aria-label="Телефон" />, headTitle: "Телефон", width: "32px", align: "center", render: (o) => (
      o.phone ? <HoverCard label={`Телефон ${phone(o.phone)}`} triggerClass="o-ic o-call" width={290} trigger={<Phone size={14} />}>
        {() => <PhoneCard o={o} />}
      </HoverCard> : <span className="o-none">—</span>
    ) },
    // додаткові (вмикаються в «Колонки»)
    { key: "phone", mobile: "hide", label: "Телефон", width: "124px", render: (o) => <span className="nowrap num">{phone(o.phone)}</span> },
    { key: "address", mobile: "hide", label: "Адреса", width: "minmax(110px, 1fr)", title: (o) => [o.city_name, o.warehouse_name].filter(Boolean).join(", "), render: (o) => <span className="ell muted">{[o.city_name, (o.warehouse_name.match(/№\s*\d+/) || [""])[0]].filter(Boolean).join(", ") || "—"}</span> },
    { key: "pay_check", mobile: "hide", label: "Опл.", headTitle: "Перевірка оплати: чи ТТН відповідає виду оплати", width: "34px", align: "center", render: (o) => <PayCheck check={o.pay_check} /> },
    { key: "ttn", mobile: "hide", label: "ТТН", width: "128px", render: (o) => (o.ttn ? <span className="mono o-ttn">{o.ttn}</span> : <span className="muted">—</span>) },
    { key: "entity", mobile: "hide", label: "Юрособа", width: "minmax(110px, 0.8fr)", render: (o) => <span className="ell">{entities[o.legal_entity_id ?? 0]?.name ?? "—"}</span> },
    { key: "utm", mobile: "hide", label: "UTM", width: "minmax(100px, 0.8fr)", render: (o) => <span className="ell muted">{[o.utm_source, o.utm_campaign].filter(Boolean).join(" · ") || "—"}</span> },
  ];
  const ALL = COLS.map((c) => ({ key: c.key, label: c.headTitle ?? (typeof c.label === "string" ? c.label : c.key), locked: c.key === "id" }));
  const DEFAULT = ["id", "customer", "items", "status", "pay", "delivery", "source", "manager", "time", "total", "call"];
  const colPrefs = useColumns(`${stage}s.columns2`, ALL, DEFAULT);
  const cols = colPrefs.visible.map((k) => COLS.find((c) => c.key === k)!).filter(Boolean);


  // телефон (мобільна v2): картка — статус і позначки, №·час; покупець і сума; товар і доставка
  const mobileCard = (o: OrderRow) => {
    const due = o.remind_at && new Date(o.remind_at) <= new Date();
    const main = o.items.filter((i) => !i.upsell);
    const first = main[0] ?? o.items[0];
    const rest = o.items.length - 1;
    const day = isoDay(new Date(o.created_at ?? Date.now())) === isoDay(new Date());
    const warn = o.blacklisted ? "Покупець у чорному списку" : o.no_stock ? "Товару не вистачає на складі" : o.duplicate_of_id ? `Можливий дубль №${o.duplicate_of_id}` : "";
    const mk = o.mark_id ? marks[o.mark_id] : null;
    return (<>
      <div className="mc-top">
        <StatusPill status={statuses[o.status_id]} />
        {warn && <span className={`mc-flag ${o.blacklisted || o.no_stock ? "bad" : "warn"}`} title={warn} aria-label={warn}><CircleAlert size={14} /></span>}
        {due && <span className="mc-flag bad" title="Нагадування настало" aria-label="Нагадування настало"><AlarmClock size={14} /></span>}
        {mk && <span className="mc-flag" style={{ background: `color-mix(in srgb, ${mk.color} 14%, white)` }} title={mk.name}><MarkIcon icon={mk.icon} color={mk.color} size={13} /></span>}
        <span className="mc-meta">№{o.id} · {day ? hhmm(o.created_at) : whenLabel(o.created_at)}</span>
      </div>
      <div className="mc-name"><b>{o.customer_name || <span className="muted">без імені</span>}</b><span className="sum">{money(o.total)} <small>₴</small></span></div>
      <div className="mc-sep" />
      <div className="mc-row">
        <span className="mc-thumb"><Package size={14} /></span>
        <span className="mc-goods">{first?.name ?? "—"}{rest > 0 && <span className="more"> +{rest}</span>}</span>
        {o.delivery_method === "novaposhta" && (o.city_name || o.ttn) ? <span className="np-b" title={o.city_name}>НП</span>
          : o.city_name || o.ttn ? <span className="mc-muted">{CARRIER_SHORT[o.delivery_method] ?? meta.delivery_methods[o.delivery_method]}</span>
          : <span className="mc-muted">без доставки</span>}
      </div>
    </>);
  };

  const anyFilter = FILTERS.some((k) => k !== "status" && k !== "q" && f[k]);
  const exportUrl = `${ROOT}/api/orders/export.csv${qs({ status: f.status, q: f.q, manager: f.manager, date_from: f.date_from, date_to: f.date_to, delivery: f.delivery })}`;
  const selectedIds = [...sel];
  const [sheet, setSheet] = useState(false);

  // ---------------- вигляд (лише ПК і лише замовлення): таблиця / картки / скринька
  const mobile = useMobile();
  const [viewPref, setViewPref] = useState<View>(readView);
  const view: View = mobile || stage !== "order" ? "table" : viewPref;
  const pickView = (k: string) => {
    if (k === "board") { nav("/board"); return; }
    const v = k as View;
    setViewPref(v);
    try { localStorage.setItem(VIEW_KEY, v); } catch { /* приватне вікно — без запам'ятовування */ }
    if (v !== "inbox" && id) nav(`${base}${window.location.search}`, { replace: true });
  };
  const [showF, setShowF] = useState(false);
  const allFilters = mobile || showF;
  const open = (oid: number) => nav(`${base}/${oid}${window.location.search}`);
  const openTtn = (oid: number) => { openTtnOnLoad(oid); open(oid); };
  const smsTtn = useMutation({
    mutationFn: (oid: number) => api.post(`/orders/${oid}/sms-ttn`, {}),
    onSuccess: () => toast("SMS з номером ТТН поставлено в чергу"),
    onError: (e) => toast(errText(e), "error"),
  });

  // скринька: завжди вибрано замовлення — перше в списку, а після зміни вкладки чи фільтра — знову перше
  const inboxKey = useRef("");
  useEffect(() => {
    if (view !== "inbox" || query.isLoading || id === "new") return;
    const changed = inboxKey.current !== filterKey;
    if (!rows.length) { inboxKey.current = filterKey; return; }
    if (!id || (changed && inboxKey.current)) nav(`${base}/${rows[0].id}${window.location.search}`, { replace: true });
    inboxKey.current = filterKey;
  }, [view, rows, id, filterKey, query.isLoading]); // eslint-disable-line react-hooks/exhaustive-deps

  // скринька: вибране завжди видно в списку, а біля кінця завантаженого — догружаємо наступну сотню, щоб J не впирався
  const ibList = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (view !== "inbox" || !id) return;
    ibList.current?.querySelector<HTMLElement>(".ib-item.on")?.scrollIntoView({ block: "nearest" });
    const i = rows.findIndex((r) => r.id === Number(id));
    if (i >= 0 && i >= rows.length - 5) endReached();
  }, [view, id, rows.length]); // eslint-disable-line react-hooks/exhaustive-deps

  // дія в картці за станом: прийняти → ТТН → нагадати SMS → відкрити
  const cardAction = (o: OrderRow) => {
    const code = statuses[o.status_id]?.code;
    if (code === "unsorted" && byCode.confirmed?.active) return <button type="button" className="ocd-go p" onClick={(e) => { e.stopPropagation(); accept([o.id]); }}><Check size={15} />Прийняти</button>;
    if (code === "confirmed" && !o.ttn && o.delivery_method !== "pickup") return <button type="button" className="ocd-go s" onClick={(e) => { e.stopPropagation(); openTtn(o.id); }}><Truck size={15} />ТТН</button>;
    if (code === "arrived" && o.ttn) return <button type="button" className="ocd-go s" title="Надіслати покупцю SMS з номером ТТН" disabled={smsTtn.isPending} onClick={(e) => { e.stopPropagation(); smsTtn.mutate(o.id); }}><MessageSquare size={15} />SMS</button>;
    return <button type="button" className="ocd-go" onClick={(e) => { e.stopPropagation(); open(o.id); }}><Eye size={15} />Відкрити</button>;
  };
  const goodsOf = (o: OrderRow) => {
    const main = o.items.filter((i) => !i.upsell);
    return { first: (main[0] ?? o.items[0])?.name ?? "—", rest: o.items.length - 1 };
  };
  const dlvShort = (o: OrderRow) => {
    if (!o.city_name && !o.ttn) return <span className="ocd-muted">{o.delivery_method === "pickup" ? "Самовивіз" : "без доставки"}</span>;
    const wh = (o.warehouse_name.match(/№\s*\d+/) || [""])[0].replace(/\s/g, "");
    if (o.delivery_method === "novaposhta") return <span className="ocd-dlv"><span className="o-np">НП</span><span className="ell">{o.city_name}{wh && `, ${wh}`}</span></span>;
    return <span className="ocd-muted ell">{CARRIER_SHORT[o.delivery_method] ?? meta.delivery_methods[o.delivery_method]}</span>;
  };

  // ---------------- фільтри: усі (під кнопкою) або лише ввімкнені (праворуч від вкладок)
  const on = (k: keyof F) => allFilters || !!f[k];
  const filterChips = (<>
    {(allFilters || f.date_from || f.date_to) && <DateChip from={f.date_from} to={f.date_to} onChange={(a, b) => setF({ date_from: a, date_to: b })} />}
    {on("manager") && <ChipSelect label="Менеджер" value={list("manager")} onChange={setList("manager")}
      options={[{ value: "none", label: "Не призначено" }, ...meta.managers.map((m) => ({ value: String(m.id), label: m.name }))]} />}
    {on("src") && <ChipSelect label="Джерело" value={list("src")} onChange={setList("src")}
      options={meta.order_sources.filter((s) => s.active).map((s) => ({ value: String(s.id), label: s.name, color: sources[s.id]?.color }))} />}
    {meta.legal_entities.length > 0 && on("entity") && (
      <ChipSelect label="Юрособа" value={list("entity")} onChange={setList("entity")} options={meta.legal_entities.map((e) => ({ value: String(e.id), label: e.name }))} />
    )}
    {on("delivery") && <ChipSelect label="Доставка" single value={list("delivery")} onChange={setList("delivery")}
      options={Object.entries(meta.delivery_methods).map(([k, n]) => ({ value: k, label: n }))} />}
    {on("pm") && <ChipSelect label="Оплата" value={list("pm")} onChange={setList("pm")}
      options={meta.payment_methods.map((m) => ({ value: String(m.id), label: m.name, color: PAY_ICONS[m.icon || ""]?.color }))} />}
    {meta.marks.length > 0 && on("mark") && (
      <ChipSelect label="Позначки" value={list("mark")} onChange={setList("mark")}
        options={meta.marks.map((m) => ({ value: String(m.id), label: m.name, icon: <MarkIcon icon={m.icon} color={m.color} size={14} /> }))} />
    )}
    {f.dup && <FilterChip label="Дублі" value="Лише дублі" onClear={() => setF({ dup: "" })} />}
    {f.remind && <FilterChip label="Нагадування" value="Нагадування настало" onClear={() => setF({ remind: "" })} />}
    {f.ttn && <FilterChip label="ТТН" value={f.ttn === "none" ? "Без ТТН" : "З ТТН"} onClear={() => setF({ ttn: "" })} />}
  </>);
  const searchBox = (
    <label className="list-search">
      <Search size={15} aria-hidden />
      <input ref={searchRef} type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Пошук у списку" aria-label="Пошук у списку (/)" />
      {!mobile && !search && <kbd aria-hidden>/</kbd>}
    </label>
  );
  // картка в сітці й рядок скриньки: малюються через Tile (memo), тож догрузка ще 100 замовлень не перемальовує тисячі вже показаних
  const cardTile = (o: OrderRow, cur: boolean) => {
    const due = o.remind_at && new Date(o.remind_at) <= new Date();
    const warn = o.blacklisted ? "Покупець у чорному списку" : o.no_stock ? "Товару не вистачає на складі" : o.duplicate_of_id ? `Можливий дубль №${o.duplicate_of_id}` : "";
    const mk = o.mark_id ? marks[o.mark_id] : null;
    const g = goodsOf(o);
    return (
      <article role="listitem" tabIndex={0} className={`ocd${cur ? " cur" : ""}${due ? " due" : ""}`}
        onClick={() => open(o.id)} onKeyDown={(e) => { if (e.key === "Enter" && e.target === e.currentTarget) open(o.id); }}>
        <div className="ocd-top">
          <StatusPill status={statuses[o.status_id]} />
          {warn && <span className={`mc-flag ${o.blacklisted || o.no_stock ? "bad" : "warn"}`} title={warn} aria-label={warn}><CircleAlert size={13} /></span>}
          {due && <span className="mc-flag bad" title="Нагадування настало" aria-label="Нагадування настало"><AlarmClock size={13} /></span>}
          {mk && <span className="mc-flag" style={{ background: `color-mix(in srgb, ${mk.color} 14%, white)` }} title={mk.name}><MarkIcon icon={mk.icon} color={mk.color} size={12} /></span>}
          <span className="ocd-meta" title={whenLabel(o.created_at)}>№{o.id} · {shortWhen(o.created_at)}</span>
        </div>
        <div className="ocd-name"><b title={o.customer_name}>{o.customer_name || <span className="muted">без імені</span>}</b><span className="sum">{money(o.total)} ₴</span></div>
        <div className="ocd-row">
          <span className="ocd-thumb" aria-hidden><Package size={13} /></span>
          <span className="ocd-goods" title={o.items.map((i) => `${i.name} × ${i.qty}`).join(", ")}>{g.first}{g.rest > 0 && <span className="more"> +{g.rest}</span>}</span>
          {dlvShort(o)}
        </div>
        <div className="ocd-acts">
          {o.phone ? <a className="ocd-go ph" href={`tel:+${o.phone.replace(/\D/g, "")}`} onClick={(e) => e.stopPropagation()} aria-label={`Подзвонити ${phone(o.phone)}`} title={phone(o.phone)}><Phone size={15} /></a>
            : <span className="ocd-go ph off" aria-hidden><Phone size={15} /></span>}
          {cardAction(o)}
        </div>
      </article>
    );
  };
  const inboxItem = (o: OrderRow, cur: boolean) => {
    const st = statuses[o.status_id];
    const g = goodsOf(o);
    return (
      <button type="button" role="option" aria-selected={cur} className={`ib-item${cur ? " on" : ""}`} onClick={() => nav(`${base}/${o.id}${window.location.search}`, { replace: true })}>
        <span className="r1"><i style={{ background: st?.color ?? "var(--faint)" }} title={st?.name} /><b>{o.customer_name || "без імені"}</b><span className="s">{money(o.total)} ₴</span></span>
        <span className="r2"><span className="no">№{o.id}</span><span className="ell">{g.first}{g.rest > 0 && ` +${g.rest}`}</span><span className="t">{shortWhen(o.created_at)}</span></span>
      </button>
    );
  };
  const emptyBox = (
    <div className="empty-state">
      {!(anyFilter || f.q) && !isUnsorted ? <EmptyState icon={ReceiptText} title="Замовлень поки немає" text="Заявки з лендингів і маркетплейсів з'являться тут самі. Або створіть замовлення вручну"
        action={{ label: "Нове замовлення", icon: Plus, onClick: () => nav("/orders/new") }} /> : <p>{anyFilter || f.q ? "За цими фільтрами нічого немає" : "Усі замовлення розібрано"}</p>}
      {(anyFilter || f.q) && <button className="btn" onClick={() => { setSearch(""); setSp(f.status ? { status: f.status } : {}, { replace: true }); }}>Скинути фільтр</button>}
    </div>
  );

  return (
    <div className={`page-list page-${stage}s v-${view}`}>
      <MobileActs><RoundButton icon={ListFilter} label="Фільтри" dot={anyFilter} onClick={() => setSheet(true)} /></MobileActs>
      {sheet && <FilterSheet f={f} onClose={() => setSheet(false)} sources={sources}
        onApply={(patch) => { setF(patch); setSheet(false); }} onReset={() => { setSp(f.status ? { status: f.status } : {}, { replace: true }); setSheet(false); }} />}
      <div className="list-head">
        <div className="lh-t">
          <h1>{stage === "lead" ? "Ліди" : "Замовлення"}</h1>
          <span className="list-sum">{summary.map(([n, t], i) => <span key={i}>{i > 0 && " · "}<b>{n}</b> {t}</span>)}</span>
        </div>
        <div className="list-acts">
          {searchBox}
          <button type="button" className={`lh-filter${showF ? " on" : ""}`} aria-label="Усі фільтри" title="Усі фільтри" aria-expanded={showF} onClick={() => setShowF((x) => !x)}>
            <ListFilter size={18} />{anyFilter && <span className="dot" />}
          </button>
          {stage === "order" && (
            <Segmented label="Вигляд" value={view} onChange={pickView}
              items={[{ key: "table", label: <span className="seg-l">Таблиця</span>, title: "Таблиця", icon: <List size={14} /> },
                { key: "cards", label: <span className="seg-l">Картки</span>, title: "Картки", icon: <LayoutGrid size={14} /> },
                { key: "inbox", label: <span className="seg-l">Скринька</span>, title: "Скринька: список ліворуч, замовлення праворуч", icon: <Inbox size={14} /> },
                { key: "board", label: <span className="seg-l">Дошка</span>, title: "Дошка", icon: <KanbanSquare size={14} /> }]} />
          )}
          <Button variant="primary" icon={Plus} onClick={() => nav(`${base}/new${window.location.search}`)}>{stage === "lead" ? "Лід" : "Замовлення"}</Button>
        </div>
      </div>

      <div className="list-tabsrow">
        <Tabs items={tabs} value={f.status} onChange={(k) => setF({ status: k })} label="Статуси" className="list-tabs" />
        {!allFilters && anyFilter && <div className="lh-active">{filterChips}</div>}
      </div>

      {allFilters && (
        <div className="chips-row">
          {filterChips}
          {anyFilter && <button className="btn quiet sm" onClick={() => setSp(f.status ? { status: f.status } : {}, { replace: true })}><X size={14} />Скинути</button>}
          {anyFilter && <SaveFilter section={stage === "lead" ? "leads" : "orders"} query={sp.toString()} />}
          {mobile ? searchBox : (
            <span className="chips-end">
              {view === "table" && <ColumnsMenu all={ALL} visible={colPrefs.visible} onChange={colPrefs.set} onReset={colPrefs.reset} />}
              <a className="btn sm" href={exportUrl}><Download size={14} />Експорт</a>
            </span>
          )}
        </div>
      )}

      {view === "cards" ? (
        <div className="ocd-wrap">
          {query.isLoading ? <div className="ocd-grid">{Array.from({ length: 12 }, (_, i) => <div key={i} className="ocd sk"><span className="skel" /><span className="skel" /><span className="skel" /></div>)}</div>
            : !rows.length ? <div className="dense-empty">{emptyBox}</div> : (
              <div className="ocd-grid" role="list" aria-label="Замовлення">
                {rows.map((o) => <Tile key={o.id} o={o} cur={!!id && Number(id) === o.id} render={cardTile} />)}
              </div>
            )}
          <EndSentinel onEnd={endReached} busy={query.isFetchingNextPage} more={!!query.hasNextPage} n={rows.length} />
        </div>
      ) : view === "inbox" ? (
        <div className="ib">
          <div className="ib-list" ref={ibList} role="listbox" aria-label="Замовлення">
            {query.isLoading ? Array.from({ length: 8 }, (_, i) => <div key={i} className="ib-item sk"><span className="skel" /><span className="skel" /></div>)
              : !rows.length ? <div className="ib-empty">{emptyBox}</div>
                : rows.map((o) => <Tile key={o.id} o={o} cur={!!id && Number(id) === o.id} render={inboxItem} />)}
            <EndSentinel onEnd={endReached} busy={query.isFetchingNextPage} more={!!query.hasNextPage} n={rows.length} />
          </div>
          <div className="ib-pane">
            {id && id !== "new" ? <OrderModal key={id} id={id} embed ids={rows.map((r) => r.id)}
              onClose={() => nav(`${base}${window.location.search}`, { replace: true })} onOpen={(oid) => nav(`${base}/${oid}${window.location.search}`, { replace: true })} />
              : <div className="ib-none">{rows.length || query.isLoading ? "" : "Тут з'явиться вибране замовлення"}</div>}
          </div>
        </div>
      ) : (
        <DenseTable<OrderRow>
          label={stage === "lead" ? "Ліди" : "Замовлення"}
          rows={rows} cols={cols} rowKey={(o) => o.id}
          selected={sel} onSelect={setSel} current={id ? Number(id) : null}
          onOpen={(o) => open(o.id)}
          isLoading={query.isLoading} onEndReached={endReached}
          rowHeight={mobile ? undefined : 40}
          rowClass={(o) => (o.remind_at && new Date(o.remind_at) <= new Date() ? "due" : "")}
          mobileCard={mobileCard}
          actions={(o) => (<>
            {isUnsorted && <Button size={30} variant="soft" icon={Check} onClick={() => accept([o.id])}>Прийняти</Button>}
            {o.phone && <a className="icon-btn s28 quiet" href={`tel:+${o.phone.replace(/\D/g, "")}`} aria-label="Подзвонити" title="Подзвонити"><Phone size={15} /></a>}
            {o.ttn && <a className="icon-btn s28 quiet" href={`${ROOT}/api/orders/${o.id}/label`} target="_blank" rel="noreferrer" aria-label="Наклейка" title="Наклейка"><Printer size={15} /></a>}
            <IconButton size={28} quiet icon={Eye} label="Перегляд" onClick={() => open(o.id)} />
          </>)}
          empty={emptyBox}
        />
      )}
      {view === "table" && !mobile && head?.total != null && rows.length > 0 && (
        <div className="sum-bar" aria-live="polite">
          <span><b>{head.total}</b> {plural(head.total, "замовлення", "замовлення", "замовлень")}</span>
          {head.sum != null && <span>на <b className="num">{money(head.sum)} ₴</b></span>}
          {!!head.cod_wait && <span>післяплата в дорозі й на пошті <b className="num">{money(head.cod_wait)} ₴</b></span>}
          {sel.size > 0 && <span className="sum-sel">вибрано <b>{sel.size}</b> на <b className="num">{money(rows.filter((r) => sel.has(r.id)).reduce((a, r) => a + r.total, 0))} ₴</b></span>}
        </div>
      )}

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
        {meta.user.role !== "warehouse" && (
          <button className="btn quiet sm danger" onClick={() => {
            if (window.confirm(`Видалити ${sel.size} ${sel.size === 1 ? "замовлення" : "замовлень"} назавжди?\n\nРезерв повернеться на склад. Замовлення з ТТН у перевізника, фіскальним чеком чи вже відвантажені не видаляться.`)) bulk.mutate({ action: "delete" });
          }}><Trash2 size={14} />Видалити</button>
        )}
      </BulkBar>

      {id && (view !== "inbox" || id === "new") && <OrderModal id={id} onClose={() => nav(`${base}${window.location.search}`)} onOpen={(oid) => nav(`${base}/${oid}${window.location.search}`)}
        ids={rows.map((r) => r.id)} />}
    </div>
  );
}

// Плитка списку: перемальовується лише коли змінилось саме замовлення чи вибір (функція малювання бере свіже з замикання)
const Tile = memo(function Tile({ o, cur, render }: { o: OrderRow; cur: boolean; render: (o: OrderRow, cur: boolean) => ReactNode }) {
  return <>{render(o, cur)}</>;
}, (a, b) => a.o === b.o && a.cur === b.cur);

// ---------------------------------------------------------------- догрузка наступної сторінки, коли низ списку видно (картки, скринька)
function EndSentinel({ onEnd, busy, more, n }: { onEnd: () => void; busy: boolean; more: boolean; n: number }) {
  const el = useRef<HTMLDivElement>(null);
  const cb = useRef(onEnd);
  cb.current = onEnd;
  useEffect(() => {
    if (!el.current || !more) return;
    const io = new IntersectionObserver((e) => { if (e[0]?.isIntersecting) cb.current(); }, { rootMargin: "400px" });
    io.observe(el.current);
    return () => io.disconnect();
  }, [more, n]);  // нова сторінка підвантажилась, а низ досі видно — перевірити ще раз
  return <div ref={el} className="end-sentinel" aria-hidden>{busy ? "Завантажую…" : ""}</div>;
}

// ---------------------------------------------------------------- телефон: усі фільтри однією панеллю знизу (макет мобільної v2, екран 7)
const PERIODS = (): [string, string, string][] => {
  const t = new Date();
  const d = (shift: number) => { const x = new Date(t); x.setDate(x.getDate() - shift); return isoDay(x); };
  return [["Сьогодні", d(0), d(0)], ["Сьогодні й учора", d(1), d(0)], ["7 днів", d(6), d(0)], ["30 днів", d(29), d(0)],
    ["Цей місяць", isoDay(new Date(t.getFullYear(), t.getMonth(), 1)), d(0)]];
};
function FilterSheet({ f, onClose, onApply, onReset, sources }: {
  f: F; onClose: () => void; onApply: (p: Partial<F>) => void; onReset: () => void; sources: Record<number, { color: string }>;
}) {
  const meta = useMeta();
  const [d, setD] = useState<Partial<F>>({ date_from: f.date_from, date_to: f.date_to, manager: f.manager, delivery: f.delivery, pm: f.pm, src: f.src, entity: f.entity });
  const has = (k: keyof F, v: string) => (d[k] ?? "").split(",").includes(v);
  const flip = (k: keyof F, v: string, single = false) => {
    const cur = (d[k] ?? "").split(",").filter(Boolean);
    const next = cur.includes(v) ? cur.filter((x) => x !== v) : single ? [v] : [...cur, v];
    setD({ ...d, [k]: next.join(",") });
  };
  const chips = (k: keyof F, opts: { value: string; label: string; color?: string }[], single = false) => (
    <div className="fs-chips">{opts.map((o) => (
      <button key={o.value} type="button" className={`fs-chip${has(k, o.value) ? " on" : ""}`} aria-pressed={has(k, o.value)} onClick={() => flip(k, o.value, single)}>
        {o.color && <i style={{ background: o.color }} />}{o.label}</button>
    ))}</div>
  );
  const periods = PERIODS();
  return (
    <Sheet title="Фільтри" onClose={onClose}
      footer={<><button type="button" className="btn" onClick={onReset}>Скинути</button><button type="button" className="btn primary" onClick={() => onApply(d)}>Показати</button></>}>
      <div className="fs-l">Період</div>
      <div className="fs-chips">{periods.map(([n, a, b]) => {
        const on = d.date_from === a && d.date_to === b;
        return <button key={n} type="button" className={`fs-chip${on ? " on" : ""}`} aria-pressed={on} onClick={() => setD({ ...d, date_from: on ? "" : a, date_to: on ? "" : b })}>{n}</button>;
      })}</div>
      <div className="fs-l">Менеджер</div>
      {chips("manager", [...meta.managers.map((m) => ({ value: String(m.id), label: m.name })), { value: "none", label: "Без менеджера" }])}
      <div className="fs-l">Доставка</div>
      {chips("delivery", Object.entries(meta.delivery_methods).map(([k, n]) => ({ value: k, label: n })), true)}
      <div className="fs-l">Джерело</div>
      {chips("src", meta.order_sources.filter((s) => s.active).map((s) => ({ value: String(s.id), label: s.name, color: sources[s.id]?.color })))}
      {meta.legal_entities.length > 0 && <><div className="fs-l">Юрособа</div>{chips("entity", meta.legal_entities.map((e) => ({ value: String(e.id), label: e.name })))}</>}
      <div className="fs-l">Оплата</div>
      {chips("pm", meta.payment_methods.map((m) => ({ value: String(m.id), label: m.name, color: PAY_ICONS[m.icon || ""]?.color })))}
    </Sheet>
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

// ---------------------------------------------------------------- значки й підказки рядка (макет v26)
const COPY = (t: string, toast: (m: string) => void) => { navigator.clipboard?.writeText(t); toast("Скопійовано"); };

/** Мітки біля імені — маленькі значки замість слів: дубль, чорний список, VIP, немає товару, настало нагадування. */
function Signals({ o, due, unsorted }: { o: OrderRow; due: boolean; unsorted: boolean }) {
  const list: [string, string, typeof Copy][] = [];
  if (o.duplicate_of_id) list.push(["warn", `Можливий дубль №${o.duplicate_of_id}`, Copy]);
  if (o.blacklisted) list.push(["bad", "Покупець у чорному списку", Ban]);
  if (o.customer_group && /vip/i.test(o.customer_group.name)) list.push(["vip", `Група «${o.customer_group.name}»`, Crown]);
  if (unsorted && o.no_stock) list.push(["bad", "Товару не вистачає на складі", PackageX]);
  if (due) list.push(["bad", "Нагадування настало", AlarmClock]);
  if (!list.length) return null;
  return <>{list.map(([k, t, I]) => <span key={t} className={`o-sig ${k}`} title={t} aria-label={t}><I size={11} strokeWidth={2.2} /></span>)}</>;
}

function GoodsCard({ o }: { o: OrderRow }) {
  return (<>
    <div className="hc-t1">Товари · №{o.id}</div>
    {o.items.map((i, k) => (
      <div key={k} className="hc-good"><span className="hc-th"><Package size={12} /></span>
        <span className="ell">{i.upsell && <span className="hc-up">допродаж · </span>}{i.name}</span><span className="muted nowrap">× {i.qty}</span><b className="num nowrap">{money((i.price ?? 0) * i.qty)} ₴</b></div>
    ))}
    <div className="hc-kv sum"><span>Разом</span><b className="num">{money(o.total)} ₴</b></div>
  </>);
}

const CARRIER_BADGE: Record<string, [string, string]> = { novaposhta: ["НП", "np"], ukrposhta: ["УП", "up"], meest: ["M", "me"], rozetka: ["R", "rz"], pickup: ["С", "pk"] };
function CarrierBadge({ method }: { method: string }) {
  const [t, c] = CARRIER_BADGE[method] ?? [method.slice(0, 2).toUpperCase(), "pk"];
  return <span className={`o-car ${c}`}>{t}</span>;
}

function DeliveryCard({ o, name, state }: { o: OrderRow; name: string; state?: string }) {
  const toast = useToast();
  const eta = o.delivery_eta ? new Date(o.delivery_eta + "T00:00:00").toLocaleDateString("uk-UA", { day: "numeric", month: "long" }) : "";
  return (<>
    <div className="hc-t1">Доставка · {name}</div>
    <div className="hc-row"><CarrierBadge method={o.delivery_method} /><b>{o.city_name || "Місто не вказано"}</b></div>
    {o.warehouse_name && <div className="hc-sub">{o.warehouse_name}</div>}
    {o.ttn ? (<>
      <div className="hc-row hc-ttn"><span className="mono">{o.ttn}</span>
        <button type="button" className="hc-ib" aria-label="Скопіювати ТТН" onClick={() => COPY(o.ttn, toast)}><Copy size={13} /></button></div>
      <div className="hc-row"><span className="hc-state"><i style={{ background: DSTATE[o.delivery_state] ?? "var(--accent-line)" }} />{state ?? "ТТН створено"}</span>
        {eta && <span className="muted">прибуде {eta}</span>}</div>
      {o.delivery_status && <div className="hc-sub">{o.delivery_status}</div>}
    </>) : <div className="hc-sub">ТТН ще немає</div>}
  </>);
}

function PhoneCard({ o }: { o: OrderRow }) {
  const toast = useToast();
  const meta = useMeta();
  const d = o.phone.replace(/\D/g, "");
  const { data: c } = useQuery({
    queryKey: ["customer-brief", o.customer_id], enabled: !!o.customer_id && meta.user.role !== "warehouse", staleTime: 60_000,
    queryFn: () => api.get<{ orders: number; refused: number; buyout_rate: number | null; delivered: number }>(`/customers/${o.customer_id}`),
  });
  return (<>
    <div className="hc-t1">Телефон · {o.customer_name || "без імені"}</div>
    <div className="hc-row"><b className="hc-phone num">{phone(o.phone)}</b>
      <button type="button" className="hc-ib" aria-label="Скопіювати номер" onClick={() => COPY(`+${d}`, toast)}><Copy size={13} /></button></div>
    <div className="hc-acts">
      <a className="btn primary sm" href={`tel:+${d}`}><Phone size={14} />Дзвінок</a>
      <a className="hc-ib v" href={`viber://chat?number=%2B${d}`} aria-label="Написати у Viber" title="Viber"><MessageCircle size={15} /></a>
      <a className="hc-ib t" href={`https://t.me/+${d}`} target="_blank" rel="noreferrer" aria-label="Написати в Telegram" title="Telegram"><Send size={15} /></a>
    </div>
    {c && <div className="hc-stats"><span>{c.orders} {c.orders % 10 === 1 && c.orders % 100 !== 11 ? "замовлення" : "замовлень"}</span>
      {c.buyout_rate != null && c.delivered + c.refused > 0 && <span>викуп {Math.round(c.buyout_rate)}%</span>}
      {c.refused > 0 && <span className="bad">відмов {c.refused}</span>}</div>}
  </>);
}

/** Статус у рядку: клік — меню статусів цього етапу; для відмови з причинами — одразу причина. */
function StatusMenu({ o, statuses, current, onPick }: { o: OrderRow; statuses: Status[]; current?: Status; onPick: (sid: number, reasonId?: number) => void }) {
  const meta = useMeta();
  const ref = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const [reasonFor, setReasonFor] = useState<Status | null>(null);
  const close = useCallback(() => { setOpen(false); setReasonFor(null); }, []);
  const reasons = (s: Status) => meta.reasons.filter((r) => r.active && r.status_ids.includes(s.id));
  const pick = (s: Status) => {
    if ((s.code === "cancelled" || s.code === "refused") && reasons(s).length) { setReasonFor(s); return; }
    close(); onPick(s.id);
  };
  if (meta.user.role === "warehouse") return <StatusPill status={current} />;
  return (<>
    <button ref={ref} type="button" className={`o-stb${open ? " on" : ""}`} aria-haspopup="menu" aria-expanded={open} title="Змінити статус"
      onClick={(e) => { e.stopPropagation(); setOpen((x) => !x); setReasonFor(null); }}>
      <StatusPill status={current} /><ChevronDown size={12} className="o-stb-ch" aria-hidden />
    </button>
    <Floating anchor={ref.current} open={open} onClose={close} width={220} className="hc-menu" role="menu" label={`Статус №${o.id}`}>
      {reasonFor ? (<>
        <div className="hc-t1">«{reasonFor.name}» — причина</div>
        {reasons(reasonFor).map((r) => <button key={r.id} type="button" className="pop-item" role="menuitem" onClick={() => { close(); onPick(reasonFor.id, r.id); }}>{r.name}</button>)}
      </>) : statuses.map((s) => (
        <button key={s.id} type="button" role="menuitemradio" aria-checked={s.id === o.status_id} className={`pop-item${s.id === o.status_id ? " on" : ""}`}
          disabled={s.id === o.status_id} onClick={() => pick(s)}><StatusPill status={s} />{s.id === o.status_id && <Check size={14} className="hc-cur" />}</button>
      ))}
    </Floating>
  </>);
}
