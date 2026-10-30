import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ChevronRight, CircleAlert, Clock, ClipboardList, Lock, PackagePlus, Plus, Search, ShoppingCart, Truck, Wallet, X } from "lucide-react";
import { api, qs } from "../lib/api";
import { errText, useDebounced, useMeta, useToast } from "../lib/app";
import { date, dt, money, num } from "../lib/format";
import type { Move, Product, Purchase, Supplier, Warehouse } from "../lib/types";
import { Badge, Button, DenseTable, Empty, Field, MobileActs, Modal, RoundButton, Segmented, Spinner, Tabs, Window, type DenseCol } from "../components/ui";


export function MovesTable({ moves, compact = false }: { moves: Move[]; compact?: boolean }) {
  return (
    <div className="card flush tablewrap">
      <table className="t dense">
        <thead><tr><th>Дата</th>{!compact && <th>Товар</th>}<th>Операція</th><th className="num">Склад</th><th className="num">Резерв</th>{!compact && <th>Хто</th>}</tr></thead>
        <tbody>
          {moves.map((m) => (
            <tr key={m.id}><td className="nowrap">{dt(m.created_at, true)}</td>{!compact && <td>{m.product}</td>}
              <td>{m.kind_name} {m.order_id && <span className="muted">№{m.order_id}</span>}{m.purchase_id && <span className="muted"> закупівля №{m.purchase_id}</span>}{m.comment && <span className="sub">{m.comment}</span>}</td>
              <td className="num">{m.stock_delta ? (m.stock_delta > 0 ? `+${m.stock_delta}` : m.stock_delta) : ""}</td>
              <td className="num">{m.reserved_delta ? (m.reserved_delta > 0 ? `+${m.reserved_delta}` : m.reserved_delta) : ""}</td>
              {!compact && <td>{m.user}</td>}</tr>
          ))}
          {!moves.length && <tr><td colSpan={6}><Empty>Руху ще не було</Empty></td></tr>}
        </tbody>
      </table>
    </div>
  );
}

// ================================================================ склад (UI-DESIGN §8, макет 11)
type StockRow = { product_id: number; variant_id: number | null; product: string; variant: string; sku: string; stock: number; reserved: number;
  available: number; min_stock: number; sold_30: number; daily: number; days_left: number | null; dead: boolean; cost: number; photo: string | null };
type StockData = { rows: StockRow[]; value: number; reserved_units: number; reserved_value: number; low: number; out: number; dead: number; all: number; moves_today: Move[] };

function leftText(r: StockRow) {
  if (r.available <= 0) return { t: "закінчились", c: "bad" };
  if (r.days_left == null) return { t: r.dead ? "неліквід" : "не продається", c: "muted" };
  const d = r.days_left;
  if (d > 365) return { t: "понад рік", c: "ok" };
  const word = d === 1 ? "день" : d >= 2 && d <= 4 ? "дні" : "днів";
  return { t: `через ${d} ${word}`, c: d <= 3 ? "bad" : d <= 10 ? "warn" : "ok" };
}

