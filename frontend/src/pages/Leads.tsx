// Ліди (UI-DESIGN §4.3, макети 06 і 07): вигляди Стрічка, Дошка, Передзвони; «Почати дзвонити» відкриває чергу.
import { useCallback, useMemo, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Clock3, Inbox, KanbanSquare, List, Phone, PhoneCall, PhoneMissed, Plus, Search, X } from "lucide-react";
import { api, ApiError, qs } from "../lib/api";
import { errText, useDebounced, useMeta, useToast } from "../lib/app";
import { money, phone } from "../lib/format";
import type { Order, OrderList, OrderRow } from "../lib/types";
import { Button, ChipSelect, DenseTable, FilterChip, Floating, HoverCard, MobileActs, Ring, RoundButton, Segmented, StatusPill, Tabs, UaPhone, Window, type DenseCol, type TabItem, EmptyState } from "../components/ui";
import { PhoneCard, SOURCE_COLORS } from "./Orders";
import LeadWindow from "./LeadWindow";
import { SourceChips } from "./NewOrder";

const TABS: [string, string][] = [["open", "Відкриті"], ["new", "Нові"], ["no_answer", "Недодзвон"], ["callback", "Передзвонити"],
  ["duplicate", "Дублі"], ["refused", "Відмова ліда"], ["converted", "Створено замовлення"], ["all", "Усі"]];
const BOARD = ["new", "no_answer", "callback", "duplicate"];

export const leadNo = (id: number) => `Л-${id}`;

/** Час очікування кольором: до порога — звичайний, далі — помаранчевий, понад другий поріг — червоний. */
export function WaitBadge({ row }: { row: Pick<OrderRow, "wait_minutes" | "remind_at" | "call_attempts" | "status_id"> }) {
  const meta = useMeta();
  const code = meta.statuses.find((s) => s.id === row.status_id)?.code;
  const future = row.remind_at && new Date(row.remind_at) > new Date();
  const attempts = row.call_attempts ? <span className="lw-att" title="Спроб дзвінка"> · {row.call_attempts}</span> : null;
  if (code === "callback" && row.remind_at && (future || row.wait_minutes == null)) {
    return <span className="lw-wait cb"><PhoneCall size={12} />{callbackTime(row.remind_at)}{attempts}</span>;
  }
  if (row.wait_minutes == null) return future ? <span className="lw-wait"><Clock3 size={12} />{callbackTime(row.remind_at!)}{attempts}</span> : <span className="muted">—</span>;
  const m = row.wait_minutes;
  const cls = m >= meta.lead_wait_bad_min ? "bad" : m >= meta.lead_wait_warn_min ? "warn" : "";
  return <span className={`lw-wait ${cls}`}><Clock3 size={12} />{waitText(m)}{attempts}</span>;
}

/** Кільце часу очікування ліда: хв / год / дн; колір і заповнення — за порогами з налаштувань. */
export function WaitRing({ minutes, size = 54 }: { minutes: number | null | undefined; size?: number }) {
  const meta = useMeta();
  const m = minutes;
  if (m == null) return <Ring value="—" frac={0} color="var(--faint)" size={size} />;
  const color = m >= meta.lead_wait_bad_min ? "#DC2626" : m >= meta.lead_wait_warn_min ? "#D97706" : "#16A34A";
  const [v, u] = m < 60 ? [Math.max(1, m), "хв"] : m < 1440 ? [Math.floor(m / 60), "год"] : [Math.floor(m / 1440), "дн"];
  return <Ring value={v} unit={u} frac={Math.min(1, m / Math.max(1, meta.lead_wait_bad_min))} color={color} size={size} />;
}

export function waitText(m: number) {
  if (m < 1) return "щойно";
  if (m < 60) return `${m} хв`;
  if (m < 60 * 24) return `${Math.floor(m / 60)} год ${m % 60 ? `${m % 60} хв` : ""}`.trim();
  return `${Math.floor(m / 1440)} дн`;
}

export function callbackTime(iso: string) {
  const d = new Date(iso);
  const t = d.toLocaleTimeString("uk-UA", { hour: "2-digit", minute: "2-digit" });
  const today = new Date();
  const tm = new Date(); tm.setDate(tm.getDate() + 1);
  if (d.toDateString() === today.toDateString()) return `о ${t}`;
  if (d.toDateString() === tm.toDateString()) return `завтра ${t}`;
  return `${d.toLocaleDateString("uk-UA", { day: "numeric", month: "short" })} ${t}`;
}

