import { useMemo, useRef, useState, type ReactNode } from "react";
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Banknote, BarChart3, CircleCheck, HandCoins, History, TriangleAlert, Upload, Wallet } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api, qs } from "../lib/api";
import { errText, useMeta, useToast } from "../lib/app";
import { date, dt, isoDay, money } from "../lib/format";
import type { Audit, Payment, Payments, Registry, Report as ReportData } from "../lib/types";
import { Empty, Kpi, Spinner , Select } from "../components/ui";

// ================================================================ оплати

export function PaymentsPage() {
  // макет v26 (19): зведення зверху й групи — що оплатили клієнти (позначити отриманим), що чекаємо, де розбіжність, що надійшло (за реєстрами)
  const nav = useNavigate();
  const qc = useQueryClient();
  const toast = useToast();
  const [sel, setSel] = useState<Set<number>>(new Set());
  const [ref, setRef] = useState("");
  const [report, setReport] = useState<Registry | null>(null);
  const [openG, setOpenG] = useState<Record<string, boolean>>({});
  const fileRef = useRef<HTMLInputElement>(null);
  const { data } = useQuery({ queryKey: ["payments", "all"], queryFn: () => api.get<Payments>(`/payments${qs({ status: "" })}`) });
  const receive = useMutation({
    mutationFn: () => api.post<{ done: number }>("/payments/receive", { ids: [...sel], reference: ref }),
    onSuccess: (r) => { toast(`Позначено як отримані: ${r.done}`); setSel(new Set()); setRef(""); qc.invalidateQueries({ queryKey: ["payments"] }); },
    onError: (e) => toast(errText(e), "error"),
  });
  const upload = useMutation({
    mutationFn: (file: File) => { const fd = new FormData(); fd.append("file", file); return api.post<Registry>("/payments/import", fd); },
    onSuccess: (r) => {
      setReport(r); qc.invalidateQueries({ queryKey: ["payments"] });
      toast(`Зараховано: ${r.matched.length}, розбіжність: ${r.mismatch.length}, не знайдено: ${r.not_found.length}`, r.mismatch.length || r.not_found.length ? "warn" : "ok");
    },
    onError: (e) => toast(errText(e), "error"),
  });
  const items = data?.items ?? [];
  const sum = (xs: Payment[], f: (p: Payment) => number = (p) => p.amount) => xs.reduce((a, p) => a + f(p), 0);
  const weekAgo = Date.now() - 7 * 86400_000;
  const collected = items.filter((p) => p.status === "collected");
  const expected = items.filter((p) => p.status === "expected");
  const received = items.filter((p) => p.status === "received");
  const mismatch = received.filter((p) => p.received_amount != null && Math.abs(p.received_amount - p.amount) > 0.009);
  const week = received.filter((p) => p.received_at && new Date(p.received_at).getTime() >= weekAgo);
  // надійшло — групами за реєстром / приміткою виписки, без неї — за днем зарахування
  const regs = new Map<string, Payment[]>();
  received.filter((p) => !mismatch.includes(p)).forEach((p) => {
    const k = p.reference ? `Реєстр · ${p.reference}` : `Зараховано ${date(p.received_at)}`;
    regs.set(k, [...(regs.get(k) ?? []), p]);
  });
  const ageDays = (iso?: string | null) => (iso ? Math.floor((Date.now() - new Date(iso).getTime()) / 86400_000) : 0);
  const toggle = (id: number) => setSel((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });

  const row = (p: Payment, kind: "collected" | "expected" | "bad" | "ok") => (
    <div key={p.id} className={`py-r${sel.has(p.id) ? " on" : ""}`}>
      {kind === "collected" ? <input type="checkbox" checked={sel.has(p.id)} onChange={() => toggle(p.id)} aria-label={`Вибрати №${p.order_id}`} /> : <span />}
      <button type="button" className="py-no" onClick={() => nav(`/orders/${p.order_id}`)}>№{p.order_id}</button>
      <span className="ell">{p.customer || "—"}</span>
      <span className="mono muted py-ttn">{p.ttn}</span>
      <span className={`py-st ${kind}`}>{kind === "collected" ? `оплачено клієнтом ${date(p.collected_at)}`
        : kind === "expected" ? (ageDays(p.created_at) > 4 ? `у дорозі ${ageDays(p.created_at)} дн` : "чекаємо")
          : kind === "bad" ? "сума не збігається" : `надійшло ${date(p.received_at)}`}</span>
      <b className="num py-sum">{kind === "bad" ? <>{money(p.amount)} → {money(p.received_amount ?? 0)} ₴</> : <>{money(p.amount)} ₴</>}</b>
    </div>
  );
  const group = (key: string, title: string, tone: string, list: Payment[], kind: "collected" | "expected" | "bad" | "ok", total: string, extra?: ReactNode) => {
    if (!list.length) return null;
    const all = openG[key];
    const shown = all ? list : list.slice(0, 5);
    return (
      <section key={key} className="py-g">
        <div className="py-gh"><i style={{ background: tone }} /><b>{title}</b><span className="muted">{list.length}</span><span className="sp" />{extra}<b style={{ color: tone }}>{total}</b></div>
        {shown.map((p) => row(p, kind))}
        {list.length > 5 && <button type="button" className="py-more" onClick={() => setOpenG({ ...openG, [key]: !all })}>{all ? "Згорнути" : `і ще ${list.length - 5}`}</button>}
      </section>
    );
  };
  const allCollected = collected.length > 0 && collected.every((p) => sel.has(p.id));
  return (
    <div className="pay-v2">
      <div className="head"><h1><span className="h-ico"><Wallet size={18} /></span>Оплати</h1>
        <div className="actions">
          <input ref={fileRef} type="file" accept=".csv,.txt" hidden onChange={(e) => { const f = e.target.files?.[0]; if (f) upload.mutate(f); e.target.value = ""; }} />
          <button className="btn" onClick={() => fileRef.current?.click()} disabled={upload.isPending}><Upload size={15} /> Імпорт реєстру НП (CSV)</button>
        </div></div>
      <div className="py-tiles">
        {([[HandCoins, "orange", "Післяплата в дорозі", `${money(sum(expected))} ₴`, `${expected.length} відправлень`],
          [Banknote, "blue", "Оплачено клієнтом — до зарахування", `${money(sum(collected))} ₴`, `${collected.length} відправлень`],
          [CircleCheck, "green", "Надійшло за 7 днів", `${money(sum(week, (p) => p.received_amount ?? p.amount))} ₴`, `${week.length} відправлень`],
          [TriangleAlert, "red", "Розбіжності", String(mismatch.length), mismatch.length ? `на ${money(sum(mismatch, (p) => p.amount - (p.received_amount ?? 0)))} ₴` : "усе збігається"]] as const)
          .map(([I, t, l, v, sub]) => (
            <div key={l} className="py-tile"><span className={`sq ${t}`}><I size={17} /></span><div><small>{l}</small><b>{v}</b><small className="s">{sub}</small></div></div>
          ))}
      </div>
      {report && (
        <div className="card" style={{ marginBottom: 12 }}>
          <div className="card-head"><h2>Результат звірки</h2><button className="btn sm ghost" onClick={() => setReport(null)}>Закрити</button></div>
          {report.mismatch.length > 0 && <><h3>Розбіжність суми ({report.mismatch.length})</h3>
            <table className="t dense"><tbody>{report.mismatch.map((r) => <tr key={r.ttn}><td className="mono">{r.ttn}</td><td><a onClick={() => nav(`/orders/${r.order_id}`)}>№{r.order_id}</a></td><td className="num">очікували {money(r.expected)}</td><td className="num lowstock">отримали {money(r.amount)}</td></tr>)}</tbody></table></>}
          {report.not_found.length > 0 && <><h3>ТТН не знайдено в CRM ({report.not_found.length})</h3><p>{report.not_found.map((r) => r.ttn).join(", ")}</p></>}
          {report.already.length > 0 && <p className="hint">Вже були зараховані раніше: {report.already.length}</p>}
          {!report.mismatch.length && !report.not_found.length && <p>Усі рядки реєстру збіглися з очікуваними сумами.</p>}
        </div>
      )}
      {!data ? <Empty><Spinner /></Empty> : !items.length ? <Empty>Платежів ще немає. Вони з'являються самі, коли відправляється замовлення з післяплатою.</Empty> : (<>
        {group("collected", "Оплачено клієнтом — позначте, коли гроші надійдуть", "#2E6BE6", collected, "collected", `${money(sum(collected))} ₴`,
          <label className="py-all" onClick={(e) => e.stopPropagation()}><input type="checkbox" checked={allCollected} onChange={() => setSel(allCollected ? new Set() : new Set(collected.map((p) => p.id)))} />усі</label>)}
        {group("bad", "Розбіжності", "#DC2626", mismatch, "bad", String(mismatch.length))}
        {group("expected", "Очікуються · у дорозі й на пошті", "#D97706", expected, "expected", `${money(sum(expected))} ₴`)}
        {[...regs.entries()].map(([k, list]) => group(k, k, "#16A34A", list, "ok", `надійшло ${money(sum(list, (p) => p.received_amount ?? p.amount))} ₴`))}
      </>)}
      {sel.size > 0 && (
        <div className="bulkbar py-bulk"><span>Вибрано: <b>{sel.size}</b> на <b>{money(sum(collected.filter((p) => sel.has(p.id))))} ₴</b></span>
          <input value={ref} onChange={(e) => setRef(e.target.value)} placeholder="№ реєстру або виписки" aria-label="Примітка" />
          <button className="btn primary sm" disabled={receive.isPending} onClick={() => receive.mutate()}>Гроші отримано</button>
          <button className="btn quiet sm" onClick={() => setSel(new Set())}>Скасувати</button></div>
      )}
      <p className="hint mt">Платіж створюється сам, коли відправляється замовлення з післяплатою. Трекінг показує «отримано» — платіж переходить в «Оплачено клієнтом». Після імпорту реєстру НП або ручної позначки — «Гроші отримано». Відмови скасовують платіж автоматично.</p>
    </div>
  );
}

