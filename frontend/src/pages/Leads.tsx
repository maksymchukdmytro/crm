// Ліди (UI-DESIGN §4.3, макети 06 і 07): вигляди Стрічка, Дошка, Передзвони; «Почати дзвонити» відкриває чергу.
import { useCallback, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Clock3, KanbanSquare, List, Phone, PhoneCall, Plus, Search, X } from "lucide-react";
import { api, qs } from "../lib/api";
import { useDebounced, useMeta } from "../lib/app";
import { money, phone } from "../lib/format";
import type { OrderList, OrderRow } from "../lib/types";
import { Button, ChipSelect, DenseTable, FilterChip, Segmented, StatusPill, Tabs, type DenseCol, type TabItem } from "../components/ui";
import { SOURCE_COLORS } from "./Orders";
import OrderModal from "./OrderCard";
import LeadWindow from "./LeadWindow";

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

  const COLS: DenseCol<OrderRow>[] = [
    { key: "id", label: "№", width: "70px", render: (o) => <span className="o-id">{leadNo(o.id)}</span> },
    { key: "name", label: "Ім'я", width: "minmax(120px, 1.1fr)", title: (o) => o.customer_name, render: (o) => <span className="ell">{o.customer_name || <span className="muted">без імені</span>}</span> },
    { key: "phone", label: "Телефон", width: "124px", render: (o) => <span className="num">{phone(o.phone)}</span> },
    { key: "items", label: "Товар з форми", width: "minmax(120px, 1.3fr)", title: (o) => o.items.map((i) => i.name).join(", "), render: (o) => <span className="ell">{o.items[0]?.name ?? "—"}</span> },
    { key: "total", label: "Сума", width: "78px", align: "right", render: (o) => <b className="num">{money(o.total)} ₴</b> },
    { key: "status", label: "Статус", width: "118px", render: (o) => <StatusPill status={statuses[o.status_id]} /> },
    { key: "wait", label: "Чекає · спроба", width: "120px", render: (o) => <WaitBadge row={o} /> },
    { key: "source", label: "Джерело", width: "minmax(80px, 0.8fr)", render: (o) => {
      const s = sources[o.source_id ?? 0];
      return s ? <span className="o-dot-txt"><i style={{ background: s.color }} /><span className="ell">{s.name}</span></span> : <span className="ell muted">{o.utm_source || "—"}</span>;
    } },
    { key: "manager", label: "Мен.", headTitle: "Менеджер", width: "36px", align: "center", render: (o) => o.manager_id
      ? <span className="o-av" title={managers[o.manager_id]?.name}>{(managers[o.manager_id]?.name ?? "").split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase()}</span>
      : <span className="muted">—</span> },
  ];

  const open = useCallback((o: { id: number }) => nav(`/leads/${o.id}${window.location.search}`), [nav]);
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
          actions={(o) => (statuses[o.status_id]?.code && ["new", "no_answer", "callback"].includes(statuses[o.status_id].code)
            ? <Button size={30} icon={Phone} onClick={() => open(o)}>Дзвонити</Button> : null)}
          empty={<div className="empty-state"><p>{tab === "open" ? "Відкритих лідів немає — заявки з форм з'являться тут" : "Тут порожньо"}</p></div>} />
      )}
      {view === "board" && <LeadBoard rows={rows} onOpen={open} sources={sources} />}
      {view === "calls" && <Callbacks rows={rows} onOpen={open} />}

      {id && id !== "new" && <LeadWindow id={Number(id)} onClose={() => nav(`/leads${window.location.search}`)} onOpen={(oid) => nav(`/leads/${oid}${window.location.search}`)} />}
      {id === "new" && <OrderModal id="new" onClose={() => nav(`/leads${window.location.search}`)} onOpen={(oid) => nav(`/leads/${oid}${window.location.search}`)} />}
    </div>
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
