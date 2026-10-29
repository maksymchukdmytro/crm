import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useVirtualizer } from "@tanstack/react-virtual";
import { Ban, Bell, Download, Inbox, Plus, ReceiptText, X } from "lucide-react";
import { api, qs, ROOT } from "../lib/api";
import { errText, useDebounced, useMeta, useToast } from "../lib/app";
import { dt, itemsLabel, money, phone } from "../lib/format";
import { PayLabel } from "../components/payicons";
import { MarkBadge } from "../components/marks";
import type { OrderList, OrderRow } from "../lib/types";
import { PayCheck, Pill } from "../components/ui";
import OrderModal from "./OrderCard";

const FILTERS = ["status", "q", "manager", "delivery", "source", "date_from", "date_to", "dup"] as const;
const ROW_H = 40;

// Один список для двох розділів: «Ліди» (обробка заявки) і «Замовлення» (після підтвердження), як у LP-CRM.
export default function OrdersPage({ stage = "order" }: { stage?: "lead" | "order" }) {
  const base = stage === "lead" ? "/leads" : "/orders";
  const meta = useMeta();
  const nav = useNavigate();
  const { id } = useParams();
  const [sp, setSp] = useSearchParams();
  const toast = useToast();
  const qc = useQueryClient();
  const statuses = useMemo(() => Object.fromEntries(meta.statuses.map((s) => [s.id, s])), [meta.statuses]);
  const pm = useMemo(() => Object.fromEntries(meta.payment_methods.map((m) => [m.id, m])), [meta.payment_methods]);
  const marks = useMemo(() => Object.fromEntries(meta.marks.map((m) => [m.id, m])), [meta.marks]);
  const managers = useMemo(() => Object.fromEntries(meta.managers.map((m) => [m.id, m])), [meta.managers]);

  const f = Object.fromEntries(FILTERS.map((k) => [k, sp.get(k) ?? ""])) as Record<(typeof FILTERS)[number], string>;
  const [search, setSearch] = useState(f.q);
  const dq = useDebounced(search, 300);
  useEffect(() => { if (dq !== f.q) setF({ q: dq }); /* eslint-disable-next-line */ }, [dq]);

  function setF(patch: Partial<typeof f>) {
    const next = new URLSearchParams(sp);
    Object.entries(patch).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    setSp(next, { replace: true });
  }

  const filterKey = stage + "|" + FILTERS.map((k) => f[k]).join("|");
  const stageStatuses = useMemo(() => meta.statuses.filter((s) => s.active && (s.stage ?? "order") === stage), [meta.statuses, stage]);
  const query = useInfiniteQuery({
    queryKey: ["orders", "list", filterKey],
    queryFn: ({ pageParam }) => api.get<OrderList>(`/orders${qs({ ...f, stage, before: pageParam || undefined, limit: 100, counts: pageParam ? 0 : 1 })}`),
    initialPageParam: 0,
    getNextPageParam: (last) => last.next ?? undefined,
  });
  const rows: OrderRow[] = useMemo(() => query.data?.pages.flatMap((p) => p.items) ?? [], [query.data]);
  const head = query.data?.pages[0];

  const { data: sources = [] } = useQuery({ queryKey: ["orders", "sources"], queryFn: () => api.get<string[]>("/orders/sources"), staleTime: 300_000 });

  // ---------------- виділення і масові дії
  const [sel, setSel] = useState<Set<number>>(new Set());
  useEffect(() => setSel(new Set()), [filterKey]);
  const toggle = (oid: number) => setSel((s) => { const n = new Set(s); n.has(oid) ? n.delete(oid) : n.add(oid); return n; });
  const allSel = rows.length > 0 && rows.every((r) => sel.has(r.id));
  const bulk = useMutation({
    mutationFn: (body: { action: string; value?: string | number }) => api.post<{ done: number; queued: number; errors: string[] }>("/orders/bulk", { ids: [...sel], ...body }),
    onSuccess: (r) => {
      toast(r.queued ? `Поставлено в чергу: ${r.queued}. Результат з'явиться автоматично.` : `Оброблено: ${r.done}`);
      r.errors.slice(0, 5).forEach((e) => toast(e, "error"));
      setSel(new Set());
      qc.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: (e) => toast(errText(e), "error"),
  });

  // ---------------- віртуалізація
  const scrollRef = useRef<HTMLDivElement>(null);
  const v = useVirtualizer({ count: rows.length, getScrollElement: () => scrollRef.current, estimateSize: () => ROW_H, overscan: 12 });
  const vItems = v.getVirtualItems();
  useEffect(() => {
    const last = vItems[vItems.length - 1];
    if (last && last.index >= rows.length - 20 && query.hasNextPage && !query.isFetchingNextPage) query.fetchNextPage();
  }, [vItems, rows.length, query]);

  const anyFilter = f.q || f.manager || f.delivery || f.source || f.date_from || f.date_to || f.dup;
  const exportUrl = `${ROOT}/classic/orders/export.csv${qs(f)}`;

  return (
    <div className="page-orders">
      <div className="head">
        <h1><span className="h-ico">{stage === "lead" ? <Inbox size={18} /> : <ReceiptText size={18} />}</span>
          {stage === "lead" ? "Ліди" : "Замовлення"} <small className="muted">{head?.total ?? ""}</small></h1>
        <div className="actions">
          <a className="btn ghost" href={exportUrl}><Download size={15} /> CSV</a>
          <button className="btn primary" onClick={() => nav(`${base}/new`)}><Plus size={15} /> Нове замовлення</button>
        </div>
      </div>
      {stage === "lead" && <p className="hint page-hint">Нові заявки з лендингів і ручні звернення. Після підтвердження лід переходить у «Замовлення».</p>}

      <div className="tabs">
        <a className={!f.status ? "on" : ""} onClick={() => setF({ status: "" })}>Усі <span className="n">{head?.all ?? ""}</span></a>
        {stageStatuses.map((s) => {
          const n = head?.counts?.[String(s.id)] ?? 0;
          return (
            <a key={s.id} className={`${f.status === String(s.id) ? "on" : ""} ${n ? "" : "empty-tab"}`} style={{ ["--c" as string]: s.color }}
              onClick={() => setF({ status: String(s.id) })}>{s.name} <span className="n">{n}</span></a>
          );
        })}
      </div>

      <div className="filters">
        <input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="№, телефон, ПІБ або ТТН" />
        <select value={f.manager} onChange={(e) => setF({ manager: e.target.value })}>
          <option value="">Усі менеджери</option><option value="none">Не призначено</option>
          {meta.managers.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
        </select>
        <select value={f.delivery} onChange={(e) => setF({ delivery: e.target.value })}>
          <option value="">Будь-яка доставка</option>
          {Object.entries(meta.delivery_methods).map(([k, n]) => <option key={k} value={k}>{n}</option>)}
        </select>
        <select value={f.source} onChange={(e) => setF({ source: e.target.value })}>
          <option value="">Усі джерела</option>
          {sources.map((s) => <option key={s}>{s}</option>)}
        </select>
        <input type="date" value={f.date_from} onChange={(e) => setF({ date_from: e.target.value })} title="Дата від" />
        <input type="date" value={f.date_to} onChange={(e) => setF({ date_to: e.target.value })} title="Дата до" />
        <label className="check"><input type="checkbox" checked={!!f.dup} onChange={(e) => setF({ dup: e.target.checked ? "1" : "" })} /> Дублі</label>
        {anyFilter && <button className="btn sm ghost" onClick={() => { setSearch(""); setSp(f.status ? { status: f.status } : {}, { replace: true }); }}><X size={14} /> Скинути</button>}
        {query.isFetching && !query.isFetchingNextPage && <span className="spinner sm" />}
      </div>

      <div className="card flush grid-table">
        {sel.size > 0 && (
          <div className="bulk on">
            Вибрано: <strong>{sel.size}</strong>
            <select defaultValue="" onChange={(e) => {
              const [action, value] = e.target.value.split(":");
              e.target.value = "";
              if (action) bulk.mutate({ action, value });
            }}>
              <option value="">Дія…</option>
              <optgroup label="Змінити статус">{meta.statuses.filter((s) => s.active).map((s) => <option key={s.id} value={`status:${s.id}`}>→ {s.name}{(s.stage ?? "order") !== stage ? (stage === "lead" ? " (у замовлення)" : " (у ліди)") : ""}</option>)}</optgroup>
              {meta.user.role !== "warehouse" && (
                <optgroup label="Призначити менеджера">
                  {meta.managers.map((m) => <option key={m.id} value={`assign:${m.id}`}>→ {m.name}</option>)}
                  <option value="assign:0">→ Зняти менеджера</option>
                </optgroup>
              )}
              <optgroup label="Доставка"><option value="ttn:">Створити ТТН</option><option value="track:">Оновити статуси доставки</option></optgroup>
              {meta.checkbox_ready && <optgroup label="Каса"><option value="fiscalize:">Фіскалізувати (чек продажу)</option></optgroup>}
            </select>
            <button className="btn sm ghost" onClick={() => setSel(new Set())}>Скасувати</button>
          </div>
        )}
        <div className="gt-head gt-row">
          <span className="c-sel"><input type="checkbox" checked={allSel} onChange={() => setSel(allSel ? new Set() : new Set(rows.map((r) => r.id)))} /></span>
          <span>№</span><span>Статус</span><span>Клієнт</span><span>Телефон</span><span>Товари</span>
          <span>Оплата</span><span className="num">Сума</span><span className="c-pc" title="Чи відповідає ТТН Нової Пошти виду оплати: контроль оплати для NovaPay, без післяплати для оплачених">Перевірка оплати</span><span>Доставка</span><span>ТТН</span><span className="c-m">Менеджер</span><span className="c-s">Джерело</span><span>Дата</span>
        </div>
        <div className="gt-body" ref={scrollRef}>
          {query.isLoading && <div className="empty"><span className="spinner" /></div>}
          {!query.isLoading && rows.length === 0 && <div className="empty">{stage === "lead" ? "Нових лідів немає — заявки з лендингів з'являться тут автоматично" : "Замовлень за цими фільтрами немає"}</div>}
          <div style={{ height: v.getTotalSize(), position: "relative" }}>
            {vItems.map((vi) => {
              const o = rows[vi.index];
              const s = statuses[o.status_id];
              return (
                <div key={o.id} className={`gt-row ${sel.has(o.id) ? "sel-on" : ""} ${String(o.id) === id ? "cur" : ""}`}
                  style={{ transform: `translateY(${vi.start}px)`, height: ROW_H }}
                  onClick={(e) => { if (!(e.target as HTMLElement).closest("input")) nav(`${base}/${o.id}${window.location.search}`); }}>
                  <span className="c-sel"><input type="checkbox" checked={sel.has(o.id)} onChange={() => toggle(o.id)} /></span>
                  <span className="nowrap"><b>{o.id}</b>{o.duplicate_of_id && <span className="badge warn" title={`Повтор з номера: №${o.duplicate_of_id}`}>дубль</span>}</span>
                  <span className="st-cell"><Pill status={s} />{o.remind_at && <span className={`remind-dot ${new Date(o.remind_at) <= new Date() ? "due" : ""}`} title={`Нагадування ${dt(o.remind_at, true)}`}><Bell size={12} /></span>}{o.mark_id && marks[o.mark_id] && <MarkBadge mark={marks[o.mark_id]} short />}</span>
                  <span className="ell">{o.blacklisted && <span className="bl-mark" title="Покупець у чорному списку"><Ban size={13} /></span>}{o.customer_name || <span className="muted">—</span>}</span>
                  <span className="nowrap">{phone(o.phone)}</span>
                  <span className="ell" title={itemsLabel(o.items)}>{itemsLabel(o.items)}{o.items.some((i) => i.upsell) && <span className="badge info">допродаж</span>}</span>
                  <span className="pay-col">{pm[o.payment_method_id ?? 0] ? <span title={pm[o.payment_method_id!].name}><PayLabel icon={pm[o.payment_method_id!].icon} image={pm[o.payment_method_id!].image} name={shortPay(pm[o.payment_method_id!].name)} /></span> : <span className="muted">—</span>}</span>
                  <span className="num"><b>{money(o.total)}</b></span>
                  <span className="c-pc"><PayCheck check={o.pay_check} /></span>
                  <span className="ell">{meta.delivery_methods[o.delivery_method]}{o.city_name && <small> · {o.city_name}</small>}</span>
                  <span className="nowrap">{o.ttn ? <><span className="mono">{o.ttn}</span>{o.delivery_state && <span className={`dstate ${o.delivery_state}`} title={`${meta.delivery_states[o.delivery_state] ?? ""}: ${o.delivery_status}`} />}</> : <span className="muted">—</span>}</span>
                  <span className="ell c-m">{o.manager_id ? managers[o.manager_id]?.name ?? "—" : <span className="muted">—</span>}</span>
                  <span className="ell c-s">{o.utm_source || <span className="muted">—</span>}{o.utm_campaign && <small> · {o.utm_campaign}</small>}</span>
                  <span className="nowrap muted">{dt(o.created_at, true)}</span>
                </div>
              );
            })}
          </div>
          {query.isFetchingNextPage && <div className="empty" style={{ padding: 12 }}><span className="spinner sm" /></div>}
        </div>
      </div>
      {id && <OrderModal id={id} onClose={() => nav(`${base}${window.location.search}`)} onOpen={(oid) => nav(`${base}/${oid}${window.location.search}`)} />}
    </div>
  );
}

/** Коротка назва виду оплати для вузької колонки: «Післяплата NovaPay» → «NovaPay» (синя крапка на значку вже каже «післяплата»). */
function shortPay(name: string) {
  return name.replace(/^Післяплата\s+/i, "").replace(/^Оплата\s+/i, "");
}