// ================================================================ звіти

function presets() {
  const t = new Date(); const d = (n: number) => { const x = new Date(t); x.setDate(x.getDate() - n); return isoDay(x); };
  const ms = new Date(t.getFullYear(), t.getMonth(), 1); const pe = new Date(ms); pe.setDate(0); const ps = new Date(pe.getFullYear(), pe.getMonth(), 1);
  return [["Сьогодні", d(0), d(0)], ["Вчора", d(1), d(1)], ["7 днів", d(6), d(0)], ["30 днів", d(29), d(0)], ["Цей місяць", isoDay(ms), d(0)], ["Минулий місяць", isoDay(ps), isoDay(pe)]];
}

export function ReportsPage() {
  const meta = useMeta();
  const [p, setP] = useState({ date_from: "", date_to: "", dim: "utm_source", manager: "" });
  const { data, isFetching } = useQuery({ queryKey: ["reports", p], queryFn: () => api.get<ReportData>(`/reports${qs(p)}`), placeholderData: (prev) => prev });
  const max = useMemo(() => Math.max(1, ...(data?.days.map((d) => d.leads) ?? [1])), [data]);
  if (!data) return <Empty><Spinner /></Empty>;
  const T = data.total;
  const pct = (v: number) => `${v.toFixed(1)}%`;
  return (
    <div>
      <div className="head"><h1><span className="h-ico"><BarChart3 size={18} /></span>Звіти</h1>{isFetching && <span className="spinner sm" />}</div>
      <div className="filters">
        <input type="date" value={data.date_from} onChange={(e) => setP({ ...p, date_from: e.target.value, date_to: data.date_to })} />
        <input type="date" value={data.date_to} onChange={(e) => setP({ ...p, date_to: e.target.value, date_from: data.date_from })} />
        {meta.user.role === "admin" && <Select value={p.manager} onChange={(e) => setP({ ...p, manager: e.target.value })}><option value="">Усі менеджери</option>{meta.managers.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</Select>}
        <span className="spacer" />
        {presets().map(([n, a, b]) => <button key={n} className={`btn sm ${data.date_from === a && data.date_to === b ? "dark" : ""}`} onClick={() => setP({ ...p, date_from: a, date_to: b })}>{n}</button>)}
      </div>
      <div className="kpis">
        <Kpi label="Заявки" value={T.leads} sub={`унікальних ${T.unique}`} /><Kpi label="Апрув" value={pct(T.approve_rate)} sub={`${T.approved} підтверджено`} />
        <Kpi label="Середній чек" value={`${money(T.avg_check)} ₴`} /><Kpi label="Відправлено" value={T.shipped} />
        <Kpi label="Викуп" value={pct(T.buyout_rate)} sub={`${T.delivered} отримано / ${T.refused} відмов`} />
        <Kpi label="Виручка (викуплені)" value={`${money(T.revenue)} ₴`} /><Kpi label="Валовий прибуток" value={`${money(T.profit)} ₴`} sub="виручка − собівартість" />
      </div>
      <div className="card">
        <div className="card-head"><h2>Заявки по днях</h2><div className="legend"><span><i style={{ background: "#a9c9ec" }} />заявки</span><span><i style={{ background: "var(--accent)" }} />підтверджено</span></div></div>
        <div className="bars">{data.days.map((d) => (
          <div className="b" key={d.day} title={`${d.day.split("-").reverse().slice(0, 2).join(".")}: заявок ${d.leads}, підтверджено ${d.approved}`} style={{ flexDirection: "row", alignItems: "flex-end", gap: 1 }}>
            <span style={{ height: `${(d.leads / max) * 100}%`, flex: 1 }} /><span className="ap" style={{ height: `${(d.approved / max) * 100}%`, flex: 1 }} />
          </div>
        ))}</div>
        <div className="bars-x"><span>{data.date_from.split("-").reverse().slice(0, 2).join(".")}</span><span>{data.date_to.split("-").reverse().slice(0, 2).join(".")}</span></div>
      </div>
      <div className="card flush mt">
        <div style={{ padding: "12px 16px 0" }}><nav className="subnav" style={{ marginBottom: 0 }}>
          {Object.entries(data.dims).filter(([k]) => k !== "manager" || meta.user.role === "admin").map(([k, n]) => <a key={k} className={data.dim === k ? "on" : ""} onClick={() => setP({ ...p, dim: k, date_from: data.date_from, date_to: data.date_to })}>{n}</a>)}
        </nav></div>
        <div className="tablewrap"><table className="t dense">
          <thead><tr><th>{data.dims[data.dim]}</th><th className="num">Заявки</th><th className="num">Унік.</th><th className="num">Апрув</th><th className="num">% апруву</th><th className="num">Сер. чек</th><th className="num">Відпр.</th><th className="num">Отрим.</th><th className="num">Відмови</th><th className="num">% викупу</th><th className="num">Виручка</th><th className="num">Прибуток</th></tr></thead>
          <tbody>{data.groups.map((g) => (
            <tr key={g.name}><td>{g.name}</td><td className="num">{g.leads}</td><td className="num">{g.unique}</td><td className="num">{g.approved}</td><td className="num"><b>{pct(g.approve_rate)}</b></td>
              <td className="num">{money(g.avg_check)}</td><td className="num">{g.shipped}</td><td className="num">{g.delivered}</td><td className="num">{g.refused}</td>
              <td className="num"><b>{pct(g.buyout_rate)}</b></td><td className="num">{money(g.revenue)}</td><td className="num">{money(g.profit)}</td></tr>
          ))}{!data.groups.length && <tr><td colSpan={12}><Empty>Немає даних за період</Empty></td></tr>}</tbody>
          {data.groups.length > 0 && <tfoot><tr><td>Разом</td><td className="num">{T.leads}</td><td className="num">{T.unique}</td><td className="num">{T.approved}</td><td className="num">{pct(T.approve_rate)}</td><td className="num">{money(T.avg_check)}</td><td className="num">{T.shipped}</td><td className="num">{T.delivered}</td><td className="num">{T.refused}</td><td className="num">{pct(T.buyout_rate)}</td><td className="num">{money(T.revenue)}</td><td className="num">{money(T.profit)}</td></tr></tfoot>}
        </table></div>
      </div>
      <div className="card flush mt">
        <div style={{ padding: "14px 16px 4px" }}><h2>Товари (у підтверджених замовленнях)</h2></div>
        <div className="tablewrap"><table className="t dense">
          <thead><tr><th>Товар</th><th className="num">Замовлень</th><th className="num">Штук</th><th className="num">з них допродаж</th><th className="num">Сума</th><th className="num">Собівартість</th><th className="num">Маржа</th></tr></thead>
          <tbody>{data.products.map((r) => (
            <tr key={r.name}><td>{r.name}</td><td className="num">{r.orders}</td><td className="num">{r.qty}</td><td className="num">{r.upsell_qty || ""}</td><td className="num">{money(r.revenue)}</td><td className="num">{money(r.cost)}</td><td className="num">{money(r.revenue - r.cost)}</td></tr>
          ))}{!data.products.length && <tr><td colSpan={7}><Empty>Немає даних</Empty></td></tr>}</tbody>
        </table></div>
      </div>
      <p className="hint mt">Апрув — від унікальних заявок (без дублів). Викуп = отримані / (отримані + відмови). Виручка й прибуток — лише по викуплених замовленнях, без реклами й доставки.</p>
    </div>
  );
}

// ================================================================ журнал дій
const ENTITIES: Record<string, string> = { order: "Замовлення", product: "Товар", purchase: "Закупівля", user: "Користувач", settings: "Налаштування" };

export function AuditPage() {
  const nav = useNavigate();
  const [f, setF] = useState({ entity: "", action: "", date_from: "", date_to: "" });
  const q = useInfiniteQuery({
    queryKey: ["audit", f],
    queryFn: ({ pageParam }) => api.get<Audit>(`/audit${qs({ ...f, before: pageParam || undefined })}`),
    initialPageParam: 0, getNextPageParam: (l) => l.next ?? undefined,
  });
  const rows = q.data?.pages.flatMap((p) => p.items) ?? [];
  const actions = q.data?.pages[0]?.actions ?? {};
  return (
    <div>
      <div className="head"><h1><span className="h-ico"><History size={18} /></span>Журнал дій</h1></div>
      <div className="filters">
        <Select value={f.entity} onChange={(e) => setF({ ...f, entity: e.target.value })}><option value="">Усі об'єкти</option>{Object.entries(ENTITIES).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</Select>
        <Select value={f.action} onChange={(e) => setF({ ...f, action: e.target.value })}><option value="">Усі дії</option>{Object.entries(actions).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</Select>
        <input type="date" value={f.date_from} onChange={(e) => setF({ ...f, date_from: e.target.value })} />
        <input type="date" value={f.date_to} onChange={(e) => setF({ ...f, date_to: e.target.value })} />
      </div>
      <div className="card flush tablewrap"><table className="t dense">
        <thead><tr><th>Час</th><th>Хто</th><th>Об'єкт</th><th>Дія</th><th>Деталі</th></tr></thead>
        <tbody>{rows.map((r) => (
          <tr key={r.id}><td className="nowrap">{dt(r.created_at)}</td><td>{r.user}</td>
            <td className="nowrap">{ENTITIES[r.entity] ?? r.entity} {r.entity === "order" && r.entity_id ? <a onClick={() => nav(`/orders/${r.entity_id}`)}>№{r.entity_id}</a> : r.entity_id ? `№${r.entity_id}` : ""}</td>
            <td>{r.action_name}</td><td style={{ maxWidth: 560 }}>{r.details}</td></tr>
        ))}{q.isLoading && <tr><td colSpan={5}><Empty><Spinner /></Empty></td></tr>}</tbody>
      </table>
        {q.hasNextPage && <div className="pager"><span /><button className="btn sm" onClick={() => q.fetchNextPage()} disabled={q.isFetchingNextPage}>Показати ще</button></div>}
      </div>
    </div>
  );
}