export default function LeadsPage() {
  const meta = useMeta();
  const nav = useNavigate();
  const { id } = useParams();
  const [sp, setSp] = useSearchParams();
  const view = (sp.get("view") as "list" | "board" | "calls") || "list";
  const tab = sp.get("tab") || "open";
  const manager = sp.get("manager") ?? "";
  const src = sp.get("src") ?? "";
  const [search, setSearch] = useState(sp.get("q") ?? "");
  const dq = useDebounced(search, 300);
  const sources = useMemo(() => Object.fromEntries(meta.order_sources.map((s, i) => [s.id, { ...s, color: SOURCE_COLORS[i % SOURCE_COLORS.length] }])), [meta.order_sources]);
  const managers = useMemo(() => Object.fromEntries(meta.managers.map((m) => [m.id, m])), [meta.managers]);
  const statuses = useMemo(() => Object.fromEntries(meta.statuses.map((s) => [s.id, s])), [meta.statuses]);

  const set = (patch: Record<string, string>) => {
    const n = new URLSearchParams(sp);
    Object.entries(patch).forEach(([k, v]) => (v ? n.set(k, v) : n.delete(k)));
    setSp(n, { replace: true });
  };

  const listTab = view === "list" ? tab : "open";
  const params = { stage: "lead", tab: view === "board" ? "all" : listTab, sort: "wait", manager, src, q: dq, limit: 500 };
  const q = useQuery({ queryKey: ["orders", "leads", params], queryFn: () => api.get<OrderList>(`/orders${qs(params)}`), refetchInterval: 60_000 });
  const rows = q.data?.items ?? [];
  const tabsN = q.data?.lead_tabs;
  const waiting = rows.filter((r) => r.wait_minutes != null);
  const longest = waiting.reduce((m, r) => Math.max(m, r.wait_minutes ?? 0), 0);
  const newCount = tabsN?.new ?? rows.filter((r) => statuses[r.status_id]?.code === "new").length;
  const qQueue = useQuery({ queryKey: ["leads", "queue"], queryFn: () => api.get<{ ids: number[] }>("/leads/queue"), refetchInterval: 60_000 });

  const tabs: TabItem<string>[] = TABS.map(([k, label]) => ({ key: k, label, count: tabsN?.[k as keyof typeof tabsN] ?? null, hot: k === "new" }));
  const meNone = `${meta.user.id},none`;

  // колонки (макет v26, 13–14): скільки чекає кольором, спроби крапками, результат дзвінка одним кліком; телефон — значком
  const COLS: DenseCol<OrderRow>[] = [
    { key: "id", label: "№", width: "64px", render: (o) => <span className="o-id">{leadNo(o.id)}</span> },
    { key: "name", label: "Лід", width: "minmax(130px, 1.2fr)", title: (o) => o.customer_name, render: (o) => {
      const s = sources[o.source_id ?? 0];
      return <span className="o-cust"><i className="o-src" style={{ background: s?.color ?? "var(--line)" }} title={s?.name ?? o.utm_source ?? "Джерело не вказано"} />
        <span className="ell">{o.customer_name || <span className="muted">без імені</span>}</span></span>;
    } },
    { key: "items", label: "Що цікавить", width: "minmax(120px, 1.2fr)", title: (o) => o.items.map((i) => i.name).join(", "), render: (o) => <span className="ell muted">{o.items[0]?.name ?? "—"}{o.total ? ` · ${money(o.total)} ₴` : ""}</span> },
    { key: "wait", label: "Чекає", width: "108px", render: (o) => <WaitPill row={o} /> },
    { key: "tries", label: "Спроби", headTitle: "Спроби дзвінка", width: "58px", render: (o) => (
      <span className="ld-dots" title={`Спроб дзвінка: ${o.call_attempts ?? 0}`} aria-label={`Спроб дзвінка: ${o.call_attempts ?? 0}`}>
        {[0, 1, 2].map((i) => <i key={i} className={i < (o.call_attempts ?? 0) ? "on" : ""} />)}{(o.call_attempts ?? 0) > 3 && <small>+{(o.call_attempts ?? 0) - 3}</small>}
      </span>
    ) },
    { key: "status", label: "Статус", width: "124px", render: (o) => <StatusPill status={statuses[o.status_id]} /> },
    { key: "result", mobile: "hide", label: "Результат дзвінка", width: "190px", render: (o) => <LeadResult o={o} open={(id) => nav(`/leads/${id}${window.location.search}`)} /> },
    { key: "manager", mobile: "hide", label: "М.", headTitle: "Менеджер", width: "28px", align: "center", render: (o) => o.manager_id
      ? <span className="o-av" title={managers[o.manager_id]?.name}>{(managers[o.manager_id]?.name ?? "").split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase()}</span>
      : <span className="muted">—</span> },
    { key: "call", mobile: "hide", label: <Phone size={13} aria-label="Телефон" />, headTitle: "Телефон", width: "32px", align: "center", render: (o) => (
      o.phone ? <HoverCard label={`Телефон ${phone(o.phone)}`} triggerClass="o-ic o-call" width={290} trigger={<Phone size={14} />}>{() => <PhoneCard o={o} />}</HoverCard> : <span className="o-none">—</span>
    ) },
  ];

  const open = useCallback((o: { id: number }) => nav(`/leads/${o.id}${window.location.search}`), [nav]);

  // телефон (мобільна v2): кільце часу очікування, статус, ім'я, товар · сума, кнопка дзвінка
  const mobileCard = (o: OrderRow) => {
    const code = statuses[o.status_id]?.code ?? "";
    const callable = ["new", "no_answer", "callback"].includes(code);
    return (
      <div className="ml-card">
        <WaitRing minutes={o.wait_minutes} />
        <div className="ml-t">
          <StatusPill status={statuses[o.status_id]} />
          <b>{o.customer_name || phone(o.phone) || "без імені"}</b>
          <small>{o.items[0]?.name ?? "—"} · {money(o.total)} ₴</small>
        </div>
        {o.phone && callable && (
          <a className="ml-call" href={`tel:+${o.phone.replace(/\D/g, "")}`} aria-label={`Подзвонити: ${o.customer_name || phone(o.phone)}`}
            onClick={(e) => { e.stopPropagation(); open(o); }}><Phone size={20} /></a>
        )}
      </div>
    );
  };
  const firstInQueue = qQueue.data?.ids[0];

  return (
    <div className="page-list">
      <div className="list-head">
        <h1>Ліди</h1>
        <span className="list-sum">
          <b>{newCount}</b> {newCount === 1 ? "новий чекає" : "нових чекають"} дзвінка
          {longest > 0 && <> · найдовше чекає <b className={longest >= meta.lead_wait_bad_min ? "t-bad" : longest >= meta.lead_wait_warn_min ? "t-warn" : ""}>{waitText(longest)}</b></>}
          {tabsN && <> · створено замовлень <b>{tabsN.converted}</b></>}
        </span>
        <div className="list-acts">
          <Segmented label="Вигляд" value={view} onChange={(k) => set({ view: k === "list" ? "" : k })}
            items={[{ key: "list", label: "Стрічка", icon: <List size={14} /> }, { key: "board", label: "Дошка", icon: <KanbanSquare size={14} /> },
              { key: "calls", label: "Передзвони", icon: <Clock3 size={14} /> }]} />
          <Button variant="primary" icon={Phone} disabled={!firstInQueue} onClick={() => firstInQueue && open({ id: firstInQueue })}
            title={firstInQueue ? "Відкрити чергу дзвінків" : "Черга порожня"}>Почати дзвонити</Button>
        </div>
      </div>

      <MobileActs><RoundButton icon={Plus} label="Новий лід" onClick={() => nav(`/leads/new${window.location.search}`)} /></MobileActs>
      <div className="lead-cta m-only">
        <div><b>{newCount}</b><small>{newCount === 1 ? "чекає дзвінка" : "чекають дзвінка"}{longest > 0 && <><br />найдовше — {waitText(longest)}</>}</small></div>
        <button type="button" className="go" disabled={!firstInQueue} onClick={() => firstInQueue && open({ id: firstInQueue })}><Phone size={18} />Дзвонити</button>
      </div>

      {view === "list" && <Tabs items={tabs} value={tab} onChange={(k) => set({ tab: k === "open" ? "" : k })} label="Вкладки лідів" className="list-tabs" />}

      <div className="chips-row">
        <FilterChip label="Мої й нічиї" value={manager === meNone ? "Мої й нічиї" : undefined} onClick={() => set({ manager: manager === meNone ? "" : meNone })} onClear={() => set({ manager: "" })} />
        {manager && manager !== meNone && (
          <ChipSelect label="Менеджер" value={manager.split(",")} onChange={(v) => set({ manager: v.join(",") })}
            options={[{ value: "none", label: "Не призначено" }, ...meta.managers.map((m) => ({ value: String(m.id), label: m.name }))]} />
        )}
        {!manager && (
          <ChipSelect label="Менеджер" value={[]} onChange={(v) => set({ manager: v.join(",") })}
            options={[{ value: "none", label: "Не призначено" }, ...meta.managers.map((m) => ({ value: String(m.id), label: m.name }))]} />
        )}
        <ChipSelect label="Джерело" value={src ? src.split(",") : []} onChange={(v) => set({ src: v.join(",") })}
          options={meta.order_sources.filter((s) => s.active).map((s) => ({ value: String(s.id), label: s.name, color: sources[s.id]?.color }))} />
        {(manager || src) && <button className="btn quiet sm" onClick={() => set({ manager: "", src: "" })}><X size={14} />Скинути</button>}
        <span className="list-hint">Вгорі — хто чекає найдовше</span>
        <label className="list-search">
          <Search size={15} aria-hidden />
          <input type="search" value={search} onChange={(e) => { setSearch(e.target.value); }} onBlur={() => set({ q: search })} placeholder="Пошук у лідах" aria-label="Пошук у лідах" />
        </label>
      </div>

      {view === "list" && (
        <DenseTable<OrderRow> label="Ліди" rows={rows} cols={COLS} rowKey={(o) => o.id} onOpen={open} current={id ? Number(id) : null}
          isLoading={q.isLoading}
          rowClass={(o) => ((o.wait_minutes ?? 0) >= meta.lead_wait_bad_min ? "late" : "")}
          mobileCard={mobileCard}
          rowHeight={44}
          empty={tab === "open" ? <EmptyState icon={Inbox} title="Відкритих лідів немає" text="Заявки з форм на сайті з'являться тут самі. Дзвінок чи повідомлення — додайте лід вручну"
            action={{ label: "Новий лід", icon: Plus, onClick: () => nav(`/leads/new${window.location.search}`) }} /> : <div className="empty-state"><p>Тут порожньо</p></div>} />
      )}
      {view === "board" && <LeadBoard rows={rows} onOpen={open} sources={sources} />}
      {view === "calls" && <Callbacks rows={rows} onOpen={open} />}

      {id && id !== "new" && <LeadWindow id={Number(id)} onClose={() => nav(`/leads${window.location.search}`)} onOpen={(oid) => nav(`/leads/${oid}${window.location.search}`)} />}
      {id === "new" && <NewLeadDialog onClose={() => nav(`/leads${window.location.search}`)} onOpen={(oid) => nav(`/leads/${oid}${window.location.search}`)} />}
    </div>
  );
}