export function WarehousePage() {
  const nav = useNavigate();
  const [sp, setSp] = useSearchParams();
  const filter = sp.get("filter") || "all";
  const [q, setQ] = useState("");
  const dq = useDebounced(q, 250);
  const [adjust, setAdjust] = useState<{ product_id: string; variant_id: string } | null>(sp.get("product") ? { product_id: sp.get("product")!, variant_id: "" } : null);
  const [allMoves, setAllMoves] = useState(false);
  const { data, isLoading } = useQuery({ queryKey: ["warehouse", "stock", filter, dq], queryFn: () => api.get<StockData>(`/stock${qs({ filter, q: dq || undefined })}`) });
  const rows = data?.rows ?? [];
  const toBuy = rows.filter((r) => r.available > 0 && r.days_left != null && r.days_left <= 7);
  const buyValue = toBuy.reduce((s, r) => s + r.cost * Math.max(0, Math.ceil(r.daily * 30) - r.available), 0);
  const COLS: DenseCol<StockRow>[] = [
    { key: "name", mobile: "title", label: "Товар · варіант", width: "minmax(200px, 2fr)", title: (r) => `${r.product}${r.variant ? ` · ${r.variant}` : ""}`, render: (r) => (
      <span className="st-name"><span className="ell">{r.product}</span><small className="ell muted">{[r.variant, r.sku].filter(Boolean).join(" · ") || "—"}</small></span>
    ) },
    { key: "stock", mobile: "sub", label: "Залишок", width: "74px", align: "right", render: (r) => <span className="num">{r.stock}</span> },
    { key: "res", mobile: "hide", label: "Резерв", width: "64px", align: "right", render: (r) => <span className="num muted">{r.reserved}</span> },
    { key: "av", mobile: "end", label: "Доступно", width: "76px", align: "right", render: (r) => <b className={`num ${r.available <= 0 ? "t-bad" : ""}`}>{r.available}</b> },
    { key: "day", mobile: "hide", label: "Шт/день", width: "66px", align: "right", render: (r) => <span className="num muted">{r.daily ? r.daily.toLocaleString("uk-UA") : "—"}</span> },
    { key: "fc", mobile: "sub", label: "Прогноз", width: "minmax(140px, 1fr)", render: (r) => { const l = leftText(r); return <span className={`st-fc ${l.c}`}>{l.c === "ok" ? <Check size={13} /> : l.c === "muted" ? null : <CircleAlert size={13} />}{l.t}</span>; } },
    { key: "buy", mobile: "sub", label: "", width: "96px", align: "right", render: (r) => (r.available <= 0 || (r.days_left != null && r.days_left <= 10))
      ? <Button size={30} onClick={() => nav(`/purchases?new=1&product=${r.product_id}`)}>Закупити</Button> : null },
  ];
  // телефон (мобільна v2): назва·артикул і «доступно» праворуч; прогноз пігулкою, резерв, «Закупити»
  const FC: Record<string, string> = { bad: "#DC2626", warn: "#D97706", ok: "#16A34A", muted: "#7C7B76" };
  const mobileCard = (r: StockRow) => {
    const l = leftText(r);
    const buy = r.available <= 0 || (r.days_left != null && r.days_left <= 10);
    return (<>
      <div className="ms-head">
        <div><b>{r.product}</b><small>{[r.variant, r.sku].filter(Boolean).join(" · ") || "—"}</small></div>
        <div className="ms-av"><b className={r.available <= 0 ? "t-bad" : ""}>{r.available}</b><br /><small>доступно</small></div>
      </div>
      <div className="ms-foot">
        <span className="pill" style={{ ["--c" as string]: FC[l.c] }}><Clock size={12} />{l.t}</span>
        <span>резерв {r.reserved}</span>
        {buy && <button type="button" className="buy" onClick={() => nav(`/purchases?new=1&product=${r.product_id}`)}>Закупити</button>}
      </div>
    </>);
  };
  return (
    <div className="page-stock">
      <MobileActs>
        <RoundButton icon={ClipboardList} label="Інвентаризація" onClick={() => setAdjust({ product_id: "", variant_id: "" })} />
        <RoundButton icon={PackagePlus} label="Прийняти товар" primary onClick={() => nav("/purchases?new=1")} />
      </MobileActs>
      <div className="list-head st-head">
        <div><div className="crumbs muted">Склад · Залишки</div><h1>Склад</h1></div>
        <div className="list-acts">
          <Button icon={ClipboardList} onClick={() => setAdjust({ product_id: "", variant_id: "" })}>Інвентаризація</Button>
          <Button icon={PackagePlus} onClick={() => nav("/purchases?new=1")}>Прийняти товар</Button>
        </div>
      </div>
      <div className="st-tiles">
        <div className="tile"><span className="lbl"><Wallet size={14} />Вартість залишку</span><b className="big-num">{money(data?.value ?? 0)} ₴</b><small>за собівартістю · {rows.reduce((s, r) => s + Math.max(r.stock, 0), 0)} шт</small></div>
        <div className="tile"><span className="lbl"><Lock size={14} />У резерві</span><b className="big-num">{data?.reserved_units ?? 0} шт</b><small>{money(data?.reserved_value ?? 0)} ₴ у прийнятих замовленнях</small></div>
        <button type="button" className="tile warn" onClick={() => setSp({ filter: "low" })}><span className="lbl"><CircleAlert size={14} />Закінчуються за тиждень</span><b className="big-num">{data?.low ?? 0}</b><small>варіантів · закупити на ≈ {money(buyValue)} ₴</small></button>
        <button type="button" className="tile" onClick={() => setSp({ filter: "out" })}><span className="lbl"><X size={14} />Немає в наявності</span><b className="big-num">{data?.out ?? 0}</b><small>товарів з нульовим доступним залишком</small></button>
      </div>
      <div className="st-grid">
        <div className="st-main">
          <Tabs className="m-only st-mtabs" label="Фільтр складу" value={filter} onChange={(k) => setSp(k === "all" ? {} : { filter: k })}
            items={[{ key: "all", label: "Усі", count: data?.all ?? null }, { key: "low", label: "Закінчуються", count: data?.low ?? null, color: "#D97706" },
              { key: "out", label: "Немає", count: data?.out ?? null, color: "#DC2626" }, { key: "dead", label: "Неліквід", count: data?.dead ?? null, color: "#7C7B76" }]} />
          <div className="chips-row d-only">
            <Segmented label="Фільтр складу" value={filter} onChange={(k) => setSp(k === "all" ? {} : { filter: k })}
              items={[{ key: "all", label: "Усі" }, { key: "low", label: "Закінчуються" }, { key: "out", label: "Немає" }, { key: "dead", label: "Неліквід" }]} />
            <label className="list-search"><Search size={15} aria-hidden /><input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Товар або артикул" aria-label="Пошук на складі" /></label>
          </div>
          <DenseTable<StockRow> label="Залишки" rows={rows} cols={COLS} rowKey={(r) => r.product_id * 100000 + (r.variant_id ?? 0)} isLoading={isLoading}
            onOpen={(r) => setAdjust({ product_id: String(r.product_id), variant_id: r.variant_id ? String(r.variant_id) : "" })}
            mobileCard={mobileCard}
            empty={<div className="empty-state"><p>{filter === "all" ? "Товарів ще немає" : "Тут порожньо — і це добре"}</p></div>} className="st-table" />
        </div>
        <aside className="block st-moves">
          <div className="block-head"><h2>Рухи сьогодні</h2><div className="acts"><button className="link-btn" onClick={() => setAllMoves(true)}>Усі рухи <ChevronRight size={13} /></button></div></div>
          {(data?.moves_today ?? []).map((m) => (
            <div key={m.id} className="mv">
              <b className={`mv-d ${m.stock_delta > 0 ? "plus" : m.stock_delta < 0 && m.kind !== "ship" ? "minus" : ""}`}>
                {m.stock_delta ? (m.stock_delta > 0 ? `+${m.stock_delta}` : m.stock_delta) : `резерв ${m.reserved_delta > 0 ? m.reserved_delta : m.reserved_delta}`}</b>
              <div className="mv-t"><span>{m.kind_name}{m.order_id ? ` · №${m.order_id}` : ""}{m.purchase_id ? ` · закупівля №${m.purchase_id}` : ""}</span><small className="muted">{m.product}{m.comment ? ` · ${m.comment}` : ""}</small></div>
              <span className="muted num mv-at">{m.created_at ? new Date(m.created_at).toLocaleTimeString("uk-UA", { hour: "2-digit", minute: "2-digit" }) : ""}</span>
            </div>
          ))}
          {data && !data.moves_today.length && <p className="hint">Сьогодні руху ще не було.</p>}
        </aside>
      </div>
      {adjust && <AdjustWindow initial={adjust} onClose={() => { setAdjust(null); if (sp.get("product")) setSp({}); }} />}
      {allMoves && <AllMoves onClose={() => setAllMoves(false)} />}
    </div>
  );
}