// ---------------------------------------------------------------- новий лід вручну: лише ім'я й телефон
// Лід з'являється в стовпці «Новий»; товари, оплату й доставку додають уже у вікні ліда («Створити замовлення»).
function NewLeadDialog({ onClose, onOpen }: { onClose: () => void; onOpen: (id: number) => void }) {
  const meta = useMeta();
  const qc = useQueryClient();
  const toast = useToast();
  const [name, setName] = useState("");
  const [tel, setTel] = useState("");
  const [src, setSrc] = useState<number | "">("");
  const newSt = meta.statuses.find((s) => s.code === "new");
  const ok = tel.replace(/\D/g, "").length >= 12;
  const lock = useRef(false);
  const add = useMutation({
    mutationFn: () => api.post<Order>("/orders", { customer_name: name.trim(), phone: tel, country: "UA", status_id: newSt?.id, source_id: src || null }),
    onSuccess: (o) => {
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["counters"] });
      qc.invalidateQueries({ queryKey: ["leads"] });
      toast(`Лід ${leadNo(o.id)} додано`, "ok", { action: { label: "Відкрити", onClick: () => onOpen(o.id) } });
      onClose();
    },
    onError: (e) => { lock.current = false; toast(errText(e), "error"); },
  });
  const addOnce = () => { if (lock.current || !ok) return; lock.current = true; add.mutate(); };
  return (
    <Window size="sm" onClose={onClose} title="Новий лід" label="Новий лід"
      footer={<><span className="spacer" /><Button onClick={onClose}>Скасувати</Button>
        <Button variant="primary" icon={Plus} disabled={!ok || add.isPending} onClick={addOnce}>{add.isPending ? "Додаю…" : "Додати лід"}</Button></>}>
      <form className="form new-lead" onSubmit={(e) => { e.preventDefault(); addOnce(); }}>
        <label className="fbox"><span className="lbl">Телефон</span>
          <UaPhone value={tel} country="UA" onChange={setTel} aria-label="Телефон" autoFocus /></label>
        <label className="fbox"><span className="lbl">Ім'я</span>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Як звати покупця" /></label>
        <div className="new-lead-src"><SourceChips form={{ source_id: src }} set={(p) => setSrc(p.source_id)} /></div>
        <p className="hint">Лід з'явиться в стовпці «Новий». Товари, оплату й доставку додасте, відкривши його.</p>
        <button type="submit" hidden aria-hidden tabIndex={-1} />
      </form>
    </Window>
  );
}

// ---------------------------------------------------------------- дошка: Новий · Недодзвон · Передзвонити · Дубль, картки 58 px
function LeadBoard({ rows, onOpen, sources }: { rows: OrderRow[]; onOpen: (o: OrderRow) => void; sources: Record<number, { name: string; color: string }> }) {
  const meta = useMeta();
  const nav = useNavigate();
  const byCode = Object.fromEntries(meta.statuses.map((s) => [s.code, s]));
  return (
    <div className="lboard">
      {BOARD.filter((c) => byCode[c]?.active).map((code) => {
        const s = byCode[code];
        const items = rows.filter((r) => r.status_id === s.id);
        return (
          <section key={code} className="lcol" aria-label={s.name}>
            <div className="lcol-head"><StatusPill status={s} /><span className="count">{items.length}</span>
              {code === "new" && <button className="icon-btn s28 quiet" aria-label="Новий лід" title="Новий лід (L)" onClick={() => nav("/leads/new")}><Plus size={15} /></button>}
            </div>
            <div className="lcol-body">
              {items.map((o) => (
                <button key={o.id} className="lcard" onClick={() => onOpen(o)}>
                  <span className="lcard-1"><b className="ell">{o.customer_name || phone(o.phone)}</b><b className="num">{money(o.total)} ₴</b></span>
                  <span className="lcard-2">
                    <i className="lcard-src" style={{ background: sources[o.source_id ?? 0]?.color ?? "var(--line)" }} title={sources[o.source_id ?? 0]?.name} />
                    <span className="ell">{o.items[0]?.name ?? "—"}</span>
                    {code === "duplicate" && o.duplicate_of_id ? <span className="lw-wait">→ №{o.duplicate_of_id}</span> : <WaitBadge row={o} />}
                  </span>
                </button>
              ))}
              {!items.length && <div className="board-empty">Порожньо</div>}
            </div>
          </section>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------- передзвони на сьогодні за годинами
function Callbacks({ rows, onOpen }: { rows: OrderRow[]; onOpen: (o: OrderRow) => void }) {
  const meta = useMeta();
  const cb = meta.statuses.find((s) => s.code === "callback")?.id;
  const today = new Date().toDateString();
  const list = rows.filter((r) => r.remind_at && (r.status_id === cb || new Date(r.remind_at).toDateString() === today))
    .filter((r) => new Date(r.remind_at!).toDateString() === today || new Date(r.remind_at!) < new Date())
    .sort((a, b) => +new Date(a.remind_at!) - +new Date(b.remind_at!));
  const hours = new Map<string, OrderRow[]>();
  list.forEach((r) => {
    const d = new Date(r.remind_at!);
    const key = d.toDateString() !== today ? "Прострочені" : `${String(d.getHours()).padStart(2, "0")}:00`;
    hours.set(key, [...(hours.get(key) ?? []), r]);
  });
  if (!list.length) return <div className="dense"><div className="dense-empty"><div className="empty-state"><p>На сьогодні передзвонів немає</p></div></div></div>;
  return (
    <div className="callbacks">
      {[...hours.entries()].map(([h, items]) => (
        <section key={h} className="cb-hour">
          <div className="cb-h">{h}</div>
          <div className="cb-items">
            {items.map((o) => (
              <button key={o.id} className="lcard cb-card" onClick={() => onOpen(o)}>
                <span className="lcard-1"><b className="ell">{o.customer_name || phone(o.phone)}</b><span className="lw-wait cb"><PhoneCall size={12} />{callbackTime(o.remind_at!)}</span></span>
                <span className="lcard-2"><span className="ell">{o.items[0]?.name ?? "—"}</span><span className="num">{phone(o.phone)}</span></span>
              </button>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------- скільки чекає — кольоровою таблеткою (зелений · жовтий · червоний)
function WaitPill({ row }: { row: OrderRow }) {
  const meta = useMeta();
  const code = meta.statuses.find((s) => s.id === row.status_id)?.code;
  const future = row.remind_at && new Date(row.remind_at) > new Date();
  if (code === "callback" && row.remind_at && (future || row.wait_minutes == null)) return <span className="ld-wait cb"><PhoneCall size={12} />{callbackTime(row.remind_at)}</span>;
  if (row.wait_minutes == null) return future ? <span className="ld-wait cb"><Clock3 size={12} />{callbackTime(row.remind_at!)}</span> : <span className="muted">—</span>;
  const m = row.wait_minutes;
  const cls = m >= meta.lead_wait_bad_min ? "bad" : m >= meta.lead_wait_warn_min ? "warn" : "ok";
  return <span className={`ld-wait ${cls}`}><Clock3 size={12} />{waitText(m)}</span>;
}

// ---------------------------------------------------------------- результат дзвінка одним кліком: не відповів · передзвонити · оформити
function LeadResult({ o, open }: { o: OrderRow; open: (id: number) => void }) {
  const meta = useMeta();
  const qc = useQueryClient();
  const toast = useToast();
  const code = meta.statuses.find((s) => s.id === o.status_id)?.code ?? "";
  const ref = useRef<HTMLButtonElement>(null);
  const [menu, setMenu] = useState(false);
  const done = () => { qc.invalidateQueries({ queryKey: ["orders"] }); qc.invalidateQueries({ queryKey: ["leads"] }); qc.invalidateQueries({ queryKey: ["counters"] }); };
  const result = useMutation({
    mutationFn: (body: { result: string; at?: string }) => api.post(`/orders/${o.id}/lead-result`, body),
    onSuccess: (_, b) => { done(); toast(b.result === "no_answer" ? `${leadNo(o.id)}: недодзвон, спроба ${(o.call_attempts ?? 0) + 1}` : `${leadNo(o.id)}: передзвонити ${callbackTime(b.at!)}`); },
    onError: (e) => toast(errText(e), "error"),
  });
  const convert = useMutation({
    mutationFn: () => api.post<{ order: { id: number } }>(`/orders/${o.id}/convert`),
    onSuccess: (r) => { done(); toast(`Створено замовлення №${r.order.id}`, "ok"); },
    onError: (e) => { if (e instanceof ApiError && e.status === 422) { toast(errText(e), "warn"); open(o.id); } else toast(errText(e), "error"); },
  });
  if (!["new", "no_answer", "callback"].includes(code)) return <span className="muted">—</span>;
  const busy = result.isPending || convert.isPending;
  const at = (fn: (d: Date) => void) => { const d = new Date(); fn(d); return d.toISOString(); };
  const now = new Date();
  const presets: [string, string][] = [
    ["Через годину", at((d) => d.setHours(d.getHours() + 1))],
    ...(now.getHours() < 17 ? [["Сьогодні о 18:00", at((d) => d.setHours(18, 0, 0, 0))] as [string, string]] : []),
    ["Завтра о 10:00", at((d) => { d.setDate(d.getDate() + 1); d.setHours(10, 0, 0, 0); })],
    ["Післязавтра о 10:00", at((d) => { d.setDate(d.getDate() + 2); d.setHours(10, 0, 0, 0); })],
  ];
  return (
    <span className="ld-res" onClick={(e) => e.stopPropagation()}>
      <button type="button" className="ld-rb" disabled={busy} onClick={() => result.mutate({ result: "no_answer" })} title="Не відповів: +1 спроба">
        <PhoneMissed size={13} />Не відповів</button>
      <button ref={ref} type="button" className="ld-rb ic v" disabled={busy} aria-label="Передзвонити — обрати час" aria-expanded={menu} title="Передзвонити" onClick={() => setMenu((x) => !x)}><Clock3 size={14} /></button>
      <button type="button" className="ld-rb ic g" disabled={busy} aria-label="Оформити замовлення з ліда" title="Оформити замовлення" onClick={() => convert.mutate()}><Check size={14} /></button>
      <Floating anchor={ref.current} open={menu} onClose={() => setMenu(false)} width={210} className="hc-menu" role="menu" label="Коли передзвонити">
        <div className="hc-t1">Передзвонити</div>
        {presets.map(([n, v]) => <button key={n} type="button" role="menuitem" className="pop-item" onClick={() => { setMenu(false); result.mutate({ result: "callback", at: v }); }}>{n}</button>)}
        <button type="button" role="menuitem" className="pop-item" onClick={() => { setMenu(false); open(o.id); }}>Свій час…</button>
      </Floating>
    </span>
  );
}