function AdjustWindow({ initial, onClose }: { initial: { product_id: string; variant_id: string }; onClose: () => void }) {
  const qc = useQueryClient();
  const toast = useToast();
  const meta = useMeta();
  const [adj, setAdj] = useState({ ...initial, mode: "set", qty: "", comment: "" });
  const adjust = useMutation({
    mutationFn: () => api.post<Product>("/warehouse/adjust", { ...adj, variant_id: adj.variant_id ? Number(adj.variant_id) : null }),
    onSuccess: (p) => { toast(`Залишок «${p.name}»: ${p.stock}`); qc.invalidateQueries({ queryKey: ["warehouse"] }); qc.invalidateQueries({ queryKey: ["products"] }); onClose(); },
    onError: (e) => toast(errText(e), "error"),
  });
  const vs = meta.products.find((p) => String(p.id) === adj.product_id)?.variants?.filter((x) => x.active) ?? [];
  return (
    <Window size="sm" onClose={onClose} title="Прийняти / списати · інвентаризація"
      footer={<><span className="spacer" /><Button onClick={onClose}>Скасувати</Button><Button variant="primary" disabled={adjust.isPending || !adj.product_id || !adj.qty} onClick={() => adjust.mutate()}>Застосувати</Button></>}>
      <form className="form" onSubmit={(e) => { e.preventDefault(); adjust.mutate(); }}>
        <Field label="Товар"><select value={adj.product_id} onChange={(e) => setAdj({ ...adj, product_id: e.target.value, variant_id: "" })} required autoFocus>
          <option value="">Оберіть товар…</option>{meta.products.map((p) => <option key={p.id} value={p.id}>{p.name} (зараз {p.stock})</option>)}</select></Field>
        {vs.length > 0 && <Field label="Варіант"><select value={adj.variant_id} onChange={(e) => setAdj({ ...adj, variant_id: e.target.value })} required>
          <option value="">Оберіть варіант…</option>{vs.map((x) => <option key={x.id} value={x.id}>{x.name} (зараз {x.stock})</option>)}</select></Field>}
        <div className="cols">
          <Field label="Режим"><select value={adj.mode} onChange={(e) => setAdj({ ...adj, mode: e.target.value })}><option value="set">Фактичний залишок</option><option value="delta">Додати / відняти (+5, −2)</option></select></Field>
          <Field label="Кількість"><input value={adj.qty} onChange={(e) => setAdj({ ...adj, qty: e.target.value })} required inputMode="numeric" /></Field>
        </div>
        <Field label="Причина"><input value={adj.comment} onChange={(e) => setAdj({ ...adj, comment: e.target.value })} placeholder="Інвентаризація, брак, пересорт…" /></Field>
      </form>
    </Window>
  );
}

function AllMoves({ onClose }: { onClose: () => void }) {
  const [kind, setKind] = useState("");
  const { data } = useQuery({ queryKey: ["warehouse", "moves", kind], queryFn: () => api.get<Warehouse>(`/warehouse${qs({ kind })}`) });
  return (
    <Window size="lg" onClose={onClose} title="Рух товарів"
      actions={data && <select style={{ width: "auto" }} value={kind} onChange={(e) => setKind(e.target.value)} aria-label="Операція"><option value="">Усі операції</option>{Object.entries(data.kinds).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select>}>
      {data ? <MovesTable moves={data.moves} /> : <Empty><Spinner /></Empty>}
    </Window>
  );
}

// ================================================================ закупівлі
const PSTATUS: Record<string, [string, "" | "ok" | "bad" | "info"]> = { draft: ["Чернетка", ""], ordered: ["Замовлено", "info"], received: ["Оприбутковано", "ok"], cancelled: ["Скасовано", "bad"] };

export function PurchasesPage() {
  const [sp, setSp] = useSearchParams();
  const [status, setStatus] = useState("");
  const [open, setOpen] = useState<number | "new" | null>(sp.get("new") ? "new" : null);
  const preset = sp.get("product") || "";
  const [suppliers, setSuppliers] = useState(false);
  const { data } = useQuery({ queryKey: ["purchases", status], queryFn: () => api.get<Purchase[]>(`/purchases${qs({ status })}`) });
  return (
    <div>
      <div className="head"><h1><span className="h-ico"><ShoppingCart size={18} /></span>Закупівлі</h1>
        <div className="actions"><button className="btn ghost" onClick={() => setSuppliers(true)}><Truck size={15} /> Постачальники</button>
          <button className="btn primary" onClick={() => setOpen("new")}><Plus size={15} /> Закупівля</button></div></div>
      <div className="tabs">
        <a className={!status ? "on" : ""} onClick={() => setStatus("")}>Усі</a>
        {Object.entries(PSTATUS).map(([k, [n]]) => <a key={k} className={status === k ? "on" : ""} onClick={() => setStatus(k)}>{n}</a>)}
      </div>
      <div className="card flush tablewrap">
        <table className="t dense">
          <thead><tr><th>№</th><th>Дата</th><th>Постачальник</th><th>Товари</th><th className="num">Сума</th><th>Статус</th></tr></thead>
          <tbody>
            {data?.map((p) => (
              <tr key={p.id} className="clickable" onClick={() => setOpen(p.id)}>
                <td><b>{p.id}</b></td><td>{date(p.created_at)}{p.received_at && <span className="sub">отримано {date(p.received_at)}</span>}</td>
                <td>{p.supplier || "—"}</td><td className="ell">{p.items.map((i) => `${i.name} ×${i.qty}`).join(", ")}</td>
                <td className="num">{money(p.total)}</td><td><Badge kind={PSTATUS[p.status]?.[1]}>{PSTATUS[p.status]?.[0]}</Badge></td></tr>
            ))}
            {data && !data.length && <tr><td colSpan={6}><Empty>Закупівель ще немає</Empty></td></tr>}
          </tbody>
        </table>
      </div>
      {open !== null && <PurchaseModal id={open} product={open === "new" ? preset : ""} onClose={() => { setOpen(null); if (sp.get("new")) setSp({}); }} />}
      {suppliers && <SuppliersModal onClose={() => setSuppliers(false)} />}
    </div>
  );
}

function PurchaseModal({ id, onClose, product = "" }: { id: number | "new"; onClose: () => void; product?: string }) {
  const meta = useMeta();
  const qc = useQueryClient();
  const toast = useToast();
  const isNew = id === "new";
  const { data } = useQuery({ queryKey: ["purchases", "one", id], queryFn: () => api.get<Purchase>(`/purchases/${id}`), enabled: !isNew });
  const { data: sups = [] } = useQuery({ queryKey: ["suppliers"], queryFn: () => api.get<Supplier[]>("/suppliers") });
  const [draft, setDraft] = useState<{ supplier_id: string; comment: string; items: { product_id: string; qty: string; cost: string }[] } | null>(null);
  const cur = draft ?? (data ? { supplier_id: String(data.supplier_id ?? ""), comment: data.comment, items: data.items.map((i) => ({ product_id: String(i.product_id), qty: String(i.qty), cost: String(i.cost) })) }
    : { supplier_id: "", comment: "", items: [{ product_id: product, qty: "1", cost: product ? String(meta.products.find((p) => String(p.id) === product)?.cost || "") : "" }] });
  const editable = isNew || (data && (data.status === "draft" || data.status === "ordered"));
  const total = cur.items.reduce((s, i) => s + num(i.qty) * num(i.cost), 0);
  const productsById = useMemo(() => Object.fromEntries(meta.products.map((p) => [String(p.id), p])), [meta.products]);
  const run = useMutation({
    mutationFn: (then: string) => isNew ? api.post<Purchase>("/purchases", { ...cur, then }) : api.patch<Purchase>(`/purchases/${id}`, { ...cur, then }),
    onSuccess: (_p, then) => {
      toast(then === "receive" ? "Товар оприбутковано, залишки оновлено" : then === "cancel" ? "Закупівлю скасовано" : "Збережено");
      qc.invalidateQueries({ queryKey: ["purchases"] }); qc.invalidateQueries({ queryKey: ["products"] }); qc.invalidateQueries({ queryKey: ["warehouse"] }); qc.invalidateQueries({ queryKey: ["meta"] });
      onClose();
    },
    onError: (e) => toast(errText(e), "error"),
  });
  const setItem = (i: number, patch: Partial<{ product_id: string; qty: string; cost: string }>) => {
    const items = cur.items.map((x, j) => (j === i ? { ...x, ...patch } : x));
    if (patch.product_id && !items[i].cost) items[i].cost = String(productsById[patch.product_id]?.cost || "");
    setDraft({ ...cur, items });
  };
  if (!isNew && !data) return <Modal onClose={onClose} size="lg"><Empty><Spinner /></Empty></Modal>;
  return (
    <Modal onClose={onClose} size="lg" title={isNew ? "Нова закупівля" : <>Закупівля №{id} <Badge kind={PSTATUS[data!.status]?.[1]}>{PSTATUS[data!.status]?.[0]}</Badge></>}>
      <fieldset disabled={!editable} className="form" style={{ border: 0, padding: 0, margin: 0 }}>
        <div className="cols">
          <Field label="Постачальник"><select value={cur.supplier_id} onChange={(e) => setDraft({ ...cur, supplier_id: e.target.value })}><option value="">—</option>{sups.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select></Field>
          <Field label="Коментар"><input value={cur.comment} onChange={(e) => setDraft({ ...cur, comment: e.target.value })} /></Field>
        </div>
        <table className="t items">
          <thead><tr><th>Товар</th><th className="num">К-сть</th><th className="num">Ціна закупівлі</th><th className="num">Сума</th><th /></tr></thead>
          <tbody>{cur.items.map((it, i) => (
            <tr key={i}>
              <td><select value={it.product_id} onChange={(e) => setItem(i, { product_id: e.target.value })}><option value="">Оберіть…</option>{meta.products.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></td>
              <td className="qty num"><input type="number" min={1} value={it.qty} onChange={(e) => setItem(i, { qty: e.target.value })} /></td>
              <td className="price num"><input value={it.cost} onChange={(e) => setItem(i, { cost: e.target.value })} inputMode="decimal" /></td>
              <td className="num">{money(num(it.qty) * num(it.cost), true)}</td>
              <td><button type="button" className="x" onClick={() => setDraft({ ...cur, items: cur.items.filter((_, j) => j !== i) })}>×</button></td>
            </tr>
          ))}</tbody>
          <tfoot><tr><td colSpan={3}>Разом</td><td className="num">{money(total, true)}</td><td /></tr></tfoot>
        </table>
        {editable && <>
          <button type="button" className="btn sm" onClick={() => setDraft({ ...cur, items: [...cur.items, { product_id: "", qty: "1", cost: "" }] })}><Plus size={14} /> Рядок</button>
          <div className="form-actions">
            <button className="btn" onClick={() => run.mutate("save")}>Зберегти</button>
            {(isNew || data?.status === "draft") && <button className="btn" onClick={() => run.mutate("ordered")}>Позначити «Замовлено»</button>}
            <button className="btn primary" onClick={() => { if (window.confirm("Оприбуткувати товар? Залишки на складі збільшаться.")) run.mutate("receive"); }}>Оприбуткувати на склад</button>
            {!isNew && <><span className="spacer" /><button className="btn danger" onClick={() => { if (window.confirm("Скасувати закупівлю?")) run.mutate("cancel"); }}>Скасувати</button></>}
          </div>
        </>}
      </fieldset>
    </Modal>
  );
}

function SuppliersModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const toast = useToast();
  const { data = [] } = useQuery({ queryKey: ["suppliers"], queryFn: () => api.get<Supplier[]>("/suppliers") });
  const [nw, setNw] = useState({ name: "", phone: "", comment: "" });
  const save = useMutation({
    mutationFn: (s: Partial<Supplier>) => api.post<Supplier>("/suppliers", s),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["suppliers"] }); toast("Збережено"); setNw({ name: "", phone: "", comment: "" }); },
    onError: (e) => toast(errText(e), "error"),
  });
  return (
    <Modal onClose={onClose} size="md" title="Постачальники">
      <div className="stack">
        {data.map((s) => <SupplierRow key={s.id} s={s} onSave={(x) => save.mutate(x)} />)}
        <form className="row" onSubmit={(e) => { e.preventDefault(); save.mutate(nw); }}>
          <input placeholder="Назва нового постачальника" value={nw.name} onChange={(e) => setNw({ ...nw, name: e.target.value })} required style={{ flex: 2 }} />
          <input placeholder="Телефон" value={nw.phone} onChange={(e) => setNw({ ...nw, phone: e.target.value })} style={{ flex: 1 }} />
          <button className="btn primary">Додати</button>
        </form>
      </div>
    </Modal>
  );
}

function SupplierRow({ s, onSave }: { s: Supplier; onSave: (s: Supplier) => void }) {
  const [v, setV] = useState(s);
  return (
    <form className="row" onSubmit={(e) => { e.preventDefault(); onSave(v); }}>
      <input value={v.name} onChange={(e) => setV({ ...v, name: e.target.value })} style={{ flex: 2 }} />
      <input value={v.phone} onChange={(e) => setV({ ...v, phone: e.target.value })} style={{ flex: 1 }} />
      <input value={v.comment} onChange={(e) => setV({ ...v, comment: e.target.value })} placeholder="Коментар" style={{ flex: 2 }} />
      <button className="btn sm">Зберегти</button>
    </form>
  );
}
